#!/usr/bin/env python3
"""
Universal Installer for AI Memory System
Универсальный инсталлятор с GUI для установки одной кнопкой
"""

import os
import sys
import json
import subprocess
import platform
import threading
import shutil
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import paramiko
from dataclasses import dataclass
import configparser
from datetime import datetime

# Импортируем обработчик ошибок
try:
    from error_handler import ErrorHandler, SafeInstaller, safe_execution
except ImportError:
    # Если модуль не найден, создаем заглушки
    ErrorHandler = None
    SafeInstaller = None
    def safe_execution(func):
        return func


@dataclass
class InstallConfig:
    """Конфигурация установки"""
    install_type: str = "local"  # local или remote
    server_ip: str = ""
    server_user: str = ""
    server_password: str = ""
    install_path: str = ""
    python_version: str = "3.11"
    memory_type: str = "chromadb"  # chromadb, qdrant, postgres
    memory_path: str = "./memory_data"
    memory_size_mb: int = 1024
    tokens: Dict[str, str] = None
    autogen_path: str = ""
    
    def __post_init__(self):
        if self.tokens is None:
            self.tokens = {}


class UniversalInstaller:
    """Универсальный инсталлятор с GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Memory System - Универсальный Инсталлятор")
        self.root.geometry("900x700")
        
        # Применяем современный стиль
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Конфигурация
        self.config = InstallConfig()
        
        # SSH клиент для удаленной установки
        self.ssh_client = None
        
        # Флаг установки
        self.installation_running = False
        
        # Обработчик ошибок
        self.error_handler = ErrorHandler(self.log) if ErrorHandler else None
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Центрируем окно
        self.center_window()
        
    def center_window(self):
        """Центрирует окно на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        """Создает интерфейс в стиле wizard"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True)
        
        # Заголовок
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(
            header_frame,
            text="AI Memory System Installer",
            font=('Arial', 18, 'bold')
        ).pack(side='left')
        
        ttk.Label(
            header_frame,
            text="Универсальный инсталлятор v1.0",
            font=('Arial', 10),
            foreground='gray'
        ).pack(side='left', padx=20)
        
        # Notebook для шагов установки
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Шаг 1: Выбор типа установки
        self.create_step1_install_type()
        
        # Шаг 2: Настройки подключения
        self.create_step2_connection()
        
        # Шаг 3: Путь и компоненты
        self.create_step3_components()
        
        # Шаг 4: Токены API
        self.create_step4_tokens()
        
        # Шаг 5: Обзор и установка
        self.create_step5_review()
        
        # Нижняя панель с кнопками
        self.create_bottom_panel(main_frame)
        
    def create_step1_install_type(self):
        """Шаг 1: Выбор типа установки"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="1. Тип установки")
        
        # Центральный контейнер
        center_frame = ttk.Frame(frame)
        center_frame.place(relx=0.5, rely=0.4, anchor='center')
        
        ttk.Label(
            center_frame,
            text="Выберите тип установки",
            font=('Arial', 16, 'bold')
        ).pack(pady=20)
        
        self.install_type_var = tk.StringVar(value="local")
        
        # Локальная установка
        local_btn = ttk.Radiobutton(
            center_frame,
            text="🖥️  Локальная установка",
            variable=self.install_type_var,
            value="local",
            style='Large.TRadiobutton'
        )
        local_btn.pack(pady=10)
        
        ttk.Label(
            center_frame,
            text="Установить на этот компьютер",
            foreground='gray'
        ).pack()
        
        ttk.Separator(center_frame, orient='horizontal').pack(fill='x', pady=20)
        
        # Удаленная установка
        remote_btn = ttk.Radiobutton(
            center_frame,
            text="🌐  Удаленная установка",
            variable=self.install_type_var,
            value="remote",
            style='Large.TRadiobutton'
        )
        remote_btn.pack(pady=10)
        
        ttk.Label(
            center_frame,
            text="Установить на сервер через SSH",
            foreground='gray'
        ).pack()
        
    def create_step2_connection(self):
        """Шаг 2: Настройки подключения"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="2. Подключение")
        
        # Контейнер для форм
        self.connection_container = ttk.Frame(frame)
        self.connection_container.pack(fill='both', expand=True, padx=40, pady=40)
        
        # Форма для удаленного подключения
        self.remote_form = ttk.LabelFrame(
            self.connection_container,
            text="SSH подключение к серверу",
            padding=20
        )
        
        # IP адрес
        ttk.Label(self.remote_form, text="IP адрес или hostname:").grid(
            row=0, column=0, sticky='w', pady=10
        )
        self.ip_entry = ttk.Entry(self.remote_form, width=30)
        self.ip_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # Имя пользователя
        ttk.Label(self.remote_form, text="Имя пользователя:").grid(
            row=1, column=0, sticky='w', pady=10
        )
        self.user_entry = ttk.Entry(self.remote_form, width=30)
        self.user_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Пароль
        ttk.Label(self.remote_form, text="Пароль:").grid(
            row=2, column=0, sticky='w', pady=10
        )
        self.password_entry = ttk.Entry(self.remote_form, width=30, show='*')
        self.password_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Порт SSH
        ttk.Label(self.remote_form, text="SSH порт:").grid(
            row=3, column=0, sticky='w', pady=10
        )
        self.port_var = tk.StringVar(value="22")
        port_entry = ttk.Entry(self.remote_form, textvariable=self.port_var, width=10)
        port_entry.grid(row=3, column=1, sticky='w', padx=10, pady=10)
        
        # Кнопка проверки
        test_btn = ttk.Button(
            self.remote_form,
            text="Проверить подключение",
            command=self.test_ssh_connection
        )
        test_btn.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Форма для локальной установки
        self.local_form = ttk.LabelFrame(
            self.connection_container,
            text="Локальная установка",
            padding=20
        )
        
        info_label = ttk.Label(
            self.local_form,
            text="✓ Дополнительные настройки не требуются\n\n"
                 "Система будет установлена на текущий компьютер",
            justify='center'
        )
        info_label.pack(pady=40)
        
    def create_step3_components(self):
        """Шаг 3: Выбор компонентов и пути"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="3. Компоненты")
        
        # Скроллируемая область
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Путь установки
        path_frame = ttk.LabelFrame(scrollable_frame, text="Путь установки", padding=15)
        path_frame.pack(fill='x', padx=20, pady=10)
        
        path_container = ttk.Frame(path_frame)
        path_container.pack(fill='x')
        
        self.path_var = tk.StringVar(value=str(Path.home() / "ai-memory-system"))
        path_entry = ttk.Entry(path_container, textvariable=self.path_var, width=50)
        path_entry.pack(side='left', padx=(0, 10))
        
        ttk.Button(
            path_container,
            text="Обзор...",
            command=self.browse_install_path
        ).pack(side='left')
        
        # Версия Python
        python_frame = ttk.LabelFrame(scrollable_frame, text="Python", padding=15)
        python_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(python_frame, text="Версия Python:").pack(side='left', padx=(0, 10))
        
        self.python_var = tk.StringVar(value="3.11")
        python_combo = ttk.Combobox(
            python_frame,
            textvariable=self.python_var,
            values=["3.9", "3.10", "3.11", "3.12"],
            width=10,
            state='readonly'
        )
        python_combo.pack(side='left')
        
        # Система памяти
        memory_frame = ttk.LabelFrame(scrollable_frame, text="Система памяти", padding=15)
        memory_frame.pack(fill='x', padx=20, pady=10)
        
        # Тип памяти
        type_container = ttk.Frame(memory_frame)
        type_container.pack(fill='x', pady=5)
        
        ttk.Label(type_container, text="Тип хранилища:").pack(side='left', padx=(0, 10))
        
        self.memory_type_var = tk.StringVar(value="chromadb")
        memory_combo = ttk.Combobox(
            type_container,
            textvariable=self.memory_type_var,
            values=["chromadb", "qdrant", "postgres", "milvus"],
            width=20,
            state='readonly'
        )
        memory_combo.pack(side='left')
        
        # Размер памяти
        size_container = ttk.Frame(memory_frame)
        size_container.pack(fill='x', pady=5)
        
        ttk.Label(size_container, text="Размер памяти:").pack(side='left', padx=(0, 10))
        
        self.memory_size_var = tk.IntVar(value=1024)
        size_spinbox = ttk.Spinbox(
            size_container,
            from_=512,
            to=10240,
            increment=512,
            textvariable=self.memory_size_var,
            width=10
        )
        size_spinbox.pack(side='left')
        
        ttk.Label(size_container, text="МБ").pack(side='left', padx=(5, 0))
        
        # Дополнительные компоненты
        components_frame = ttk.LabelFrame(scrollable_frame, text="Дополнительные компоненты", padding=15)
        components_frame.pack(fill='x', padx=20, pady=10)
        
        self.install_docker_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            components_frame,
            text="Установить Docker (если не установлен)",
            variable=self.install_docker_var
        ).pack(anchor='w', pady=5)
        
        self.install_nodejs_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            components_frame,
            text="Установить Node.js (для веб-интерфейса)",
            variable=self.install_nodejs_var
        ).pack(anchor='w', pady=5)
        
        self.create_service_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            components_frame,
            text="Создать системный сервис (автозапуск)",
            variable=self.create_service_var
        ).pack(anchor='w', pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_step4_tokens(self):
        """Шаг 4: API токены"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="4. API токены")
        
        # Заголовок
        header = ttk.Label(
            frame,
            text="Настройка API токенов",
            font=('Arial', 14, 'bold')
        )
        header.pack(pady=20)
        
        info = ttk.Label(
            frame,
            text="Введите API ключи для сервисов, которые планируете использовать.\n"
                 "Вы можете оставить поля пустыми и добавить токены позже.",
            justify='center'
        )
        info.pack(pady=(0, 20))
        
        # Контейнер для токенов
        tokens_container = ttk.Frame(frame)
        tokens_container.pack(fill='both', expand=True, padx=40)
        
        # Создаем Canvas для прокрутки
        canvas = tk.Canvas(tokens_container)
        scrollbar = ttk.Scrollbar(tokens_container, orient="vertical", command=canvas.yview)
        tokens_frame = ttk.Frame(canvas)
        
        tokens_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=tokens_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Словарь для хранения Entry виджетов
        self.token_entries = {}
        
        # Список токенов
        token_configs = [
            {
                "key": "OPENAI_API_KEY",
                "name": "OpenAI",
                "desc": "Для работы с GPT-3.5/GPT-4",
                "icon": "🤖"
            },
            {
                "key": "ANTHROPIC_API_KEY",
                "name": "Anthropic",
                "desc": "Для работы с Claude",
                "icon": "🧠"
            },
            {
                "key": "GOOGLE_API_KEY",
                "name": "Google AI",
                "desc": "Для работы с Gemini",
                "icon": "🔍"
            },
            {
                "key": "YANDEX_API_KEY",
                "name": "Yandex",
                "desc": "Для работы с YandexGPT",
                "icon": "🇷🇺"
            },
            {
                "key": "TELEGRAM_BOT_TOKEN",
                "name": "Telegram Bot",
                "desc": "Токен для Telegram бота",
                "icon": "✈️"
            },
            {
                "key": "SPEECHKIT_API_KEY",
                "name": "SpeechKit",
                "desc": "Для синтеза и распознавания речи",
                "icon": "🎤"
            }
        ]
        
        for i, token_config in enumerate(token_configs):
            # Фрейм для каждого токена
            token_frame = ttk.Frame(tokens_frame)
            token_frame.pack(fill='x', pady=10)
            
            # Иконка и название
            header_frame = ttk.Frame(token_frame)
            header_frame.pack(fill='x')
            
            ttk.Label(
                header_frame,
                text=f"{token_config['icon']} {token_config['name']}",
                font=('Arial', 12, 'bold')
            ).pack(side='left')
            
            ttk.Label(
                header_frame,
                text=token_config['desc'],
                foreground='gray'
            ).pack(side='left', padx=20)
            
            # Поле ввода
            entry_frame = ttk.Frame(token_frame)
            entry_frame.pack(fill='x', pady=5)
            
            entry = ttk.Entry(entry_frame, width=60, show='*')
            entry.pack(side='left', padx=(20, 10))
            
            # Кнопка показать/скрыть
            show_var = tk.BooleanVar()
            ttk.Checkbutton(
                entry_frame,
                text="Показать",
                variable=show_var,
                command=lambda e=entry, v=show_var: e.config(show='' if v.get() else '*')
            ).pack(side='left')
            
            self.token_entries[token_config['key']] = entry
            
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_step5_review(self):
        """Шаг 5: Обзор и установка"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="5. Установка")
        
        # Обзор настроек
        review_frame = ttk.LabelFrame(frame, text="Обзор настроек", padding=15)
        review_frame.pack(fill='x', padx=20, pady=10)
        
        self.review_text = tk.Text(review_frame, height=10, width=70)
        self.review_text.pack(fill='both', expand=True)
        
        # Прогресс установки
        progress_frame = ttk.LabelFrame(frame, text="Прогресс установки", padding=15)
        progress_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Прогресс бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(pady=10)
        
        # Статус
        self.status_label = ttk.Label(progress_frame, text="Готов к установке")
        self.status_label.pack()
        
        # Лог
        log_container = ttk.Frame(progress_frame)
        log_container.pack(fill='both', expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_container,
            height=12,
            width=80,
            wrap='word'
        )
        self.log_text.pack(side='left', fill='both', expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        log_scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
    def create_bottom_panel(self, parent):
        """Создает нижнюю панель с кнопками"""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill='x', padx=20, pady=10)
        
        # Кнопка "Назад"
        self.back_btn = ttk.Button(
            bottom_frame,
            text="← Назад",
            command=self.go_back,
            state='disabled'
        )
        self.back_btn.pack(side='left')
        
        # Кнопка "Далее"
        self.next_btn = ttk.Button(
            bottom_frame,
            text="Далее →",
            command=self.go_next
        )
        self.next_btn.pack(side='right', padx=(10, 0))
        
        # Кнопка "Установить"
        self.install_btn = ttk.Button(
            bottom_frame,
            text="🚀 Установить",
            command=self.start_installation,
            style='Accent.TButton'
        )
        self.install_btn.pack(side='right')
        self.install_btn.pack_forget()  # Скрываем пока
        
        # Кнопка "Отмена"
        ttk.Button(
            bottom_frame,
            text="Отмена",
            command=self.cancel_installation
        ).pack(side='right', padx=10)
        
        # Обработчик изменения вкладки
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
    def on_tab_changed(self, event=None):
        """Обработчик изменения вкладки"""
        current_tab = self.notebook.index(self.notebook.select())
        total_tabs = len(self.notebook.tabs())
        
        # Управление кнопками
        self.back_btn.config(state='normal' if current_tab > 0 else 'disabled')
        
        if current_tab == total_tabs - 1:  # Последняя вкладка
            self.next_btn.pack_forget()
            self.install_btn.pack(side='right')
            self.update_review()
        else:
            self.install_btn.pack_forget()
            self.next_btn.pack(side='right', padx=(10, 0))
            
        # Обновляем формы подключения
        if current_tab == 1:  # Вкладка подключения
            self.update_connection_form()
            
    def go_back(self):
        """Переход на предыдущую вкладку"""
        current = self.notebook.index(self.notebook.select())
        if current > 0:
            self.notebook.select(current - 1)
            
    def go_next(self):
        """Переход на следующую вкладку"""
        current = self.notebook.index(self.notebook.select())
        
        # Валидация текущего шага
        if current == 1 and self.install_type_var.get() == "remote":
            if not self.validate_connection():
                return
                
        if current < len(self.notebook.tabs()) - 1:
            self.notebook.select(current + 1)
            
    def update_connection_form(self):
        """Обновляет форму подключения в зависимости от типа установки"""
        if self.install_type_var.get() == "local":
            self.remote_form.pack_forget()
            self.local_form.pack(fill='both', expand=True)
        else:
            self.local_form.pack_forget()
            self.remote_form.pack(fill='both', expand=True)
            
    def validate_connection(self):
        """Валидация настроек подключения"""
        if self.install_type_var.get() == "remote":
            if not all([self.ip_entry.get(), self.user_entry.get()]):
                messagebox.showerror(
                    "Ошибка",
                    "Заполните обязательные поля подключения"
                )
                return False
        return True
        
    def browse_install_path(self):
        """Выбор папки установки"""
        path = filedialog.askdirectory(
            title="Выберите папку для установки",
            initialdir=self.path_var.get()
        )
        if path:
            self.path_var.set(path)
            
    def test_ssh_connection(self):
        """Тест SSH подключения"""
        if not all([self.ip_entry.get(), self.user_entry.get()]):
            messagebox.showerror("Ошибка", "Заполните поля подключения")
            return
            
        # Показываем прогресс
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Проверка подключения")
        progress_window.geometry("300x100")
        progress_window.transient(self.root)
        
        ttk.Label(
            progress_window,
            text="Проверка подключения...",
            font=('Arial', 12)
        ).pack(pady=20)
        
        progress_bar = ttk.Progressbar(
            progress_window,
            mode='indeterminate'
        )
        progress_bar.pack(padx=20, pady=10)
        progress_bar.start()
        
        def test_connection():
            try:
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                ssh.connect(
                    self.ip_entry.get(),
                    port=int(self.port_var.get()),
                    username=self.user_entry.get(),
                    password=self.password_entry.get(),
                    timeout=10
                )
                
                stdin, stdout, stderr = ssh.exec_command("echo 'OK'")
                result = stdout.read().decode().strip()
                ssh.close()
                
                progress_window.destroy()
                
                if result == "OK":
                    messagebox.showinfo(
                        "Успех",
                        "Подключение установлено успешно!"
                    )
                else:
                    messagebox.showerror(
                        "Ошибка",
                        "Не удалось выполнить команду на сервере"
                    )
                    
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror(
                    "Ошибка подключения",
                    f"Не удалось подключиться:\n{str(e)}"
                )
                
        thread = threading.Thread(target=test_connection)
        thread.start()
        
    def update_review(self):
        """Обновляет обзор настроек перед установкой"""
        self.review_text.delete(1.0, tk.END)
        
        review = "НАСТРОЙКИ УСТАНОВКИ\n" + "=" * 50 + "\n\n"
        
        # Тип установки
        install_type = "Локальная" if self.install_type_var.get() == "local" else "Удаленная"
        review += f"Тип установки: {install_type}\n"
        
        if self.install_type_var.get() == "remote":
            review += f"Сервер: {self.ip_entry.get()}:{self.port_var.get()}\n"
            review += f"Пользователь: {self.user_entry.get()}\n"
            
        review += f"\nПуть установки: {self.path_var.get()}\n"
        review += f"Версия Python: {self.python_var.get()}\n"
        
        review += f"\nСистема памяти: {self.memory_type_var.get()}\n"
        review += f"Размер памяти: {self.memory_size_var.get()} МБ\n"
        
        # Дополнительные компоненты
        review += "\nДополнительные компоненты:\n"
        if self.install_docker_var.get():
            review += "  ✓ Docker\n"
        if self.install_nodejs_var.get():
            review += "  ✓ Node.js\n"
        if self.create_service_var.get():
            review += "  ✓ Системный сервис\n"
            
        # Токены
        tokens_count = sum(1 for entry in self.token_entries.values() if entry.get())
        review += f"\nНастроено токенов: {tokens_count}\n"
        
        self.review_text.insert(1.0, review)
        self.review_text.config(state='disabled')
        
    def log(self, message: str, level: str = "INFO"):
        """Добавляет сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Цветовая схема
        colors = {
            "INFO": "black",
            "SUCCESS": "green",
            "WARNING": "orange",
            "ERROR": "red"
        }
        
        # Добавляем тег для цвета
        tag_name = f"tag_{level}"
        self.log_text.tag_config(tag_name, foreground=colors.get(level, "black"))
        
        # Вставляем текст
        log_line = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_line, tag_name)
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_progress(self, value: float, status: str = ""):
        """Обновляет прогресс бар"""
        self.progress_var.set(value)
        if status:
            self.status_label.config(text=status)
        self.root.update()
        
    def collect_config(self):
        """Собирает конфигурацию из GUI"""
        self.config.install_type = self.install_type_var.get()
        self.config.server_ip = self.ip_entry.get()
        self.config.server_user = self.user_entry.get()
        self.config.server_password = self.password_entry.get()
        self.config.install_path = self.path_var.get()
        self.config.python_version = self.python_var.get()
        self.config.memory_type = self.memory_type_var.get()
        self.config.memory_size_mb = self.memory_size_var.get()
        
        # Собираем токены
        self.config.tokens = {}
        for key, entry in self.token_entries.items():
            value = entry.get().strip()
            if value:
                self.config.tokens[key] = value
                
    def start_installation(self):
        """Начинает процесс установки"""
        if self.installation_running:
            messagebox.showwarning("Внимание", "Установка уже запущена")
            return
            
        # Собираем конфигурацию
        self.collect_config()
        
        # Подтверждение
        if not messagebox.askyesno(
            "Подтверждение",
            "Начать установку с выбранными настройками?"
        ):
            return
            
        # Блокируем интерфейс
        self.installation_running = True
        self.install_btn.config(state='disabled')
        self.back_btn.config(state='disabled')
        
        # Очищаем лог
        self.log_text.delete(1.0, tk.END)
        
        # Запускаем установку в отдельном потоке
        thread = threading.Thread(target=self._install_thread)
        thread.daemon = True
        thread.start()
        
    def _install_thread(self):
        """Основной поток установки"""
        try:
            self.log("🚀 Начинаем установку AI Memory System", "INFO")
            self.log("=" * 60, "INFO")
            
            # Этапы установки
            steps = [
                ("Проверка системы", self.check_system, 5),
                ("Подготовка окружения", self.prepare_environment, 10),
                ("Установка Python пакетов", self.install_python_packages, 15),
                ("Установка Autogen", self.install_autogen, 15),
                ("Копирование файлов", self.copy_project_files, 10),
                ("Настройка системы памяти", self.setup_memory_system, 15),
                ("Создание конфигурации", self.create_configuration, 10),
                ("Установка дополнительных компонентов", self.install_additional, 10),
                ("Финальная настройка", self.finalize_installation, 10),
            ]
            
            total_progress = 0
            
            for step_name, step_func, step_weight in steps:
                self.log(f"\n▶ {step_name}...", "INFO")
                self.update_progress(total_progress, step_name)
                
                try:
                    success = step_func()
                    if success:
                        self.log(f"✓ {step_name} - завершено", "SUCCESS")
                    else:
                        raise Exception(f"Ошибка на этапе: {step_name}")
                except Exception as e:
                    # Используем обработчик ошибок если доступен
                    if self.error_handler:
                        if self.error_handler.handle_error(e, context=step_name):
                            # Если ошибка обработана, пробуем этот шаг еще раз
                            self.log(f"↻ Повторяем {step_name} после исправления ошибки", "INFO")
                            try:
                                success = step_func()
                                if success:
                                    self.log(f"✓ {step_name} - завершено после повтора", "SUCCESS")
                                else:
                                    raise Exception(f"Повторная ошибка: {step_name}")
                            except Exception as retry_error:
                                self.log(f"✗ {step_name} - повторная ошибка: {str(retry_error)}", "ERROR")
                                raise
                        else:
                            self.log(f"✗ {step_name} - не удалось исправить ошибку", "ERROR")
                            raise
                    else:
                        self.log(f"✗ {step_name} - ошибка: {str(e)}", "ERROR")
                        raise
                    
                total_progress += step_weight
                self.update_progress(total_progress)
                
            self.update_progress(100, "Установка завершена!")
            self.log("\n🎉 Установка успешно завершена!", "SUCCESS")
            
            # Показываем результаты
            self.show_completion_dialog()
            
        except Exception as e:
            self.log(f"\n❌ Установка прервана: {str(e)}", "ERROR")
            
            # Даем расширенные рекомендации при ошибке
            error_message = f"Произошла ошибка:\n{str(e)}\n\n"
            
            if self.error_handler:
                error_message += "Рекомендации:\n"
                error_message += "• Проверьте логи для деталей\n"
                error_message += "• Запустите проверку системы\n"
                error_message += "• Попробуйте другой тип установки\n"
                
                if "permission" in str(e).lower():
                    error_message += "\n⚠️ Возможно требуются права администратора"
                elif "space" in str(e).lower():
                    error_message += "\n⚠️ Проверьте свободное место на диске"
                elif "connection" in str(e).lower():
                    error_message += "\n⚠️ Проверьте интернет соединение"
                    
            messagebox.showerror("Ошибка установки", error_message)
            
        finally:
            self.installation_running = False
            self.install_btn.config(state='normal')
            self.back_btn.config(state='normal')
            
    def check_system(self) -> bool:
        """Проверка системы"""
        checks = [
            ("Python", self._check_python),
            ("Git", self._check_git),
            ("Место на диске", self._check_disk_space),
            ("Права доступа", self._check_permissions),
        ]
        
        for check_name, check_func in checks:
            self.log(f"  Проверяем {check_name}...", "INFO")
            if not check_func():
                self.log(f"  ✗ {check_name} - проблема", "ERROR")
                return False
            self.log(f"  ✓ {check_name} - OK", "SUCCESS")
            
        return True
        
    def _check_python(self) -> bool:
        """Проверка Python"""
        required = tuple(map(int, self.config.python_version.split('.')))
        current = sys.version_info[:2]
        return current >= required
        
    def _check_git(self) -> bool:
        """Проверка Git"""
        return shutil.which("git") is not None
        
    def _check_disk_space(self) -> bool:
        """Проверка места на диске"""
        stat = shutil.disk_usage(Path(self.config.install_path).parent)
        free_gb = stat.free / (1024**3)
        return free_gb >= 2  # Минимум 2GB
        
    def _check_permissions(self) -> bool:
        """Проверка прав доступа"""
        try:
            test_path = Path(self.config.install_path) / ".test"
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.touch()
            test_path.unlink()
            return True
        except:
            return False
            
    def prepare_environment(self) -> bool:
        """Подготовка окружения"""
        # Создаем директории
        Path(self.config.install_path).mkdir(parents=True, exist_ok=True)
        
        # Обновляем pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        return True
        
    def install_python_packages(self) -> bool:
        """Установка Python пакетов"""
        # Создаем виртуальное окружение
        venv_path = Path(self.config.install_path) / "venv"
        self.log(f"  Создаем виртуальное окружение: {venv_path}", "INFO")
        
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)])
        
        # Путь к pip
        if platform.system() == "Windows":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
            
        # Базовые пакеты
        packages = [
            "requests", "pyyaml", "python-dotenv",
            "rich", "typer", "paramiko"
        ]
        
        for package in packages:
            self.log(f"  Устанавливаем {package}...", "INFO")
            subprocess.run([str(pip_path), "install", package])
            
        return True
        
    def install_autogen(self) -> bool:
        """Установка Autogen"""
        venv_path = Path(self.config.install_path) / "venv"
        
        if platform.system() == "Windows":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
            
        self.log("  Устанавливаем Microsoft Autogen...", "INFO")
        subprocess.run([str(pip_path), "install", "pyautogen[retrievechat]"])
        
        return True
        
    def copy_project_files(self) -> bool:
        """Копирование файлов проекта"""
        source_path = Path(__file__).parent.parent
        dest_path = Path(self.config.install_path) / "ai-memory-system"
        
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Копируем файлы
        for item in source_path.iterdir():
            if item.name in ['.git', '__pycache__', 'venv', '.env', 'installer']:
                continue
                
            self.log(f"  Копируем {item.name}...", "INFO")
            
            if item.is_file():
                shutil.copy2(item, dest_path / item.name)
            elif item.is_dir():
                shutil.copytree(
                    item,
                    dest_path / item.name,
                    dirs_exist_ok=True
                )
                
        return True
        
    def setup_memory_system(self) -> bool:
        """Настройка системы памяти"""
        venv_path = Path(self.config.install_path) / "venv"
        
        if platform.system() == "Windows":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
            
        # Устанавливаем пакеты в зависимости от типа памяти
        if self.config.memory_type == "chromadb":
            self.log("  Устанавливаем ChromaDB...", "INFO")
            subprocess.run([str(pip_path), "install", "chromadb"])
        elif self.config.memory_type == "qdrant":
            self.log("  Устанавливаем Qdrant...", "INFO")
            subprocess.run([str(pip_path), "install", "qdrant-client"])
        elif self.config.memory_type == "postgres":
            self.log("  Устанавливаем PostgreSQL драйверы...", "INFO")
            subprocess.run([str(pip_path), "install", "psycopg2-binary", "pgvector"])
        elif self.config.memory_type == "milvus":
            self.log("  Устанавливаем Milvus...", "INFO")
            subprocess.run([str(pip_path), "install", "pymilvus"])
            
        # Создаем директорию для данных
        memory_path = Path(self.config.install_path) / "memory_data"
        memory_path.mkdir(exist_ok=True)
        
        return True
        
    def create_configuration(self) -> bool:
        """Создание конфигурационных файлов"""
        config_path = Path(self.config.install_path) / "ai-memory-system"
        
        # Создаем .env файл
        env_content = "# AI Memory System Configuration\n\n"
        
        for key, value in self.config.tokens.items():
            env_content += f"{key}={value}\n"
            
        env_content += f"\n# System Settings\n"
        env_content += f"MEMORY_TYPE={self.config.memory_type}\n"
        env_content += f"MEMORY_PATH=../memory_data\n"
        env_content += f"MEMORY_SIZE_MB={self.config.memory_size_mb}\n"
        
        env_file = config_path / ".env"
        env_file.write_text(env_content)
        
        self.log("  ✓ Создан файл .env", "SUCCESS")
        
        # Создаем config.yaml
        config_content = f"""# AI Memory System Configuration

system:
  install_path: {self.config.install_path}
  python_version: {self.config.python_version}
  
memory:
  type: {self.config.memory_type}
  path: ../memory_data
  size_mb: {self.config.memory_size_mb}
  
logging:
  level: INFO
  path: ../logs
  
api:
  enabled: true
  host: 0.0.0.0
  port: 8000
"""
        
        config_file = config_path / "config.yaml"
        config_file.write_text(config_content)
        
        self.log("  ✓ Создан файл config.yaml", "SUCCESS")
        
        return True
        
    def install_additional(self) -> bool:
        """Установка дополнительных компонентов"""
        if self.install_docker_var.get():
            self.log("  Установка Docker...", "INFO")
            # Здесь код установки Docker
            
        if self.install_nodejs_var.get():
            self.log("  Установка Node.js...", "INFO")
            # Здесь код установки Node.js
            
        if self.create_service_var.get() and platform.system() == "Linux":
            self.log("  Создание системного сервиса...", "INFO")
            self.create_systemd_service()
            
        return True
        
    def create_systemd_service(self):
        """Создание systemd сервиса"""
        service_content = f"""[Unit]
Description=AI Memory System
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={self.config.install_path}/ai-memory-system
ExecStart={self.config.install_path}/venv/bin/python run_system.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
        
        service_path = Path("/tmp/ai-memory-system.service")
        service_path.write_text(service_content)
        
        try:
            subprocess.run(
                ["sudo", "cp", str(service_path), "/etc/systemd/system/"],
                check=True
            )
            subprocess.run(["sudo", "systemctl", "daemon-reload"])
            subprocess.run(["sudo", "systemctl", "enable", "ai-memory-system"])
            self.log("    ✓ Сервис создан", "SUCCESS")
        except:
            self.log("    ✗ Не удалось создать сервис (нужны sudo права)", "WARNING")
            
    def finalize_installation(self) -> bool:
        """Финализация установки"""
        # Устанавливаем зависимости проекта
        project_path = Path(self.config.install_path) / "ai-memory-system"
        req_file = project_path / "requirements.txt"
        
        if req_file.exists():
            venv_path = Path(self.config.install_path) / "venv"
            if platform.system() == "Windows":
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
                
            self.log("  Устанавливаем зависимости проекта...", "INFO")
            subprocess.run([str(pip_path), "install", "-r", str(req_file)])
            
        # Создаем скрипты запуска
        self.create_launch_scripts()
        
        # Создаем необходимые директории
        dirs = ["logs", "cache", "data", "backups"]
        for dir_name in dirs:
            (project_path / dir_name).mkdir(exist_ok=True)
            
        return True
        
    def create_launch_scripts(self):
        """Создание скриптов запуска"""
        if platform.system() == "Windows":
            # Batch файл для Windows
            bat_content = f"""@echo off
echo Starting AI Memory System...
cd /d "{self.config.install_path}\\ai-memory-system"
"..\\venv\\Scripts\\python.exe" run_system.py
pause
"""
            bat_file = Path(self.config.install_path) / "start_ai_memory.bat"
            bat_file.write_text(bat_content)
            
            self.log("  ✓ Создан start_ai_memory.bat", "SUCCESS")
            
        else:
            # Shell скрипт для Linux/Mac
            sh_content = f"""#!/bin/bash
echo "Starting AI Memory System..."
cd "{self.config.install_path}/ai-memory-system"
../venv/bin/python run_system.py
"""
            sh_file = Path(self.config.install_path) / "start_ai_memory.sh"
            sh_file.write_text(sh_content)
            sh_file.chmod(0o755)
            
            self.log("  ✓ Создан start_ai_memory.sh", "SUCCESS")
            
    def show_completion_dialog(self):
        """Показывает диалог завершения установки"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Установка завершена")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        
        # Заголовок
        header = ttk.Label(
            dialog,
            text="🎉 Установка успешно завершена!",
            font=('Arial', 16, 'bold')
        )
        header.pack(pady=20)
        
        # Информация
        info_frame = ttk.Frame(dialog)
        info_frame.pack(fill='both', expand=True, padx=20)
        
        info_text = tk.Text(info_frame, height=15, width=70)
        info_text.pack(fill='both', expand=True)
        
        info = f"""
AI Memory System установлена в:
{self.config.install_path}

Для запуска системы используйте:
"""
        
        if platform.system() == "Windows":
            info += f"\n  {self.config.install_path}\\start_ai_memory.bat\n"
        else:
            info += f"\n  {self.config.install_path}/start_ai_memory.sh\n"
            
            if self.create_service_var.get():
                info += "\nИли через systemd:\n"
                info += "  sudo systemctl start ai-memory-system\n"
                
        info += f"""
Конфигурация:
  • Тип памяти: {self.config.memory_type}
  • Размер: {self.config.memory_size_mb} МБ
  • Токенов настроено: {len(self.config.tokens)}

Дополнительные файлы:
  • Конфигурация: {self.config.install_path}/ai-memory-system/.env
  • Логи: {self.config.install_path}/ai-memory-system/logs/
"""
        
        info_text.insert(1.0, info)
        info_text.config(state='disabled')
        
        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Button(
            button_frame,
            text="Открыть папку установки",
            command=lambda: self.open_install_folder()
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Закрыть",
            command=dialog.destroy
        ).pack(side='right', padx=5)
        
    def open_install_folder(self):
        """Открывает папку установки"""
        path = Path(self.config.install_path)
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(path)])
        else:  # Linux
            subprocess.run(["xdg-open", str(path)])
            
    def cancel_installation(self):
        """Отмена установки"""
        if self.installation_running:
            if not messagebox.askyesno(
                "Подтверждение",
                "Установка в процессе. Вы уверены, что хотите прервать?"
            ):
                return
                
        self.root.destroy()
        
    def run(self):
        """Запуск GUI"""
        self.root.mainloop()


def main():
    """Главная функция"""
    # Проверяем наличие tkinter
    try:
        import tkinter
    except ImportError:
        print("Ошибка: Требуется установка tkinter")
        print("Ubuntu/Debian: sudo apt-get install python3-tk")
        print("Fedora: sudo dnf install python3-tkinter")
        print("macOS: brew install python-tk")
        print("Windows: Обычно включен в стандартную поставку Python")
        return
        
    # Создаем и запускаем инсталлятор
    installer = UniversalInstaller()
    installer.run()


if __name__ == "__main__":
    main()
