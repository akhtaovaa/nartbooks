"""Скрипт для добавления тестового кода авторизации в базу данных.
Используется для тестирования авторизации в режиме разработки.
"""
import sys
import os
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import AuthCode

def add_test_code(identifier: str, code: str):
    """Добавляет тестовый код в базу данных."""
    db = SessionLocal()
    try:
        # Удаляем старые коды для этого идентификатора
        db.query(AuthCode).filter(AuthCode.identifier == identifier).delete()
        
        # Добавляем новый код
        auth_code = AuthCode(
            identifier=identifier,
            code=code,
            created_at=datetime.now().isoformat(),
            is_used=0,
        )
        db.add(auth_code)
        db.commit()
        print(f"✅ Код {code} успешно добавлен для {identifier}")
        print(f"   Используйте этот код для входа через /auth/verify-code")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python scripts/add_test_code.py <email_or_phone> <code>")
        print("Пример: python scripts/add_test_code.py test@example.com 123456")
        sys.exit(1)
    
    identifier = sys.argv[1]
    code = sys.argv[2]
    add_test_code(identifier, code)
