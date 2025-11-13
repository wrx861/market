#!/bin/bash

# Установочный скрипт для Market Auto Parts Telegram Mini App
# Автоматическая установка на сервер с настройкой SSL

set -e

echo "================================================"
echo "  Market Auto Parts - Установка на сервер"
echo "================================================"
echo ""

# Цвета для вывода
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для логирования
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    log_error "Запустите скрипт с правами root: sudo bash install.sh"
    exit 1
fi

echo "📋 Сбор информации для установки..."
echo ""

# Запрос данных от пользователя
read -p "🌐 Введите домен для Mini App (например: shop.example.com): " MINI_APP_DOMAIN
read -p "🌐 Введите домен для Backend API (например: api.example.com): " BACKEND_DOMAIN

echo ""
log_info "Токены и ключи API"
read -p "🤖 Telegram Bot Token: " TELEGRAM_BOT_TOKEN
read -p "👤 Telegram Admin ID: " TELEGRAM_ADMIN_ID
read -p "🧠 Google AI API Key (Gemini): " GOOGLE_API_KEY
read -p "🔑 Rossko API KEY1: " ROSSKO_KEY1
read -p "🔑 Rossko API KEY2: " ROSSKO_KEY2

echo ""
log_info "Начинаем установку..."
echo ""

# Обновление системы
log_info "Обновление системы..."
apt-get update -qq
apt-get upgrade -y -qq

# Установка необходимых пакетов
log_info "Установка зависимостей..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    mongodb \
    nginx \
    certbot \
    python3-certbot-nginx \
    supervisor \
    git \
    curl \
    wget

# Установка Yarn
log_info "Установка Yarn..."
npm install -g yarn

# Создание директории приложения
APP_DIR="/opt/market-autoparts"
log_info "Создание директории приложения: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Клонирование репозитория (если указан) или копирование файлов
if [ -d "/app" ]; then
    log_info "Копирование файлов из /app..."
    cp -r /app/* $APP_DIR/
else
    log_error "Исходные файлы не найдены в /app"
    exit 1
fi

# Создание Python виртуального окружения
log_info "Создание Python виртуального окружения..."
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate

# Установка Python зависимостей
log_info "Установка Python зависимостей..."
cd $APP_DIR/backend
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Установка Playwright браузеров
log_info "Установка Playwright Chromium..."
playwright install chromium

# Установка Frontend зависимостей
log_info "Установка Frontend зависимостей..."
cd $APP_DIR/frontend
yarn install --silent

# Настройка MongoDB
log_info "Настройка MongoDB..."
systemctl enable mongodb
systemctl start mongodb

# Создание .env файлов
log_info "Создание конфигурационных файлов..."

# Backend .env
cat > $APP_DIR/backend/.env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=market_db
CORS_ORIGINS=*

# Telegram Bot
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_ID=$TELEGRAM_ADMIN_ID

# Google AI Studio
GOOGLE_API_KEY=$GOOGLE_API_KEY

# Rossko API
ROSSKO_API_KEY1=$ROSSKO_KEY1
ROSSKO_API_KEY2=$ROSSKO_KEY2
ROSSKO_API_URL=http://api.rossko.ru/index.php

# Web App URL
REACT_APP_WEBAPP_URL=https://$MINI_APP_DOMAIN
EOF

# Frontend .env
cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$BACKEND_DOMAIN
WDS_SOCKET_PORT=443
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF

# Build Frontend
log_info "Сборка Frontend..."
cd $APP_DIR/frontend
yarn build

# Настройка Nginx
log_info "Настройка Nginx..."

# Конфигурация для Mini App
cat > /etc/nginx/sites-available/$MINI_APP_DOMAIN << EOF
server {
    listen 80;
    server_name $MINI_APP_DOMAIN;
    
    root $APP_DIR/frontend/build;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Конфигурация для Backend API
cat > /etc/nginx/sites-available/$BACKEND_DOMAIN << EOF
server {
    listen 80;
    server_name $BACKEND_DOMAIN;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Активация конфигураций
ln -sf /etc/nginx/sites-available/$MINI_APP_DOMAIN /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/$BACKEND_DOMAIN /etc/nginx/sites-enabled/

# Удаление default конфига
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
nginx -t

# Перезапуск Nginx
systemctl restart nginx

# Установка SSL сертификатов
log_info "Установка SSL сертификатов..."
certbot --nginx -d $MINI_APP_DOMAIN -d $BACKEND_DOMAIN --non-interactive --agree-tos --email admin@$MINI_APP_DOMAIN --redirect

# Настройка Supervisor
log_info "Настройка Supervisor..."

# Backend supervisor config
cat > /etc/supervisor/conf.d/market-backend.conf << EOF
[program:market-backend]
command=$APP_DIR/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
directory=$APP_DIR/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/market-backend.err.log
stdout_logfile=/var/log/market-backend.out.log
user=root
environment=PATH="$APP_DIR/venv/bin"
EOF

# Telegram Bot supervisor config
cat > /etc/supervisor/conf.d/market-telegram-bot.conf << EOF
[program:market-telegram-bot]
command=$APP_DIR/venv/bin/python telegram_bot.py
directory=$APP_DIR/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/market-telegram-bot.err.log
stdout_logfile=/var/log/market-telegram-bot.out.log
user=root
environment=PATH="$APP_DIR/venv/bin"
EOF

# Обновление supervisor
supervisorctl reread
supervisorctl update
supervisorctl start all

# Настройка автообновления SSL
log_info "Настройка автообновления SSL сертификатов..."
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet") | crontab -

# Настройка файрвола (если ufw установлен)
if command -v ufw &> /dev/null; then
    log_info "Настройка файрвола..."
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 22/tcp
    ufw --force enable
fi

# Проверка статуса сервисов
log_info "Проверка статуса сервисов..."
sleep 3
systemctl status nginx --no-pager
supervisorctl status

echo ""
echo "================================================"
log_info "✅ Установка завершена успешно!"
echo "================================================"
echo ""
echo "📱 Mini App URL: https://$MINI_APP_DOMAIN"
echo "🔧 Backend API: https://$BACKEND_DOMAIN"
echo ""
echo "🤖 Настройка Telegram бота:"
echo "   1. Откройте @BotFather"
echo "   2. /mybots → [ваш бот] → Bot Settings → Menu Button"
echo "   3. URL: https://$MINI_APP_DOMAIN"
echo ""
echo "📊 Управление сервисами:"
echo "   sudo supervisorctl status           - Статус"
echo "   sudo supervisorctl restart all      - Перезапуск всех"
echo "   sudo supervisorctl restart market-backend  - Перезапуск backend"
echo ""
echo "📝 Логи:"
echo "   Backend: tail -f /var/log/market-backend.out.log"
echo "   Bot: tail -f /var/log/market-telegram-bot.out.log"
echo "   Nginx: tail -f /var/log/nginx/error.log"
echo ""
log_info "Готово к использованию! 🚀"
