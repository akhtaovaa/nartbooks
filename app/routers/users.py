"""User-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db, require_admin_role
from ..models import User
from ..schemas import RoleUpdate, UserCreate, UserUpdate

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
        birth_date=data.birth_date,
        fav_authors=", ".join(data.fav_authors),
        fav_genres=", ".join(data.fav_genres),
        fav_books=", ".join(data.fav_books),
        discuss_books=", ".join(data.discuss_books),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Регистрация прошла успешно!", "user_id": user.id}


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
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
        "discuss_books": current_user.discuss_books.split(", ") if current_user.discuss_books else [],
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
        "discuss_books": current_user.discuss_books.split(", ") if current_user.discuss_books else [],
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
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_role),
):
    total = db.query(User).count()
    offset_value = (page - 1) * limit
    users = db.query(User).order_by(User.id.desc()).offset(offset_value).limit(limit).all()
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


@router.get("/users/{id}")
def get_user_by_id(
    id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_role),
):
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

