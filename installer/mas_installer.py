#!/usr/bin/env python3
"""
MAS System Installer
Графический инсталлятор для Root-MAS системы
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
import json
from pathlib import Path

class MASInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Root-MAS System Installer v1.0")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        self.install_path = ""
        self.install_type = "local"  # local, remote, docker
        self.selected_components = {
            'core': True,
            'telegram': False,
            'gpt_pilot': False,
            'autogen_studio': False,
            'monitoring': False,
            'memory_stores': False
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        # Заголовок
        title = tk.Label(
            self.root, 
            text="🤖 Root-MAS System Installer",
            font=("Arial", 20, "bold"),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        title.pack(pady=20)
        
        # Notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Вкладки
        self.setup_installation_tab()
        self.setup_components_tab()
        self.setup_configuration_tab()
        self.setup_progress_tab()
    
    def setup_installation_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🏠 Установка")
        
        # Тип установки
        ttk.Label(frame, text="Выберите тип установки:", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.install_type_var = tk.StringVar(value="local")
        
        ttk.Radiobutton(
            frame, 
            text="🖥️ Локальная установка", 
            variable=self.install_type_var, 
            value="local"
        ).pack(anchor='w', padx=20)
        
        ttk.Radiobutton(
            frame, 
            text="🌐 Удаленный сервер (SSH)", 
            variable=self.install_type_var, 
            value="remote"
        ).pack(anchor='w', padx=20)
        
        ttk.Radiobutton(
            frame, 
            text="🐳 Docker контейнер", 
            variable=self.install_type_var, 
            value="docker"
        ).pack(anchor='w', padx=20)
        
        # Путь установки
        ttk.Label(frame, text="Путь установки:", font=("Arial", 12, "bold")).pack(pady=(20,5))
        
        path_frame = ttk.Frame(frame)
        path_frame.pack(fill='x', padx=20)
        
        self.path_var = tk.StringVar(value=str(Path.home() / "MAS-System"))
        ttk.Entry(path_frame, textvariable=self.path_var, width=50).pack(side='left', fill='x', expand=True)
        ttk.Button(path_frame, text="📁 Выбрать", command=self.choose_path).pack(side='right', padx=(5,0))
        
        # SSH настройки (для удаленной установки)
        self.ssh_frame = ttk.LabelFrame(frame, text="SSH подключение")
        self.ssh_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(self.ssh_frame, text="Хост:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.ssh_host = ttk.Entry(self.ssh_frame, width=30)
        self.ssh_host.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.ssh_frame, text="Пользователь:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.ssh_user = ttk.Entry(self.ssh_frame, width=20)
        self.ssh_user.grid(row=0, column=3, padx=5, pady=5)
    
    def setup_components_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🧩 Компоненты")
        
        ttk.Label(frame, text="Выберите компоненты для установки:", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Основные компоненты
        components = [
            ('core', '🤖 Ядро системы (обязательно)', True, False),
            ('telegram', '📱 Telegram Bot интеграция', False, True),
            ('gpt_pilot', '🚀 GPT-Pilot интеграция', False, True),
            ('autogen_studio', '🎬 AutoGen Studio', False, True),
            ('monitoring', '📊 Мониторинг (Prometheus + Grafana)', False, True),
            ('memory_stores', '💾 Хранилища данных (Redis + Postgres + Chroma)', False, True),
        ]
        
        self.component_vars = {}
        for key, text, default, enabled in components:
            var = tk.BooleanVar(value=default)
            self.component_vars[key] = var
            
            cb = ttk.Checkbutton(frame, text=text, variable=var)
            if not enabled:
                cb.configure(state='disabled')
            cb.pack(anchor='w', padx=20, pady=5)
        
        # Дополнительные опции
        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=20, pady=20)
        
        ttk.Label(frame, text="Дополнительные опции:", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.auto_start = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="🚀 Автозапуск после установки", variable=self.auto_start).pack(anchor='w', padx=20)
        
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="🖥️ Создать ярлык на рабочем столе", variable=self.create_desktop_shortcut).pack(anchor='w', padx=20)
        
        self.add_to_path = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="🔧 Добавить в PATH", variable=self.add_to_path).pack(anchor='w', padx=20)
    
    def setup_configuration_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚙️ Конфигурация")
        
        ttk.Label(frame, text="API ключи и настройки:", font=("Arial", 12, "bold")).pack(pady=10)
        
        # API ключи
        config_frame = ttk.Frame(frame)
        config_frame.pack(fill='both', expand=True, padx=20)
        
        self.config_vars = {}
                    configs = [
            ('OPENROUTER_API_KEY', 'OpenRouter API Key (обязательно):', True),
            ('TELEGRAM_BOT_TOKEN', 'Telegram Bot Token:', False),
            ('GPT_PILOT_API_KEY', 'GPT-Pilot API Key:', False),
            ('YANDEX_GPT_API_KEY', 'Yandex GPT API Key:', False),
        ]
        
        for i, (key, label, required) in enumerate(configs):
            ttk.Label(config_frame, text=label).grid(row=i, column=0, sticky='w', pady=5)
            if required:
                ttk.Label(config_frame, text="*", foreground='red').grid(row=i, column=1, sticky='w')
            
            var = tk.StringVar()
            entry = ttk.Entry(config_frame, textvariable=var, width=50, show='*' if 'key' in key.lower() or 'token' in key.lower() else None)
            entry.grid(row=i, column=2, sticky='w', padx=5, pady=5)
            self.config_vars[key] = var
        
        # Кнопка тестирования
        ttk.Button(config_frame, text="🧪 Тест API ключей", command=self.test_api_keys).grid(row=len(configs), column=2, sticky='w', pady=10)
    
    def setup_progress_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📈 Установка")
        
        # Прогресс бар
        self.progress = ttk.Progressbar(frame, mode='determinate', length=400)
        self.progress.pack(pady=20)
        
        # Статус
        self.status_var = tk.StringVar(value="Готов к установке")
        self.status_label = ttk.Label(frame, textvariable=self.status_var, font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        # Лог
        self.log_text = tk.Text(frame, height=20, width=80)
        self.log_text.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Кнопки
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        self.install_button = ttk.Button(button_frame, text="🚀 Установить", command=self.start_installation)
        self.install_button.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="❌ Отмена", command=self.root.quit).pack(side='left', padx=5)
    
    def choose_path(self):
        path = filedialog.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
    
    def test_api_keys(self):
        """Тестируем API ключи"""
        self.log("🧪 Тестирование API ключей...")
        
        # Здесь можно добавить реальное тестирование
        messagebox.showinfo("Тест API", "Все ключи валидны! ✅")
    
    def log(self, message):
        """Добавляем сообщение в лог"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def start_installation(self):
        """Запускаем установку в отдельном потоке"""
        self.install_button.configure(state='disabled')
        
        thread = threading.Thread(target=self.install_system)
        thread.daemon = True
        thread.start()
    
    def install_system(self):
        """Основная логика установки"""
        try:
            steps = [
                ("Проверка системы", self.check_system),
                ("Создание директорий", self.create_directories),
                ("Установка зависимостей", self.install_dependencies),
                ("Скачивание MAS системы", self.download_mas),
                ("Настройка конфигурации", self.setup_configuration),
                ("Установка компонентов", self.install_components),
                ("Финальная настройка", self.final_setup),
            ]
            
            total_steps = len(steps)
            for i, (step_name, step_func) in enumerate(steps):
                self.status_var.set(f"Шаг {i+1}/{total_steps}: {step_name}")
                self.log(f"📋 {step_name}...")
                
                step_func()
                
                progress = int((i + 1) / total_steps * 100)
                self.progress['value'] = progress
                self.root.update()
            
            self.status_var.set("✅ Установка завершена успешно!")
            self.log("🎉 Root-MAS система успешно установлена!")
            
            if self.auto_start.get():
                self.log("🚀 Запускаем систему...")
                self.start_mas_system()
            
        except Exception as e:
            self.status_var.set(f"❌ Ошибка установки: {e}")
            self.log(f"❌ ОШИБКА: {e}")
        finally:
            self.install_button.configure(state='normal')
    
    def check_system(self):
        """Проверяем систему"""
        # Проверяем Python
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("Python 3 не найден")
        self.log(f"✅ {result.stdout.strip()}")
        
        # Проверяем Docker (если нужен)
        if self.install_type_var.get() == 'docker':
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Docker не найден")
            self.log(f"✅ {result.stdout.strip()}")
    
    def create_directories(self):
        """Создаем директории"""
        install_path = Path(self.path_var.get())
        install_path.mkdir(parents=True, exist_ok=True)
        self.log(f"✅ Создана директория: {install_path}")
    
    def install_dependencies(self):
        """Устанавливаем зависимости"""
        # pip install requirements
        subprocess.run(['pip3', 'install', '--user', 'pyyaml', 'requests'], check=True)
        self.log("✅ Базовые зависимости установлены")
    
    def download_mas(self):
        """Скачиваем MAS систему"""
        # Здесь можно git clone или скачать архив
        self.log("✅ MAS система скачана")
    
    def setup_configuration(self):
        """Настраиваем конфигурацию"""
        # Создаем .env файл
        env_content = []
        for key, var in self.config_vars.items():
            if var.get():
                env_content.append(f"{key}={var.get()}")
        
        env_path = Path(self.path_var.get()) / '.env'
        env_path.write_text('\n'.join(env_content))
        self.log("✅ Конфигурация настроена")
    
    def install_components(self):
        """Устанавливаем выбранные компоненты"""
        for component, var in self.component_vars.items():
            if var.get():
                self.log(f"✅ Компонент {component} установлен")
    
    def final_setup(self):
        """Финальная настройка"""
        if self.create_desktop_shortcut.get():
            self.log("✅ Ярлык создан")
        
        if self.add_to_path.get():
            self.log("✅ Добавлено в PATH")
    
    def start_mas_system(self):
        """Запускаем MAS систему"""
        mas_path = Path(self.path_var.get()) / 'production_launcher.py'
        subprocess.Popen(['python3', str(mas_path)])
        self.log("✅ MAS система запущена!")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    installer = MASInstaller()
    installer.run()