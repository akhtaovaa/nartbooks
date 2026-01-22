@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Запуск NartBooks Backend...
echo Backend будет доступен на: http://localhost:8000
echo API документация: http://localhost:8000/docs
echo.
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
if errorlevel 1 (
    echo.
    echo ОШИБКА при запуске!
    echo Убедитесь, что:
    echo 1. Python установлен
    echo 2. Зависимости установлены: pip install -r requirements.txt
    pause
)
