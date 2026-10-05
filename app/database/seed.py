"""Automatic seeding of the catalogue with demo products."""

import logging

from app.database.db import Database

logger = logging.getLogger(__name__)

SEED_PRODUCTS: list[dict[str, str | float]] = [
    # ---------------- coffee ----------------
    {
        "title": "Капучино",
        "description": "Двойной эспрессо из обжарки недели и бархатистое молоко.",
        "price": 260.0,
        "category": "coffee",
        "image_url": "☕",
    },
    {
        "title": "Латте «Ванильный»",
        "description": "Мягкий латте с натуральной ванилью и молочной пенкой.",
        "price": 290.0,
        "category": "coffee",
        "image_url": "🥛",
    },
    {
        "title": "Фильтр-кофе V60",
        "description": "Альтернативная заварка: Эфиопия, ноты цитруса и жасмина.",
        "price": 320.0,
        "category": "coffee",
        "image_url": "🫖",
    },
    {
        "title": "Эспрессо",
        "description": "Классический шот из смеси 80% арабики и 20% робусты.",
        "price": 180.0,
        "category": "coffee",
        "image_url": "⚡",
    },
    # ---------------- desserts ----------------
    {
        "title": "Чизкейк «Нью-Йорк»",
        "description": "Плотный сливочный чизкейк с ягодным соусом.",
        "price": 380.0,
        "category": "desserts",
        "image_url": "🍰",
    },
    {
        "title": "Круассан",
        "description": "Слоёный круассан на масле 82,5%, выпекается каждое утро.",
        "price": 220.0,
        "category": "desserts",
        "image_url": "🥐",
    },
    {
        "title": "Эклер «Фисташка»",
        "description": "Хрустящий эклер с фисташковым кремом и золотой глазурью.",
        "price": 310.0,
        "category": "desserts",
        "image_url": "🥧",
    },
    {
        "title": "Медовик",
        "description": "Восьмислойный медовый торт со сметанным кремом.",
        "price": 340.0,
        "category": "desserts",
        "image_url": "🍯",
    },
    # ---------------- breakfast ----------------
    {
        "title": "Сырники с малиной",
        "description": "Три нежных сырника, сметана и свежая малина.",
        "price": 420.0,
        "category": "breakfast",
        "image_url": "🫐",
    },
    {
        "title": "Каша на кокосовом молоке",
        "description": "Овсяная каша с бананом, корицей и кокосовой стружкой.",
        "price": 290.0,
        "category": "breakfast",
        "image_url": "🥣",
    },
    {
        "title": "Омлет с томатами",
        "description": "Пышный омлет с черри, зеленью и тостом из бриоши.",
        "price": 450.0,
        "category": "breakfast",
        "image_url": "🍳",
    },
    {
        "title": "Тост с авокадо",
        "description": "Тост на закваске, авокадо, яйцо пашот и хлопья чили.",
        "price": 470.0,
        "category": "breakfast",
        "image_url": "🥑",
    },
]


async def seed_if_empty(db: Database) -> None:
    """Insert demo products only when the catalogue is empty (first launch)."""
    if await db.count_products() > 0:
        logger.info("Products table already populated — seeding skipped")
        return

    async with db.cursor() as conn:
        await conn.executemany(
            "INSERT INTO products (title, description, price, category, image_url) "
            "VALUES (:title, :description, :price, :category, :image_url)",
            SEED_PRODUCTS,
        )
        await conn.commit()
    logger.info("Seeded %d demo products", len(SEED_PRODUCTS))