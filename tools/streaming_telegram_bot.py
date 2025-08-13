"""
Streaming Telegram Bot
Расширение ModernTelegramBot с поддержкой потоковой отправки сообщений
"""
import asyncio
import logging
from typing import AsyncIterator, Optional, Callable, Any
from datetime import datetime
import time

from tools.modern_telegram_bot import ModernTelegramBot, TELEGRAM_AVAILABLE

if TELEGRAM_AVAILABLE:
    from telegram import Update
    from telegram.ext import ContextTypes
    from telegram.error import BadRequest, NetworkError


class StreamingTelegramBot(ModernTelegramBot):
    """Telegram бот с поддержкой streaming ответов"""
    
    def __init__(
        self,
        token: str,
        mas_callback: Callable[[str], str],
        enable_voice: bool = False,
        streaming_callback: Optional[Callable[[str, str], AsyncIterator[str]]] = None,
        streaming_delay: float = 0.5  # Задержка между обновлениями в секундах
    ):
        super().__init__(token, mas_callback, enable_voice)
        self.streaming_callback = streaming_callback
        self.streaming_delay = streaming_delay
        self.active_streams = {}  # chat_id -> message_id для активных стримов
        
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений с поддержкой streaming"""
        if not update.message or not update.message.text:
            return
        
        user_text = update.message.text
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        self.logger.info(f"📨 Получено сообщение от {user_id}: {user_text[:100]}...")
        self.stats["messages_received"] += 1
        
        try:
            # Если есть streaming callback - используем его
            if self.streaming_callback and asyncio.iscoroutinefunction(self.streaming_callback):
                await self._handle_streaming_response(
                    update, context, user_text, str(user_id)
                )
            else:
                # Иначе используем обычный обработчик
                await super().handle_text(update, context)
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки: {e}")
            await update.message.reply_text(
                "🛠️ Произошла ошибка при обработке вашего сообщения."
            )
            self.stats["errors"] += 1
    
    async def _handle_streaming_response(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_text: str,
        user_id: str
    ):
        """Обработка с потоковой отправкой ответа"""
        chat_id = update.effective_chat.id
        
        # Отправляем начальное сообщение
        sent_message = await update.message.reply_text("💭 Думаю...")
        message_id = sent_message.message_id
        
        # Сохраняем ID для возможности прерывания
        self.active_streams[chat_id] = message_id
        
        try:
            # Буфер для накопления текста
            buffer = ""
            last_update_time = time.time()
            update_counter = 0
            
            # Получаем поток ответов
            async for chunk in self.streaming_callback(user_text, user_id):
                # Проверяем, не прервал ли пользователь
                if chat_id not in self.active_streams or self.active_streams[chat_id] != message_id:
                    self.logger.info("Streaming прерван пользователем")
                    break
                
                buffer += chunk
                current_time = time.time()
                
                # Обновляем сообщение с определенной частотой
                if (current_time - last_update_time >= self.streaming_delay and 
                    len(buffer) > 10):  # Минимум 10 символов для обновления
                    
                    try:
                        # Добавляем курсор печати
                        display_text = buffer + "▌"
                        
                        # Ограничиваем длину сообщения
                        if len(display_text) > 4000:
                            display_text = display_text[:4000] + "...\n[Сообщение сокращено]▌"
                        
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=display_text
                        )
                        
                        last_update_time = current_time
                        update_counter += 1
                        
                        # Показываем индикатор набора каждые 5 обновлений
                        if update_counter % 5 == 0:
                            await context.bot.send_chat_action(
                                chat_id=chat_id,
                                action="typing"
                            )
                            
                    except BadRequest as e:
                        # Игнорируем ошибки если сообщение не изменилось
                        if "message is not modified" not in str(e):
                            self.logger.warning(f"Ошибка обновления сообщения: {e}")
                    except NetworkError:
                        # Пропускаем сетевые ошибки
                        pass
            
            # Финальное обновление без курсора
            if buffer:
                try:
                    # Разбиваем на части если слишком длинное
                    if len(buffer) > 4096:
                        # Обновляем первое сообщение
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=buffer[:4096]
                        )
                        
                        # Отправляем остальные части
                        for i in range(4096, len(buffer), 4096):
                            chunk = buffer[i:i+4096]
                            await update.message.reply_text(chunk)
                            self.stats["messages_sent"] += 1
                    else:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=buffer
                        )
                    
                    self.stats["messages_sent"] += 1
                    
                except Exception as e:
                    self.logger.error(f"Ошибка финального обновления: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка streaming: {e}")
            
            # Пытаемся обновить сообщение с ошибкой
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="🛠️ Произошла ошибка при генерации ответа."
                )
            except:
                pass
                
            self.stats["errors"] += 1
            
        finally:
            # Удаляем из активных стримов
            if chat_id in self.active_streams and self.active_streams[chat_id] == message_id:
                del self.active_streams[chat_id]
    
    async def handle_stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для остановки активного streaming"""
        chat_id = update.effective_chat.id
        
        if chat_id in self.active_streams:
            del self.active_streams[chat_id]
            await update.message.reply_text("⏹️ Генерация остановлена.")
        else:
            await update.message.reply_text("ℹ️ Нет активной генерации.")
    
    def setup_handlers(self):
        """Настройка обработчиков с дополнительными командами"""
        super().setup_handlers()
        
        # Добавляем команду остановки
        from telegram.ext import CommandHandler
        self.application.add_handler(
            CommandHandler("stop", self.handle_stop_command)
        )


