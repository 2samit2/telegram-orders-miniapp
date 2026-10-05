"""FastAPI routers: REST API (/api) and request helpers."""

import asyncio
import hashlib
import hmac
import html
import json
import logging
import urllib.parse
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.bot.handlers import format_order_for_admin
from app.config import Settings
from app.database.db import Database
from app.models import OrderCreate, OrderItemOut, Product

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api", tags=["api"])


def get_db(request: Request) -> Database:
    """Retrieve the shared Database instance from app.state."""
    return request.app.state.db


def get_bot(request: Request) -> Bot:
    """Retrieve the shared Bot instance from app.state."""
    return request.app.state.bot


def get_settings_dep(request: Request) -> Settings:
    """Retrieve the shared Settings instance from app.state."""
    return request.app.state.settings


def verify_init_data(init_data: str, bot_token: str) -> dict[str, str] | None:
    """Validate Telegram WebApp initData signature (HMAC-SHA256).

    Returns the parsed key-value pairs on success, or None when the
    signature is invalid / the payload is malformed.
    """
    try:
        pairs = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = pairs.pop("hash", "")
        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{key}={value}" for key, value in sorted(pairs.items())
        )
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None
        return pairs
    except Exception:  # noqa: BLE001 — any parse failure means "untrusted"
        return None


@api_router.get("/products")
async def list_products(db: Database = Depends(get_db)) -> list[Product]:
    """Return the full catalogue (used by the Mini App)."""
    return await db.get_products()


@api_router.post("/order")
async def create_order(
    payload: OrderCreate,
    request: Request,
    db: Database = Depends(get_db),
    bot: Bot = Depends(get_bot),
    settings: Settings = Depends(get_settings_dep),
) -> JSONResponse:
    """Accept an order, store it in SQLite and notify the manager chat."""
    # ------------------------------------------------------- identify the client
    user_id: int | None = None
    user_name = payload.guest_name.strip() or "Гость"
    username = ""

    init_data = request.headers.get("X-Init-Data", "")
    if init_data and "TEST_TOKEN" not in settings.bot_token:
        pairs = verify_init_data(init_data, settings.bot_token)
        if pairs is None:
            raise HTTPException(status_code=403, detail="Невалидная подпись initData")
        user_raw = json.loads(pairs.get("user", "{}"))
        user_id = user_raw.get("id")
        if not payload.guest_name.strip():
            user_name = user_raw.get("first_name", "") or "Клиент"
        username = user_raw.get("username", "") or ""

    # ------------------------------------------------------ recompute the total
    # Trust server-side prices: fetch products from the DB by id and rebuild
    # order items so a tampered client cannot change the real price.
    db_products = {p.id: p for p in await db.get_products()}
    items_out: list[OrderItemOut] = []
    for item in payload.items:
        product = db_products.get(item.product_id)
        if product is None:
            raise HTTPException(
                status_code=400, detail=f"Товар с id={item.product_id} не найден"
            )
        items_out.append(
            OrderItemOut(
                product_id=product.id,
                title=product.title,
                price=product.price,
                quantity=item.quantity,
            )
        )

    total_price = round(sum(i.price * i.quantity for i in items_out), 2)
    address = html.escape(payload.address.strip())
    comment = html.escape(payload.comment.strip())
    safe_user_name = html.escape(user_name.strip() or "Гость")

    # ------------------------------------------------------------- persist order
    try:
        order_id = await db.create_order(
            user_id=user_id,
            user_name=safe_user_name,
            username=username,
            items=items_out,
            total_price=total_price,
            address=address,
            comment=comment,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to store order")
        raise HTTPException(
            status_code=500, detail="Не удалось сохранить заказ"
        ) from exc

    # ------------------------------------------------------------ notify manager
    order_record = {
        "id": order_id,
        "user_id": user_id,
        "user_name": safe_user_name,
        "username": username,
        "items_json": json.dumps(
            [i.model_dump() for i in items_out], ensure_ascii=False
        ),
        "total_price": total_price,
        "address": address,
        "comment": comment,
        "phone_or_table": "",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    notification_sent = False
    if settings.admin_id and "TEST_TOKEN" not in settings.bot_token:
        try:
            await bot.send_message(
                chat_id=settings.admin_id,
                text="🆕 <b>Новый заказ!</b>\n\n" + format_order_for_admin(order_record),
                disable_web_page_preview=True,
            )
            notification_sent = True
        except (TelegramAPIError, asyncio.CancelledError) as exc:
            logger.error("Failed to notify admin %s: %s", settings.admin_id, exc)

    logger.info(
        "Order #%d stored (total %.2f RUB, items=%d, admin_notified=%s)",
        order_id,
        total_price,
        len(items_out),
        notification_sent,
    )

    return JSONResponse(
        status_code=201,
        content={
            "ok": True,
            "order_id": order_id,
            "total_price": total_price,
            "admin_notified": notification_sent,
        },
    )