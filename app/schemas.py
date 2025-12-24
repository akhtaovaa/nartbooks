"""Pydantic schemas used for request/response models."""

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, validator

from .enums import UserRole


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    fav_authors: List[str]
    fav_genres: List[str]
    fav_books: List[str]
    discuss_books: List[str]

    @validator("phone")
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        cleaned = re.sub(r"[\s\-\(\)]", "", value)
        if re.match(r"^(\+7|8)\d{10}$", cleaned):
            return value
        if re.match(r"^\+\d{10,15}$", cleaned):
            return value
        raise ValueError("Неверный формат телефона. Используйте формат: +7XXXXXXXXXX или 8XXXXXXXXXX")

    @validator("birth_date")
    def validate_birth_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        try:
            birth = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Неверный формат даты рождения. Используйте YYYY-MM-DD")

        today = datetime.now().date()
        if birth > today:
            raise ValueError("Дата рождения не может быть в будущем")

        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        if age < 5 or age > 120:
            raise ValueError("Недопустимый возраст. Допустимо от 5 до 120 лет")
        return value


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    fav_authors: Optional[List[str]] = None
    fav_genres: Optional[List[str]] = None
    fav_books: Optional[List[str]] = None
    discuss_books: Optional[List[str]] = None

    @validator("phone")
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        cleaned = re.sub(r"[\s\-\(\)]", "", value)
        if re.match(r"^(\+7|8)\d{10}$", cleaned):
            return value
        if re.match(r"^\+\d{10,15}$", cleaned):
            return value
        raise ValueError("Неверный формат телефона. Используйте формат: +7XXXXXXXXXX или 8XXXXXXXXXX")

    @validator("birth_date")
    def validate_birth_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        try:
            birth = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Неверный формат даты рождения. Используйте YYYY-MM-DD")

        today = datetime.now().date()
        if birth > today:
            raise ValueError("Дата рождения не может быть в будущем")

        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        if age < 5 or age > 120:
            raise ValueError("Недопустимый возраст. Допустимо от 5 до 120 лет")
        return value


class BookCreate(BaseModel):
    title: str
    author: str
    date: str
    location: str
    description: Optional[str] = None


class AuthRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class AuthVerify(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    code: str


class RoleUpdate(BaseModel):
    role: UserRole


class FavoriteCreate(BaseModel):
    """Request body for adding a book to favorites."""

    book_id: int


class ReviewCreate(BaseModel):
    """Request body for creating a review."""

    rating: int
    comment: Optional[str] = None

    @validator("rating")
    def validate_rating(cls, value: int) -> int:
        if not 1 <= value <= 5:
            raise ValueError("Оценка должна быть от 1 до 5")
        return value
