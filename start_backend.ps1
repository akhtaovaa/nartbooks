# Скрипт запуска backend для NartBooks
$ErrorActionPreference = "Continue"

# Переходим в директорию скрипта
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Запуск NartBooks Backend..." -ForegroundColor Green
Write-Host "Backend будет доступен на: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API документация: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Устанавливаем PYTHONPATH для текущей директории
$env:PYTHONPATH = $scriptDir

try {
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
} catch {
    Write-Host "Ошибка при запуске:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Убедитесь, что:" -ForegroundColor Yellow
    Write-Host "1. Python установлен и доступен в PATH" -ForegroundColor Yellow
    Write-Host "2. Все зависимости установлены: pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
}
