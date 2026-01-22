"""FastAPI dependencies shared across routers."""

from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .config import ADMIN_TOKEN
from .database import SessionLocal
from .enums import UserRole
from .models import User
from .security import verify_token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Недостаточно прав")


def get_current_user(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Токен авторизации не предоставлен")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Неверная схема авторизации")
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверный формат токена")

    payload = verify_token(token)
    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return user


def require_admin_role(current_user: User = Depends(get_current_user)):
    # Проверяем роль из БД - сравниваем строки, так как в БД роль хранится как строка
    user_role = (current_user.role or "").strip().lower()
    admin_role = UserRole.ADMIN.value.lower()
    
    if user_role != admin_role:
        raise HTTPException(status_code=403, detail="Недостаточно прав. Требуется роль администратора")
    return current_user

