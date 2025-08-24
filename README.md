# SGR vs Function Calling: Практическое руководство

Этот репозиторий содержит комплексное сравнение подходов **Schema-Guided Reasoning (SGR)** и **Function Calling** в LLM-системах, основанное на современных трендах и практическом опыте.

## 📁 Структура проекта

### 📋 Основные файлы

- **`sgr_vs_tools_guide.md`** - Полное руководство по выбору между SGR и Function Calling
- **`production_guide.md`** - Критические рекомендации для production внедрения  
- **`demo_sgr_simple.py`** - Работающая демонстрация SGR (запускается без зависимостей)

### 🔧 Примеры реализации

- **`sgr_example.py`** - Подробный пример SGR с Pydantic схемами
- **`function_calling_example.py`** - Реализация агента с Function Calling
- **`hybrid_approach_example.py`** - Гибридный подход: SGR + Function Calling

## 🚀 Быстрый старт

Запустите демонстрацию SGR:

```bash
python3 demo_sgr_simple.py
```

Этот пример показывает:
- ✅ Структурированное рассуждение по шагам
- ✅ Полную трассировку решений
- ✅ Метрики качества (completeness, confidence)
- ✅ JSON-формат для мониторинга

## 🎯 Ключевые выводы

### Когда использовать SGR:

```python
# ✅ Идеально для production
{
  "reasoning": {
    "query_analysis": {...},      # Прозрачно
    "information_search": {...},  # Контролируемо  
    "quality_check": {...}        # Измеримо
  },
  "confidence_score": 0.85        # Мониторится
}
```

**Преимущества:**
- 🔍 Полная наблюдаемость процесса
- 📊 Простые метрики и мониторинг  
- 🐛 Легкая отладка
- ⚡ Работает на локальных моделях (Qwen 3 4B)

### Когда использовать Function Calling:

```python
# ⚠️ Сложнее в production
agent.tools = [web_search, database, email]
result = agent.process(query)  # Непредсказуемая цепочка
```

**Преимущества:**
- 🤖 Настоящее агентское поведение
- 🔗 Нативная интеграция с внешними системами
- 🔄 Динамическая адаптация

**Недостатки:**
- 🔍 Сложный мониторинг
- 🐛 Трудная отладка ("черный ящик")
- 📈 Непредсказуемые цепочки вызовов

## 💡 Практические рекомендации

### 🎯 Для начинающих проектов:
```
Старт → SGR-only → Добавление Tools → Гибридный подход
```

### 🏢 Для enterprise:
```python
class ProductionStrategy:
    def choose_approach(self, requirements):
        if requirements.need_control:
            return "SGR"
        elif requirements.need_external_apis:
            return "Controlled Hybrid"  
        else:
            return "SGR with monitoring"
```

### 🔥 Золотое правило production:

> **В production качество мониторинга = выживание продукта**

## 📊 Сравнительная таблица

| Критерий | SGR | Function Calling |
|----------|-----|-----------------|
| **Мониторинг** | ✅ Простой | ❌ Сложный |
| **Отладка** | ✅ Прозрачная | ❌ "Черный ящик" |
| **Агентность** | ❌ Ограниченная | ✅ Полная |
| **Production готовность** | ✅ Высокая | ⚠️ Требует осторожности |

## 🛠️ Установка зависимостей

Для полных примеров с Pydantic:

```bash
# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости  
pip install pydantic requests
```

## 📈 Современные тренды

### MCP + Structured Output + SGR
- **MCP** (Anthropic) стандартизирует инструменты
- **Structured Output** обеспечивает надежность
- **SGR** добавляет контроль качества

### Сдвиг к гибридным решениям:
```
Агент = Tool Calling + Structured Output + SGR
```

## 🎓 Изучите примеры

1. **`demo_sgr_simple.py`** - Базовое понимание SGR
2. **`sgr_example.py`** - Продвинутые схемы 
3. **`function_calling_example.py`** - Агентское поведение
4. **`hybrid_approach_example.py`** - Лучшее из двух миров

## 🤝 Благодарности

Респект **Ринату Абдуллину** за систематизацию Schema-Guided Reasoning подхода!

## 📝 Лицензия

MIT License - используйте в своих проектах!

---

**SGR** - это про контролируемое качество и прозрачность.  
**Function Calling** - это про истинную агентность и гибкость.  
**Гибридный подход** дает лучшее из двух миров.

Выбор зависит от ваших приоритетов: **контроль vs агентность**.