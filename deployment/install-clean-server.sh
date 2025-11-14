#!/bin/bash

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Конфигурация
DOMAIN="miniapp.shopmarketbot.ru"
APP_DIR="/opt/market-auto-parts"
BACKEND_PORT="8001"
FRONTEND_PORT="3001"
MONGO_PORT="27017"

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Market Auto Parts - Установка на сервер${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Функция для проверки root прав
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}✗ Пожалуйста, запустите скрипт с правами root (sudo)${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Права root подтверждены${NC}"
}

# Проверка занятых портов
check_ports() {
    echo -e "${YELLOW}Проверка портов...${NC}"
    
    for port in $BACKEND_PORT $FRONTEND_PORT $MONGO_PORT; do
        if ss -tulpn | grep -q ":$port "; then
            echo -e "${RED}✗ Порт $port уже занят!${NC}"
            ss -tulpn | grep ":$port "
            exit 1
        fi
    done
    
    echo -e "${GREEN}✓ Порты $BACKEND_PORT, $FRONTEND_PORT, $MONGO_PORT свободны${NC}"
}

# Исправление DNS
fix_dns() {
    echo -e "${YELLOW}Настройка DNS...${NC}"
    
    # Добавляем Google DNS
    if ! grep -q "8.8.8.8" /etc/resolv.conf; then
        cp /etc/resolv.conf /etc/resolv.conf.backup 2>/dev/null || true
        echo "nameserver 8.8.8.8" | cat - /etc/resolv.conf > /tmp/resolv.conf.tmp
        echo "nameserver 8.8.4.4" >> /tmp/resolv.conf.tmp
        echo "nameserver 1.1.1.1" >> /tmp/resolv.conf.tmp
        cat /etc/resolv.conf >> /tmp/resolv.conf.tmp
        mv /tmp/resolv.conf.tmp /etc/resolv.conf
    fi
    
    # Настраиваем DNS для Docker
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json <<EOF
{
  "dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"]
}
EOF
    
    echo -e "${GREEN}✓ DNS настроен${NC}"
}

# Установка зависимостей
install_dependencies() {
    echo -e "${YELLOW}Установка зависимостей...${NC}"
    
    apt-get update -qq
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Установка Docker...${NC}"
        curl -fsSL https://get.docker.com | bash
        systemctl enable docker
        systemctl start docker
        
        # Перезапускаем с DNS настройками
        systemctl restart docker
        sleep 3
    fi
    echo -e "${GREEN}✓ Docker установлен${NC}"
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}Установка Docker Compose...${NC}"
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    echo -e "${GREEN}✓ Docker Compose установлен${NC}"
    
    if ! command -v certbot &> /dev/null; then
        echo -e "${YELLOW}Установка certbot...${NC}"
        apt-get install -y certbot
    fi
    echo -e "${GREEN}✓ Certbot установлен${NC}"
}

# Создание директорий
create_directories() {
    echo -e "${YELLOW}Создание директорий...${NC}"
    
    mkdir -p $APP_DIR
    mkdir -p $APP_DIR/backend
    mkdir -p $APP_DIR/frontend
    mkdir -p $APP_DIR/nginx
    mkdir -p $APP_DIR/ssl
    mkdir -p $APP_DIR/mongodb/data
    
    echo -e "${GREEN}✓ Директории созданы${NC}"
}

# Интерактивный ввод credentials
input_credentials() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}    Ввод API ключей и учетных данных${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Перенаправляем stdin на /dev/tty для интерактивного ввода
    exec < /dev/tty
    
    echo -e "${YELLOW}Telegram Bot${NC}"
    read -p "Введите TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
    read -p "Введите TELEGRAM_ADMIN_ID: " TELEGRAM_ADMIN_ID
    echo ""
    
    echo -e "${YELLOW}Google AI Studio (Gemini)${NC}"
    read -p "Введите GOOGLE_API_KEY: " GOOGLE_API_KEY
    echo ""
    
    echo -e "${YELLOW}Rossko API (поставщик запчастей)${NC}"
    read -p "Введите ROSSKO_API_KEY1: " ROSSKO_API_KEY1
    read -p "Введите ROSSKO_API_KEY2: " ROSSKO_API_KEY2
    echo ""
    
    echo -e "${YELLOW}Autotrade API (поставщик запчастей)${NC}"
    read -p "Введите логин (email): " AUTOTRADE_LOGIN
    read -sp "Введите пароль: " AUTOTRADE_PASSWORD
    echo ""
    read -p "Введите API ключ: " AUTOTRADE_API_KEY
    echo ""
    
    echo -e "${YELLOW}Berg API (поставщик запчастей)${NC}"
    read -p "Введите BERG_API_KEY: " BERG_API_KEY
    echo ""
    
    echo -e "${YELLOW}PartsAPI.ru (поиск по VIN)${NC}"
    read -p "Введите PARTSAPI_KEY: " PARTSAPI_KEY
    echo ""
    
    echo -e "${YELLOW}OpenAI API (AI диагностика)${NC}"
    read -sp "Введите OpenAI API ключ: " OPENAI_API_KEY
    echo ""
    echo ""
    
    echo -e "${GREEN}✓ Все данные получены${NC}"
}

