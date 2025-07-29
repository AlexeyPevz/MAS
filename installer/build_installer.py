#!/usr/bin/env python3
"""
Build script для создания исполняемого инсталлятора
Компилирует MAS инсталлятор в standalone .exe файл
"""

import os
import subprocess
import sys
from pathlib import Path
import shutil

def check_pyinstaller():
    """Проверяем наличие PyInstaller"""
    try:
        import PyInstaller
        print("✅ PyInstaller найден")
        return True
    except ImportError:
        print("❌ PyInstaller не найден. Устанавливаем...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        return True

def create_installer_spec():
    """Создаем .spec файл для PyInstaller"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['mas_installer.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('web_installer.html', '.'),
        ('../requirements.txt', 'mas_system'),
        ('../config', 'mas_system/config'),
        ('../deploy.sh', 'mas_system'),
        ('../docker-compose.*.yml', 'mas_system'),
        ('../production_launcher.py', 'mas_system'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'requests',
        'yaml',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MAS-System-Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI приложение
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='mas_icon.ico',  # Иконка приложения
)
'''
    
    with open('mas_installer.spec', 'w') as f:
        f.write(spec_content.strip())
    
    print("✅ Создан mas_installer.spec")

def create_icon():
    """Создаем иконку для приложения (placeholder)"""
    # В реальном проекте здесь будет создание или копирование .ico файла
    print("💡 Создайте файл mas_icon.ico для иконки приложения")

def build_executable():
    """Компилируем в исполняемый файл"""
    print("🔨 Компиляция инсталлятора...")
    
    # Компилируем с помощью PyInstaller
    result = subprocess.run([
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=MAS-System-Installer',
        '--add-data=web_installer.html;.',
        '--hidden-import=tkinter',
        '--hidden-import=requests',
        'mas_installer.py'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Компиляция успешна!")
        print("📦 Исполняемый файл: dist/MAS-System-Installer.exe")
        return True
    else:
        print(f"❌ Ошибка компиляции: {result.stderr}")
        return False

def create_web_installer_bundle():
    """Создаем веб-версию инсталлятора"""
    print("🌐 Создаем веб-инсталлятор...")
    
    # Создаем папку для веб-инсталлятора
    web_dir = Path('dist/web_installer')
    web_dir.mkdir(parents=True, exist_ok=True)
    
    # Копируем HTML файл
    shutil.copy('web_installer.html', web_dir / 'index.html')
    
    # Создаем простой сервер для демо
    server_script = '''#!/usr/bin/env python3
import http.server
import socketserver
import webbrowser
from pathlib import Path

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🌐 Веб-инсталлятор запущен на http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    httpd.serve_forever()
'''
    
    with open(web_dir / 'start_web_installer.py', 'w') as f:
        f.write(server_script)
    
    print(f"✅ Веб-инсталлятор создан в {web_dir}")

def create_distribution_package():
    """Создаем полный пакет для распространения"""
    print("📦 Создаем пакет для распространения...")
    
    dist_dir = Path('dist/MAS-Installer-Package')
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # README для пользователей
    readme_content = '''# Root-MAS System Installer

## Варианты установки:

### 1. 🖥️ GUI Инсталлятор (Windows)
Запустите: `MAS-System-Installer.exe`

### 2. 🌐 Веб-инсталлятор
1. Запустите: `web_installer/start_web_installer.py`
2. Откроется браузер с инсталлятором

### 3. 🛠️ Ручная установка
1. Убедитесь что установлен Python 3.8+
2. Запустите: `python install_manual.py`

## Системные требования:
- Python 3.8 или выше
- 2GB свободного места
- Интернет соединение

## Поддержка:
- Документация: https://github.com/your-org/root-mas
- Поддержка: support@your-company.com
'''
    
    with open(dist_dir / 'README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Копируем исполняемые файлы
    if Path('dist/MAS-System-Installer.exe').exists():
        shutil.copy('dist/MAS-System-Installer.exe', dist_dir)
    
    # Копируем веб-инсталлятор
    if Path('dist/web_installer').exists():
        shutil.copytree('dist/web_installer', dist_dir / 'web_installer', dirs_exist_ok=True)
    
    print(f"✅ Пакет готов: {dist_dir}")

def main():
    """Основная функция сборки"""
    print("🚀 Сборка MAS System Installer")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_pyinstaller():
        print("❌ Не удалось установить PyInstaller")
        return False
    
    # Создаем иконку
    create_icon()
    
    # Компилируем GUI инсталлятор
    if build_executable():
        print("✅ GUI инсталлятор готов")
    else:
        print("⚠️ GUI инсталлятор не собран")
    
    # Создаем веб-инсталлятор
    create_web_installer_bundle()
    
    # Создаем финальный пакет
    create_distribution_package()
    
    print("\n🎉 Сборка завершена!")
    print("📦 Файлы готовы в папке dist/MAS-Installer-Package/")
    print("\n💡 Для продажи:")
    print("1. Загрузите пакет на файлообменник")
    print("2. Создайте лендинг с описанием")
    print("3. Добавьте систему оплаты")
    print("4. Настройте автоматическую выдачу ссылок")
    
    return True

if __name__ == "__main__":
    main()