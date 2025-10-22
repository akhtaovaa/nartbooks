from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Optional, List
import smtplib
from email.mime.text import MIMEText
import os
import random
import string

# -----------------------------
# Настройки приложения и базы данных
# -----------------------------
app = FastAPI(title="NartBooks API")

DATABASE_URL = "sqlite:///./nartbooks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

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

class AuthCode(Base):
    __tablename__ = "auth_codes"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, nullable=False, index=True)  # email или phone
    code = Column(String, nullable=False)
    created_at = Column(String, nullable=False)  # timestamp
    is_used = Column(Integer, default=0)  # 0 - не использован, 1 - использован

Base.metadata.create_all(bind=engine)

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

class BookCreate(BaseModel):
    title: str
    author: str
    date: str
    location: str

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
# Настройки администратора
# -----------------------------
ADMIN_TOKEN = "my_secret_token"

def require_admin(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Недостаточно прав")

def generate_verification_code():
    """Генерирует 6-значный код подтверждения"""
    return ''.join(random.choices(string.digits, k=6))

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

@app.post("/auth/send-code")
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

@app.post("/auth/verify-code")
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

    return {"message": "Авторизация успешна", "user_id": user.id}

# -----------------------------
# Эндпоинты API
# -----------------------------
@app.get("/")
def home():
    return {"message": "Добро пожаловать в NartBooks!"}

@app.post("/register")
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

@app.post("/admin/add_book")
def add_book(book: BookCreate, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    book_entry = BookOfMonth(**book.dict())
    db.add(book_entry)
    db.commit()
    return {"message": "Книга месяца успешно добавлена"}

@app.get("/book_of_month")
def get_book_of_month(db: Session = Depends(get_db)):
    book = db.query(BookOfMonth).order_by(BookOfMonth.id.desc()).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга месяца не найдена")
    return {
        "title": book.title,
        "author": book.author,
        "date": book.date,
        "location": book.location
    }
