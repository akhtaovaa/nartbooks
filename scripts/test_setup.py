"""Проверка работоспособности инструментов разработки."""
import subprocess
import sys
from pathlib import Path

def check_command(command, description):
    """Проверяет наличие команды в системе."""
    try:
        result = subprocess.run(
            command.split() + ["--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"✅ {description}: {version}")
            return True
        else:
            print(f"❌ {description}: команда не найдена")
            return False
    except FileNotFoundError:
        print(f"❌ {description}: команда не установлена")
        return False
    except Exception as e:
        print(f"⚠️ {description}: ошибка проверки - {e}")
        return False

def check_file_exists(filepath, description):
    """Проверяет наличие файла."""
    if Path(filepath).exists():
        print(f"✅ {description}: файл существует")
        return True
    else:
        print(f"❌ {description}: файл не найден")
        return False

def main():
    """Запускает все проверки."""
    print("🔍 Проверка работоспособности инструментов разработки\n")
    
    results = []
    
    # Проверка файлов конфигурации
    print("📁 Проверка конфигурационных файлов:")
    results.append(check_file_exists("pyproject.toml", "pyproject.toml"))
    results.append(check_file_exists(".pre-commit-config.yaml", ".pre-commit-config.yaml"))
    results.append(check_file_exists("requirements.txt", "requirements.txt"))
    results.append(check_file_exists(".env.example", ".env.example"))
    print()
    
    # Проверка установленных инструментов
    print("🛠️ Проверка установленных инструментов:")
    results.append(check_command("ruff", "ruff"))
    results.append(check_command("pre-commit", "pre-commit"))
    print()
    
    # Проверка скриптов
    print("📜 Проверка скриптов:")
    results.append(check_file_exists("scripts/format.py", "scripts/format.py"))
    results.append(check_file_exists("scripts/lint.py", "scripts/lint.py"))
    results.append(check_file_exists("scripts/check.py", "scripts/check.py"))
    print()
    
    # Итоги
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Результаты: {passed}/{total} проверок пройдено")
    
    if passed == total:
        print("🎉 Все проверки пройдены успешно!")
        return 0
    else:
        print("⚠️ Некоторые проверки не пройдены. Установите недостающие инструменты:")
        print("   pip install -r requirements.txt")
        print("   pre-commit install")
        return 1

if __name__ == "__main__":
    sys.exit(main())

