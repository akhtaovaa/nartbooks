# Руководство по разработке

## Быстрый старт для разработчиков

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка pre-commit хуков

После установки зависимостей установите pre-commit хуки:

```bash
pre-commit install
```

Теперь перед каждым коммитом будут автоматически выполняться проверки кода.

### 3. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
# На Linux/Mac
cp .env.example .env

# На Windows
copy .env.example .env
```

Отредактируйте `.env` файл с вашими настройками.

## Работа с кодом

### Форматирование кода

Автоматически форматировать весь код:

```bash
# Через ruff напрямую
ruff format app/

# Или через скрипт
python scripts/format.py
```

### Проверка кода (линтинг)

Проверить код на ошибки:

```bash
# Через ruff напрямую
ruff check app/

# Автоматически исправить исправимые ошибки
ruff check --fix app/

# Или через скрипт
python scripts/lint.py
```

### Запуск всех проверок

Запустить форматирование и линтинг вместе:

```bash
python scripts/check.py
```

## Pre-commit хуки

После установки (`pre-commit install`) хуки будут автоматически запускаться перед каждым коммитом.

Если нужно пропустить хуки (не рекомендуется):

```bash
git commit --no-verify -m "your message"
```

Запустить хуки вручную для всех файлов:

```bash
pre-commit run --all-files
```

## Структура проекта

- `app/` - основной код приложения
- `scripts/` - вспомогательные скрипты для разработки
- `pyproject.toml` - конфигурация Ruff
- `.pre-commit-config.yaml` - конфигурация pre-commit хуков

## Полезные команды

```bash
# Запуск сервера разработки
uvicorn app.main:app --reload

# Просмотр документации API
# Откройте http://localhost:8000/docs в браузере

# Проверка всех зависимостей на обновления
pip list --outdated

# Обновление ruff
pip install --upgrade ruff

# Обновление pre-commit
pip install --upgrade pre-commit
```

