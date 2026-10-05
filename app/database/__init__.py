"""Database package: connection wrapper and seeding."""

from app.database.db import Database
from app.database.seed import seed_if_empty

__all__ = ["Database", "seed_if_empty"]