"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import auth, books, favorites, general, users

init_db()

app = FastAPI(title="NartBooks API")

# Настройка CORS для работы фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажи конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(general.router)
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(favorites.router)
app.include_router(users.router)

