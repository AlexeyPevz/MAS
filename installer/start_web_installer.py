#!/usr/bin/env python3
"""
Web Installer Launcher
Удобный запуск веб-инсталлятора AI Memory System
"""

import os
import sys
import webbrowser
import time
import socket
import argparse
from pathlib import Path
import http.server
import socketserver
import threading

class WebInstallerServer:
    """Сервер для веб-инсталлятора"""
    
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        
    def find_free_port(self, start_port=5000):
        """Находит свободный порт"""
        for port in range(start_port, start_port + 100):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('', port))
                sock.close()
                return port
            except:
                continue
        return None
        
    def start_server(self):
        """Запускает HTTP сервер"""
        # Переходим в директорию installer
        installer_dir = Path(__file__).parent
        os.chdir(installer_dir)
        
        # Настраиваем handler
        handler = http.server.SimpleHTTPRequestHandler
        
        # Создаем сервер с поддержкой reuse address
        class ReuseAddrTCPServer(socketserver.TCPServer):
            allow_reuse_address = True
            
        try:
            self.server = ReuseAddrTCPServer((self.host, self.port), handler)
            print(f"🌐 Веб-сервер запущен на {self.host}:{self.port}")
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Остановка сервера...")
            self.stop_server()
            
    def start_in_thread(self):
        """Запускает сервер в отдельном потоке"""
        self.thread = threading.Thread(target=self.start_server, daemon=True)
        self.thread.start()
        
    def stop_server(self):
        """Останавливает сервер"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            

def print_banner():
    """Выводит красивый баннер"""
    banner = """
    ╔══════════════════════════════════════════════╗
    ║      🌐 AI Memory System Web Installer       ║
    ║          Веб-инсталлятор системы             ║
    ╚══════════════════════════════════════════════╝
    """
    print(banner)
    

def check_browser():
    """Проверяет наличие браузера"""
    try:
        # Пробуем получить браузер по умолчанию
        browser = webbrowser.get()
        return True
    except:
        return False
        

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Запуск веб-инсталлятора AI Memory System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Запуск на localhost:5000 (по умолчанию)
  python start_web_installer.py
  
  # Запуск на другом порту
  python start_web_installer.py --port 8080
  
  # Запуск с доступом из сети
  python start_web_installer.py --host 0.0.0.0
  
  # Только запуск сервера (без открытия браузера)
  python start_web_installer.py --no-browser
        """
    )
    
    parser.add_argument(
        '--host',
        default='localhost',
        help='Хост для веб-сервера (по умолчанию: localhost)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Порт для веб-сервера (по умолчанию: 5000)'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Не открывать браузер автоматически'
    )
    
    parser.add_argument(
        '--file',
        default='web_installer.html',
        help='HTML файл инсталлятора (по умолчанию: web_installer.html)'
    )
    
    args = parser.parse_args()
    
    # Выводим баннер
    print_banner()
    
    # Проверяем наличие файла инсталлятора
    installer_file = Path(__file__).parent / args.file
    if not installer_file.exists():
        print(f"❌ Файл {args.file} не найден!")
        print(f"   Искали в: {installer_file}")
        sys.exit(1)
        
    # Создаем сервер
    server = WebInstallerServer(args.host, args.port)
    
    # Проверяем доступность порта
    if not server.find_free_port(args.port):
        print(f"❌ Не удалось найти свободный порт начиная с {args.port}")
        sys.exit(1)
        
    # Если порт занят, используем следующий свободный
    free_port = server.find_free_port(args.port)
    if free_port != args.port:
        print(f"⚠️  Порт {args.port} занят, используем порт {free_port}")
        server.port = free_port
        
    # Формируем URL
    if args.host == '0.0.0.0':
        # Для 0.0.0.0 показываем реальный IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        urls = [
            f"http://localhost:{server.port}/{args.file}",
            f"http://{local_ip}:{server.port}/{args.file}",
        ]
        print("\n📡 Инсталлятор доступен по адресам:")
        for url in urls:
            print(f"   • {url}")
    else:
        url = f"http://{args.host}:{server.port}/{args.file}"
        print(f"\n📡 Инсталлятор доступен по адресу:")
        print(f"   {url}")
        
    # Запускаем сервер в отдельном потоке
    server.start_in_thread()
    
    # Небольшая задержка для запуска сервера
    time.sleep(1)
    
    # Открываем браузер если нужно
    if not args.no_browser:
        if check_browser():
            print("\n🌐 Открываю браузер...")
            if args.host == '0.0.0.0':
                webbrowser.open(f"http://localhost:{server.port}/{args.file}")
            else:
                webbrowser.open(url)
        else:
            print("\n⚠️  Не удалось определить браузер по умолчанию")
            print("   Откройте указанный выше URL вручную")
            
    print("\n✅ Сервер запущен!")
    print("   Нажмите Ctrl+C для остановки\n")
    
    try:
        # Держим основной поток активным
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Остановка сервера...")
        server.stop_server()
        print("✅ Сервер остановлен")
        

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        sys.exit(1)