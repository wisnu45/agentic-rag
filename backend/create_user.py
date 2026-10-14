"""Provision an application user from a trusted administrative terminal.

Run from the backend directory after initializing the database:
    python create_user.py --username admin --role admin
"""
import argparse
import getpass

from sqlalchemy import select

from auth import ALLOWED_ROLES, hash_password
from database import SessionLocal
from models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an Agentic RAG user.")
    parser.add_argument("--username", required=True, help="Login name (3-80 characters)")
    parser.add_argument("--role", choices=sorted(ALLOWED_ROLES), default="viewer")
    args = parser.parse_args()
    username = args.username.strip()
    if len(username) < 3 or len(username) > 80:
        parser.error("Username must contain 3 to 80 characters.")

    password = getpass.getpass("Password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")
    try:
        password_hash = hash_password(password)
    except ValueError as exc:
        parser.error(str(exc))

    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.username == username)):
            parser.error("Username already exists.")
        db.add(User(username=username, password_hash=password_hash, role=args.role, is_active=True))
        db.commit()
        print(f"Created user '{username}' with role '{args.role}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
