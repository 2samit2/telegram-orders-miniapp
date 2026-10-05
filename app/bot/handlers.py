"""aiogram 3.x handlers: /start, /admin and admin callbacks."""

import json
import logging
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import admin_refresh_keyboard, storefront_keyboard
from app.config import Settings
from app.database.db import Database

logger = logging.getLogger(__name__)

router = Router(name="main")


def format_order_for_admin(order: dict) -> str:
    """Render one order as a formatted Telegram message block."""
    items = json.loads(order["items_json"])
    items_lines = "\n".join(
        f"  • {item['title']} × {item['quantity']} — "
        f"{item['price'] * item['quantity']:.0f} ₽"
        for item in items
    )
    username_part = f"@{order['username']}" if order.get("username") else "нет username"
    created = datetime.fromisoformat(order["created_at"]).strftime("%d.%m.%Y %H:%M")
    phone_part = (
        f"📞 Телефон/столик: {order['phone_or_table']}\n"
        if order.get("phone_or_table")
        else ""
    )
    comment_part = (
        f"💬 Комментарий: {order['comment']}\n" if order.get("comment") else ""
    )
    return (
        f"🧾 <b>Заказ №{order['id']}</b>\n"
        f"👤 Клиент: {order['user_name']} ({username_part})\n"
        f"{phone_part}"
        f"📍 Адрес/столик: {order['address']}\n"
        f"{comment_part}"
        f"🛒 <b>Состав заказа:</b>\n{items_lines}\n"
        f"💰 <b>Итого: {order['total_price']:.0f} ₽</b>\n"
        f"🕒 {created}"
    )


@router.message(CommandStart())
async def cmd_start(message: Message, settings: Settings) -> None:
    """Welcome message with a button that opens the Web App."""
    first_name = message.from_user.first_name if message.from_user else "друг"
    await message.answer(
        f"☕ <b>Привет, {first_name}!</b>\n\n"
        f"Добро пожаловать в <b>Artisan Coffee &amp; Bakery</b> — небольшую "
        f"кофейню, где каждый заказ готовится с любовью.\n\n"
        "🍫 Свежая выпечка каждое утро\n"
        "☕ Спешелти-обжарка каждую неделю\n\n"
        "Нажмите кнопку ниже, чтобы открыть витрину, собрать корзину "
        "и оформить заказ прямо в Telegram.",
        reply_markup=storefront_keyboard(settings),
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, settings: Settings, db: Database) -> None:
    """Show the 5 most recent orders to the manager."""
    user_id = message.from_user.id if message.from_user else 0
    if settings.admin_id and user_id != settings.admin_id:
        await message.answer("⛔ Эта команда доступна только менеджеру магазина.")
        return

    orders = await db.get_last_orders(limit=5)
    if not orders:
        await message.answer(
            "📭 Заказов пока нет. Как только поступит первый — вы увидите его здесь."
        )
        return

    text = "📊 <b>Последние 5 заказов:</b>\n\n" + "\n\n".join(
        format_order_for_admin(order) for order in orders
    )
    await message.answer(
        text, reply_markup=admin_refresh_keyboard(), disable_web_page_preview=True
    )


@router.callback_query(lambda callback: callback.data == "admin:orders")
async def cb_admin_orders(
    callback: CallbackQuery, settings: Settings, db: Database
) -> None:
    """Refresh the recent-orders list for the manager."""
    if settings.admin_id and callback.from_user.id != settings.admin_id:
        await callback.answer("⛔ Доступно только менеджеру", show_alert=True)
        return

    orders = await db.get_last_orders(limit=5)
    if not orders:
        await callback.answer("📭 Заказов пока нет", show_alert=True)
        return

    text = "📊 <b>Последние 5 заказов:</b>\n\n" + "\n\n".join(
        format_order_for_admin(order) for order in orders
    )
    if callback.message is not None:
        await callback.message.edit_text(
            text, reply_markup=admin_refresh_keyboard()
        )
    await callback.answer("Список обновлён ✅")