# Вспомогательная функция для создания streaming callback из SmartGroupChatManager
def create_streaming_callback(groupchat_manager) -> Callable[[str, str], AsyncIterator[str]]:
    """Создает streaming callback для использования с SmartGroupChatManager"""
    
    async def streaming_callback(message: str, user_id: str) -> AsyncIterator[str]:
        """Генератор потокового ответа"""
        try:
            # Если у менеджера есть метод stream_response
            if hasattr(groupchat_manager, 'stream_response'):
                async for chunk in groupchat_manager.stream_response(message, user_id):
                    yield chunk
            else:
                # Fallback на обычный ответ, разбитый на части
                response = await groupchat_manager.process_message(message, user_id)
                
                # Имитируем streaming, разбивая по словам
                words = response.split()
                chunk = ""
                
                for i, word in enumerate(words):
                    chunk += word + " "
                    
                    # Отправляем каждые 5 слов или в конце
                    if (i + 1) % 5 == 0 or i == len(words) - 1:
                        yield chunk
                        chunk = ""
                        await asyncio.sleep(0.1)  # Небольшая задержка для эффекта
                        
        except Exception as e:
            yield f"\n\n❌ Ошибка: {str(e)}"


# Пример использования
if __name__ == "__main__":
    import os
    
    # Пример streaming callback
    async def example_streaming(message: str, user_id: str) -> AsyncIterator[str]:
        """Пример генератора streaming ответов"""
        response = f"Обрабатываю ваш запрос: '{message}'\n\n"
        
        # Имитируем постепенную генерацию
        parts = [
            "Анализирую запрос... ",
            "Подбираю информацию... ",
            "Формирую ответ... ",
            "\n\nВот мой ответ:\n",
            "Это пример потоковой генерации текста. ",
            "Каждая часть появляется постепенно, ",
            "создавая эффект 'печати' в реальном времени. ",
            "\n\nНадеюсь, это помогло! 😊"
        ]
        
        for part in parts:
            yield part
            await asyncio.sleep(0.5)
    
    async def main():
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("❌ TELEGRAM_BOT_TOKEN не установлен")
            return
        
        # Создаем бот с поддержкой streaming
        bot = StreamingTelegramBot(
            token=token,
            mas_callback=lambda msg: f"Обычный ответ на: {msg}",
            streaming_callback=example_streaming,
            streaming_delay=0.3  # Обновление каждые 0.3 секунды
        )
        
        await bot.run()
    
    asyncio.run(main())