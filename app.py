from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi import status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, or_
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Optional, List
import smtplib
from email.mime.text import MIMEText
import os
import random
import string
import jwt
import re
from datetime import datetime, timedelta
from enum import Enum

# -----------------------------
# Настройки приложения и базы данных
# -----------------------------
app = FastAPI(title="NartBooks API")

DATABASE_URL = "sqlite:///./nartbooks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# -----------------------------
# Enum для ролей пользователей
# -----------------------------
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# -----------------------------
# Модели базы данных
# -----------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    role = Column(String, nullable=False, default=UserRole.USER)  # Роль пользователя
    fav_authors = Column(Text)
    fav_genres = Column(Text)
    fav_books = Column(Text)
    discuss_books = Column(Text)

class BookOfMonth(Base):
    __tablename__ = "books_of_month"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    date = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=True)

class AuthCode(Base):
    __tablename__ = "auth_codes"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, nullable=False, index=True)  # email или phone
    code = Column(String, nullable=False)
    created_at = Column(String, nullable=False)  # timestamp
    is_used = Column(Integer, default=0)  # 0 - не использован, 1 - использован

class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    token = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(String, nullable=False)  # timestamp
    expires_at = Column(String, nullable=False)  # timestamp
    is_active = Column(Integer, default=1)  # 1 - активен, 0 - неактивен

Base.metadata.create_all(bind=engine)

# -----------------------------
# Актуализация схемы БД (SQLite): добавляем колонку description при отсутствии
# -----------------------------
def ensure_description_column_exists():
    try:
        with engine.connect() as conn:
            info = conn.execute("PRAGMA table_info(books_of_month)").fetchall()
            columns = {row[1] for row in info}  # row[1] = name
            if "description" not in columns:
                # Добавляем nullable колонку для обратной совместимости
                conn.execute("ALTER TABLE books_of_month ADD COLUMN description TEXT")
    except Exception:
        # Молча игнорируем, чтобы не ломать запуск в окружениях без прав/доступа
        pass

ensure_description_column_exists()

# -----------------------------
# Pydantic-схемы (валидация данных)
# -----------------------------
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
        # Удаляем все пробелы, скобки и дефисы
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        # Проверяем на российские форматы: +7XXXXXXXXXX или 8XXXXXXXXXX
        if re.match(r'^(\+7|8)\d{10}$', cleaned):
            return value
        # Проверяем на международный формат: +XXXXXXXXX
        if re.match(r'^\+\d{10,15}$', cleaned):
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
        # Удаляем все пробелы, скобки и дефисы
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        # Проверяем на российские форматы: +7XXXXXXXXXX или 8XXXXXXXXXX
        if re.match(r'^(\+7|8)\d{10}$', cleaned):
            return value
        # Проверяем на международный формат: +XXXXXXXXX
        if re.match(r'^\+\d{10,15}$', cleaned):
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

# -----------------------------
# Зависимости
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# Настройки JWT и администратора
# -----------------------------
JWT_SECRET_KEY = "your-secret-key-here"  # ⚠️ В продакшене используйте более безопасный ключ
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Токен действителен 24 часа

ADMIN_TOKEN = "my_secret_token"

def require_admin(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Недостаточно прав")

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Зависимость для получения текущего пользователя по JWT токену"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Токен авторизации не предоставлен")
    
    try:
        # Извлекаем токен из заголовка "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Неверная схема авторизации")
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверный формат токена")
    
    # Проверяем токен
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    # Проверяем, что пользователь существует
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    return user

def require_admin_role(current_user: User = Depends(get_current_user)):
    """Зависимость для проверки роли администратора"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Недостаточно прав. Требуется роль администратора")
    return current_user

def generate_verification_code():
    """Генерирует 6-значный код подтверждения"""
    return ''.join(random.choices(string.digits, k=6))

def create_access_token(user_id: int, user_role: str = UserRole.USER) -> str:
    """Создает JWT токен для пользователя"""
    now = datetime.now()
    expire = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "user_id": user_id,
        "role": user_role,
        "iat": now,
        "exp": expire
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def verify_token(token: str) -> dict:
    """Проверяет JWT токен и возвращает payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истек")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")

