# Market Auto Parts - Инструкции по Deployment

## 📋 Обзор

Этот документ содержит инструкции по развертыванию приложения Market Auto Parts на чистом Ubuntu сервере.

## 🎯 Два способа установки

### Способ 1: Установка через Git Clone (Рекомендуется)

Этот способ клонирует весь репозиторий и гарантирует что все файлы будут на месте.

```bash
# Скачать скрипт установки
wget https://raw.githubusercontent.com/wrx861/market/main/deployment/install-with-git.sh

# Сделать исполняемым
chmod +x install-with-git.sh

# Запустить с правами root
sudo bash install-with-git.sh
```

### Способ 2: Установка через curl (Файл за файлом)

Этот способ скачивает каждый файл отдельно через curl.

```bash
# Скачать скрипт установки
wget https://raw.githubusercontent.com/wrx861/market/main/deployment/install-clean-server.sh

# Сделать исполняемым
chmod +x install-clean-server.sh

# Запустить с правами root
sudo bash install-clean-server.sh
```

## 📦 Что устанавливается

Скрипт автоматически установит:
- **Docker** и **Docker Compose**
- **Certbot** для SSL сертификатов
- **Git** (только для способа 1)
- Все необходимые зависимости

## 🔑 Необходимые API ключи

Скрипт запросит следующие данные:

### Telegram Bot
- `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
- `TELEGRAM_ADMIN_ID` - ваш Telegram user ID

### Google AI Studio (Gemini)
- `GOOGLE_API_KEY` - ключ от https://aistudio.google.com/

### Rossko API
- `ROSSKO_API_KEY1` - первый ключ API
- `ROSSKO_API_KEY2` - второй ключ API

### Autotrade API
- Логин (email)
- Пароль
- API ключ

### PartsAPI.ru
- `PARTSAPI_KEY` - ключ от https://partsapi.ru/

### OpenAI API
- `OPENAI_API_KEY` - ключ от https://platform.openai.com/

## 🏗️ Архитектура

Проект состоит из 4 Docker контейнеров:

1. **market-mongodb** - База данных MongoDB 7.0
2. **market-backend** - FastAPI приложение (Python 3.11)
3. **market-frontend** - React приложение (Node 20)
4. **market-nginx** - Reverse proxy с SSL

## 📁 Структура после установки

```
/opt/market-auto-parts/
├── backend/
│   ├── .env
│   ├── server.py
│   ├── models.py
│   ├── requirements.txt
│   ├── rossko_client.py
│   ├── autotrade_client.py
│   ├── partsapi_client.py
│   ├── openai_client.py
│   ├── gemini_client.py
│   ├── cache_manager.py
│   ├── rate_limiter.py       ← КРИТИЧЕСКИ ВАЖНЫЙ!
│   ├── proxy_manager.py      ← КРИТИЧЕСКИ ВАЖНЫЙ!
│   ├── n8n_client.py
│   └── ... другие файлы
├── frontend/
│   ├── .env
│   ├── package.json
│   ├── src/
│   └── public/
├── nginx/
│   └── nginx.conf
├── ssl/
│   ├── fullchain.pem
│   └── privkey.pem
├── mongodb/
│   └── data/
└── docker-compose.yml
```

## ⚠️ Критические файлы

Следующие файлы ОБЯЗАТЕЛЬНО должны присутствовать:

### Backend
- `rate_limiter.py` - управление rate limiting для API
- `proxy_manager.py` - управление прокси
- `cache_manager.py` - кэширование запросов
- `n8n_client.py` - уведомления через n8n

### Deployment
- `docker-compose.yml` - оркестрация контейнеров
- `backend.Dockerfile` - сборка backend
- `frontend.Dockerfile` - сборка frontend
- `nginx.conf` - конфигурация прокси

## 🚀 Команды управления

После установки:

```bash
cd /opt/market-auto-parts

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx

# Перезапуск сервисов
docker-compose restart backend
docker-compose restart frontend
docker-compose restart all

# Остановка
docker-compose down

# Запуск
docker-compose up -d

# Полная пересборка
docker-compose down
docker-compose up --build -d
```

## 🔍 Диагностика проблем

### Backend не запускается

```bash
# Проверить логи
docker-compose logs --tail=100 backend

# Проверить что все файлы на месте
ls -la backend/

# Проверить конкретно rate_limiter.py
ls -la backend/rate_limiter.py

# Войти в контейнер
docker exec -it market-backend bash
ls -la
```

### Frontend не собирается

```bash
# Проверить логи сборки
docker-compose logs --tail=100 frontend

# Проверить что все файлы на месте
ls -la frontend/src/pages/
```

### SSL проблемы

```bash
# Проверить сертификаты
ls -la ssl/

# Обновить сертификаты вручную
sudo certbot renew
sudo cp /etc/letsencrypt/live/miniapp.shopmarketbot.ru/*.pem /opt/market-auto-parts/ssl/
docker-compose restart nginx
```

## 🧪 Проверка перед deployment

Перед развертыванием на сервере можно проверить целостность проекта:

```bash
cd /app
./deployment/check-completeness.sh
```

Этот скрипт проверит:
- ✅ Наличие всех backend файлов
- ✅ Наличие всех deployment файлов
- ✅ Наличие frontend конфигурации
- ✅ Python импорты и зависимости

## 📊 Порты

- **80** - HTTP (редирект на HTTPS)
- **443** - HTTPS (Nginx)
- **8001** - Backend API (внутренний)
- **3001** - Frontend (внутренний)
- **27017** - MongoDB (внутренний)

## 🔒 Безопасность

- SSL сертификаты устанавливаются автоматически через Let's Encrypt
- Автоматическое обновление сертификатов настроено через cron
- Все credentials хранятся в `.env` файлах
- Порты 8001, 3001, 27017 доступны только внутри Docker сети

## 🆘 Частые проблемы

### Проблема: ModuleNotFoundError: No module named 'rate_limiter'

**Причина:** Файл `rate_limiter.py` не был скачан на сервер

**Решение:**
```bash
cd /opt/market-auto-parts/backend
curl -fsSL https://raw.githubusercontent.com/wrx861/market/main/backend/rate_limiter.py -o rate_limiter.py
docker-compose restart backend
```

### Проблема: Frontend показывает белый экран

**Причина:** Не все файлы frontend скопированы

**Решение:** Используйте способ установки через Git Clone

### Проблема: Порт уже занят

**Решение:**
```bash
# Проверить что занимает порт
sudo ss -tulpn | grep :8001
sudo ss -tulpn | grep :3001

# Остановить конфликтующий сервис
docker-compose down
```

## 📞 Поддержка

При проблемах с deployment:
1. Проверьте логи: `docker-compose logs --tail=100`
2. Проверьте что все файлы на месте
3. Используйте скрипт `check-completeness.sh`
4. Попробуйте альтернативный способ установки

## 🎉 Успешная установка

После успешной установки приложение будет доступно по адресу:
```
https://miniapp.shopmarketbot.ru
```

Все 4 контейнера должны иметь статус "Up":
```
docker-compose ps
```

Ожидаемый вывод:
```
NAME               IMAGE                 STATUS
market-backend     market-backend:latest Up X minutes
market-frontend    market-frontend:latest Up X minutes
market-mongodb     mongo:7.0             Up X minutes
market-nginx       nginx:alpine          Up X minutes
```
