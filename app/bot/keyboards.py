"""Inline keyboards used by the Telegram bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import Settings


def storefront_keyboard(settings: Settings) -> InlineKeyboardMarkup:
    """Keyboard with a web_app button that opens the Mini App storefront."""
    if settings.webapp_url:
        # Real deployment: WebAppInfo requires an HTTPS URL.
        button = InlineKeyboardButton(
            text="🛍 Открыть витрину",
            web_app=WebAppInfo(url=settings.webapp_url),
        )
    else:
        # Local development without a public URL — open the site in a browser.
        button = InlineKeyboardButton(
            text="🌐 Открыть витрину в браузере",
            url=f"http://localhost:{settings.port}/",
        )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


def admin_refresh_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for the manager: refresh the list of recent orders."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить заказы", callback_data="admin:orders"
                )
            ]
        ]
    )