"""Security helpers for tokens and verification codes."""

import random
import string
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .config import JWT_ALGORITHM, JWT_EXPIRATION_HOURS, JWT_SECRET_KEY
from .models import AuthCode


def generate_verification_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def create_access_token(user_id: int, user_role: str) -> str:
    now = datetime.now()
    expire = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "role": user_role,
        "iat": now,
        "exp": expire,
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истек")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")


def cleanup_old_codes(db: Session) -> None:
    cutoff_time = datetime.now() - timedelta(hours=1)
    cutoff_str = cutoff_time.isoformat()

    old_codes = db.query(AuthCode).filter(AuthCode.created_at < cutoff_str).all()
    for code in old_codes:
        db.delete(code)
    db.commit()

