"""Favorites-related endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models import BookOfMonth, Favorite, User
from ..schemas import FavoriteCreate

router = APIRouter(prefix="/favorites", tags=["Избранное"])


@router.post("", status_code=status.HTTP_201_CREATED)
def add_favorite(
    payload: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(BookOfMonth).filter(BookOfMonth.id == payload.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    existing = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.book_id == payload.book_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Книга уже есть в избранном")

    favorite = Favorite(
        user_id=current_user.id,
        book_id=payload.book_id,
        created_at=datetime.now().isoformat(),
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return {
        "message": "Книга добавлена в избранное",
        "id": favorite.id,
        "user_id": favorite.user_id,
        "book_id": favorite.book_id,
        "created_at": favorite.created_at,
    }


@router.get("")
def list_favorites(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_query = db.query(Favorite).filter(Favorite.user_id == current_user.id)
    total = base_query.count()
    offset_value = (page - 1) * limit
    favorites = base_query.order_by(Favorite.id.desc()).offset(offset_value).limit(limit).all()
    total_pages = (total + limit - 1) // limit if total else 0

    book_ids = [f.book_id for f in favorites]
    books_map = {}
    if book_ids:
        books = db.query(BookOfMonth).filter(BookOfMonth.id.in_(book_ids)).all()
        books_map = {b.id: b for b in books}

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": total_pages,
        "items": [
            {
                "id": f.id,
                "book": {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "date": book.date,
                    "location": book.location,
                    "description": book.description,
                }
                if (book := books_map.get(f.book_id))
                else None,
                "created_at": f.created_at,
            }
            for f in favorites
        ],
    }


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    favorite = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.book_id == book_id)
        .first()
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="Книга не найдена в избранном")

    db.delete(favorite)
    db.commit()
    return None



