"""Запуск всех проверок кода (форматирование + линтинг)."""
import subprocess
import sys
from pathlib import Path

def main():
    """Запускает форматирование и линтинг."""
    project_root = Path(__file__).parent.parent
    
    print("🔍 Запуск проверок кода...\n")
    
    # Сначала форматируем
    print("1️⃣ Форматирование кода...")
    format_result = subprocess.run(
        ["ruff", "format", "app/", "scripts/"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if format_result.stdout:
        print(format_result.stdout)
    
    if format_result.returncode != 0:
        if format_result.stderr:
            print(format_result.stderr, file=sys.stderr)
        sys.exit(1)
    
    print("✅ Форматирование завершено\n")
    
    # Затем проверяем
    print("2️⃣ Проверка кода (линтинг)...")
    lint_result = subprocess.run(
        ["ruff", "check", "app/", "scripts/"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if lint_result.stdout:
        print(lint_result.stdout)
    
    if lint_result.returncode != 0:
        print("\n❌ Обнаружены ошибки в коде", file=sys.stderr)
        print("Запустите 'ruff check --fix app/' для автоматического исправления", file=sys.stderr)
        sys.exit(1)
    
    print("✅ Линтинг пройден успешно\n")
    print("🎉 Все проверки пройдены!")

if __name__ == "__main__":
    main()