def cleanup_old_codes(db: Session):
    """Удаляет старые коды (старше 1 часа)"""
    cutoff_time = datetime.now() - timedelta(hours=1)
    cutoff_str = cutoff_time.isoformat()
    
    old_codes = db.query(AuthCode).filter(AuthCode.created_at < cutoff_str).all()
    for code in old_codes:
        db.delete(code)
    db.commit()
    

# -----------------------------
# Авторизация через msg.ovrx.ru/api
# -----------------------------
import requests
from datetime import datetime, timedelta

MSG_OVRX_BASE_URL = "https://msg.ovrx.ru"
MSG_OVRX_API_KEY = "ТВОЙ_API_КЛЮЧ"  # ⚠️ сюда вставь реальный API-ключ

# Для хранения времени последней отправки кода (ограничение 1 минута)
last_sent = {}

class AuthRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class AuthVerify(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    code: str

@app.post("/auth/send-code", tags=["Авторизация"])
def send_auth_code(req: AuthRequest, db: Session = Depends(get_db)):
    """Отправка одноразового кода (OTP)"""
    identifier = req.email or req.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Укажите email или телефон")

    # Очищаем старые коды
    cleanup_old_codes(db)

    # Проверка времени последней отправки
    if identifier in last_sent:
        if datetime.now() - last_sent[identifier] < timedelta(minutes=1):
            raise HTTPException(status_code=429, detail="Можно отправлять код не чаще 1 раза в минуту")

    code = generate_verification_code()

    # Запрос к msg.ovrx.ru
    payload = {"email": req.email, "code": code} if req.email else {"phone": req.phone, "code": code}

    try:
        r = requests.post(
            f"{MSG_OVRX_BASE_URL}/auth-code/email" if req.email else f"{MSG_OVRX_BASE_URL}/auth-code/sms",
            json=payload
        )
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке кода: {e}")

    # Сохраняем код в базе данных
    auth_code = AuthCode(
        identifier=identifier,
        code=code,
        created_at=datetime.now().isoformat(),
        is_used=0
    )
    db.add(auth_code)
    db.commit()

    last_sent[identifier] = datetime.now()
    return {"message": "Код отправлен успешно"}

@app.post("/auth/verify-code", tags=["Авторизация"])
def verify_auth_code(req: AuthVerify, db: Session = Depends(get_db)):
    """Проверка кода и создание пользователя, если он новый"""
    identifier = req.email or req.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Укажите email или телефон")

    # Ищем неиспользованный код для данного идентификатора
    auth_code = db.query(AuthCode).filter(
        AuthCode.identifier == identifier,
        AuthCode.code == req.code,
        AuthCode.is_used == 0
    ).first()

    if not auth_code:
        raise HTTPException(status_code=400, detail="Неверный код или код уже использован")

    # Проверяем, не истек ли код (например, 10 минут)
    code_created = datetime.fromisoformat(auth_code.created_at)
    if datetime.now() - code_created > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="Код истек")

    # Помечаем код как использованный
    auth_code.is_used = 1
    db.commit()

    # Проверяем, есть ли пользователь в базе
    user = db.query(User).filter(
        (User.email == req.email) | (User.phone == req.phone)
    ).first()

    if not user:
        # Создаем нового пользователя с минимальными данными
        user = User(
            first_name="",
            last_name="",
            email=req.email or "",
            phone=req.phone or "",
            fav_authors="",
            fav_genres="",
            fav_books="",
            discuss_books=""
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Создаем JWT токен с ролью пользователя
    access_token = create_access_token(user.id, user.role)
    
    # Сохраняем токен в базе данных
    now = datetime.now()
    expires_at = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    auth_token = AuthToken(
        user_id=user.id,
        token=access_token,
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        is_active=1
    )
    db.add(auth_token)
    db.commit()

    return {
        "message": "Авторизация успешна", 
        "user_id": user.id,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600  # в секундах
    }

# -----------------------------
# Эндпоинты API
# -----------------------------
@app.get("/", tags=["Общие"])
def home():
    return {"message": "Добро пожаловать в NartBooks!"}

@app.post("/register", include_in_schema=False, status_code=status.HTTP_201_CREATED)
def register_user(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        birth_date=data.birth_date,
        fav_authors=", ".join(data.fav_authors),
        fav_genres=", ".join(data.fav_genres),
        fav_books=", ".join(data.fav_books),
        discuss_books=", ".join(data.discuss_books)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Отправляем приветственное письмо
    # TODO: Реализовать функцию send_email
    # send_email(
    #     to_email=data.email,
    #     subject="Добро пожаловать в NartBooks!",
    #     body=f"Привет, {data.first_name}! 🎉 Добро пожаловать в книжный клуб NartBooks!"
    # )

    return {"message": "Регистрация прошла успешно!", "user_id": user.id}

@app.post("/books", tags=["Книги"], status_code=status.HTTP_201_CREATED)
def add_book(book: BookCreate, db: Session = Depends(get_db), admin_user: User = Depends(require_admin_role)):
    """Добавление книги месяца (только для администраторов)"""
    book_entry = BookOfMonth(**book.dict())
    db.add(book_entry)
    db.commit()
    db.refresh(book_entry)
    return {
        "message": "Книга месяца успешно добавлена",
        "id": book_entry.id,
        "title": book_entry.title,
        "author": book_entry.author,
        "date": book_entry.date,
        "location": book_entry.location,
        "description": book_entry.description
    }

@app.get("/books/current", tags=["Книги"])
def get_current_book_of_month(db: Session = Depends(get_db)):
    """Получение текущей книги месяца"""
    book = db.query(BookOfMonth).order_by(BookOfMonth.id.desc()).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга месяца не найдена")
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "date": book.date,
        "location": book.location,
        "description": book.description
    }

@app.get("/books", tags=["Книги"])
def list_books(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Поиск по названию или автору"),
    db: Session = Depends(get_db)
):
    """Получение списка книг месяца с пагинацией и поиском"""
    base_query = db.query(BookOfMonth)
    if search:
        like = f"%{search}%"
        base_query = base_query.filter(
            or_(BookOfMonth.title.ilike(like), BookOfMonth.author.ilike(like))
        )

    total = base_query.count()
    offset_value = (page - 1) * limit
    books = (
        base_query
        .order_by(BookOfMonth.id.desc())
        .offset(offset_value)
        .limit(limit)
        .all()
    )

    total_pages = (total + limit - 1) // limit if total else 0

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": total_pages,
        "items": [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "date": b.date,
                "location": b.location,
                "description": b.description,
            }
            for b in books
        ],
    }

