"""
Modern Telegram Bot Integration
Современная интеграция Telegram бота с MAS системой
"""
import asyncio
import os
import logging
from typing import Callable, Optional, Any, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

# Telegram imports с обработкой ошибок
try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    # Заглушки для случая отсутствия telegram
    class Update:
        pass
    class ContextTypes:
        DEFAULT_TYPE = Any


class ModernTelegramBot:
    """Современный Telegram бот для интеграции с MAS"""
    
    def __init__(
        self, 
        token: str, 
        mas_callback: Callable[[str], str],
        enable_voice: bool = False
    ):
        if not TELEGRAM_AVAILABLE:
            raise RuntimeError(
                "❌ python-telegram-bot не установлен. Установите: pip install python-telegram-bot>=20.0"
            )
        
        self.token = token
        self.mas_callback = mas_callback
        self.enable_voice = enable_voice
        self.logger = logging.getLogger(__name__)
        
        # Загружаем таймзону из конфигурации
        try:
            from config.config_loader import load_config
            config = load_config()
            proactive_config = config.get('proactive_mode', {})
            personalization = proactive_config.get('personalization', {})
            tz_str = personalization.get('timezone', 'UTC')
            
            # Преобразуем UTC+3 в Europe/Moscow или подобное
            if tz_str == 'UTC+3':
                self.timezone = ZoneInfo('Europe/Moscow')
            elif tz_str.startswith('UTC'):
                # Для других UTC смещений используем UTC по умолчанию
                self.timezone = ZoneInfo('UTC')
            else:
                self.timezone = ZoneInfo(tz_str)
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось загрузить таймзону: {e}, используем UTC")
            self.timezone = ZoneInfo('UTC')
        
        # Создаем Application
        self.application = Application.builder().token(token).build()
        
        # Статистика
        self.stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "errors": 0,
            "start_time": datetime.now(self.timezone)
        }
        
        # Настраиваем обработчики
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Текстовые сообщения
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
        )
        
        # Голосовые сообщения (если включены)
        if self.enable_voice:
            self.application.add_handler(
                MessageHandler(filters.VOICE, self.handle_voice)
            )
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        welcome_message = """
🤖 Добро пожаловать в MAS System!

Я — интеллектуальный бот с многоагентной системой под капотом.

Доступные команды:
• /help — справка
• /status — статус системы

Просто напишите мне любое сообщение, и я обработаю его через 12 специализированных агентов!
        """
        
        await update.message.reply_text(welcome_message.strip())
        self.stats["messages_sent"] += 1
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_message = """
📖 Справка по MAS System Bot

🎯 Возможности:
• Обработка текстовых сообщений через многоагентную систему
• Интеллектуальная маршрутизация между специализированными агентами
• Планирование и выполнение сложных задач

🤖 Агенты системы:
• Meta — координация и планирование
• Researcher — поиск информации
• Fact-Checker — проверка фактов
• Coordination — управление задачами
• И еще 8 специализированных агентов!

💬 Примеры запросов:
• "Создай план проекта по разработке мобильного приложения"
• "Найди информацию о последних трендах в ИИ"
• "Помоги написать техническое задание"

📊 Команды:
• /start — начало работы
• /status — статус системы
• /help — эта справка
        """
        
        await update.message.reply_text(help_message.strip())
        self.stats["messages_sent"] += 1
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /status"""
        uptime = datetime.now(self.timezone) - self.stats["start_time"]
        
        status_message = f"""
📊 Статус MAS System

⏰ Время работы: {uptime}
📨 Сообщений получено: {self.stats['messages_received']}
📤 Сообщений отправлено: {self.stats['messages_sent']}
❌ Ошибок: {self.stats['errors']}

