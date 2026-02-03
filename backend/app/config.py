"""
Application configuration via environment variables.
Loads from .env in backend folder if present.
"""
import os
from pathlib import Path
from typing import Optional

# Base directory for backend (for resolving relative paths)
BASE_DIR = Path(__file__).resolve().parent.parent

# Project root (parent of backend)
PROJECT_ROOT = BASE_DIR.parent

# Load .env from backend folder so OPENAI_API_KEY etc. are available
_env_loaded = False
def _load_dotenv():
    global _env_loaded
    if _env_loaded:
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")
    except ImportError:
        pass
    _env_loaded = True


def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    _load_dotenv()
    return os.environ.get(key, default)


def get_settings():
    """Return settings object with env-based config."""
    class Settings:
        APP_NAME = os.environ.get("APP_NAME", "Legal Lens API")
        DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
        DATABASE_URL = os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{BASE_DIR / 'instance' / 'legal_lens.db'}",
        )
        SECRET_KEY = os.environ.get(
            "SECRET_KEY", "change-me-in-production-use-openssl-rand-hex-32"
        )
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
        DATA_PATH = _get_env("DATA_PATH")
        BM25_TOP_K = int(os.environ.get("BM25_TOP_K", "10"))
        OPENAI_API_KEY = _get_env("OPENAI_API_KEY")
        CHATBOT_MURDER_PDF = _get_env("CHATBOT_MURDER_PDF")
        CHATBOT_CHILD_PDF = _get_env("CHATBOT_CHILD_PDF")
        CHATBOT_MATERNITY_PDF = _get_env("CHATBOT_MATERNITY_PDF")
        CHATBOT_IPC_PDF = _get_env("CHATBOT_IPC_PDF")
    return Settings()
