#!/usr/bin/env python3
"""
Утилита для переключения режимов работы MAS
"""

import argparse
import os
from pathlib import Path


def get_project_root() -> Path:
    """Найти корень проекта"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / ".env.example").exists():
            return current
        current = current.parent
    return Path.cwd()


def update_env_file(goal: str, env_file: Path = None) -> None:
    """Обновить MAS_GOAL в .env файле"""
    if env_file is None:
        env_file = get_project_root() / ".env"
    
    if not env_file.exists():
        print(f"❌ Файл {env_file} не найден!")
        print("Создайте .env файл на основе .env.example")
        return
    
    # Читаем текущий .env
    content = env_file.read_text()
    lines = content.split('\n')
    
    # Обновляем или добавляем MAS_GOAL
    mas_goal_updated = False
    for i, line in enumerate(lines):
        if line.startswith('MAS_GOAL='):
            lines[i] = f'MAS_GOAL={goal}'
            mas_goal_updated = True
            break
    
    if not mas_goal_updated:
        lines.append(f'MAS_GOAL={goal}')
    
    # Записываем обратно
    env_file.write_text('\n'.join(lines))
    print(f"✅ MAS_GOAL обновлен в {env_file}")


def main():
    parser = argparse.ArgumentParser(description="Переключение режимов работы MAS")
    
    # Предустановленные режимы
    parser.add_argument('--proactive', action='store_true', 
                       help='Режим проактивного AI-ассистента')
    parser.add_argument('--test', action='store_true', 
                       help='Тестовый режим (echo)')
    parser.add_argument('--coding', action='store_true', 
                       help='Помощник по программированию')
    parser.add_argument('--productivity', action='store_true', 
                       help='Помощник по продуктивности')
    
    # Кастомная цель
    parser.add_argument('--custom', type=str, 
                       help='Кастомная цель для MAS')
    
    # Файл .env
    parser.add_argument('--env-file', type=Path, 
                       help='Путь к .env файлу (по умолчанию: .env в корне проекта)')
    
    # Показать текущую цель
    parser.add_argument('--show', action='store_true', 
                       help='Показать текущую цель')
    
    args = parser.parse_args()
    
    env_file = args.env_file or get_project_root() / ".env"
    
    # Показать текущую цель
    if args.show:
        if env_file.exists():
            content = env_file.read_text()
            for line in content.split('\n'):
                if line.startswith('MAS_GOAL='):
                    current_goal = line.split('=', 1)[1]
                    print(f"Текущая цель: {current_goal}")
                    return
            print("MAS_GOAL не найден в .env файле")
        else:
            print(f"❌ Файл {env_file} не найден!")
        return
    
    # Определить цель
    goal = None
    
    if args.proactive:
        goal = "act as a proactive AI assistant helping with any questions and tasks"
        print("🤖 Режим: Проактивный AI-ассистент")
    elif args.test:
        goal = "echo"
        print("🔧 Режим: Тестовый")
    elif args.coding:
        goal = "be my coding assistant and help with development tasks"
        print("💻 Режим: Помощник по программированию")
    elif args.productivity:
        goal = "act as my personal productivity assistant"
        print("📊 Режим: Помощник по продуктивности")
    elif args.custom:
        goal = args.custom
        print(f"🎯 Кастомный режим: {goal}")
    else:
        print("❌ Не указан режим работы!")
        print("\nДоступные режимы:")
        print("  --proactive     Проактивный AI-ассистент")
        print("  --test          Тестовый режим")
        print("  --coding        Помощник по программированию")
        print("  --productivity  Помощник по продуктивности")
        print("  --custom 'цель' Кастомная цель")
        print("  --show          Показать текущую цель")
        return
    
    # Обновить .env файл
    update_env_file(goal, env_file)
    
    print("\n📋 Следующие шаги:")
    if os.path.exists("deploy/deploy.sh"):
        print("  sudo ./deploy/deploy.sh restart")
    else:
        print("  docker-compose restart")
    print("  или перезапустите приложение для применения изменений")


if __name__ == "__main__":
    main()