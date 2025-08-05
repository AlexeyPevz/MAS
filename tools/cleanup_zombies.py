#!/usr/bin/env python3
"""
Утилита для очистки зомби-процессов
"""
import os
import sys
import time
import signal

try:
    import psutil
except ImportError:
    print("❌ Требуется установить psutil: pip install psutil")
    sys.exit(1)


def cleanup_zombies():
    """Очистка зомби-процессов"""
    zombie_count = 0
    cleaned_count = 0
    
    print("🔍 Поиск зомби-процессов...")
    
    for proc in psutil.process_iter(['pid', 'ppid', 'name', 'status', 'create_time']):
        try:
            if proc.info['status'] == psutil.STATUS_ZOMBIE:
                zombie_count += 1
                age = time.time() - proc.info['create_time']
                age_str = f"{int(age/3600)}ч {int((age%3600)/60)}м" if age > 3600 else f"{int(age/60)}м"
                
                print(f"🧟 Зомби PID: {proc.info['pid']}, "
                      f"Имя: {proc.info['name']}, "
                      f"PPID: {proc.info['ppid']}, "
                      f"Возраст: {age_str}")
                
                # Если родитель - init (PID 1), зомби можно попытаться очистить
                if proc.info['ppid'] == 1:
                    try:
                        # Пытаемся очистить через waitpid
                        pid, status = os.waitpid(proc.info['pid'], os.WNOHANG)
                        if pid != 0:
                            cleaned_count += 1
                            print(f"  ✅ Очищен зомби PID: {pid}")
                    except:
                        print(f"  ❌ Не удалось очистить PID: {proc.info['pid']}")
                else:
                    # Если родитель не init, пытаемся послать SIGCHLD родителю
                    try:
                        parent = psutil.Process(proc.info['ppid'])
                        os.kill(proc.info['ppid'], signal.SIGCHLD)
                        print(f"  📨 Отправлен SIGCHLD родителю PID: {proc.info['ppid']}")
                    except:
                        print(f"  ⚠️ Родитель недоступен")
                        
        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            pass
    
    print(f"\n📊 Статистика:")
    print(f"  Найдено зомби: {zombie_count}")
    print(f"  Очищено: {cleaned_count}")
    
    if zombie_count == 0:
        print("✨ Зомби-процессов не найдено!")
    elif cleaned_count < zombie_count:
        print("\n⚠️ Некоторые зомби не удалось очистить.")
        print("💡 Попробуйте:")
        print("   1. Запустить с sudo: sudo python3 cleanup_zombies.py")
        print("   2. Перезагрузить систему")
        print("   3. Найти и перезапустить родительские процессы")


def show_process_tree():
    """Показать дерево процессов с зомби"""
    print("\n🌳 Дерево процессов с зомби:")
    
    zombies = []
    for proc in psutil.process_iter(['pid', 'ppid', 'name', 'status']):
        try:
            if proc.info['status'] == psutil.STATUS_ZOMBIE:
                zombies.append(proc.info)
        except:
            pass
    
    if zombies:
        for zombie in sorted(zombies, key=lambda x: x['ppid']):
            print(f"  └─ PID: {zombie['pid']} ({zombie['name']}) "
                  f"← Родитель: {zombie['ppid']}")
            
            # Показываем информацию о родителе
            try:
                parent = psutil.Process(zombie['ppid'])
                print(f"     └─ Родитель: {parent.name()} (PID: {parent.pid})")
            except:
                print(f"     └─ Родитель: недоступен")


if __name__ == "__main__":
    print("🧹 Утилита очистки зомби-процессов")
    print("=" * 40)
    
    cleanup_zombies()
    show_process_tree()
    
    print("\n✅ Завершено!")