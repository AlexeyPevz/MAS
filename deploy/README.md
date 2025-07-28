# Root-MAS Deployment Guide

Это руководство поможет вам развернуть проект Root-MAS на вашем сервере.

## Быстрый старт

### 1. Подготовка локального окружения

Убедитесь, что у вас установлены:
- `ssh` клиент для подключения к серверу
- `rsync` для синхронизации файлов

### 2. Загрузка проекта на сервер

```bash
# Простая загрузка
./deploy/upload.sh root@your-server.com

# Загрузка с нестандартным портом SSH
./deploy/upload.sh -p 2222 root@your-server.com

# Загрузка с автоматическим развертыванием
./deploy/upload.sh -d root@your-server.com

# Загрузка с указанием приватного ключа
./deploy/upload.sh -i ~/.ssh/id_rsa ubuntu@your-server.com
```

### 3. Настройка окружения на сервере

После загрузки подключитесь к серверу и настройте переменные окружения:

```bash
ssh root@your-server.com
cd /opt/root-mas
cp .env.example .env
nano .env  # Заполните ваши API ключи и настройки
```

### 4. Развертывание

```bash
sudo ./deploy/deploy.sh deploy
```

## Подробное руководство

### Требования к серверу

- **ОС**: Ubuntu 20.04+ или CentOS 8+
- **RAM**: минимум 2GB, рекомендуется 4GB+
- **Диск**: минимум 10GB свободного места
- **Сеть**: открытые порты 80, 443, 8000, 9000, 9090
- **Права**: sudo доступ

### Переменные окружения

Обязательные переменные в `.env` файле:

```bash
# API ключи
OPENROUTER_API_KEY=your_api_key_here
YANDEX_API_KEY=your_yandex_key_here
YANDEX_FOLDER_ID=your_folder_id_here

# База данных (измените пароли!)
CLIENT_POSTGRES_PASSWORD=your_secure_password
```

### Команды управления

После развертывания доступны следующие команды:

```bash
# Проверка статуса
sudo ./deploy/deploy.sh status

# Просмотр логов
sudo ./deploy/deploy.sh logs

# Просмотр логов конкретного сервиса
sudo ./deploy/deploy.sh logs app

# Перезапуск
sudo ./deploy/deploy.sh restart

# Остановка
sudo ./deploy/deploy.sh stop

# Создание резервной копии
sudo ./deploy/deploy.sh backup
```

### Мониторинг

После развертывания доступны:

- **Prometheus**: `http://your-server:9090`
- **Метрики приложения**: `http://your-server:9000/metrics`
- **API приложения**: `http://your-server:8000` (в будущих версиях)

### Автоматический запуск

Скрипт автоматически создает systemd сервис для автозапуска при перезагрузке сервера:

```bash
# Проверка статуса сервиса
systemctl status root-mas

# Ручное управление
systemctl start root-mas
systemctl stop root-mas
systemctl restart root-mas
```

### Обновление проекта

Для обновления проекта:

```bash
# 1. Загрузите новую версию
./deploy/upload.sh root@your-server.com

# 2. На сервере выполните:
ssh root@your-server.com
cd /opt/root-mas
sudo ./deploy/deploy.sh backup  # Создать резервную копию
sudo ./deploy/deploy.sh deploy  # Развернуть обновление
```

### Резервное копирование

Автоматические резервные копии сохраняются в `/opt/backups/root-mas/`

Ручное создание резервной копии:
```bash
sudo ./deploy/deploy.sh backup
```

### Настройка firewall

Если используется UFW:

```bash
# Разрешить SSH
ufw allow ssh

# Разрешить HTTP/HTTPS
ufw allow 80
ufw allow 443

# Разрешить порты приложения
ufw allow 8000
ufw allow 9000
ufw allow 9090

# Включить firewall
ufw enable
```

### Логи и отладка

Логи развертывания: `/var/log/root-mas_deploy.log`

Логи приложения:
```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs

# Логи конкретного сервиса
docker-compose -f docker-compose.prod.yml logs app
docker-compose -f docker-compose.prod.yml logs postgres
docker-compose -f docker-compose.prod.yml logs redis
```

### Решение проблем

#### Проблема: Контейнеры не запускаются

1. Проверьте логи:
   ```bash
   sudo ./deploy/deploy.sh logs
   ```

2. Проверьте ресурсы:
   ```bash
   df -h  # Место на диске
   free -h  # Оперативная память
   ```

3. Проверьте Docker:
   ```bash
   docker system df
   docker system prune  # Очистка (осторожно!)
   ```

#### Проблема: Ошибки подключения к базе данных

1. Проверьте, что PostgreSQL запущен:
   ```bash
   docker-compose -f docker-compose.prod.yml ps postgres
   ```

2. Проверьте настройки в `.env` файле

3. Перезапустите сервисы:
   ```bash
   sudo ./deploy/deploy.sh restart
   ```

#### Проблема: Нет доступа к метрикам

1. Проверьте, что порт 9000 открыт:
   ```bash
   netstat -tulpn | grep 9000
   ```

2. Проверьте firewall настройки

3. Проверьте логи приложения

### Безопасность

1. **Измените пароли по умолчанию** в `.env` файле
2. **Настройте SSH ключи** вместо паролей
3. **Ограничьте доступ** к портам через firewall
4. **Регулярно обновляйте** систему и Docker образы
5. **Мониторьте логи** на предмет подозрительной активности

### Производительность

Для оптимизации производительности:

1. **Увеличьте RAM** если видите ошибки OutOfMemory
2. **Используйте SSD** для базы данных
3. **Настройте Redis** для кэширования
4. **Мониторьте метрики** в Prometheus

## Получение помощи

При возникновении проблем:

1. Проверьте логи развертывания: `/var/log/root-mas_deploy.log`
2. Проверьте логи приложения: `sudo ./deploy/deploy.sh logs`
3. Проверьте статус системы: `sudo ./deploy/deploy.sh status`

Дополнительная информация в основном README.md проекта.