"""Application entry point: FastAPI + aiogram polling in one process."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.bot.handlers import router as bot_router
from app.config import get_settings
from app.database import Database, seed_if_empty
from app.web.routes import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")

STATIC_DIR = Path(__file__).resolve().parent / "app" / "static"
if not STATIC_DIR.exists():
    # Running from a different working directory (e.g. Docker WORKDIR).
    STATIC_DIR = Path(__file__).resolve().parent / "static"

settings = get_settings()

db = Database(settings.database_path)
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dispatcher = Dispatcher()
dispatcher.include_router(bot_router)

# Inject settings/db into handlers via the dispatcher's workflow data.
dispatcher["settings"] = settings
dispatcher["db"] = db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: open DB, seed, start polling. Shutdown: stop everything."""
    await db.connect()
    await seed_if_empty(db)

    polling_task: asyncio.Task | None = None
    if settings.bot_token and "TEST_TOKEN" not in settings.bot_token:
        try:
            me = await bot.get_me()
            logger.info("Bot @%s authorised — starting polling", me.username)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Bot token invalid (%s); running in web-only mode", exc)
        else:
            polling_task = asyncio.create_task(_polling(), name="aiogram-polling")

    yield

    if polling_task is not None and not polling_task.done():
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    await bot.session.close()
    await db.close()


async def _polling() -> None:
    """Long-polling loop for Telegram updates (no webhook needed)."""
    try:
        await dispatcher.start_polling(
            bot,
            handle_signals=False,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    except asyncio.CancelledError:
        logger.info("Polling cancelled")
        raise


app = FastAPI(title=settings.app_title, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org", "https://telegram.org"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(api_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def serve_web_app() -> FileResponse:
    """Serve the Mini App single page."""
    return FileResponse(STATIC_DIR / "index.html")


app.state.db = db
app.state.bot = bot
app.state.settings = settings


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )