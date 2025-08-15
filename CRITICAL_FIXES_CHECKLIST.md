# ⚡ Чеклист критических исправлений Root-MAS

## 🔴 КРИТИЧЕСКИЕ БАГИ (сломан код - исправить СЕЙЧАС!)

### 1. Файл `api/security.py` (строка ~54)
```python
# ПРОБЛЕМА: Role используется до объявления
# БЫЛО:
class TokenData(BaseModel):
    role: str = Role.USER  # ❌ NameError!

# ИСПРАВИТЬ: Переместить Role ВЫШЕ TokenData
class Role:
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    READONLY = "readonly"

class TokenData(BaseModel):
    role: str = Role.USER  # ✅
```

### 2. Файл `api/main.py` (строки 35-41)
```python
# УДАЛИТЬ несуществующие импорты:
from tools.multitool import (
    list_instances,           # ❌ НЕ СУЩЕСТВУЕТ
    get_instance_versions,    # ❌ НЕ СУЩЕСТВУЕТ
    rollback_instance,        # ❌ НЕ СУЩЕСТВУЕТ
)
```

### 3. Файл `api/main.py` (строка ~489)
```python
# ПРОБЛЕМА: Вызов несуществующей функции
# БЫЛО:
chat_response = await send_message(chat_msg)  # ❌ Функция не определена

# ИСПРАВИТЬ НА:
response_text = await mas_integration.process_message(text, user_id)
chat_response = ChatResponse(
    response=response_text,
    timestamp=time.time(),
    agent="voice_assistant"
)
```

## 🔐 КРИТИЧЕСКИЕ УЯЗВИМОСТИ БЕЗОПАСНОСТИ

### 4. Удалить секретный ключ из Git
```bash
# В терминале выполнить:
git rm --cached .secret_key
echo ".secret_key" >> .gitignore
git commit -m "security: remove secret key from repository"
git push
```

### 5. Файл `api/main.py` (строки ~1140)
```python
# ПРОБЛЕМА: Открытая выдача токенов без проверки
# ИСПРАВИТЬ в функции issue_token:
if not expected:
    # БЫЛО: logger.warning + продолжение работы
    # СТАЛО:
    raise HTTPException(
        status_code=500, 
        detail="ADMIN_SECRET not configured"
    )
```

### 6. Файл `api/main.py` (строки 305-312)
```python
# ПРОБЛЕМА: CORS разрешает всё
# БЫЛО:
allow_origins=["*"],
allow_credentials=True,  # ❌ Нельзя с "*"

# ИСПРАВИТЬ:
allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
allow_credentials=False,
allow_methods=["GET", "POST"],
allow_headers=["Authorization", "Content-Type"],
```

### 7. Файл `api/main.py` (строка ~1261)
```python
# ПРОБЛЕМА: reload=True в production
# БЫЛО:
uvicorn.run("api.main:app", reload=True)

# ИСПРАВИТЬ:
if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development"
    )
```

## ✅ Проверочный чеклист

После исправлений убедитесь:
- [ ] API запускается без ошибок импорта
- [ ] `POST /api/v1/voice/chat` работает
- [ ] Токены НЕ выдаются без `X-Admin-Secret`
- [ ] CORS отклоняет запросы с неизвестных доменов
- [ ] `.secret_key` удален из Git истории

## 🚀 Команды для быстрой проверки

```bash
# Проверить импорты
python -c "from api import main"

# Запустить API
python api/main.py

# Тест voice endpoint
curl -X POST http://localhost:8000/api/v1/voice/chat \
  -F "audio_file=@test.wav" \
  -F "user_id=test"

# Тест безопасности токенов
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test"}' \
  # Должен вернуть 403 или 500
```

---
**Время на исправление: ~30 минут**