# Создание .env файлов
create_env_files() {
    echo -e "${YELLOW}Создание .env файлов...${NC}"
    
    cat > $APP_DIR/backend/.env << EOF
MONGO_URL=mongodb://mongodb:27017
DB_NAME=market_db
CORS_ORIGINS=*

TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_ADMIN_ID=${TELEGRAM_ADMIN_ID}

GOOGLE_API_KEY=${GOOGLE_API_KEY}

ROSSKO_API_KEY1=${ROSSKO_API_KEY1}
ROSSKO_API_KEY2=${ROSSKO_API_KEY2}
ROSSKO_API_URL=http://api.rossko.ru/service/v2.1/GetSearch

AUTOTRADE_LOGIN=${AUTOTRADE_LOGIN}
AUTOTRADE_PASSWORD=${AUTOTRADE_PASSWORD}
AUTOTRADE_API_KEY=${AUTOTRADE_API_KEY}

BERG_API_KEY=${BERG_API_KEY}

PARTSAPI_KEY=${PARTSAPI_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}

REACT_APP_WEBAPP_URL=https://$DOMAIN
PLAYWRIGHT_BROWSERS_PATH=/pw-browsers
EOF

    cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

    echo -e "${GREEN}✓ .env файлы созданы${NC}"
}

# Скачивание файлов проекта с GitHub
download_project() {
    echo -e "${YELLOW}Скачивание файлов проекта с GitHub...${NC}"
    
    cd $APP_DIR
    
    # Скачивание deployment файлов
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/deployment/docker-compose.yml -o docker-compose.yml
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/deployment/backend.Dockerfile -o backend/Dockerfile
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/deployment/frontend.Dockerfile -o frontend/Dockerfile
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/deployment/nginx.conf -o nginx/nginx.conf
    
    # Скачивание backend кода
    echo -e "${YELLOW}Скачивание backend...${NC}"
    cd $APP_DIR/backend
    
    # Основные файлы backend
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/server.py -o server.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/models.py -o models.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/requirements.txt -o requirements.txt
    
    # Клиенты API поставщиков
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/rossko_client.py -o rossko_client.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/autotrade_client.py -o autotrade_client.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/autotrade_oem_parser.py -o autotrade_oem_parser.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/autostels_client.py -o autostels_client.py
    
    # Клиенты для VIN и AI
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/partsapi_client.py -o partsapi_client.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/openai_client.py -o openai_client.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/gemini_client.py -o gemini_client.py
    
    # Вспомогательные модули (КРИТИЧЕСКИ ВАЖНЫЕ!)
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/cache_manager.py -o cache_manager.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/rate_limiter.py -o rate_limiter.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/proxy_manager.py -o proxy_manager.py
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/n8n_client.py -o n8n_client.py
    
    # Парсеры (опциональные, но скачаем на всякий случай)
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/partkom_parser.py -o partkom_parser.py 2>/dev/null || true
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/rossko_parser.py -o rossko_parser.py 2>/dev/null || true
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/berg_parser.py -o berg_parser.py 2>/dev/null || true
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/backend/telegram_bot.py -o telegram_bot.py 2>/dev/null || true
    
    # Скачивание frontend кода
    echo -e "${YELLOW}Скачивание frontend...${NC}"
    cd $APP_DIR/frontend
    
    # Создание структуры папок
    mkdir -p src/pages src/components/ui src/hooks src/lib src/utils public
    
    # Конфигурационные файлы
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/package.json -o package.json
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/yarn.lock -o yarn.lock
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/craco.config.js -o craco.config.js
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/tailwind.config.js -o tailwind.config.js
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/postcss.config.js -o postcss.config.js
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/jsconfig.json -o jsconfig.json
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/components.json -o components.json
    
    # Основные файлы src
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/src/App.js -o src/App.js
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/src/App.css -o src/App.css
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/src/index.js -o src/index.js
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/src/index.css -o src/index.css
    
    # Pages
    for page in Home SearchArticle SearchVIN Garage AddVehicle VehicleDetail AddService ServiceLog AddLog BoardJournal AddReminder Reminders Expenses Diagnostics Cart Orders Admin; do
        curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/src/pages/${page}.js -o src/pages/${page}.js 2>/dev/null || true
    done
    
    # Utils и Hooks
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/src/utils/telegram.js -o src/utils/telegram.js
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/src/hooks/use-toast.js -o src/hooks/use-toast.js
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/src/lib/utils.js -o src/lib/utils.js
    
    # UI Components (shadcn/ui)
    for component in button card input label select badge avatar toast toaster tabs dialog alert separator; do
        curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/src/components/ui/${component}.jsx -o src/components/ui/${component}.jsx 2>/dev/null || true
    done
    
    # Public files
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/public/index.html -o public/index.html
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/public/manifest.json -o public/manifest.json 2>/dev/null || true
    curl -fsSL https://raw.githubusercontent.com/wrx861/market/clean-main/frontend/public/robots.txt -o public/robots.txt 2>/dev/null || true
    
    echo -e "${GREEN}✓ Файлы проекта скачаны${NC}"
}

# Установка SSL сертификата
install_ssl() {
    echo -e "${YELLOW}Установка SSL сертификата для $DOMAIN...${NC}"
    
    # Открытие порта 80 временно
    ufw allow 80 2>/dev/null || true
    
    # Остановка всех контейнеров которые могут занимать порт 80
    docker-compose -f $APP_DIR/docker-compose.yml down 2>/dev/null || true
    
    # Получение сертификата
    certbot certonly --standalone \
        --non-interactive \
        --agree-tos \
        --email admin@$DOMAIN \
        -d $DOMAIN \
        --preferred-challenges http
    
    # Копирование сертификатов
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $APP_DIR/ssl/
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $APP_DIR/ssl/
    
    # Закрытие порта 80
    ufw delete allow 80 2>/dev/null || true
    
    # Настройка автоматического обновления
    (crontab -l 2>/dev/null | grep -v "certbot renew"; echo "0 5 * * 0 ufw allow 80 && certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/*.pem $APP_DIR/ssl/ && docker-compose -f $APP_DIR/docker-compose.yml restart nginx && ufw delete allow 80") | crontab -
    
    echo -e "${GREEN}✓ SSL сертификат установлен${NC}"
}

# Запуск проекта
start_project() {
    echo -e "${YELLOW}Запуск проекта...${NC}"
    
    cd $APP_DIR
    docker-compose down 2>/dev/null || true
    docker-compose up --build -d
    
    echo -e "${GREEN}✓ Проект запущен${NC}"
}

# Проверка статуса
check_status() {
    echo ""
    echo -e "${YELLOW}Ожидание запуска сервисов (60 сек)...${NC}"
    sleep 60
    
    echo ""
    echo -e "${YELLOW}Статус контейнеров:${NC}"
    docker-compose -f $APP_DIR/docker-compose.yml ps
    
    echo ""
    echo -e "${YELLOW}Логи backend (последние 20 строк):${NC}"
    docker-compose -f $APP_DIR/docker-compose.yml logs --tail=20 backend
}

# Финальная информация
print_info() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}         Установка завершена успешно!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}📱 Приложение:${NC} https://$DOMAIN"
    echo -e "${YELLOW}📁 Директория:${NC} $APP_DIR"
    echo ""
    echo -e "${YELLOW}🔄 АВТООБНОВЛЕНИЕ С GITHUB:${NC}"
    echo -e "${GREEN}Сначала инициализируйте Git репозиторий:${NC}"
    echo ""
    echo "  cd $APP_DIR"
    echo "  git init"
    echo "  git remote add origin <URL-вашего-репозитория>"
    echo "  git add ."
    echo "  git commit -m 'Initial commit'"
    echo "  git push -u origin main"
    echo ""
    echo -e "${GREEN}Затем для обновлений используйте:${NC}"
    echo ""
    echo "  cd $APP_DIR"
    echo "  bash deployment/update.sh"
    echo ""
    echo -e "${GREEN}Скрипт автоматически:${NC}"
    echo "  • Получит последний код с GitHub"
    echo "  • Пересоберет Docker образы"
    echo "  • Перезапустит все сервисы"
    echo ""
    echo -e "${YELLOW}Команды управления:${NC}"
    echo "cd $APP_DIR"
    echo "bash deployment/update.sh            # обновление с GitHub"
    echo "docker-compose ps                    # статус"
    echo "docker-compose logs -f backend       # логи backend"
    echo "docker-compose logs -f frontend      # логи frontend"
    echo "docker-compose restart               # перезапуск"
    echo "docker-compose down                  # остановка"
    echo "docker-compose up -d                 # запуск"
    echo ""
}

# Основной процесс установки
main() {
    check_root
    check_ports
    fix_dns                    # Исправляем DNS перед установкой
    install_dependencies
    create_directories
    input_credentials
    create_env_files
    download_project
    install_ssl
    start_project
    check_status
    print_info
}

main
