#!/usr/bin/env python3
"""Тестовый скрипт для проверки новых функций: запись на встречи, выбор текущей книги, профиль"""

import json
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8080"

def make_request(method, path, data=None, token=None):
    """Выполнить HTTP запрос"""
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req = Request(url, data=json.dumps(data).encode() if data else None, headers=headers, method=method)
    
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode()), response.status
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else "{}"
        try:
            return json.loads(error_body), e.code
        except:
            return {"detail": error_body}, e.code

def test_auth():
    """Тест авторизации"""
    print("\n=== Тест авторизации ===")
    
    email = "admin@nartbooks.com"
    
    # Отправка кода
    resp, status = make_request("POST", "/auth/send-code", {"email": email})
    print(f"📧 Отправка кода: {status}")
    
    if status != 200:
        print(f"❌ Ошибка отправки кода: {resp}")
        return None
    
    code = resp.get("code")
    if not code:
        print(f"❌ Код не получен: {resp}")
        return None
    
    print(f"✅ Код получен: {code}")
    
    # Верификация
    time.sleep(1)  # Небольшая задержка
    resp, status = make_request("POST", "/auth/verify-code", {"email": email, "code": code})
    print(f"🔐 Верификация: {status}")
    
    if status != 200:
        print(f"❌ Ошибка верификации: {resp}")
        return None
    
    token = resp.get("access_token")
    if not token:
        print(f"❌ Токен не получен: {resp}")
        return None
    
    print(f"✅ Токен получен: {token[:50]}...")
    return token

def test_current_user(token):
    """Тест получения текущего пользователя"""
    print("\n=== Тест получения текущего пользователя ===")
    
    resp, status = make_request("GET", "/me", token=token)
    print(f"👤 GET /me: {status}")
    
    if status == 200:
        print(f"✅ Пользователь: {resp.get('first_name')} {resp.get('last_name')} ({resp.get('role')})")
        return resp
    else:
        print(f"❌ Ошибка: {resp}")
        return None

def test_books(token):
    """Тест работы с книгами"""
    print("\n=== Тест работы с книгами ===")
    
    # Получение списка книг
    resp, status = make_request("GET", "/books?limit=5", token=token)
    print(f"📚 GET /books: {status}")
    
    if status != 200:
        print(f"❌ Ошибка получения книг: {resp}")
        return None
    
    books = resp.get("items", [])
    print(f"✅ Найдено книг: {len(books)}")
    
    if not books:
        print("⚠️  Нет книг для тестирования")
        return None
    
    book = books[0]
    book_id = book.get("id")
    print(f"📖 Тестируем книгу ID {book_id}: {book.get('title')}")
    print(f"   is_current: {book.get('is_current')}, registered_count: {book.get('registered_count')}")
    
    return book_id

def test_set_current_book(token, book_id):
    """Тест установки текущей книги"""
    print("\n=== Тест установки текущей книги ===")
    
    resp, status = make_request("PUT", f"/books/{book_id}/set-current", token=token)
    print(f"⭐ PUT /books/{book_id}/set-current: {status}")
    
    if status == 200:
        print(f"✅ Книга установлена как текущая: {resp.get('title')}")
        return True
    else:
        print(f"❌ Ошибка: {resp}")
        return False

def test_register_for_meeting(token, book_id):
    """Тест записи на встречу"""
    print("\n=== Тест записи на встречу ===")
    
    resp, status = make_request("POST", f"/meetings/register/{book_id}", token=token)
    print(f"📝 POST /meetings/register/{book_id}: {status}")
    
    if status == 201:
        print(f"✅ Запись успешна: {resp.get('message')}")
        return True
    else:
        print(f"❌ Ошибка: {resp}")
        return False

def test_my_meetings(token):
    """Тест получения моих встреч"""
    print("\n=== Тест получения моих встреч ===")
    
    resp, status = make_request("GET", "/meetings/my", token=token)
    print(f"📅 GET /meetings/my: {status}")
    
    if status == 200:
        meetings = resp.get("items", [])
        print(f"✅ Найдено встреч: {len(meetings)}")
        for meeting in meetings:
            print(f"   - {meeting.get('book_title')} ({meeting.get('book_date')})")
        return True
    else:
        print(f"❌ Ошибка: {resp}")
        return False

def test_users_list(token):
    """Тест получения списка пользователей (админ)"""
    print("\n=== Тест получения списка пользователей ===")
    
    resp, status = make_request("GET", "/users/users?limit=5", token=token)
    print(f"👥 GET /users/users: {status}")
    
    if status == 200:
        users = resp.get("items", [])
        print(f"✅ Найдено пользователей: {len(users)}")
        for user in users[:3]:
            stats = f"Встреч: {user.get('meetings_count', 0)}, Избранных: {user.get('favorites_count', 0)}, Отзывов: {user.get('reviews_count', 0)}"
            print(f"   - {user.get('first_name')} {user.get('last_name')} ({user.get('role')}) - {stats}")
        return True
    else:
        print(f"❌ Ошибка: {resp}")
        return False

def test_current_book():
    """Тест получения текущей книги"""
    print("\n=== Тест получения текущей книги ===")
    
    resp, status = make_request("GET", "/books/current")
    print(f"📖 GET /books/current: {status}")
    
    if status == 200:
        print(f"✅ Текущая книга: {resp.get('title')}")
        print(f"   ID: {resp.get('id')}, is_current: {resp.get('is_current')}, записавшихся: {resp.get('registered_count')}")
        return True
    else:
        print(f"❌ Ошибка: {resp}")
        return False

def main():
    print("=" * 60)
    print("🧪 Тестирование новых функций NartBooks")
    print("=" * 60)
    
    # Тест авторизации
    token = test_auth()
    if not token:
        print("\n❌ Не удалось получить токен. Прерываем тесты.")
        sys.exit(1)
    
    # Тест получения текущего пользователя
    user = test_current_user(token)
    if not user:
        print("\n⚠️  Не удалось получить данные пользователя, но продолжаем...")
    
    # Тест работы с книгами
    book_id = test_books(token)
    
    # Тест установки текущей книги
    if book_id:
        test_set_current_book(token, book_id)
        time.sleep(0.5)
        test_current_book()  # Проверяем, что книга действительно текущая
    
    # Тест записи на встречу
    if book_id:
        test_register_for_meeting(token, book_id)
        time.sleep(0.5)
        test_my_meetings(token)
    
    # Тест получения списка пользователей (только для админа)
    if user and user.get("role") == "admin":
        test_users_list(token)
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    print("=" * 60)
    print(f"\n🌐 Фронтенд доступен по адресу: {FRONTEND_URL}")
    print(f"📡 API доступен по адресу: {BASE_URL}")

if __name__ == "__main__":
    main()
