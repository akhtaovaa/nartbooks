"""Book-related endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db, require_admin_role
from ..models import BookOfMonth, MeetingRegistration, Review, User
from ..schemas import BookCreate, ReviewCreate

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
    try:
        # Сначала ищем книгу с флагом is_current
        book = db.query(BookOfMonth).filter(BookOfMonth.is_current == 1).first()
        
        # Если нет текущей книги, берём последнюю добавленную
        if not book:
            book = db.query(BookOfMonth).order_by(BookOfMonth.id.desc()).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="Книга месяца не найдена")

        avg_rating = (
            db.query(func.avg(Review.rating))
            .filter(Review.book_id == book.id)
            .scalar()
        )
        
        # Подсчитываем количество записавшихся
        from ..models import MeetingRegistration
        registered_count = (
            db.query(func.count(MeetingRegistration.id))
            .filter(
                MeetingRegistration.book_id == book.id,
                MeetingRegistration.status == "registered"
            )
            .scalar()
        ) or 0

        return {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "date": book.date,
            "location": book.location,
            "description": book.description if hasattr(book, 'description') else None,
            "avg_rating": float(avg_rating) if avg_rating is not None else None,
            "is_current": bool(book.is_current) if hasattr(book, 'is_current') else False,
            "registered_count": registered_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении книги месяца: {str(e)}")


@router.get("")
def list_books(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Поиск по названию или автору"),
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

    # Получаем средние рейтинги для всех выбранных книг одним запросом
    book_ids = [b.id for b in books]
    ratings_map: dict[int, float] = {}
    registered_counts: dict[int, int] = {}
    
    if book_ids:
        ratings = (
            db.query(Review.book_id, func.avg(Review.rating).label("avg_rating"))
            .filter(Review.book_id.in_(book_ids))
            .group_by(Review.book_id)
            .all()
        )
        ratings_map = {r.book_id: float(r.avg_rating) for r in ratings}
        
        # Подсчитываем количество записавшихся на каждую встречу
        registrations = (
            db.query(
                MeetingRegistration.book_id,
                func.count(MeetingRegistration.id).label("count")
            )
            .filter(
                MeetingRegistration.book_id.in_(book_ids),
                MeetingRegistration.status == "registered"
            )
            .group_by(MeetingRegistration.book_id)
            .all()
        )
        registered_counts = {r.book_id: r.count for r in registrations}

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
                "avg_rating": ratings_map.get(b.id),
                "is_current": bool(b.is_current) if hasattr(b, 'is_current') else False,
                "registered_count": registered_counts.get(b.id, 0),
            }
            for b in books
        ],
    }


@router.get("/{book_id}")
def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    avg_rating = (
        db.query(func.avg(Review.rating))
        .filter(Review.book_id == book_id)
        .scalar()
    )
    
    # Подсчитываем количество записавшихся
    registered_count = (
        db.query(func.count(MeetingRegistration.id))
        .filter(
            MeetingRegistration.book_id == book_id,
            MeetingRegistration.status == "registered"
        )
        .scalar()
    ) or 0

    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "date": book.date,
        "location": book.location,
        "description": book.description,
        "avg_rating": float(avg_rating) if avg_rating is not None else None,
        "is_current": bool(book.is_current) if hasattr(book, 'is_current') else False,
        "registered_count": registered_count,
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


@router.put("/{book_id}/set-current")
def set_current_book(
    book_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_role),
):
    """Установить книгу как текущую книгу месяца (только админ)."""
    book = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    # Снимаем флаг is_current со всех книг
    db.query(BookOfMonth).update({BookOfMonth.is_current: 0})
    
    # Устанавливаем флаг is_current для выбранной книги
    book.is_current = 1
    db.commit()
    db.refresh(book)

    return {
        "message": f"Книга '{book.title}' установлена как текущая книга месяца",
        "id": book.id,
        "title": book.title,
        "is_current": True,
    }


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db), admin_user: User = Depends(require_admin_role)):
    book_entry = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
    if not book_entry:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    db.delete(book_entry)
    db.commit()
    return None


@router.post("/{book_id}/reviews", status_code=status.HTTP_201_CREATED)
def add_review(
    book_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    review_entry = Review(
        user_id=current_user.id,
        book_id=book_id,
        rating=review.rating,
        comment=review.comment,
        created_at=datetime.now().isoformat(),
    )
    db.add(review_entry)
    db.commit()
    db.refresh(review_entry)

    return {
        "message": "Отзыв успешно добавлен",
        "id": review_entry.id,
        "user_id": review_entry.user_id,
        "book_id": review_entry.book_id,
        "rating": review_entry.rating,
        "comment": review_entry.comment,
        "created_at": review_entry.created_at,
    }


@router.get("/{book_id}/reviews")
def list_reviews(
    book_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    book = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    base_query = db.query(Review).filter(Review.book_id == book_id)
    total = base_query.count()
    offset_value = (page - 1) * limit
    reviews = base_query.order_by(Review.id.desc()).offset(offset_value).limit(limit).all()
    total_pages = (total + limit - 1) // limit if total else 0

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": total_pages,
        "items": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "book_id": r.book_id,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at,
            }
            for r in reviews
        ],
    }

