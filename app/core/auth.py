import hashlib
import hmac
import secrets
import time

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.support import AuthSession, User

COOKIE_NAME = "rag_session"
SESSION_SECONDS = 8 * 60 * 60


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or int(rounds) != 600_000:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def check_csrf(request: Request):
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("X-CSRF-Protection") != "1":
        raise HTTPException(403, "Missing CSRF protection header")


def require_staff(request: Request, db: Session = Depends(get_db)) -> User:
    check_csrf(request)
    token = request.cookies.get(COOKIE_NAME, "")
    session = db.get(AuthSession, token_hash(token)) if token else None
    user = db.get(User, session.user_id) if session and session.expires_at > int(time.time()) else None
    if user is None or not user.active:
        raise HTTPException(401, "Authentication required")
    if user.role not in {"admin", "agent"}:
        raise HTTPException(403, "Staff role required")
    return user


def require_admin(user: User = Depends(require_staff)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Administrator role required")
    return user


def public_user(user: User) -> dict:
    return {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role}
