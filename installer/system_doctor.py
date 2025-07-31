#!/usr/bin/env python3
"""
System Doctor - Diagnostic and Recovery Tool
Утилита диагностики и восстановления для AI Memory System
"""

import os
import sys
import platform
import psutil
import subprocess
import socket
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse

# Импортируем rich для красивого вывода
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None
    rprint = print

# Импортируем обработчик ошибок
try:
    from error_handler import ErrorHandler, SystemRequirements
except ImportError:
    ErrorHandler = None
    SystemRequirements = None


class SystemDoctor:
    """Доктор системы - диагностика и восстановление"""
    
    def __init__(self):
        self.error_handler = ErrorHandler() if ErrorHandler else None
        self.requirements = SystemRequirements() if SystemRequirements else None
        self.issues_found = []
        self.fixes_applied = []
        
    def print_banner(self):
        """Выводит баннер"""
        banner = """
╔══════════════════════════════════════════════╗
║         AI Memory System Doctor              ║
║     Диагностика и восстановление v1.0        ║
╚══════════════════════════════════════════════╝
        """
        if RICH_AVAILABLE:
            console.print(Panel(banner, style="bold blue"))
        else:
            print(banner)
            
    def run_diagnostics(self) -> Dict[str, Dict]:
        """Запускает полную диагностику системы"""
        self.print_banner()
        
        if RICH_AVAILABLE:
            console.print("\n[bold yellow]🔍 Запуск диагностики системы...[/bold yellow]\n")
        else:
            print("\n🔍 Запуск диагностики системы...\n")
            
        diagnostics = {
            "system": self.check_system_info(),
            "resources": self.check_resources(),
            "network": self.check_network(),
            "dependencies": self.check_dependencies(),
            "installation": self.check_installation(),
            "services": self.check_services(),
            "logs": self.analyze_logs(),
        }
        
        return diagnostics
        
    def check_system_info(self) -> Dict:
        """Проверяет информацию о системе"""
        info = {
            "platform": platform.system(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "hostname": socket.gethostname(),
            "user": os.getenv('USER', os.getenv('USERNAME', 'unknown')),
        }
        
        # Проверяем виртуальное окружение
        info["in_venv"] = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        return info
        
    def check_resources(self) -> Dict:
        """Проверяет системные ресурсы"""
        # CPU
        cpu_info = {
            "count": psutil.cpu_count(),
            "usage_percent": psutil.cpu_percent(interval=1),
            "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        }
        
        # Память
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
            "status": "OK" if memory.percent < 85 else "WARNING" if memory.percent < 95 else "CRITICAL"
        }
        
        # Диск
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
            "status": "OK" if disk.percent < 85 else "WARNING" if disk.percent < 95 else "CRITICAL"
        }
        
        # Проверяем проблемы
        if memory.percent > 85:
            self.issues_found.append({
                "type": "memory",
                "severity": "high" if memory.percent > 95 else "medium",
                "message": f"Высокое использование памяти: {memory.percent}%",
                "fix": "free_memory"
            })
            
        if disk.percent > 85:
            self.issues_found.append({
                "type": "disk",
                "severity": "high" if disk.percent > 95 else "medium",
                "message": f"Мало свободного места на диске: {disk.free / (1024**3):.1f} GB",
                "fix": "free_disk_space"
            })
            
        return {
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info
        }
        
    def check_network(self) -> Dict:
        """Проверяет сетевое подключение"""
        network_info = {
            "internet": False,
            "dns": False,
            "proxy": None,
            "speed": None,
            "ports": {}
        }
        
        # Проверка интернета
        test_hosts = [
            ("pypi.org", 443),
            ("github.com", 443),
            ("google.com", 443)
        ]
        
        for host, port in test_hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    network_info["internet"] = True
                    break
            except:
                pass
                
        # Проверка DNS
        try:
            socket.gethostbyname("pypi.org")
            network_info["dns"] = True
        except:
            self.issues_found.append({
                "type": "network",
                "severity": "high",
                "message": "Проблемы с DNS разрешением",
                "fix": "fix_dns"
            })
            
        # Проверка прокси
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            if os.getenv(var):
                network_info["proxy"] = os.getenv(var)
                break
                
        # Проверка портов
        if self.requirements:
            for port in self.requirements.required_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.bind(('', port))
                    sock.close()
                    network_info["ports"][port] = "free"
                except:
                    network_info["ports"][port] = "occupied"
                    
                    # Находим процесс
                    try:
                        for conn in psutil.net_connections():
                            if conn.laddr.port == port:
                                proc = psutil.Process(conn.pid)
                                self.issues_found.append({
                                    "type": "port",
                                    "severity": "medium",
                                    "message": f"Порт {port} занят процессом {proc.name()} (PID: {conn.pid})",
                                    "fix": "free_port",
                                    "data": {"port": port, "pid": conn.pid}
                                })
                                break
                    except:
                        pass
                        
        if not network_info["internet"]:
            self.issues_found.append({
                "type": "network",
                "severity": "critical",
                "message": "Нет подключения к интернету",
                "fix": "check_network"
            })
            
        return network_info
        
    def check_dependencies(self) -> Dict:
        """Проверяет зависимости"""
        deps = {
            "python": {
                "installed": True,
                "version": sys.version,
                "path": sys.executable
            },
            "pip": self._check_command("pip"),
            "git": self._check_command("git"),
            "docker": self._check_command("docker"),
            "node": self._check_command("node"),
        }
        
        # Проверяем Python пакеты
        required_packages = [
            "autogen",
            "chromadb",
            "paramiko",
            "rich",
            "pyyaml"
        ]
        
        deps["packages"] = {}
        for package in required_packages:
            try:
                __import__(package)
                deps["packages"][package] = {"installed": True}
            except ImportError:
                deps["packages"][package] = {"installed": False}
                self.issues_found.append({
                    "type": "dependency",
                    "severity": "medium",
                    "message": f"Пакет {package} не установлен",
                    "fix": "install_package",
                    "data": {"package": package}
                })
                
        return deps
        
    def check_installation(self) -> Dict:
        """Проверяет установку AI Memory System"""
        installation = {
            "found": False,
            "path": None,
            "version": None,
            "config": None,
            "issues": []
        }
        
        # Ищем установку
        search_paths = [
            Path.home() / "ai-memory-system",
            Path("/opt/ai-memory-system"),
            Path.cwd().parent,
            Path.cwd()
        ]
        
        for path in search_paths:
            if (path / "run_system.py").exists():
                installation["found"] = True
                installation["path"] = str(path)
                break
                
        if not installation["found"]:
            self.issues_found.append({
                "type": "installation",
                "severity": "critical",
                "message": "AI Memory System не найдена",
                "fix": "install_system"
            })
            return installation
            
        # Проверяем конфигурацию
        config_path = Path(installation["path"]) / ".env"
        if config_path.exists():
            installation["config"] = "found"
            
            # Проверяем токены
            with open(config_path) as f:
                env_content = f.read()
                
            required_tokens = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
            missing_tokens = []
            
            for token in required_tokens:
                if token not in env_content or f"{token}=" not in env_content:
                    missing_tokens.append(token)
                    
            if missing_tokens:
                installation["issues"].append("missing_tokens")
                self.issues_found.append({
                    "type": "config",
                    "severity": "medium",
                    "message": f"Отсутствуют токены: {', '.join(missing_tokens)}",
                    "fix": "configure_tokens"
                })
        else:
            installation["config"] = "missing"
            self.issues_found.append({
                "type": "config",
                "severity": "high",
                "message": "Файл конфигурации .env не найден",
                "fix": "create_config"
            })
            
        # Проверяем структуру директорий
        required_dirs = ["logs", "memory_data", "cache"]
        for dir_name in required_dirs:
            dir_path = Path(installation["path"]) / dir_name
            if not dir_path.exists():
                installation["issues"].append(f"missing_dir_{dir_name}")
                
        return installation
        
    def check_services(self) -> Dict:
        """Проверяет запущенные сервисы"""
        services = {
            "systemd": False,
            "ai_memory_service": None,
            "docker": None,
            "processes": []
        }
        
        # Проверяем systemd (Linux)
        if platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["systemctl", "is-system-running"],
                    capture_output=True,
                    text=True
                )
                services["systemd"] = result.returncode == 0
                
                # Проверяем наш сервис
                if services["systemd"]:
                    result = subprocess.run(
                        ["systemctl", "status", "ai-memory-system"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        services["ai_memory_service"] = "running"
                    elif "could not be found" in result.stderr:
                        services["ai_memory_service"] = "not_installed"
                    else:
                        services["ai_memory_service"] = "stopped"
                        
            except:
                pass
                
        # Проверяем Docker
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True
            )
            services["docker"] = "running" if result.returncode == 0 else "not_running"
        except:
            services["docker"] = "not_installed"
            
        # Проверяем процессы системы
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'run_system.py' in cmdline or 'ai-memory' in cmdline:
                    services["processes"].append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cmdline": cmdline
                    })
            except:
                pass
                
        return services
        
    def analyze_logs(self) -> Dict:
        """Анализирует логи на наличие ошибок"""
        log_analysis = {
            "logs_found": False,
            "recent_errors": [],
            "error_patterns": {},
            "recommendations": []
        }
        
        # Ищем логи
        log_locations = [
            Path.cwd() / "logs",
            Path.home() / "ai-memory-system" / "logs",
            Path("/var/log/ai-memory-system"),
        ]
        
        log_files = []
        for location in log_locations:
            if location.exists():
                log_files.extend(location.glob("*.log"))
                
        if not log_files:
            return log_analysis
            
        log_analysis["logs_found"] = True
        
        # Анализируем последние логи
        error_keywords = [
            "ERROR", "CRITICAL", "FATAL", "Exception", "Traceback",
            "Failed", "Error:", "failed to", "unable to"
        ]
        
        recent_logs = sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True)[:5]
        
        for log_file in recent_logs:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-100:]  # Последние 100 строк
                    
                for line in lines:
                    for keyword in error_keywords:
                        if keyword in line:
                            log_analysis["recent_errors"].append({
                                "file": log_file.name,
                                "line": line.strip(),
                                "timestamp": datetime.fromtimestamp(log_file.stat().st_mtime)
                            })
                            
                            # Категоризируем ошибки
                            if "memory" in line.lower():
                                log_analysis["error_patterns"]["memory"] = \
                                    log_analysis["error_patterns"].get("memory", 0) + 1
                            elif "disk" in line.lower() or "space" in line.lower():
                                log_analysis["error_patterns"]["disk"] = \
                                    log_analysis["error_patterns"].get("disk", 0) + 1
                            elif "connection" in line.lower() or "network" in line.lower():
                                log_analysis["error_patterns"]["network"] = \
                                    log_analysis["error_patterns"].get("network", 0) + 1
                            elif "permission" in line.lower() or "denied" in line.lower():
                                log_analysis["error_patterns"]["permissions"] = \
                                    log_analysis["error_patterns"].get("permissions", 0) + 1
                                    
            except:
                pass
                
        # Даем рекомендации на основе анализа
        if log_analysis["error_patterns"]:
            most_common = max(log_analysis["error_patterns"], 
                            key=log_analysis["error_patterns"].get)
            
            recommendations = {
                "memory": "Увеличьте объем памяти или закройте ненужные приложения",
                "disk": "Освободите место на диске или перенесите данные",
                "network": "Проверьте интернет соединение и настройки прокси",
                "permissions": "Проверьте права доступа к файлам и директориям"
            }
            
            if most_common in recommendations:
                log_analysis["recommendations"].append(recommendations[most_common])
                
        return log_analysis
        
    def _check_command(self, cmd: str) -> Dict:
        """Проверяет наличие команды"""
        try:
            path = shutil.which(cmd)
            if path:
                # Получаем версию
                version_cmd = f"{cmd} --version"
                result = subprocess.run(
                    version_cmd.split(),
                    capture_output=True,
                    text=True
                )
                version = result.stdout.strip().split('\n')[0] if result.stdout else "unknown"
                
                return {
                    "installed": True,
                    "path": path,
                    "version": version
                }
        except:
            pass
            
        return {"installed": False}
        
    def show_report(self, diagnostics: Dict):
        """Показывает отчет диагностики"""
        if RICH_AVAILABLE:
            self._show_rich_report(diagnostics)
        else:
            self._show_simple_report(diagnostics)
            
    def _show_rich_report(self, diagnostics: Dict):
        """Показывает красивый отчет с rich"""
        # Системная информация
        console.print("\n[bold cyan]📊 Системная информация[/bold cyan]")
        
        sys_table = Table(show_header=False)
        sys_table.add_column("Параметр", style="cyan")
        sys_table.add_column("Значение")
        
        for key, value in diagnostics["system"].items():
            sys_table.add_row(key.replace('_', ' ').title(), str(value))
            
        console.print(sys_table)
        
        # Ресурсы
        console.print("\n[bold cyan]💾 Системные ресурсы[/bold cyan]")
        
        res_table = Table()
        res_table.add_column("Ресурс", style="cyan")
        res_table.add_column("Использование")
        res_table.add_column("Статус")
        
        # CPU
        cpu = diagnostics["resources"]["cpu"]
        res_table.add_row(
            "CPU",
            f"{cpu['usage_percent']}% ({cpu['count']} ядер)",
            "[green]OK[/green]" if cpu['usage_percent'] < 80 else "[yellow]HIGH[/yellow]"
        )
        
        # Память
        mem = diagnostics["resources"]["memory"]
        res_table.add_row(
            "Память",
            f"{mem['percent']:.1f}% ({mem['used'] / (1024**3):.1f} / {mem['total'] / (1024**3):.1f} GB)",
            f"[{'green' if mem['status'] == 'OK' else 'yellow' if mem['status'] == 'WARNING' else 'red'}]{mem['status']}[/]"
        )
        
        # Диск
        disk = diagnostics["resources"]["disk"]
        res_table.add_row(
            "Диск",
            f"{disk['percent']:.1f}% (свободно {disk['free'] / (1024**3):.1f} GB)",
            f"[{'green' if disk['status'] == 'OK' else 'yellow' if disk['status'] == 'WARNING' else 'red'}]{disk['status']}[/]"
        )
        
        console.print(res_table)
        
        # Сеть
        console.print("\n[bold cyan]🌐 Сетевое подключение[/bold cyan]")
        
        net = diagnostics["network"]
        net_table = Table(show_header=False)
        net_table.add_column("Параметр", style="cyan")
        net_table.add_column("Статус")
        
        net_table.add_row(
            "Интернет",
            "[green]✓ Подключен[/green]" if net["internet"] else "[red]✗ Нет подключения[/red]"
        )
        net_table.add_row(
            "DNS",
            "[green]✓ Работает[/green]" if net["dns"] else "[red]✗ Проблемы[/red]"
        )
        
        if net["proxy"]:
            net_table.add_row("Прокси", net["proxy"])
            
        console.print(net_table)
        
        # Проблемы
        if self.issues_found:
            console.print("\n[bold red]⚠️  Обнаруженные проблемы[/bold red]")
            
            issues_table = Table()
            issues_table.add_column("Тип", style="cyan")
            issues_table.add_column("Проблема")
            issues_table.add_column("Важность")
            
            severity_colors = {
                "critical": "red",
                "high": "yellow", 
                "medium": "blue",
                "low": "green"
            }
            
            for issue in self.issues_found:
                issues_table.add_row(
                    issue["type"].upper(),
                    issue["message"],
                    f"[{severity_colors.get(issue['severity'], 'white')}]{issue['severity'].upper()}[/]"
                )
                
            console.print(issues_table)
        else:
            console.print("\n[bold green]✓ Проблемы не обнаружены![/bold green]")
            
    def _show_simple_report(self, diagnostics: Dict):
        """Показывает простой отчет"""
        print("\n📊 СИСТЕМНАЯ ИНФОРМАЦИЯ")
        print("-" * 50)
        for key, value in diagnostics["system"].items():
            print(f"{key}: {value}")
            
        print("\n💾 СИСТЕМНЫЕ РЕСУРСЫ")
        print("-" * 50)
        cpu = diagnostics["resources"]["cpu"]
        print(f"CPU: {cpu['usage_percent']}% ({cpu['count']} ядер)")
        
        mem = diagnostics["resources"]["memory"]
        print(f"Память: {mem['percent']:.1f}% - {mem['status']}")
        
        disk = diagnostics["resources"]["disk"]
        print(f"Диск: {disk['percent']:.1f}% (свободно {disk['free'] / (1024**3):.1f} GB) - {disk['status']}")
        
        print("\n🌐 СЕТЬ")
        print("-" * 50)
        net = diagnostics["network"]
        print(f"Интернет: {'✓ Подключен' if net['internet'] else '✗ Нет подключения'}")
        print(f"DNS: {'✓ Работает' if net['dns'] else '✗ Проблемы'}")
        
        if self.issues_found:
            print("\n⚠️  ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ")
            print("-" * 50)
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. [{issue['severity'].upper()}] {issue['message']}")
        else:
            print("\n✓ Проблемы не обнаружены!")
            
    def fix_issues(self, auto_fix: bool = False):
        """Исправляет обнаруженные проблемы"""
        if not self.issues_found:
            print("\n✓ Нет проблем для исправления")
            return
            
        print(f"\n🔧 Обнаружено проблем: {len(self.issues_found)}")
        
        if not auto_fix:
            response = input("\nПопытаться исправить автоматически? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                return
                
        fixes = {
            "free_memory": self._fix_memory,
            "free_disk_space": self._fix_disk_space,
            "free_port": self._fix_port,
            "install_package": self._fix_install_package,
            "check_network": self._fix_network,
            "create_config": self._fix_create_config,
            "install_system": self._fix_install_system,
        }
        
        for issue in self.issues_found:
            fix_func = fixes.get(issue.get("fix"))
            if fix_func:
                print(f"\n🔧 Исправление: {issue['message']}")
                try:
                    if fix_func(issue):
                        print("✓ Исправлено")
                        self.fixes_applied.append(issue)
                    else:
                        print("✗ Не удалось исправить автоматически")
                except Exception as e:
                    print(f"✗ Ошибка при исправлении: {str(e)}")
                    
    def _fix_memory(self, issue: Dict) -> bool:
        """Освобождает память"""
        if self.error_handler:
            freed = self.error_handler._free_memory()
            return freed > 0
        return False
        
    def _fix_disk_space(self, issue: Dict) -> bool:
        """Освобождает место на диске"""
        if self.error_handler:
            return self.error_handler._handle_disk_space_error()
        return False
        
    def _fix_port(self, issue: Dict) -> bool:
        """Освобождает порт"""
        if "data" in issue and "pid" in issue["data"]:
            try:
                proc = psutil.Process(issue["data"]["pid"])
                proc.terminate()
                return True
            except:
                pass
        return False
        
    def _fix_install_package(self, issue: Dict) -> bool:
        """Устанавливает отсутствующий пакет"""
        if "data" in issue and "package" in issue["data"]:
            try:
                cmd = f"{sys.executable} -m pip install {issue['data']['package']}"
                result = subprocess.run(cmd.split(), capture_output=True)
                return result.returncode == 0
            except:
                pass
        return False
        
    def _fix_network(self, issue: Dict) -> bool:
        """Дает рекомендации по исправлению сети"""
        print("\n💡 Рекомендации по восстановлению сети:")
        print("1. Проверьте кабель/WiFi подключение")
        print("2. Перезапустите роутер")
        print("3. Проверьте настройки прокси")
        print("4. Попробуйте: ping google.com")
        return False
        
    def _fix_create_config(self, issue: Dict) -> bool:
        """Создает базовую конфигурацию"""
        print("\n📝 Создание базовой конфигурации...")
        # Здесь можно вызвать инсталлятор для создания конфига
        return False
        
    def _fix_install_system(self, issue: Dict) -> bool:
        """Предлагает установить систему"""
        print("\n💡 AI Memory System не установлена")
        print("Запустите установку:")
        print("  python install.py")
        return False
        
    def generate_report_file(self, diagnostics: Dict, filename: str = None):
        """Генерирует файл отчета"""
        if not filename:
            filename = f"system_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        report = {
            "timestamp": datetime.now().isoformat(),
            "diagnostics": diagnostics,
            "issues": self.issues_found,
            "fixes_applied": self.fixes_applied,
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n📄 Отчет сохранен: {filename}")
        
        return filename


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='AI Memory System Doctor - Диагностика и восстановление',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  
  # Запуск диагностики
  python system_doctor.py
  
  # Автоматическое исправление проблем
  python system_doctor.py --fix
  
  # Сохранение отчета
  python system_doctor.py --report diagnostic_report.json
  
  # Проверка конкретной подсистемы
  python system_doctor.py --check memory
  python system_doctor.py --check network
        """
    )
    
    parser.add_argument(
        '--fix', '-f',
        action='store_true',
        help='Автоматически исправить обнаруженные проблемы'
    )
    
    parser.add_argument(
        '--report', '-r',
        type=str,
        help='Сохранить отчет в файл'
    )
    
    parser.add_argument(
        '--check', '-c',
        choices=['system', 'resources', 'network', 'dependencies', 'installation', 'services', 'logs'],
        help='Проверить только указанную подсистему'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Вывести результат в формате JSON'
    )
    
    args = parser.parse_args()
    
    # Создаем доктора
    doctor = SystemDoctor()
    
    # Запускаем диагностику
    if args.check:
        # Проверяем только указанную подсистему
        check_method = getattr(doctor, f"check_{args.check}")
        result = check_method()
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{args.check.upper()}:")
            print(json.dumps(result, indent=2))
    else:
        # Полная диагностика
        diagnostics = doctor.run_diagnostics()
        
        if args.json:
            print(json.dumps({
                "diagnostics": diagnostics,
                "issues": doctor.issues_found
            }, indent=2))
        else:
            doctor.show_report(diagnostics)
            
            # Исправляем проблемы если указано
            if args.fix or doctor.issues_found:
                doctor.fix_issues(auto_fix=args.fix)
                
        # Сохраняем отчет если указано
        if args.report:
            doctor.generate_report_file(diagnostics, args.report)
            
        # Показываем итоговый статус
        if not args.json:
            if doctor.fixes_applied:
                print(f"\n✓ Исправлено проблем: {len(doctor.fixes_applied)}")
            
            remaining_issues = len(doctor.issues_found) - len(doctor.fixes_applied)
            if remaining_issues > 0:
                print(f"\n⚠️  Осталось проблем: {remaining_issues}")
                print("Некоторые проблемы требуют ручного вмешательства")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\nОшибка: {str(e)}")
        sys.exit(1)