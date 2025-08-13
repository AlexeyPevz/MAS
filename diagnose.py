#!/usr/bin/env python3
"""Диагностика проблем с запуском"""

import sys
import importlib.util
import traceback

def test_import(module_name):
    """Безопасно тестирует импорт модуля"""
    print(f"\nTesting import: {module_name}")
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"  ❌ Module not found: {module_name}")
            return False
            
        # Импортируем модуль
        module = importlib.import_module(module_name)
        print(f"  ✅ Successfully imported: {module_name}")
        
        # Проверяем наличие проблемных паттернов
        if hasattr(module, '__file__'):
            with open(module.__file__, 'r') as f:
                content = f.read()
                
            # Проверки
            issues = []
            
            # asyncio.run вне if __name__
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'asyncio.run(' in line and not any('if __name__' in lines[max(0, i-10):i] for i in range(i)):
                    issues.append(f"Line {i+1}: asyncio.run() outside if __name__")
                    
            # Код выполняющийся при импорте
            import_exec_patterns = [
                'print(',
                'logger.',
                '.initialize()',
                '.start()',
                '.run()'
            ]
            
            in_function = False
            indent_level = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Отслеживаем вхождение в функции/классы
                if stripped.startswith('def ') or stripped.startswith('class '):
                    in_function = True
                elif not line.startswith(' ') and not line.startswith('\t') and line.strip():
                    in_function = False
                    
                # Ищем проблемный код на верхнем уровне
                if not in_function and not stripped.startswith('#'):
                    for pattern in import_exec_patterns:
                        if pattern in stripped and 'if __name__' not in content[max(0, i-100):i]:
                            issues.append(f"Line {i+1}: Possible execution on import: {stripped[:50]}...")
                            
            if issues:
                print(f"  ⚠️  Found potential issues:")
                for issue in issues[:5]:  # Показываем первые 5
                    print(f"     - {issue}")
                    
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {type(e).__name__}: {str(e)[:100]}")
        if '--verbose' in sys.argv:
            traceback.print_exc()
        return False

def main():
    """Главная функция диагностики"""
    print("🔍 Root-MAS Import Diagnostics")
    print("=" * 50)
    
    # Критические модули для проверки
    modules_to_test = [
        # Базовые
        "fastapi",
        "pydantic",
        "redis",
        
        # Memory
        "memory.in_memory_store",
        "memory.redis_store",
        "memory.chroma_store",
        
        # Agents  
        "agents.base",
        "agents.core_agents",
        "agents.specialized_agents",
        "agents.lazy_loader",
        
        # Tools
        "tools.smart_groupchat",
        "tools.semantic_llm_cache",
        "tools.modern_telegram_bot",
        "tools.streaming_telegram_bot",
        "tools.teams_groupchat_manager",
        
        # API
        "api.main",
        "api.integration",
        "api.models",
        
        # Configs
        "config.config_loader",
    ]
    
    failed = []
    passed = []
    
    for module in modules_to_test:
        if test_import(module):
            passed.append(module)
        else:
            failed.append(module)
            
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"✅ Passed: {len(passed)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print(f"\n❌ Failed modules:")
        for module in failed:
            print(f"   - {module}")
            
    # Специальная проверка api.main
    if "api.main" in failed:
        print("\n⚠️  API module failed to import. This is critical!")
        print("Try running: python3 safe_start.py")
    
    return len(failed)

if __name__ == "__main__":
    sys.exit(main())