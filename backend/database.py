"""Database engine and connection helpers."""
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import get_settings

settings = get_settings()

engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


def check_database_connection() -> bool:
    """Return True only when PostgreSQL accepts a simple query."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
