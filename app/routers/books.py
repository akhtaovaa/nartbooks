"""Book-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..dependencies import get_db, require_admin_role
from ..models import BookOfMonth, User
from ..schemas import BookCreate

router = APIRouter(prefix="/books", tags=["Книги"])


@router.post("", status_code=status.HTTP_201_CREATED)
def add_book(book: BookCreate, db: Session = Depends(get_db), admin_user: User = Depends(require_admin_role)):
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
        "description": book_entry.description,
    }


@router.get("/current")
def get_current_book_of_month(db: Session = Depends(get_db)):
    book = db.query(BookOfMonth).order_by(BookOfMonth.id.desc()).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга месяца не найдена")
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "date": book.date,
        "location": book.location,
        "description": book.description,
    }


@router.get("")
def list_books(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, description="Поиск по названию или автору"),
    db: Session = Depends(get_db),
):
    base_query = db.query(BookOfMonth)
    if search:
        like = f"%{search}%"
        base_query = base_query.filter(or_(BookOfMonth.title.ilike(like), BookOfMonth.author.ilike(like)))

    total = base_query.count()
    offset_value = (page - 1) * limit
    books = base_query.order_by(BookOfMonth.id.desc()).offset(offset_value).limit(limit).all()

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


@router.get("/{book_id}")
def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "date": book.date,
        "location": book.location,
        "description": book.description,
    }


@router.put("/{book_id}")
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db), admin_user: User = Depends(require_admin_role)):
    book_entry = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
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
        "description": book_entry.description,
    }


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db), admin_user: User = Depends(require_admin_role)):
    book_entry = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
    if not book_entry:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    db.delete(book_entry)
    db.commit()
    return None

