from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and ensure instance dir exists for SQLite."""
    from pathlib import Path
    from app.config import BASE_DIR
    if "sqlite" in settings.DATABASE_URL:
        (BASE_DIR / "instance").mkdir(parents=True, exist_ok=True)
    from app.models import User, Feedback  # noqa: F401
    Base.metadata.create_all(bind=engine)
