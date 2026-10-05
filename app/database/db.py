"""Async SQLite storage layer (aiosqlite)."""

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

import aiosqlite

from app.models import OrderItemOut, Product

logger = logging.getLogger(__name__)


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL,
    price       REAL    NOT NULL CHECK (price > 0),
    category    TEXT    NOT NULL CHECK (category IN ('coffee', 'desserts', 'breakfast')),
    image_url   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER,
    user_name      TEXT    NOT NULL DEFAULT 'Гость',
    username       TEXT    NOT NULL DEFAULT '',
    items_json     TEXT    NOT NULL,
    total_price    REAL    NOT NULL,
    address        TEXT    NOT NULL,
    comment        TEXT    NOT NULL DEFAULT '',
    phone_or_table TEXT    NOT NULL DEFAULT '',
    created_at     TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at);
"""


class Database:
    """Thin wrapper around aiosqlite with typed helpers for products/orders."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open the connection and create tables (idempotent)."""
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.executescript(CREATE_TABLES_SQL)
        await self._conn.commit()
        logger.info("SQLite database ready: %s", self._path)

    async def close(self) -> None:
        """Close the connection gracefully."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
            logger.info("SQLite connection closed")

    @asynccontextmanager
    async def cursor(self) -> AsyncIterator[aiosqlite.Connection]:
        """Yield the live connection; guard against usage before connect()."""
        if self._conn is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        yield self._conn

    # ------------------------------------------------------------------ products

    async def get_products(self) -> list[Product]:
        """Return the full catalogue ordered by category and id."""
        async with self.cursor() as conn:
            rows = await conn.execute_fetchall(
                "SELECT id, title, description, price, category, image_url "
                "FROM products ORDER BY category, id"
            )
        return [Product.model_validate(dict(row)) for row in rows]

    async def count_products(self) -> int:
        """Return the number of products in the catalogue."""
        async with self.cursor() as conn:
            row = await conn.execute("SELECT COUNT(*) AS n FROM products")
            result = await row.fetchone()
            return int(result["n"]) if result else 0

    # ------------------------------------------------------------------- orders

    async def create_order(
        self,
        *,
        user_id: int | None,
        user_name: str,
        username: str,
        items: list[OrderItemOut],
        total_price: float,
        address: str,
        comment: str,
        phone_or_table: str = "",
    ) -> int:
        """Insert a new order and return its id."""
        items_json = json.dumps(
            [item.model_dump() for item in items], ensure_ascii=False
        )
        created_at = datetime.now().isoformat(timespec="seconds")
        async with self.cursor() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO orders
                    (user_id, user_name, username, items_json, total_price,
                     address, comment, phone_or_table, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    user_name,
                    username,
                    items_json,
                    total_price,
                    address,
                    comment,
                    phone_or_table,
                    created_at,
                ),
            )
            await conn.commit()
            return int(cursor.lastrowid)

    async def get_last_orders(self, limit: int = 5) -> list[dict[str, Any]]:
        """Return the most recent orders (newest first)."""
        async with self.cursor() as conn:
            rows = await conn.execute_fetchall(
                "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
            )
        return [dict(row) for row in rows]