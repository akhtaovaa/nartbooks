"""User-related endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from sqlalchemy import func, or_

from ..dependencies import get_current_user, get_db, require_admin_role
from ..models import BookOfMonth, Favorite, MeetingRegistration, Review, User
from ..schemas import RoleUpdate, UserCreate, UserUpdate

# Импорт для получения сессии БД
from sqlalchemy.orm import Session

router = APIRouter(tags=["Пользователи"])


@router.post("/register", include_in_schema=False, status_code=status.HTTP_201_CREATED)
def register_user(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        birthdate=data.birth_date,  # Используем birthdate из БД
        fav_authors=", ".join(data.fav_authors),
        fav_genres=", ".join(data.fav_genres),
        fav_books=", ".join(data.fav_books),
        wanted_books=", ".join(data.discuss_books),  # Используем wanted_books из БД
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Регистрация прошла успешно!", "user_id": user.id}


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Обновляем роль из БД (на случай если она была изменена)
    # Убеждаемся, что роль корректна - всегда берём из БД, а не из токена
    user_role = current_user.role if current_user.role and current_user.role.strip() else "user"
    if user_role.lower() not in ['admin', 'user']:
        user_role = "user"
        # Обновляем роль в БД если она некорректна
        current_user.role = user_role
        db.commit()
        db.refresh(current_user)
    
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "birth_date": current_user.birthdate,  # Используем birthdate из БД
        "role": user_role,  # Возвращаем проверенную роль из БД, а не из токена
        "fav_authors": current_user.fav_authors.split(", ") if current_user.fav_authors else [],
        "fav_genres": current_user.fav_genres.split(", ") if current_user.fav_genres else [],
        "fav_books": current_user.fav_books.split(", ") if current_user.fav_books else [],
        "discuss_books": (current_user.wanted_books or "").split(", ") if current_user.wanted_books else [],  # Используем wanted_books из БД
    }


@router.patch("/me")
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.birth_date is not None:
        current_user.birthdate = user_update.birth_date  # Используем birthdate из БД
    if user_update.fav_authors is not None:
        current_user.fav_authors = ", ".join(user_update.fav_authors)
    if user_update.fav_genres is not None:
        current_user.fav_genres = ", ".join(user_update.fav_genres)
    if user_update.fav_books is not None:
        current_user.fav_books = ", ".join(user_update.fav_books)
    if user_update.discuss_books is not None:
        current_user.wanted_books = ", ".join(user_update.discuss_books)  # Используем wanted_books из БД

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Профиль успешно обновлен",
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "birth_date": current_user.birthdate,  # Используем birthdate из БД
        "role": current_user.role,
        "fav_authors": current_user.fav_authors.split(", ") if current_user.fav_authors else [],
        "fav_genres": current_user.fav_genres.split(", ") if current_user.fav_genres else [],
        "fav_books": current_user.fav_books.split(", ") if current_user.fav_books else [],
        "discuss_books": (current_user.wanted_books or "").split(", ") if current_user.wanted_books else [],  # Используем wanted_books из БД
    }


@router.put("/users/{id}/role")
def update_user_role(
    id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_role),
):
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
        "role": user.role,
    }


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Поиск по имени или email"),
    role: Optional[str] = Query(None, description="Фильтр по роли"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_role),
):
    base_query = db.query(User)
    
    # Фильтр по роли
    if role:
        base_query = base_query.filter(User.role == role)
    
    # Поиск по имени или email
    if search:
        search_pattern = f"%{search}%"
        base_query = base_query.filter(
            or_(
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    total = base_query.count()
    offset_value = (page - 1) * limit
    users = base_query.order_by(User.id.desc()).offset(offset_value).limit(limit).all()
    total_pages = (total + limit - 1) // limit if total else 0

    # Подсчитываем статистику для каждого пользователя
    user_ids = [u.id for u in users]
    stats_map = {}
    
    if user_ids:
        # Количество записей на встречи
        meeting_stats = (
            db.query(
                MeetingRegistration.user_id,
                func.count(MeetingRegistration.id).label("meetings_count")
            )
            .filter(
                MeetingRegistration.user_id.in_(user_ids),
                MeetingRegistration.status == "registered"
            )
            .group_by(MeetingRegistration.user_id)
            .all()
        )
        
        # Количество избранных книг
        favorite_stats = (
            db.query(
                Favorite.user_id,
                func.count(Favorite.id).label("favorites_count")
            )
            .filter(Favorite.user_id.in_(user_ids))
            .group_by(Favorite.user_id)
            .all()
        )
        
        # Количество отзывов
        review_stats = (
            db.query(
                Review.user_id,
                func.count(Review.id).label("reviews_count")
            )
            .filter(Review.user_id.in_(user_ids))
            .group_by(Review.user_id)
            .all()
        )
        
        # Собираем статистику
        for u_id in user_ids:
            stats_map[u_id] = {
                "meetings_count": 0,
                "favorites_count": 0,
                "reviews_count": 0,
            }
        
        for stat in meeting_stats:
            stats_map[stat.user_id]["meetings_count"] = stat.meetings_count
        
        for stat in favorite_stats:
            stats_map[stat.user_id]["favorites_count"] = stat.favorites_count
        
        for stat in review_stats:
            stats_map[stat.user_id]["reviews_count"] = stat.reviews_count

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
                "birth_date": u.birthdate,  # Используем birthdate из БД
                "role": u.role,
                "created_at": u.created_at if hasattr(u, 'created_at') else None,
                "meetings_count": stats_map.get(u.id, {}).get("meetings_count", 0),
                "favorites_count": stats_map.get(u.id, {}).get("favorites_count", 0),
                "reviews_count": stats_map.get(u.id, {}).get("reviews_count", 0),
            }
            for u in users
        ],
    }


@router.get("/users/{id}")
def get_user_by_id(
    id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_role),
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем статистику
    meetings_count = (
        db.query(func.count(MeetingRegistration.id))
        .filter(
            MeetingRegistration.user_id == id,
            MeetingRegistration.status == "registered"
        )
        .scalar()
    ) or 0
    
    favorites_count = (
        db.query(func.count(Favorite.id))
        .filter(Favorite.user_id == id)
        .scalar()
    ) or 0
    
    reviews_count = (
        db.query(func.count(Review.id))
        .filter(Review.user_id == id)
        .scalar()
    ) or 0
    
    # Получаем список записанных встреч
    registrations = (
        db.query(MeetingRegistration, BookOfMonth)
        .join(BookOfMonth, MeetingRegistration.book_id == BookOfMonth.id)
        .filter(
            MeetingRegistration.user_id == id,
            MeetingRegistration.status == "registered"
        )
        .order_by(MeetingRegistration.id.desc())
        .limit(10)
        .all()
    )
    
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "birth_date": user.birthdate,  # Используем birthdate из БД
        "role": user.role,
        "created_at": user.created_at if hasattr(user, 'created_at') else None,
        "fav_authors": user.fav_authors.split(", ") if user.fav_authors else [],
        "fav_genres": user.fav_genres.split(", ") if user.fav_genres else [],
        "fav_books": user.fav_books.split(", ") if user.fav_books else [],
        "discuss_books": (user.wanted_books or "").split(", ") if user.wanted_books else [],  # Используем wanted_books из БД
        "statistics": {
            "meetings_count": meetings_count,
            "favorites_count": favorites_count,
            "reviews_count": reviews_count,
        },
        "registered_meetings": [
            {
                "book_id": book.id,
                "book_title": book.title,
                "book_author": book.author,
                "book_date": book.date,
                "book_location": book.location,
                "registered_at": reg.registered_at,
            }
            for reg, book in registrations
        ],
    }

