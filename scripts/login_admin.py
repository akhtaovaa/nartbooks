#!/usr/bin/env python3
"""
Скрипт для входа администратора и получения токена
"""

import sys
import os
import requests
import json

API_BASE_URL = "http://localhost:8000"

def login_admin(email: str, code: str):
    """Вход администратора и получение токена"""
    try:
        # Верифицируем код
        response = requests.post(
            f"{API_BASE_URL}/auth/verify-code",
            json={"email": email, "code": code},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            
            print("=" * 60)
            print("✅ Авторизация успешна!")
            print("=" * 60)
            print(f"\n📧 Email: {email}")
            print(f"🔑 Токен: {token[:50]}...")
            print(f"\n💾 Токен сохранён в localStorage браузера")
            print(f"\n🌐 Откройте админ-панель:")
            print(f"   http://localhost:8080/admin.html")
            print(f"\n📋 Или используйте этот токен в запросах:")
            print(f"   Authorization: Bearer {token}")
            
            return token
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("detail", f"Ошибка {response.status_code}")
            print(f"❌ Ошибка авторизации: {error_msg}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу.")
        print("   Убедитесь, что бэкенд запущен на http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Войти как администратор")
    parser.add_argument("--email", type=str, default="admin@nartbooks.local", help="Email администратора")
    parser.add_argument("--code", type=str, help="Код авторизации (если не указан, будет создан новый)")
    
    args = parser.parse_args()
    
    if not args.code:
        print("=" * 60)
        print("Вход администратора")
        print("=" * 60)
        print(f"\n📧 Email: {args.email}")
        print("\n⚠️  Код не указан. Сначала нужно получить код:")
        print(f"   1. Откройте: http://localhost:8080/auth.html")
        print(f"   2. Введите email: {args.email}")
        print(f"   3. Нажмите 'Отправить код'")
        print(f"   4. Используйте полученный код с этим скриптом:")
        print(f"      python scripts/login_admin.py --email {args.email} --code <КОД>")
        sys.exit(1)
    
    token = login_admin(args.email, args.code)
    
    if token:
        print("\n" + "=" * 60)
        print("✅ Готово!")
        print("=" * 60)
