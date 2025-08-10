#!/usr/bin/env python3
"""
System Health Check for Root-MAS
Проверка работоспособности всех компонентов системы
"""
import asyncio
import sys
import os
from pathlib import Path
import importlib
from typing import Dict, List, Tuple


class SystemChecker:
    def __init__(self):
        self.results = {
            "dependencies": {},
            "modules": {},
            "components": {},
            "config": {}
        }
        self.errors = []
        self.warnings = []
    
    def check_dependencies(self) -> None:
        """Проверка установленных зависимостей"""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            ("fastapi", "FastAPI"),
            ("uvicorn", "Uvicorn"),
            ("pydantic", "Pydantic"),
            ("autogen_agentchat", "AutoGen Chat"),
            ("autogen_ext", "AutoGen Extensions"),
            ("redis", "Redis"),
            ("psycopg2", "PostgreSQL"),
            ("chromadb", "ChromaDB"),
            ("openai", "OpenAI"),
            ("telegram", "Python-Telegram-Bot"),
            ("prometheus_client", "Prometheus"),
            ("numpy", "NumPy"),
            ("scipy", "SciPy"),
            ("networkx", "NetworkX"),
            ("aiohttp", "AioHTTP")
        ]
        
        for package, name in required_packages:
            try:
                importlib.import_module(package)
                self.results["dependencies"][package] = "✅ Installed"
                print(f"  ✅ {name}")
            except ImportError:
                self.results["dependencies"][package] = "❌ Missing"
                self.errors.append(f"Missing dependency: {package}")
                print(f"  ❌ {name} - NOT INSTALLED")
    
    def check_modules(self) -> None:
        """Проверка основных модулей системы"""
        print("\n🔍 Checking system modules...")
        
        modules_to_check = [
            ("agents.base", "Base Agent"),
            ("agents.core_agents", "Core Agents"),
            ("agents.specialized_agents", "Specialized Agents"),
            ("tools.smart_groupchat", "Smart GroupChat"),
            ("tools.quality_metrics", "Quality Metrics"),
            ("tools.error_handler", "Error Handler"),
            ("tools.event_sourcing", "Event Sourcing"),
            ("tools.learning_loop", "Learning Loop"),
            ("tools.knowledge_graph", "Knowledge Graph"),
            ("tools.ab_testing", "A/B Testing"),
            ("tools.federated_learning", "Federated Learning"),
            ("api.main", "API Server"),
            ("api.security", "Security Module"),
            ("memory.redis_store", "Redis Memory"),
            ("memory.chroma_store", "ChromaDB Memory"),
            ("memory.postgres_store", "PostgreSQL Memory")
        ]
        
        for module_path, name in modules_to_check:
            try:
                importlib.import_module(module_path)
                self.results["modules"][module_path] = "✅ OK"
                print(f"  ✅ {name}")
            except Exception as e:
                self.results["modules"][module_path] = f"❌ Error: {str(e)}"
                self.errors.append(f"Module error in {module_path}: {str(e)}")
                print(f"  ❌ {name} - ERROR: {str(e)}")
    
    def check_config_files(self) -> None:
        """Проверка конфигурационных файлов"""
        print("\n🔍 Checking configuration files...")
        
        config_files = [
            ("config/agents.yaml", "Agents Configuration"),
            ("config/llm_tiers.yaml", "LLM Tiers"),
            ("config/routing.yaml", "Agent Routing"),
            ("config/proactive_mode.yaml", "Proactive Mode"),
            (".env.example", "Environment Example")
        ]
        
        for file_path, name in config_files:
            full_path = Path(file_path)
            if full_path.exists():
                self.results["config"][file_path] = "✅ Found"
                print(f"  ✅ {name}")
            else:
                self.results["config"][file_path] = "❌ Missing"
                self.warnings.append(f"Missing config file: {file_path}")
                print(f"  ⚠️  {name} - MISSING")
    
    def check_prompts(self) -> None:
        """Проверка системных промптов"""
        print("\n🔍 Checking agent prompts...")
        
        agents_dir = Path("prompts/agents")
        if not agents_dir.exists():
            self.errors.append("Prompts directory not found")
            print("  ❌ Prompts directory missing!")
            return
        
        agent_count = 0
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir():
                system_prompt = agent_dir / "system.md"
                if system_prompt.exists():
                    agent_count += 1
                    print(f"  ✅ {agent_dir.name} agent")
                else:
                    self.warnings.append(f"Missing system prompt for {agent_dir.name}")
                    print(f"  ⚠️  {agent_dir.name} agent - missing system.md")
        
        print(f"\n  Found {agent_count} agent configurations")
    
    def check_environment(self) -> None:
        """Проверка переменных окружения"""
        print("\n🔍 Checking environment variables...")
        
        required_vars = [
            "OPENAI_API_KEY",
            "TELEGRAM_BOT_TOKEN",
            "REDIS_HOST",
            "POSTGRES_HOST"
        ]
        
        env_file = Path(".env")
        if env_file.exists():
            print("  ✅ .env file found")
        else:
            print("  ⚠️  .env file not found - using defaults")
            self.warnings.append(".env file not found")
        
        for var in required_vars:
            if os.getenv(var):
                print(f"  ✅ {var} is set")
            else:
                print(f"  ⚠️  {var} is NOT set")
                self.warnings.append(f"Environment variable {var} not set")
    
    async def test_basic_functionality(self) -> None:
        """Базовый тест функциональности"""
        print("\n🔍 Testing basic functionality...")
        
        # Test memory systems
        try:
            from memory.redis_store import RedisStore
            redis = RedisStore()
            print("  ✅ Redis connection")
        except Exception as e:
            print(f"  ❌ Redis connection failed: {e}")
            self.warnings.append("Redis not available")
        
        # Test agent creation
        try:
            from agents.core_agents import MetaAgent
            agent = MetaAgent()
            print("  ✅ Agent creation")
        except Exception as e:
            print(f"  ❌ Agent creation failed: {e}")
            self.errors.append(f"Agent creation error: {e}")
        
        # Test smart groupchat
        try:
            from tools.smart_groupchat import SmartGroupChatManager
            chat = SmartGroupChatManager()
            print("  ✅ GroupChat initialization")
        except Exception as e:
            print(f"  ❌ GroupChat failed: {e}")
            self.errors.append(f"GroupChat error: {e}")
    
    def generate_report(self) -> None:
        """Генерация итогового отчета"""
        print("\n" + "="*60)
        print("📊 SYSTEM CHECK SUMMARY")
        print("="*60)
        
        if not self.errors:
            print("\n✅ System is READY TO RUN!")
            print("\nYou can start the system with:")
            print("  python run_system.py")
            print("\nOr run individual components:")
            print("  python api/main.py          # Start API server")
            print("  python install_and_run.py   # Full installation")
        else:
            print(f"\n❌ Found {len(self.errors)} CRITICAL ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print("\n" + "="*60)
        
        # Save detailed report
        report_path = Path("system_check_report.json")
        import json
        with open(report_path, "w") as f:
            json.dump({
                "timestamp": str(asyncio.get_event_loop().time()),
                "results": self.results,
                "errors": self.errors,
                "warnings": self.warnings,
                "ready": len(self.errors) == 0
            }, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_path}")


async def main():
    print("🚀 Root-MAS System Health Check")
    print("="*60)
    
    checker = SystemChecker()
    
    # Run all checks
    checker.check_dependencies()
    checker.check_modules()
    checker.check_config_files()
    checker.check_prompts()
    checker.check_environment()
    await checker.test_basic_functionality()
    
    # Generate report
    checker.generate_report()
    
    # Return exit code based on errors
    sys.exit(0 if not checker.errors else 1)


if __name__ == "__main__":
    asyncio.run(main())