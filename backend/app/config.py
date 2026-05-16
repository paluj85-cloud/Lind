"""Application configuration - loaded from .env using pydantic-settings."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class Settings:
    """Application settings loaded from environment variables."""

    # DeepSeek API
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv(
        "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
    )
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))

    # Database
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH",
        str(Path(__file__).parent.parent / "data" / "lind.db"),
    )

    # Logging
    LOG_DIR: str = os.getenv(
        "LOG_DIR", str(Path(__file__).parent.parent / "logs")
    )
    LOG_FILE: str = os.getenv(
        "LOG_FILE", str(Path(LOG_DIR) / "game.log")
    )
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))  # 10 MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", 5))

    # Game
    CONTEXT_MAX_MESSAGES: int = int(os.getenv("CONTEXT_MAX_MESSAGES", 20))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 3))
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", 60))

    # Admin
    ADMIN_BASIC_AUTH_USER: str = os.getenv("ADMIN_USER", "exis")
    ADMIN_BASIC_AUTH_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")

# Singleton instance
settings = Settings()


def ensure_directories() -> None:
    """Create required directories if they don't exist."""
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    data_dir = Path(settings.DATABASE_PATH).parent
    data_dir.mkdir(parents=True, exist_ok=True)