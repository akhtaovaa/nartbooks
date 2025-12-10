"""Проверка кода на ошибки."""
import subprocess
import sys
from pathlib import Path

def main():
    """Проверяет код на ошибки."""
    project_root = Path(__file__).parent.parent
    
    # Проверяем код
    result = subprocess.run(
        ["ruff", "check", "app/", "scripts/"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        print("\n❌ Обнаружены ошибки в коде", file=sys.stderr)
        print("Запустите 'ruff check --fix app/' для автоматического исправления", file=sys.stderr)
        sys.exit(1)
    
    print("✅ Линтинг пройден успешно")

if __name__ == "__main__":
    main()

