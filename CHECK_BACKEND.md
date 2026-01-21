# Проверка бэкенда - Инструкция

## Быстрая проверка

```bash
# 1. Проверить, запущен ли бэкенд
ps aux | grep uvicorn | grep -v grep

# 2. Проверить порт 8000
lsof -i :8000

# 3. Проверить доступность API
curl http://localhost:8000/

# 4. Проверить документацию
curl http://localhost:8000/docs

# 5. Создать код для входа
cd /Users/gwuino/Developer/re/nartbooks
source venv/bin/activate
python scripts/create_admin.py --email admin@nartbooks.com
```

## Если бэкенд не запущен

```bash
cd /Users/gwuino/Developer/re/nartbooks
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Если есть ошибки

1. Проверьте логи в терминале, где запущен uvicorn
2. Проверьте структуру базы данных
3. Убедитесь, что все зависимости установлены