@app.get("/books/{id}", tags=["Книги"])
def get_book_by_id(id: int, db: Session = Depends(get_db)):
    """Получение книги по ID"""
    book = db.query(BookOfMonth).filter(BookOfMonth.id == id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "date": book.date,
        "location": book.location,
        "description": book.description
    }

@app.put("/books/{id}", tags=["Книги"])
def update_book(id: int, book: BookCreate, db: Session = Depends(get_db), admin_user: User = Depends(require_admin_role)):
    """Обновление книги по ID (только для администраторов)"""
    book_entry = db.query(BookOfMonth).filter(BookOfMonth.id == id).first()
    if not book_entry:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    
    book_entry.title = book.title
    book_entry.author = book.author
    book_entry.date = book.date
    book_entry.location = book.location
    book_entry.description = book.description
    
    db.commit()
    db.refresh(book_entry)
    
    return {
        "message": "Книга успешно обновлена",
        "id": book_entry.id,
        "title": book_entry.title,
        "author": book_entry.author,
        "date": book_entry.date,
        "location": book_entry.location,
        "description": book_entry.description
    }

@app.delete("/books/{id}", tags=["Книги"], status_code=status.HTTP_204_NO_CONTENT)
def delete_book(id: int, db: Session = Depends(get_db), admin_user: User = Depends(require_admin_role)):
    """Удаление книги по ID (только для администраторов)"""
    book_entry = db.query(BookOfMonth).filter(BookOfMonth.id == id).first()
    if not book_entry:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    
    db.delete(book_entry)
    db.commit()
    
    return None

