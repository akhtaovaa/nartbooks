"""Meeting registration endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db, require_admin_role
from ..models import BookOfMonth, MeetingRegistration, User

router = APIRouter(prefix="/meetings", tags=["Встречи"])


@router.post("/register/{book_id}", status_code=status.HTTP_201_CREATED)
def register_for_meeting(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Записаться на встречу (книгу месяца)."""
    # Проверяем, существует ли книга
    book = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    # Проверяем, не записан ли пользователь уже
    existing = (
        db.query(MeetingRegistration)
        .filter(
            MeetingRegistration.user_id == current_user.id,
            MeetingRegistration.book_id == book_id,
            MeetingRegistration.status == "registered",
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже записаны на эту встречу")

    # Создаём запись
    registration = MeetingRegistration(
        user_id=current_user.id,
        book_id=book_id,
        registered_at=datetime.now().isoformat(),
        status="registered",
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    return {
        "message": "Вы успешно записались на встречу",
        "id": registration.id,
        "user_id": registration.user_id,
        "book_id": registration.book_id,
        "registered_at": registration.registered_at,
        "status": registration.status,
        "book_title": book.title,
        "book_date": book.date,
        "book_location": book.location,
    }


@router.delete("/register/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_meeting_registration(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Отменить запись на встречу."""
    registration = (
        db.query(MeetingRegistration)
        .filter(
            MeetingRegistration.user_id == current_user.id,
            MeetingRegistration.book_id == book_id,
            MeetingRegistration.status == "registered",
        )
        .first()
    )
    if not registration:
        raise HTTPException(status_code=404, detail="Запись на встречу не найдена")

    registration.status = "cancelled"
    db.commit()
    return None


@router.get("/my")
def get_my_meetings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить список встреч, на которые записан текущий пользователь."""
    registrations_raw = (
        db.query(MeetingRegistration, BookOfMonth)
        .join(BookOfMonth, MeetingRegistration.book_id == BookOfMonth.id)
        .filter(
            MeetingRegistration.user_id == current_user.id,
            MeetingRegistration.status == "registered",
        )
        .order_by(MeetingRegistration.id.desc())
        .all()
    )
    
    registrations = [(reg, book) for reg, book in registrations_raw]

    return {
        "items": [
            {
                "id": reg.id,
                "book_id": reg.book_id,
                "registered_at": reg.registered_at,
                "book_title": book.title,
                "book_author": book.author,
                "book_date": book.date,
                "book_location": book.location,
                "book_description": book.description,
            }
            for reg, book in registrations
        ]
    }


@router.get("/{book_id}/participants")
def get_meeting_participants(
    book_id: int,
    admin_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db),
):
    """Получить список участников встречи (только для админов)."""
    # Проверяем, существует ли книга
    book = db.query(BookOfMonth).filter(BookOfMonth.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    participants = (
        db.query(MeetingRegistration, User)
        .join(User, MeetingRegistration.user_id == User.id)
        .filter(
            MeetingRegistration.book_id == book_id,
            MeetingRegistration.status == "registered",
        )
        .order_by(MeetingRegistration.registered_at.asc())
        .all()
    )

    return {
        "book_id": book_id,
        "book_title": book.title,
        "book_date": book.date,
        "book_location": book.location,
        "total_participants": len(participants),
        "participants": [
            {
                "registration_id": reg.id,
                "user_id": user.id,
                "user_name": f"{user.first_name} {user.last_name}".strip(),
                "user_email": user.email,
                "user_phone": user.phone,
                "registered_at": reg.registered_at,
            }
            for reg, user in participants
        ],
    }
