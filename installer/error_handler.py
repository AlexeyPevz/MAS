#!/usr/bin/env python3
"""
Error Handler and Recovery System for AI Memory System Installer
Система обработки ошибок и восстановления
"""

import os
import sys
import psutil
import shutil
import subprocess
import socket
import time
import signal
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class SystemRequirements:
    """Системные требования"""
    min_disk_space_gb: float = 2.0
    min_memory_mb: int = 512
    required_ports: List[int] = None
    
    def __post_init__(self):
        if self.required_ports is None:
            self.required_ports = [8000, 8080, 5000, 6333, 19530]  # API, Web, Installer, Qdrant, Milvus


class ErrorHandler:
    """Обработчик ошибок и восстановление"""
    
    def __init__(self, log_callback=None):
        self.log = log_callback or print
        self.requirements = SystemRequirements()
        self.recovery_attempts = {}
        self.max_recovery_attempts = 3
        
    def handle_error(self, error: Exception, context: str = "") -> bool:
        """Обрабатывает ошибку и пытается восстановиться"""
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        self.log(f"Обнаружена ошибка: {error_type} - {error}", "ERROR")
        
        # Словарь обработчиков ошибок
        handlers = {
            "OSError": self._handle_os_error,
            "PermissionError": self._handle_permission_error,
            "ConnectionError": self._handle_connection_error,
            "MemoryError": self._handle_memory_error,
            "subprocess.CalledProcessError": self._handle_subprocess_error,
        }
        
        # Проверяем специфичные ошибки по содержимому
        if "no space left" in error_msg or "disk full" in error_msg:
            return self._handle_disk_space_error()
        elif "address already in use" in error_msg or "port" in error_msg:
            return self._handle_port_conflict()
        elif "connection refused" in error_msg:
            return self._handle_connection_refused()
        elif "package not found" in error_msg or "module not found" in error_msg:
            return self._handle_missing_package(error_msg)
        elif "timeout" in error_msg:
            return self._handle_timeout_error()
        
        # Используем специфичный обработчик если есть
        handler = handlers.get(error_type)
        if handler:
            return handler(error, context)
        
        # Общая обработка
        return self._handle_generic_error(error, context)
        
    def _handle_disk_space_error(self) -> bool:
        """Обработка ошибок нехватки места на диске"""
        self.log("\n⚠️  Недостаточно места на диске!", "WARNING")
        
        # Анализируем использование диска
        disk_usage = shutil.disk_usage("/")
        free_gb = disk_usage.free / (1024**3)
        total_gb = disk_usage.total / (1024**3)
        used_percent = (disk_usage.used / disk_usage.total) * 100
        
        self.log(f"Свободно: {free_gb:.1f} GB из {total_gb:.1f} GB ({used_percent:.1f}% занято)")
        
        # Предлагаем варианты очистки
        self.log("\n🧹 Варианты освобождения места:")
        
        cleanable_space = 0
        
        # 1. Очистка логов
        log_dirs = self._find_log_directories()
        if log_dirs:
            log_size = self._calculate_directory_size(log_dirs)
            if log_size > 0:
                self.log(f"1. Очистить логи ({self._format_size(log_size)})")
                cleanable_space += log_size
        
        # 2. Очистка кэша
        cache_dirs = self._find_cache_directories()
        if cache_dirs:
            cache_size = self._calculate_directory_size(cache_dirs)
            if cache_size > 0:
                self.log(f"2. Очистить кэш ({self._format_size(cache_size)})")
                cleanable_space += cache_size
        
        # 3. Очистка временных файлов
        temp_size = self._calculate_temp_size()
        if temp_size > 0:
            self.log(f"3. Очистить временные файлы ({self._format_size(temp_size)})")
            cleanable_space += temp_size
        
        # 4. Старые виртуальные окружения
        old_venvs = self._find_old_venvs()
        if old_venvs:
            venv_size = self._calculate_directory_size(old_venvs)
            if venv_size > 0:
                self.log(f"4. Удалить старые виртуальные окружения ({self._format_size(venv_size)})")
                cleanable_space += venv_size
        
        if cleanable_space > 0:
            self.log(f"\n💾 Можно освободить до {self._format_size(cleanable_space)}")
            
            if self._confirm("Выполнить автоматическую очистку?"):
                freed_space = self._perform_cleanup(log_dirs, cache_dirs, old_venvs)
                self.log(f"✓ Освобождено {self._format_size(freed_space)}")
                
                # Проверяем, достаточно ли теперь места
                disk_usage = shutil.disk_usage("/")
                free_gb = disk_usage.free / (1024**3)
                if free_gb >= self.requirements.min_disk_space_gb:
                    self.log("✓ Теперь достаточно места для установки")
                    return True
        
        # Предлагаем альтернативные пути установки
        self.log("\n📁 Альтернативные варианты:")
        self.log("1. Выбрать другой диск для установки")
        self.log("2. Использовать внешний накопитель")
        self.log("3. Освободить место вручную и повторить")
        
        return False
        
    def _handle_port_conflict(self) -> bool:
        """Обработка конфликтов портов"""
        self.log("\n⚠️  Обнаружен конфликт портов!", "WARNING")
        
        # Проверяем занятые порты
        occupied_ports = []
        for port in self.requirements.required_ports:
            if self._is_port_occupied(port):
                process = self._find_process_by_port(port)
                occupied_ports.append((port, process))
                
        if not occupied_ports:
            return True
            
        self.log("\n🔍 Занятые порты:")
        for port, process in occupied_ports:
            if process:
                self.log(f"  Порт {port}: {process['name']} (PID: {process['pid']})")
            else:
                self.log(f"  Порт {port}: неизвестный процесс")
                
        # Предлагаем варианты
        self.log("\n🛠️  Варианты решения:")
        self.log("1. Остановить конфликтующие процессы")
        self.log("2. Использовать другие порты")
        self.log("3. Перезапустить с --force флагом")
        
        if self._confirm("Попытаться остановить конфликтующие процессы?"):
            success = True
            for port, process in occupied_ports:
                if process and self._stop_process(process['pid']):
                    self.log(f"✓ Остановлен процесс {process['name']} (PID: {process['pid']})")
                else:
                    self.log(f"✗ Не удалось остановить процесс на порту {port}")
                    success = False
                    
            if success:
                self.log("✓ Все конфликтующие процессы остановлены")
                return True
                
        return False
        
    def _handle_memory_error(self, error: Exception = None, context: str = "") -> bool:
        """Обработка ошибок памяти"""
        self.log("\n⚠️  Недостаточно оперативной памяти!", "WARNING")
        
        # Анализируем использование памяти
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        self.log(f"\n💾 Использование памяти:")
        self.log(f"  RAM: {memory.percent}% ({self._format_size(memory.used)} из {self._format_size(memory.total)})")
        self.log(f"  Swap: {swap.percent}% ({self._format_size(swap.used)} из {self._format_size(swap.total)})")
        
        # Находим процессы, потребляющие много памяти
        memory_hogs = self._find_memory_intensive_processes()
        if memory_hogs:
            self.log("\n🔍 Процессы с высоким потреблением памяти:")
            for proc in memory_hogs[:5]:
                self.log(f"  {proc['name']}: {self._format_size(proc['memory'])} ({proc['percent']:.1f}%)")
                
        # Предлагаем решения
        self.log("\n🛠️  Варианты решения:")
        self.log("1. Закрыть ненужные приложения")
        self.log("2. Увеличить swap файл")
        self.log("3. Перезагрузить систему")
        self.log("4. Использовать --low-memory режим установки")
        
        # Пытаемся освободить память
        if self._confirm("Попытаться освободить память автоматически?"):
            freed = self._free_memory()
            if freed > 0:
                self.log(f"✓ Освобождено примерно {self._format_size(freed)} памяти")
                
                # Проверяем, достаточно ли теперь
                memory = psutil.virtual_memory()
                if memory.available >= self.requirements.min_memory_mb * 1024 * 1024:
                    self.log("✓ Теперь достаточно памяти для продолжения")
                    return True
                    
        return False
        
    def _handle_permission_error(self, error: Exception, context: str = "") -> bool:
        """Обработка ошибок прав доступа"""
        self.log("\n⚠️  Недостаточно прав доступа!", "WARNING")
        
        # Анализируем контекст ошибки
        error_msg = str(error)
        
        if "sudo" in error_msg or "root" in error_msg or "/etc" in error_msg:
            self.log("Требуются права администратора (sudo)")
            self.log("\n🛠️  Варианты решения:")
            self.log("1. Перезапустить с sudo: sudo python install.py")
            self.log("2. Изменить путь установки на домашнюю директорию")
            self.log("3. Исправить права на директорию установки")
            
        elif "write" in error_msg or "read-only" in error_msg:
            self.log("Нет прав на запись в указанную директорию")
            
            # Пытаемся определить проблемную директорию
            problem_path = self._extract_path_from_error(error_msg)
            if problem_path and Path(problem_path).exists():
                self.log(f"Проблемная директория: {problem_path}")
                
                # Проверяем владельца
                import pwd
                stat_info = os.stat(problem_path)
                owner = pwd.getpwuid(stat_info.st_uid).pw_name
                current_user = os.getenv('USER')
                
                if owner != current_user:
                    self.log(f"Владелец: {owner}, текущий пользователь: {current_user}")
                    
                    if self._confirm(f"Попытаться изменить владельца на {current_user}?"):
                        if self._change_ownership(problem_path, current_user):
                            self.log("✓ Права изменены успешно")
                            return True
                            
        return False
        
    def _handle_connection_error(self, error: Exception, context: str = "") -> bool:
        """Обработка ошибок подключения"""
        self.log("\n⚠️  Ошибка подключения!", "WARNING")
        
        # Проверяем интернет соединение
        if not self._check_internet_connection():
            self.log("✗ Нет подключения к интернету")
            self.log("\n🛠️  Варианты решения:")
            self.log("1. Проверить сетевое подключение")
            self.log("2. Проверить настройки прокси")
            self.log("3. Использовать офлайн установку (если доступна)")
            
            # Проверяем наличие офлайн пакетов
            offline_cache = Path("installer/offline_cache")
            if offline_cache.exists():
                if self._confirm("Использовать офлайн кэш для установки?"):
                    os.environ['PIP_NO_INDEX'] = '1'
                    os.environ['PIP_FIND_LINKS'] = str(offline_cache)
                    self.log("✓ Переключено на офлайн установку")
                    return True
                    
        else:
            # Интернет есть, проблема в чем-то другом
            error_msg = str(error).lower()
            
            if "timeout" in error_msg:
                self.log("Превышено время ожидания")
                self.log("Возможные причины:")
                self.log("- Медленное соединение")
                self.log("- Перегруженный сервер")
                self.log("- Блокировка firewall")
                
                if self._confirm("Увеличить время ожидания и повторить?"):
                    os.environ['PIP_DEFAULT_TIMEOUT'] = '120'
                    return True
                    
            elif "certificate" in error_msg or "ssl" in error_msg:
                self.log("Проблема с SSL сертификатом")
                self.log("\n🛠️  Варианты решения:")
                self.log("1. Обновить сертификаты: pip install --upgrade certifi")
                self.log("2. Временно отключить проверку SSL (небезопасно)")
                
                if self._confirm("Временно отключить проверку SSL?"):
                    os.environ['PYTHONHTTPSVERIFY'] = '0'
                    os.environ['PIP_TRUSTED_HOST'] = 'pypi.org files.pythonhosted.org'
                    self.log("⚠️  SSL проверка отключена (только для этой сессии)")
                    return True
                    
        return False
        
    def _handle_subprocess_error(self, error: Exception, context: str = "") -> bool:
        """Обработка ошибок подпроцессов"""
        self.log("\n⚠️  Ошибка выполнения команды!", "WARNING")
        
        if hasattr(error, 'cmd'):
            self.log(f"Команда: {' '.join(error.cmd) if isinstance(error.cmd, list) else error.cmd}")
        if hasattr(error, 'returncode'):
            self.log(f"Код возврата: {error.returncode}")
            
        # Анализируем вывод ошибки
        error_output = ""
        if hasattr(error, 'stderr'):
            error_output = error.stderr.decode() if isinstance(error.stderr, bytes) else str(error.stderr)
        elif hasattr(error, 'output'):
            error_output = error.output.decode() if isinstance(error.output, bytes) else str(error.output)
            
        if error_output:
            # Ищем специфичные проблемы
            if "command not found" in error_output or "not recognized" in error_output:
                missing_cmd = self._extract_command_from_error(error_output)
                self.log(f"Команда '{missing_cmd}' не найдена")
                
                # Предлагаем установить
                install_cmds = {
                    'git': {
                        'apt': 'sudo apt-get install git',
                        'yum': 'sudo yum install git',
                        'brew': 'brew install git',
                        'windows': 'Скачайте с https://git-scm.com/'
                    },
                    'docker': {
                        'apt': 'sudo apt-get install docker.io',
                        'yum': 'sudo yum install docker',
                        'brew': 'brew install docker',
                        'windows': 'Скачайте Docker Desktop'
                    },
                    'node': {
                        'apt': 'sudo apt-get install nodejs',
                        'yum': 'sudo yum install nodejs',
                        'brew': 'brew install node',
                        'windows': 'Скачайте с https://nodejs.org/'
                    }
                }
                
                if missing_cmd in install_cmds:
                    self.log(f"\n🛠️  Установка {missing_cmd}:")
                    pkg_manager = self._detect_package_manager()
                    if pkg_manager in install_cmds[missing_cmd]:
                        cmd = install_cmds[missing_cmd][pkg_manager]
                        self.log(f"  {cmd}")
                        
                        if self._confirm(f"Установить {missing_cmd} автоматически?"):
                            if self._run_command(cmd):
                                self.log(f"✓ {missing_cmd} установлен")
                                return True
                                
        return False
        
    def _handle_timeout_error(self) -> bool:
        """Обработка ошибок таймаута"""
        self.log("\n⚠️  Превышено время ожидания!", "WARNING")
        
        # Увеличиваем таймауты
        self.log("Увеличиваем время ожидания...")
        os.environ['PIP_DEFAULT_TIMEOUT'] = '120'
        
        # Проверяем скорость соединения
        speed = self._check_connection_speed()
        if speed and speed < 1.0:  # Меньше 1 Мбит/с
            self.log(f"⚠️  Медленное соединение: {speed:.2f} Мбит/с")
            self.log("Рекомендуется:")
            self.log("- Использовать проводное подключение")
            self.log("- Закрыть другие приложения, использующие интернет")
            self.log("- Попробовать в другое время")
            
        return True
        
    def _handle_missing_package(self, error_msg: str) -> bool:
        """Обработка отсутствующих пакетов"""
        self.log("\n⚠️  Отсутствует необходимый пакет!", "WARNING")
        
        # Извлекаем имя пакета
        package_name = self._extract_package_name(error_msg)
        if package_name:
            self.log(f"Отсутствует пакет: {package_name}")
            
            # Пытаемся установить
            if self._confirm(f"Установить {package_name}?"):
                if self._install_package(package_name):
                    self.log(f"✓ Пакет {package_name} установлен")
                    return True
                    
        return False
        
    def _handle_generic_error(self, error: Exception, context: str = "") -> bool:
        """Общая обработка неизвестных ошибок"""
        self.log("\n⚠️  Неизвестная ошибка!", "WARNING")
        
        # Проверяем количество попыток восстановления
        error_key = f"{type(error).__name__}_{context}"
        self.recovery_attempts[error_key] = self.recovery_attempts.get(error_key, 0) + 1
        
        if self.recovery_attempts[error_key] >= self.max_recovery_attempts:
            self.log(f"Превышено количество попыток восстановления ({self.max_recovery_attempts})")
            return False
            
        self.log(f"Попытка восстановления {self.recovery_attempts[error_key]} из {self.max_recovery_attempts}")
        
        # Общие действия восстановления
        self.log("\n🛠️  Попытка восстановления:")
        
        # 1. Очистка временных файлов
        self.log("1. Очистка временных файлов...")
        self._cleanup_temp_files()
        
        # 2. Сброс переменных окружения
        self.log("2. Сброс переменных окружения...")
        self._reset_environment()
        
        # 3. Небольшая задержка
        self.log("3. Ожидание перед повторной попыткой...")
        time.sleep(2)
        
        return True
        
    # Вспомогательные методы
    
    def _find_log_directories(self) -> List[Path]:
        """Находит директории с логами"""
        log_dirs = []
        search_paths = [
            Path.home() / ".cache",
            Path("/var/log"),
            Path("/tmp"),
            Path.cwd() / "logs",
        ]
        
        for base_path in search_paths:
            if base_path.exists():
                for path in base_path.rglob("*.log"):
                    log_dirs.append(path.parent)
                    
        return list(set(log_dirs))
        
    def _find_cache_directories(self) -> List[Path]:
        """Находит директории с кэшем"""
        cache_dirs = []
        cache_paths = [
            Path.home() / ".cache" / "pip",
            Path.home() / ".cache" / "pypoetry",
            Path.home() / ".npm",
            Path.home() / ".yarn",
            Path("/tmp") / "pip-cache",
        ]
        
        for path in cache_paths:
            if path.exists():
                cache_dirs.append(path)
                
        return cache_dirs
        
    def _find_old_venvs(self) -> List[Path]:
        """Находит старые виртуальные окружения"""
        venvs = []
        
        # Ищем в текущей директории и родительской
        for base in [Path.cwd(), Path.cwd().parent]:
            for venv_name in ['venv', 'env', '.venv', 'virtualenv']:
                venv_path = base / venv_name
                if venv_path.exists() and (venv_path / 'bin' / 'python').exists():
                    # Проверяем возраст
                    age = datetime.now() - datetime.fromtimestamp(venv_path.stat().st_mtime)
                    if age > timedelta(days=30):  # Старше 30 дней
                        venvs.append(venv_path)
                        
        return venvs
        
    def _calculate_directory_size(self, directories: List[Path]) -> int:
        """Вычисляет размер директорий"""
        total_size = 0
        for directory in directories:
            if directory.exists():
                for path in directory.rglob('*'):
                    if path.is_file():
                        try:
                            total_size += path.stat().st_size
                        except:
                            pass
        return total_size
        
    def _calculate_temp_size(self) -> int:
        """Вычисляет размер временных файлов"""
        temp_size = 0
        temp_dir = Path("/tmp") if os.name != 'nt' else Path(os.environ.get('TEMP', '/tmp'))
        
        if temp_dir.exists():
            for path in temp_dir.iterdir():
                try:
                    if path.is_file():
                        # Проверяем возраст файла
                        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
                        if age > timedelta(hours=24):  # Старше 24 часов
                            temp_size += path.stat().st_size
                except:
                    pass
                    
        return temp_size
        
    def _format_size(self, size_bytes: int) -> str:
        """Форматирует размер в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
        
    def _confirm(self, message: str) -> bool:
        """Запрашивает подтверждение у пользователя"""
        response = input(f"{message} [y/N]: ").strip().lower()
        return response in ['y', 'yes', 'да']
        
    def _perform_cleanup(self, log_dirs: List[Path], cache_dirs: List[Path], old_venvs: List[Path]) -> int:
        """Выполняет очистку файлов"""
        freed_space = 0
        
        # Очистка логов
        for log_dir in log_dirs:
            try:
                for log_file in log_dir.glob("*.log"):
                    if log_file.stat().st_size > 100 * 1024 * 1024:  # Больше 100MB
                        size = log_file.stat().st_size
                        log_file.unlink()
                        freed_space += size
            except:
                pass
                
        # Очистка кэша
        for cache_dir in cache_dirs:
            try:
                size = self._calculate_directory_size([cache_dir])
                shutil.rmtree(cache_dir, ignore_errors=True)
                freed_space += size
            except:
                pass
                
        # Удаление старых venv
        for venv in old_venvs:
            try:
                size = self._calculate_directory_size([venv])
                shutil.rmtree(venv, ignore_errors=True)
                freed_space += size
            except:
                pass
                
        return freed_space
        
    def _is_port_occupied(self, port: int) -> bool:
        """Проверяет, занят ли порт"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('', port))
            sock.close()
            return False
        except:
            return True
            
    def _find_process_by_port(self, port: int) -> Optional[Dict]:
        """Находит процесс, занимающий порт"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    try:
                        proc = psutil.Process(conn.pid)
                        return {
                            'pid': conn.pid,
                            'name': proc.name(),
                            'cmdline': ' '.join(proc.cmdline())
                        }
                    except:
                        pass
        except:
            pass
        return None
        
    def _stop_process(self, pid: int) -> bool:
        """Останавливает процесс"""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            time.sleep(1)
            
            if proc.is_running():
                proc.kill()
                time.sleep(1)
                
            return not proc.is_running()
        except:
            return False
            
    def _find_memory_intensive_processes(self) -> List[Dict]:
        """Находит процессы с высоким потреблением памяти"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
                    memory_percent = proc.memory_percent()
                    
                    if memory_percent > 5.0:  # Больше 5% памяти
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory': proc.info['memory_info'].rss,
                            'percent': memory_percent
                        })
                except:
                    pass
                    
            # Сортируем по использованию памяти
            processes.sort(key=lambda x: x['memory'], reverse=True)
            
        except:
            pass
            
        return processes
        
    def _free_memory(self) -> int:
        """Пытается освободить память"""
        freed = 0
        
        # 1. Очистка системного кэша (Linux)
        if os.name != 'nt' and os.geteuid() == 0:
            try:
                subprocess.run(['sync'], check=True)
                subprocess.run(['sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], check=True)
                freed += 500 * 1024 * 1024  # Примерно
            except:
                pass
                
        # 2. Сборка мусора Python
        import gc
        gc.collect()
        
        # 3. Закрытие неиспользуемых файловых дескрипторов
        try:
            max_fd = os.sysconf('SC_OPEN_MAX')
            for fd in range(3, min(max_fd, 1024)):
                try:
                    os.close(fd)
                except:
                    pass
        except:
            pass
            
        return freed
        
    def _check_internet_connection(self) -> bool:
        """Проверяет подключение к интернету"""
        test_urls = [
            "https://pypi.org",
            "https://google.com",
            "https://github.com"
        ]
        
        for url in test_urls:
            try:
                import urllib.request
                urllib.request.urlopen(url, timeout=5)
                return True
            except:
                continue
                
        return False
        
    def _check_connection_speed(self) -> Optional[float]:
        """Проверяет скорость соединения (Мбит/с)"""
        try:
            import urllib.request
            import time
            
            # Скачиваем небольшой файл для теста
            url = "https://pypi.org/static/images/logo-small.svg"
            start_time = time.time()
            
            response = urllib.request.urlopen(url)
            data = response.read()
            
            elapsed = time.time() - start_time
            size_bits = len(data) * 8
            speed_bps = size_bits / elapsed
            speed_mbps = speed_bps / (1024 * 1024)
            
            return speed_mbps
        except:
            return None
            
    def _extract_path_from_error(self, error_msg: str) -> Optional[str]:
        """Извлекает путь из сообщения об ошибке"""
        import re
        
        # Ищем пути в сообщении
        path_patterns = [
            r"'([^']+)'",  # В одинарных кавычках
            r'"([^"]+)"',  # В двойных кавычках
            r'`([^`]+)`',  # В обратных кавычках
            r'(\S+/\S+)',  # Unix пути
            r'([A-Za-z]:\\[^\\]+(?:\\[^\\]+)*)',  # Windows пути
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, error_msg)
            if match:
                potential_path = match.group(1)
                if '/' in potential_path or '\\' in potential_path:
                    return potential_path
                    
        return None
        
    def _change_ownership(self, path: str, user: str) -> bool:
        """Изменяет владельца файла/директории"""
        try:
            cmd = f"sudo chown -R {user}:{user} {path}"
            return self._run_command(cmd)
        except:
            return False
            
    def _detect_package_manager(self) -> str:
        """Определяет менеджер пакетов системы"""
        if os.name == 'nt':
            return 'windows'
            
        managers = {
            'apt': '/usr/bin/apt-get',
            'yum': '/usr/bin/yum',
            'dnf': '/usr/bin/dnf',
            'brew': '/usr/local/bin/brew',
            'pacman': '/usr/bin/pacman',
        }
        
        for name, path in managers.items():
            if Path(path).exists():
                return name
                
        return 'unknown'
        
    def _run_command(self, cmd: str) -> bool:
        """Выполняет команду"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
            
    def _extract_command_from_error(self, error_msg: str) -> str:
        """Извлекает имя команды из сообщения об ошибке"""
        import re
        
        patterns = [
            r"command not found: (\w+)",
            r"'(\w+)' is not recognized",
            r"(\w+): command not found",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                return match.group(1)
                
        return "unknown"
        
    def _install_package(self, package_name: str) -> bool:
        """Устанавливает Python пакет"""
        try:
            cmd = f"{sys.executable} -m pip install {package_name}"
            return self._run_command(cmd)
        except:
            return False
            
    def _extract_package_name(self, error_msg: str) -> Optional[str]:
        """Извлекает имя пакета из сообщения об ошибке"""
        import re
        
        patterns = [
            r"No module named '(\w+)'",
            r"ModuleNotFoundError: (\w+)",
            r"ImportError: (\w+)",
            r"Package '(\w+)' not found",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                return match.group(1)
                
        return None
        
    def _cleanup_temp_files(self):
        """Очищает временные файлы"""
        temp_patterns = [
            "*.tmp",
            "*.temp",
            "*.pyc",
            "__pycache__",
            ".pytest_cache",
            ".coverage",
        ]
        
        for pattern in temp_patterns:
            for path in Path.cwd().rglob(pattern):
                try:
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)
                except:
                    pass
                    
    def _reset_environment(self):
        """Сбрасывает критичные переменные окружения"""
        critical_vars = [
            'PYTHONPATH',
            'LD_LIBRARY_PATH',
            'DYLD_LIBRARY_PATH',
            'PIP_NO_INDEX',
            'PIP_FIND_LINKS',
            'PYTHONHTTPSVERIFY',
        ]
        
        for var in critical_vars:
            if var in os.environ:
                del os.environ[var]


class SafeInstaller:
    """Безопасный инсталлятор с обработкой ошибок"""
    
    def __init__(self, base_installer, log_callback=None):
        self.base_installer = base_installer
        self.error_handler = ErrorHandler(log_callback)
        self.install_attempts = 0
        self.max_attempts = 3
        
    def safe_install(self, *args, **kwargs):
        """Безопасная установка с обработкой ошибок"""
        while self.install_attempts < self.max_attempts:
            self.install_attempts += 1
            
            try:
                # Пытаемся выполнить установку
                return self.base_installer(*args, **kwargs)
                
            except Exception as e:
                # Обрабатываем ошибку
                if self.error_handler.handle_error(e, context="installation"):
                    # Если удалось восстановиться, пробуем снова
                    continue
                else:
                    # Если не удалось восстановиться
                    if self.install_attempts < self.max_attempts:
                        if self._confirm_retry():
                            continue
                    
                    # Финальная ошибка
                    self._handle_final_error(e)
                    raise
                    
    def _confirm_retry(self) -> bool:
        """Запрашивает подтверждение повторной попытки"""
        remaining = self.max_attempts - self.install_attempts
        response = input(f"\nПопробовать еще раз? (осталось попыток: {remaining}) [y/N]: ")
        return response.strip().lower() in ['y', 'yes', 'да']
        
    def _handle_final_error(self, error: Exception):
        """Обработка финальной ошибки"""
        print("\n" + "=" * 60)
        print("❌ УСТАНОВКА НЕ УДАЛАСЬ")
        print("=" * 60)
        print(f"\nОшибка: {type(error).__name__}: {str(error)}")
        print("\n📋 Что можно сделать:")
        print("1. Проверить логи установки в installer/logs/")
        print("2. Запустить проверку системы: python installer/cli_installer.py --check")
        print("3. Обратиться за помощью с логами ошибки")
        print("4. Попробовать другой тип инсталлятора")
        print("\n💡 Полезные команды:")
        print("  make check     # Проверка системы")
        print("  make clean     # Очистка временных файлов")
        print("  make install   # Повторная попытка установки")


# Декоратор для безопасного выполнения функций
def safe_execution(func):
    """Декоратор для безопасного выполнения функций с обработкой ошибок"""
    def wrapper(*args, **kwargs):
        error_handler = ErrorHandler()
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            attempts += 1
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_handler.handle_error(e, context=func.__name__):
                    continue
                else:
                    if attempts < max_attempts:
                        time.sleep(1)  # Небольшая задержка
                        continue
                    raise
                    
    return wrapper