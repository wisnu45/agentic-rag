"""Create the pgvector extension and initial application tables.

Run from the backend directory after PostgreSQL is available:
    python init_db.py
"""
from sqlalchemy import text

from database import engine
from models import Base


def initialize_database() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialize_database()
    print("Database schema initialized.")
