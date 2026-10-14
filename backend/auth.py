"""JWT authentication and lightweight role-based access control."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import get_settings
from database import SessionLocal
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
ALLOWED_ROLES = {"admin", "editor", "viewer"}
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def hash_password(password: str) -> str:
    """Hash a password with scrypt and a random salt."""
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    salt = os.urandom(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return "scrypt$" + salt.hex() + "$" + derived.hex()


def verify_password(password: str, encoded: str) -> bool:
    """Verify an scrypt password hash without leaking comparison timing."""
    try:
        algorithm, salt_hex, expected_hex = encoded.split("$", 2)
        if algorithm != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(username: str) -> str:
    """Issue a short-lived JWT; refuses to operate without an explicit secret."""
    settings = get_settings()
    secret = settings.jwt_secret_key.strip()
    if len(secret) < 32 or secret.startswith("REPLACE_WITH"):
        raise RuntimeError("JWT_SECRET_KEY must be configured with at least 32 characters.")
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": username, "iat": now, "exp": now + timedelta(minutes=settings.jwt_access_token_minutes)},
        secret,
        algorithm="HS256",
    )


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Decode the bearer token and load the current user/role from PostgreSQL."""
    settings = get_settings()
    secret = settings.jwt_secret_key.strip()
    if len(secret) < 32 or secret.startswith("REPLACE_WITH"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Set JWT_SECRET_KEY.",
        )
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        username = payload.get("sub")
        if not isinstance(username, str) or not username:
            raise _unauthorized()
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc

    db: Session = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == username, User.is_active.is_(True)))
        if user is None:
            raise _unauthorized()
        return user
    finally:
        db.close()


def require_roles(*roles: str):
    """Return a dependency enforcing one of the allowed roles."""
    if not roles or not set(roles).issubset(ALLOWED_ROLES):
        raise ValueError("A valid role allowlist is required.")

    def role_guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions.")
        return user

    return role_guard
