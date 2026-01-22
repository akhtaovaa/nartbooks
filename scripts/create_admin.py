#!/usr/bin/env python3
"""
Скрипт для создания администраторского аккаунта
"""

import sys
import os
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models import User, AuthCode
from app.enums import UserRole
from app.security import generate_verification_code

def create_admin_user(email: str, phone: str = None, first_name: str = "Admin", last_name: str = "User"):
    """Создает администраторского пользователя"""
    db: Session = SessionLocal()
    
    try:
        # Используем SQL напрямую для проверки и создания, чтобы избежать проблем с миграциями
        from sqlalchemy import text
        
        # Проверяем структуру таблицы и добавляем недостающие колонки
        table_info = db.execute(text("PRAGMA table_info(users)")).fetchall()
        columns = {row[1] for row in table_info}
        
        # Добавляем колонку role, если её нет
        if 'role' not in columns:
            try:
                db.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
                db.commit()
                print("ℹ️  Добавлена колонка 'role' в таблицу users")
            except Exception as e:
                print(f"⚠️  Не удалось добавить колонку role: {e}")
        
        # Проверяем, существует ли пользователь
        if 'role' in columns:
            result = db.execute(text("SELECT id, email, role FROM users WHERE email = :email"), {"email": email}).fetchone()
        else:
            result = db.execute(text("SELECT id, email FROM users WHERE email = :email"), {"email": email}).fetchone()
        
        if result:
            if len(result) >= 3:
                user_id, user_email, user_role = result[0], result[1], result[2]
            else:
                user_id, user_email = result[0], result[1]
                user_role = None
            
            print(f"⚠️  Пользователь с email {email} уже существует!")
            print(f"   ID: {user_id}")
            print(f"   Роль: {user_role or 'не указана'}")
            
            # Если пользователь существует, но не админ, делаем его админом
            if user_role != UserRole.ADMIN:
                db.execute(text("UPDATE users SET role = :role WHERE id = :id"), {"role": UserRole.ADMIN, "id": user_id})
                db.commit()
                print(f"✅ Роль пользователя изменена на 'admin'")
            else:
                print(f"✅ Пользователь уже является администратором")
        else:
            # Создаем нового пользователя-админа через SQL
            # Проверяем структуру таблицы
            table_info = db.execute(text("PRAGMA table_info(users)")).fetchall()
            columns = {row[1] for row in table_info}
            
            # Формируем SQL запрос в зависимости от структуры таблицы
            # Проверяем наличие колонок
            has_birthdate = 'birthdate' in columns or 'birth_date' in columns
            has_role = 'role' in columns
            has_discuss = 'discuss_books' in columns
            has_wanted = 'wanted_books' in columns
            
            # Формируем список колонок и значений
            cols = ["first_name", "last_name", "email"]
            vals = [":first_name", ":last_name", ":email"]
            params = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
            }
            
            if phone:
                cols.append("phone")
                vals.append(":phone")
                params["phone"] = phone
            
            if has_birthdate:
                cols.append("birthdate" if 'birthdate' in columns else "birth_date")
                vals.append("NULL")
            
            if has_role:
                cols.append("role")
                vals.append(":role")
                params["role"] = UserRole.ADMIN
            
            cols.extend(["fav_authors", "fav_genres", "fav_books"])
            vals.extend(["''", "''", "''"])
            
            if has_discuss:
                cols.append("discuss_books")
                vals.append("''")
            elif has_wanted:
                cols.append("wanted_books")
                vals.append("''")
            
            sql = f"INSERT INTO users ({', '.join(cols)}) VALUES ({', '.join(vals)})"
            db.execute(text(sql), params)
            db.commit()
            
            # Получаем ID созданного пользователя
            result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).fetchone()
            user_id = result[0]
            print(f"✅ Администраторский аккаунт создан!")
            print(f"   ID: {user_id}")
            print(f"   Email: {email}")
            print(f"   Роль: {UserRole.ADMIN}")
        
        # Создаем код авторизации для входа
        code = generate_verification_code()
        auth_code = AuthCode(
            identifier=email,
            code=code,
            created_at=datetime.now().isoformat(),
            is_used=0,
        )
        db.add(auth_code)
        db.commit()
        
        print(f"\n📧 Код авторизации создан!")
        print(f"   Email: {email}")
        print(f"   Код: {code}")
        print(f"\n🔐 Инструкция по входу:")
        print(f"   1. Откройте: http://localhost:8080/auth.html?redirect=admin.html")
        print(f"   2. Введите email: {email}")
        print(f"   3. Нажмите 'Отправить код'")
        print(f"   4. Введите код: {code}")
        print(f"   5. Нажмите 'Подтвердить код'")
        print(f"\n   Или используйте прямой URL:")
        print(f"   http://localhost:8080/admin.html")
        
        return user_id, code
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании администратора: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Создать администраторский аккаунт")
    parser.add_argument("--email", type=str, default="admin@nartbooks.local", help="Email администратора")
    parser.add_argument("--phone", type=str, default=None, help="Телефон администратора (опционально)")
    parser.add_argument("--first-name", type=str, default="Admin", help="Имя администратора")
    parser.add_argument("--last-name", type=str, default="User", help="Фамилия администратора")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Создание администраторского аккаунта для NartBooks")
    print("=" * 60)
    print()
    
    try:
        init_db()  # Инициализируем базу данных
        user, code = create_admin_user(
            email=args.email,
            phone=args.phone,
            first_name=args.first_name,
            last_name=args.last_name
        )
        print()
        print("=" * 60)
        print("✅ Готово! Администраторский аккаунт создан.")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Ошибка: {e}")
        print("=" * 60)
        sys.exit(1)
