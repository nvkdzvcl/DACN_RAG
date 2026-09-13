import os
import secrets
import time
from collections import deque
from threading import Lock
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.auth import COOKIE_NAME, SESSION_SECONDS, check_csrf, hash_password, public_user, require_admin, require_staff, token_hash, verify_password
from app.db.session import get_db
from app.models.support import AuthSession, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
_attempts = {}
_attempt_lock = Lock()
_dummy_hash = hash_password(secrets.token_urlsafe(32))


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value):
        return value.lower()


class UserCreate(LoginRequest):
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=160)
    role: Literal["admin", "agent"] = "agent"

    @field_validator("display_name")
    @classmethod
    def nonblank_name(cls, value):
        if not value.strip():
            raise ValueError("Display name cannot be blank")
        return value.strip()


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(id=str(uuid4()), username=payload.username, display_name=payload.display_name,
                password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Username already exists")
    return user


@router.post("/login", dependencies=[Depends(check_csrf)])
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    now = time.time()
    # ponytail: one local API worker; use shared rate limits before multi-worker hosting.
    address = request.client.host if request.client else "unknown"
    with _attempt_lock:
        for key in list(_attempts):
            if _attempts[key][-1] <= now - 60:
                del _attempts[key]
        attempts = _attempts.setdefault(address, deque(maxlen=10))
        while attempts and attempts[0] <= now - 60:
            attempts.popleft()
        if len(attempts) >= 10:
            raise HTTPException(429, "Too many login attempts", headers={"Retry-After": "60"})
        attempts.append(now)
    user = db.query(User).filter_by(username=payload.username).first()
    valid = verify_password(payload.password, user.password_hash if user else _dummy_hash)
    if not valid or user is None or not user.active:
        raise HTTPException(401, "Invalid username or password")
    token = secrets.token_urlsafe(32)
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= int(now)))
    old_token = request.cookies.get(COOKIE_NAME)
    if old_token:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(old_token)))
    db.add(AuthSession(token_hash=token_hash(token), user_id=user.id, expires_at=int(now) + SESSION_SECONDS))
    db.commit()
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=os.getenv("APP_ENV", "development") != "development", samesite="strict", path="/api")
    response.headers["Cache-Control"] = "no-store"
    return public_user(user)


@router.get("/me")
def me(response: Response, user: User = Depends(require_staff)):
    response.headers["Cache-Control"] = "no-store"
    return public_user(user)


@router.post("/logout", dependencies=[Depends(check_csrf)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(request.cookies.get(COOKIE_NAME, ""))))
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/api")
    return {"status": "logged_out"}


@router.post("/users", status_code=201, dependencies=[Depends(require_admin)])
def add_user(payload: UserCreate, db: Session = Depends(get_db)):
    return public_user(create_user(db, payload))
