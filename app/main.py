"""FastAPI application factory."""

from fastapi import FastAPI

from .database import init_db
from .routers import auth, books, favorites, general, users

init_db()

app = FastAPI(title="NartBooks API")

app.include_router(general.router)
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(favorites.router)
app.include_router(users.router)

