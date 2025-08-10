# 🚀 Быстрый старт Root-MAS

Для запуска системы используйте один из следующих способов:

## Рекомендуемый способ:

```bash
chmod +x quickstart.sh
./quickstart.sh
```

## Подробная документация:

📖 **[Полное руководство по установке](docs/INSTALLATION.md)**

Включает:
- Все способы установки и запуска
- Детальную конфигурацию
- Решение типичных проблем
- Production deployment

## Минимальные шаги:

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройте API ключ:**
   ```bash
   cp .env.example .env
   # Добавьте OPENAI_API_KEY в .env
   ```

3. **Запустите API сервер:**
   ```bash
   python3 api/main.py
   ```

4. **Откройте в браузере:**
   - API документация: http://localhost:8000/docs
   - PWA интерфейс: http://localhost:8000/pwa

---

**Нужна помощь?** См. [документацию по установке](docs/INSTALLATION.md) или создайте [Issue](https://github.com/yourusername/root-mas/issues).
