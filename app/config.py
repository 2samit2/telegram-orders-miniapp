"""Application configuration loaded from environment variables / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central project settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Telegram ---
    bot_token: str = "1234567890:TEST_TOKEN_REPLACE_ME"
    admin_id: int = 0

    # --- Web ---
    host: str = "0.0.0.0"
    port: int = 8000
    # Public HTTPS URL of the Web App (required by BotFather / Telegram).
    # Leave empty for local development (standalone browser mode).
    webapp_url: str = ""

    # --- Database ---
    database_path: str = "artisan_coffee.sqlite3"

    # --- Misc ---
    app_title: str = "Artisan Coffee & Bakery — Order Bot"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (one per process)."""
    return Settings()