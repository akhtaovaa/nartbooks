"""Автоматическое форматирование кода."""
import subprocess
import sys
from pathlib import Path

def main():
    """Форматирует весь код проекта."""
    project_root = Path(__file__).parent.parent
    
    # Форматируем код
    result = subprocess.run(
        ["ruff", "format", "app/", "scripts/"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)
    
    print("✅ Код отформатирован успешно")

if __name__ == "__main__":
    main()

