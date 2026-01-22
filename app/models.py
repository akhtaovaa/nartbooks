"""SQLAlchemy models."""

from sqlalchemy import Column, Integer, String, Text

from .database import Base
from .enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    birthdate = Column(String, nullable=True)  # В БД используется birthdate без подчёркивания
    role = Column(String, nullable=False, default=UserRole.USER)
    fav_authors = Column(Text)
    fav_genres = Column(Text)
    fav_books = Column(Text)
    wanted_books = Column(Text)  # В БД используется wanted_books вместо discuss_books
    created_at = Column(String, nullable=True)  # Добавляем created_at, если есть в БД
    
    # Свойство для обратной совместимости с discuss_books
    @property
    def discuss_books(self):
        return self.wanted_books or ""
    
    @discuss_books.setter
    def discuss_books(self, value):
        self.wanted_books = value
    
    # Свойство для обратной совместимости с birth_date
    @property
    def birth_date(self):
        return self.birthdate
    
    @birth_date.setter
    def birth_date(self, value):
        self.birthdate = value


class BookOfMonth(Base):
    __tablename__ = "books_of_month"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    date = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_current = Column(Integer, default=0)  # 0 или 1 для совместимости с SQLite


class AuthCode(Base):
    __tablename__ = "auth_codes"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    is_used = Column(Integer, default=0)


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    token = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(String, nullable=False)
    expires_at = Column(String, nullable=False)
    is_active = Column(Integer, default=1)


class Favorite(Base):
    """User's favorite books."""

    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    created_at = Column(String, nullable=False)


class Review(Base):
    """User reviews for books."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(String, nullable=False)


class MeetingRegistration(Base):
    """User registration for book meetings."""

    __tablename__ = "meeting_registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    registered_at = Column(String, nullable=False)
    status = Column(String, default="registered")  # "registered" or "cancelled"