@app.get("/me", tags=["Пользователи"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "birth_date": current_user.birth_date,
        "role": current_user.role,
        "fav_authors": current_user.fav_authors.split(", ") if current_user.fav_authors else [],
        "fav_genres": current_user.fav_genres.split(", ") if current_user.fav_genres else [],
        "fav_books": current_user.fav_books.split(", ") if current_user.fav_books else [],
        "discuss_books": current_user.discuss_books.split(", ") if current_user.discuss_books else []
    }

@app.patch("/me", tags=["Пользователи"])
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление профиля текущего пользователя"""
    # Обновляем только те поля, которые были предоставлены
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.birth_date is not None:
        current_user.birth_date = user_update.birth_date
    if user_update.fav_authors is not None:
        current_user.fav_authors = ", ".join(user_update.fav_authors)
    if user_update.fav_genres is not None:
        current_user.fav_genres = ", ".join(user_update.fav_genres)
    if user_update.fav_books is not None:
        current_user.fav_books = ", ".join(user_update.fav_books)
    if user_update.discuss_books is not None:
        current_user.discuss_books = ", ".join(user_update.discuss_books)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Профиль успешно обновлен",
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "birth_date": current_user.birth_date,
        "role": current_user.role,
        "fav_authors": current_user.fav_authors.split(", ") if current_user.fav_authors else [],
        "fav_genres": current_user.fav_genres.split(", ") if current_user.fav_genres else [],
        "fav_books": current_user.fav_books.split(", ") if current_user.fav_books else [],
        "discuss_books": current_user.discuss_books.split(", ") if current_user.discuss_books else []
    }
    

class RoleUpdate(BaseModel):
    role: UserRole

@app.put("/users/{id}/role", tags=["Пользователи"])
def update_user_role(id: int, role_update: RoleUpdate, db: Session = Depends(get_db), admin_user: User = Depends(require_admin_role)):
    """Обновление роли пользователя по ID (только для администраторов)"""
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"Роль пользователя {user.email} обновлена на {role_update.role}",
        "id": user.id,
        "email": user.email,
        "role": user.role
    }

@app.get("/users", tags=["Пользователи"])
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_role)
):
    """Список пользователей (только для администраторов) c пагинацией"""
    total = db.query(User).count()
    offset_value = (page - 1) * limit
    users = (
        db.query(User)
        .order_by(User.id.desc())
        .offset(offset_value)
        .limit(limit)
        .all()
    )
    total_pages = (total + limit - 1) // limit if total else 0

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": total_pages,
        "items": [
            {
                "id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "phone": u.phone,
                "birth_date": u.birth_date,
                "role": u.role,
            }
            for u in users
        ],
    }

@app.get("/users/{id}", tags=["Пользователи"])
def get_user_by_id(
    id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_role)
):
    """Получение конкретного пользователя по id (только для администраторов)"""
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "birth_date": user.birth_date,
        "role": user.role,
        "fav_authors": user.fav_authors.split(", ") if user.fav_authors else [],
        "fav_genres": user.fav_genres.split(", ") if user.fav_genres else [],
        "fav_books": user.fav_books.split(", ") if user.fav_books else [],
        "discuss_books": user.discuss_books.split(", ") if user.discuss_books else [],
    }
