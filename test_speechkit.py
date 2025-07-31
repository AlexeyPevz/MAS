#!/usr/bin/env python3
"""
Тест Yandex SpeechKit
Проверка настройки без внешних зависимостей
"""

import os
import sys


def check_environment():
    """Проверка переменных окружения"""
    print("🔧 Проверка настроек Yandex SpeechKit")
    print("=" * 50)
    
    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')
    
    print(f"🔑 YANDEX_API_KEY: {'✅ Установлен' if api_key else '❌ Не установлен'}")
    print(f"📁 YANDEX_FOLDER_ID: {'✅ Установлен' if folder_id else '❌ Не установлен'}")
    
    if api_key:
        print(f"   Key начинается с: {api_key[:10]}...")
    
    if folder_id:
        print(f"   Folder ID: {folder_id}")
    
    if api_key and folder_id:
        print("\n✅ SpeechKit настроен правильно!")
        print("🎤 Голосовые функции будут работать")
        return True
    else:
        print("\n❌ SpeechKit не настроен")
        print("📝 Для настройки выполните:")
        if not api_key:
            print("   export YANDEX_API_KEY='your-api-key'")
        if not folder_id:
            print("   export YANDEX_FOLDER_ID='your-folder-id'")
        
        print("\n📚 Где взять:")
        print("1. Зайдите в Yandex Cloud Console")
        print("2. API Key: в разделе 'Сервисные аккаунты' → 'API-ключи'")
        print("3. Folder ID: в URL консоли или в свойствах проекта")
        return False


def check_api_access():
    """Проверка доступа к API (без aiohttp)"""
    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')
    
    if not api_key or not folder_id:
        return False
    
    try:
        import urllib.request
        import json
        
        # Тестовый запрос к TTS API
        url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
        
        data = {
            'text': 'Тест',
            'lang': 'ru-RU',
            'voice': 'alena',
            'format': 'oggopus',
            'folderId': folder_id
        }
        
        # Кодируем данные
        data_encoded = '&'.join([f"{k}={v}" for k, v in data.items()]).encode('utf-8')
        
        # Создаем запрос
        request = urllib.request.Request(
            url,
            data=data_encoded,
            headers={
                'Authorization': f'Api-Key {api_key}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        
        # Отправляем запрос
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status == 200:
                print("✅ SpeechKit API отвечает")
                print("🎤 Голосовые функции работают!")
                return True
            else:
                print(f"❌ Ошибка API: {response.status}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        print("🔧 Проверьте:")
        print("  - Правильность API ключа")
        print("  - Правильность Folder ID") 
        print("  - Подключение к интернету")
        print("  - Включен ли SpeechKit в Yandex Cloud")
        return False


def main():
    """Главная функция"""
    print("🧪 ТЕСТ YANDEX SPEECHKIT")
    print("=" * 50)
    
    # Проверяем переменные окружения
    env_ok = check_environment()
    
    if env_ok:
        print(f"\n🌐 Проверка доступа к API...")
        api_ok = check_api_access()
        
        if api_ok:
            print(f"\n🎉 ВСЕ РАБОТАЕТ!")
            print(f"✅ SpeechKit полностью настроен")
            print(f"🎤 Голосовые функции доступны в PWA и Telegram боте")
        else:
            print(f"\n⚠️ Настройки есть, но API не отвечает")
            print(f"🔧 Проверьте настройки в Yandex Cloud")
    else:
        print(f"\n📝 Настройте переменные окружения для использования голоса")
    
    print(f"\n📊 Что означает 'если настроен':")
    print(f"  - Просто проверка наличия YANDEX_API_KEY и YANDEX_FOLDER_ID")
    print(f"  - Если есть - голос работает")
    print(f"  - Если нет - голос отключен, но текст работает")


if __name__ == "__main__":
    main()