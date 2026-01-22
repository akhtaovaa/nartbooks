"""Authorization related endpoints."""

from datetime import datetime, timedelta
from typing import Dict

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import JWT_EXPIRATION_HOURS, MSG_OVRX_BASE_URL, MSG_OVRX_API_KEY
from ..dependencies import get_db
from ..enums import UserRole
from ..models import AuthCode, AuthToken, User
from ..schemas import AuthRequest, AuthVerify
from ..security import cleanup_old_codes, create_access_token, generate_verification_code
from fastapi import HTTPException

router = APIRouter(prefix="/auth", tags=["Авторизация"])

# Track last send time per identifier (1 per minute limit)
last_sent: Dict[str, datetime] = {}


@router.post("/send-code")
def send_auth_code(req: AuthRequest, db: Session = Depends(get_db)):
    identifier = req.email or req.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Укажите email или телефон")

    cleanup_old_codes(db)

    if identifier in last_sent and datetime.now() - last_sent[identifier] < timedelta(minutes=1):
        raise HTTPException(status_code=429, detail="Можно отправлять код не чаще 1 раза в минуту")

    code = generate_verification_code()
    payload = {"email": req.email, "code": code} if req.email else {"phone": req.phone, "code": code}

    # Проверяем, включен ли режим разработки (когда API ключ не настроен)
    dev_mode = not MSG_OVRX_API_KEY or MSG_OVRX_API_KEY == "ТВОЙ_API_КЛЮЧ" or MSG_OVRX_API_KEY == "your_api_key_here"
    
    if not dev_mode:
        try:
            endpoint = "email" if req.email else "sms"
            headers = {}
            if MSG_OVRX_API_KEY:
                headers["Authorization"] = f"Bearer {MSG_OVRX_API_KEY}"
                headers["X-API-Key"] = MSG_OVRX_API_KEY
            
            response = requests.post(
                f"{MSG_OVRX_BASE_URL}/auth-code/{endpoint}",
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            # В режиме разработки сохраняем код даже при ошибке отправки
            if dev_mode:
                pass
            else:
                raise HTTPException(status_code=500, detail="Таймаут при отправке кода. Попробуйте позже.")
        except requests.exceptions.ConnectionError:
            # В режиме разработки сохраняем код даже при ошибке отправки
            if dev_mode:
                pass
            else:
                raise HTTPException(status_code=500, detail="Не удалось подключиться к сервису отправки. Проверьте подключение к интернету.")
        except requests.exceptions.HTTPError as e:
            # Если ошибка 502 или другая ошибка сервиса, в режиме разработки продолжаем
            if dev_mode or e.response.status_code in [502, 503, 504]:
                pass
            else:
                error_detail = f"Ошибка сервиса отправки: {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    if "detail" in error_data:
                        error_detail = error_data["detail"]
                except:
                    pass
                raise HTTPException(status_code=500, detail=error_detail)
        except Exception as exc:
            # В режиме разработки продолжаем даже при других ошибках
            if not dev_mode:
                raise HTTPException(status_code=500, detail=f"Ошибка при отправке кода: {str(exc)}")

    # Сохраняем код в базе данных (всегда, даже если отправка не удалась)
    auth_code = AuthCode(
        identifier=identifier,
        code=code,
        created_at=datetime.now().isoformat(),
        is_used=0,
    )
    db.add(auth_code)
    db.commit()

    last_sent[identifier] = datetime.now()
    
    # В режиме разработки возвращаем код в ответе
    if dev_mode:
        return {
            "message": "Код создан (режим разработки). Сервис отправки недоступен.",
            "code": code,  # Возвращаем код для режима разработки
            "dev_mode": True
        }
    
    return {"message": "Код отправлен успешно"}


@router.post("/verify-code")
def verify_auth_code(req: AuthVerify, db: Session = Depends(get_db)):
    identifier = req.email or req.phone
    if not identifier:
        raise HTTPException(status_code=400, detail="Укажите email или телефон")

    auth_code = (
        db.query(AuthCode)
        .filter(AuthCode.identifier == identifier, AuthCode.code == req.code, AuthCode.is_used == 0)
        .first()
    )
    if not auth_code:
        raise HTTPException(status_code=400, detail="Неверный код или код уже использован")

    code_created = datetime.fromisoformat(auth_code.created_at)
    if datetime.now() - code_created > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="Код истек")

    auth_code.is_used = 1
    db.commit()

    # Ищем пользователя по email или phone
    # ВАЖНО: используем req.email или req.phone напрямую, не identifier
    user = None
    if req.email:
        user = db.query(User).filter(User.email == req.email).first()
    elif req.phone:
        user = db.query(User).filter(User.phone == req.phone).first()
    
    # Проверяем email - только определённые адреса могут быть админами
    admin_emails = ['admin@nartbooks.com', 'admin@nartbooks.local']
    is_admin_email = req.email and req.email.lower() in [e.lower() for e in admin_emails]
    
    if not user:
        # Создаём нового пользователя
        # Если это админский email, устанавливаем роль admin, иначе user
        initial_role = UserRole.ADMIN.value if is_admin_email else UserRole.USER.value
        user = User(
            first_name="",
            last_name="",
            email=req.email or "",
            phone=req.phone or "",
            fav_authors="",
            fav_genres="",
            fav_books="",
            wanted_books="",  # Используем wanted_books из БД
            role=initial_role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # КРИТИЧЕСКАЯ ПРОВЕРКА: убеждаемся, что это правильный пользователь
    # и что роль корректна
    if req.email and user.email != req.email:
        raise HTTPException(status_code=500, detail="Ошибка: найден неправильный пользователь")
    if req.phone and user.phone != req.phone:
        raise HTTPException(status_code=500, detail="Ошибка: найден неправильный пользователь")
    
    # Убеждаемся, что роль установлена и корректна
    user_role = user.role if user.role and user.role.strip() else UserRole.USER.value
    
    # ДОПОЛНИТЕЛЬНАЯ ЗАЩИТА: если пользователь не является явно админом, устанавливаем user
    # Если email админский, устанавливаем роль admin (если еще не установлена)
    if is_admin_email:
        if user_role.lower() != 'admin':
            user_role = UserRole.ADMIN.value
            user.role = user_role
            db.commit()
            db.refresh(user)
    else:
        # Если email не в списке админов, принудительно устанавливаем роль user
        if user_role.lower() != 'user':
            user_role = UserRole.USER.value
            user.role = user_role
            db.commit()
            db.refresh(user)
    
    # Дополнительная проверка: если роль не admin и не user, устанавливаем user
    if user_role.lower() not in ['admin', 'user']:
        user_role = UserRole.USER.value
        user.role = user_role
        db.commit()
        db.refresh(user)
    
    access_token = create_access_token(user.id, user_role)

    now = datetime.now()
    expires_at = now + timedelta(hours=JWT_EXPIRATION_HOURS)

    auth_token = AuthToken(
        user_id=user.id,
        token=access_token,
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        is_active=1,
    )
    db.add(auth_token)
    db.commit()

    return {
        "message": "Авторизация успешна",
        "user_id": user.id,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
    }