🤖 Система: Активна
🔗 Агенты: 12 активных
🧠 LLM: OpenRouter интеграция
        """
        
        await update.message.reply_text(status_message.strip())
        self.stats["messages_sent"] += 1
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        if not update.message or not update.message.text:
            return
        
        user_text = update.message.text
        user_id = update.effective_user.id
        
        self.logger.info(f"📨 Получено сообщение от {user_id}: {user_text[:100]}...")
        self.stats["messages_received"] += 1
        
        try:
            # Показываем что бот печатает
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, 
                action="typing"
            )
            
            # Обрабатываем через MAS
            response = await self._process_with_mas(user_text, str(user_id))
            
            # Отправляем ответ
            if response:
                # Разбиваем длинные сообщения
                if len(response) > 4096:
                    chunks = [response[i:i+4096] for i in range(0, len(response), 4096)]
                    for chunk in chunks:
                        await update.message.reply_text(chunk)
                        self.stats["messages_sent"] += 1
                else:
                    await update.message.reply_text(response)
                    self.stats["messages_sent"] += 1
            else:
                await update.message.reply_text("🤔 Получен пустой ответ от системы")
                self.stats["messages_sent"] += 1
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки сообщения: {e}")
            self.stats["errors"] += 1
            
            await update.message.reply_text(
                f"😔 Произошла ошибка при обработке сообщения:\n{str(e)[:200]}..."
            )
            self.stats["messages_sent"] += 1
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка голосовых сообщений"""
        await update.message.reply_text(
            "🎤 Голосовые сообщения будут поддержаны в следующей версии.\n"
            "Пока пишите текстом! 😊"
        )
        self.stats["messages_sent"] += 1
    
    async def _process_with_mas(self, message: str, user_id: str) -> str:
        """Обработка сообщения через MAS систему"""
        try:
            # Если callback асинхронный
            if asyncio.iscoroutinefunction(self.mas_callback):
                response = await self.mas_callback(message)
            else:
                # Если callback синхронный - выполняем в executor с правильным event loop
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None, self.mas_callback, message
                )
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка MAS callback: {e}")
            return f"🛠️ Системная ошибка: {str(e)}"
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        self.logger.error(f"❌ Telegram bot error: {context.error}")
        self.stats["errors"] += 1
    
    async def send_message(self, chat_id: int, text: str):
        """Отправка сообщения (для callbacks)"""
        try:
            await self.application.bot.send_message(chat_id=chat_id, text=text)
            self.stats["messages_sent"] += 1
        except Exception as e:
            self.logger.error(f"❌ Ошибка отправки сообщения: {e}")
            self.stats["errors"] += 1
    
    async def run(self):
        """Запуск бота"""
        self.logger.info("🚀 Запуск Telegram бота...")
        
        try:
            # Инициализация
            await self.application.initialize()
            await self.application.start()
            
            # Запуск polling
            await self.application.updater.start_polling()
            
            self.logger.info("✅ Telegram бот запущен и готов к работе!")
            
            # Ожидание остановки
            await self.application.updater.idle()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска бота: {e}")
            raise
        finally:
            # Graceful shutdown
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful остановка бота"""
        try:
            self.logger.info("🛑 Останавливаем Telegram бота...")
            
            if hasattr(self.application, 'updater') and self.application.updater.running:
                await self.application.updater.stop()
            
            if hasattr(self.application, 'stop'):
                await self.application.stop()
                
            if hasattr(self.application, 'shutdown'):
                await self.application.shutdown()
                
            self.logger.info("✅ Telegram бот остановлен")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка остановки бота: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики бота"""
        return {
            **self.stats,
            "uptime": str(datetime.now(self.timezone) - self.stats["start_time"])
        }


# Функция для интеграции с существующей системой
async def start_telegram_integration(token: str, mas_callback: Callable[[str], str]) -> ModernTelegramBot:
    """Запуск Telegram интеграции"""
    if not TELEGRAM_AVAILABLE:
        raise RuntimeError("❌ python-telegram-bot не доступен")
    
    bot = ModernTelegramBot(token, mas_callback, enable_voice=False)
    
    # Запускаем в фоне
    asyncio.create_task(bot.run())
    
    return bot


if __name__ == "__main__":
    # Тестирование бота
    async def test_callback(message: str) -> str:
        return f"[TEST] Получено: {message}"
    
    async def main():
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("❌ TELEGRAM_BOT_TOKEN не установлен")
            return
        
        bot = ModernTelegramBot(token, test_callback)
        await bot.run()
    
    asyncio.run(main())