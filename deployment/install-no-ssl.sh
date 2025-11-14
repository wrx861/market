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
GITHUB_BRANCH="main"

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Market Auto Parts - Установка БЕЗ SSL${NC}"
echo -e "${GREEN}    (для тестирования или отладки)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}⚠️  SSL будет отключен - используйте HTTP${NC}"
echo ""

# Функция для проверки root прав
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}✗ Пожалуйста, запустите скрипт с правами root (sudo)${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Права root подтверждены${NC}"
}

# Проверка DNS
check_dns() {
    echo -e "${YELLOW}Проверка DNS...${NC}"
    
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        echo -e "${RED}✗ Нет интернет подключения!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Интернет подключение работает${NC}"
    
    # Проверяем DNS резолвинг
    if ! nslookup google.com &> /dev/null; then
        echo -e "${YELLOW}⚠️  Проблемы с DNS, пытаюсь исправить...${NC}"
        
        # Добавляем Google DNS
        echo "nameserver 8.8.8.8" > /etc/resolv.conf
        echo "nameserver 8.8.4.4" >> /etc/resolv.conf
        
        if nslookup google.com &> /dev/null; then
            echo -e "${GREEN}✓ DNS исправлен${NC}"
        else
            echo -e "${RED}✗ Не удалось исправить DNS${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ DNS работает${NC}"
    fi
}

# Проверка занятых портов
check_ports() {
    echo -e "${YELLOW}Проверка портов...${NC}"
    
    for port in $BACKEND_PORT $FRONTEND_PORT $MONGO_PORT 80; do
        if ss -tulpn | grep -q ":$port "; then
            echo -e "${RED}✗ Порт $port уже занят!${NC}"
            ss -tulpn | grep ":$port "
            exit 1
        fi
    done
    
    echo -e "${GREEN}✓ Порты свободны${NC}"
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
    fi
    echo -e "${GREEN}✓ Docker установлен${NC}"
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}Установка Docker Compose...${NC}"
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    echo -e "${GREEN}✓ Docker Compose установлен${NC}"
    
    # Устанавливаем git и dnsutils
    apt-get install -y git dnsutils iputils-ping
    echo -e "${GREEN}✓ Утилиты установлены${NC}"
}

# Создание директорий
create_directories() {
    echo -e "${YELLOW}Создание директорий...${NC}"
    
    mkdir -p $APP_DIR
    mkdir -p $APP_DIR/mongodb/data
    mkdir -p $APP_DIR/nginx
    
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
    
    echo -e "${YELLOW}Google AI Studio (Gemini) - опционально${NC}"
    read -p "Введите GOOGLE_API_KEY (или Enter для пропуска): " GOOGLE_API_KEY
    GOOGLE_API_KEY=${GOOGLE_API_KEY:-""}
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
    
    echo -e "${YELLOW}PartsAPI.ru (поиск по VIN) - опционально${NC}"
    read -p "Введите PARTSAPI_KEY (или Enter для пропуска): " PARTSAPI_KEY
    PARTSAPI_KEY=${PARTSAPI_KEY:-""}
    echo ""
    
    echo -e "${YELLOW}OpenAI API (AI диагностика) - опционально${NC}"
    read -sp "Введите OpenAI API ключ (или Enter для пропуска): " OPENAI_API_KEY
    OPENAI_API_KEY=${OPENAI_API_KEY:-""}
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

PARTSAPI_KEY=${PARTSAPI_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}

REACT_APP_WEBAPP_URL=http://$DOMAIN
PLAYWRIGHT_BROWSERS_PATH=/pw-browsers
EOF

    cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=http://$DOMAIN
EOF

    echo -e "${GREEN}✓ .env файлы созданы${NC}"
}

# Клонирование репозитория
clone_repository() {
    echo -e "${YELLOW}Клонирование репозитория с GitHub...${NC}"
    
    cd $APP_DIR
    
    # Удаляем старые директории если есть
    rm -rf backend frontend
    
    # Клонируем репозиторий во временную директорию
    rm -rf /tmp/market-clone
    git clone --depth 1 --branch $GITHUB_BRANCH https://github.com/wrx861/market.git /tmp/market-clone
    
    # Копируем нужные директории
    cp -r /tmp/market-clone/backend ./
    cp -r /tmp/market-clone/frontend ./
    
    # Копируем deployment файлы
    cp /tmp/market-clone/deployment/docker-compose.yml ./
    
    # Проверяем что важные файлы скопировались
    echo -e "${YELLOW}Проверка скопированных файлов...${NC}"
    if [ ! -f "./frontend/craco.config.js" ]; then
        echo -e "${RED}✗ craco.config.js не найден!${NC}"
        echo -e "${YELLOW}Скачиваю отдельно...${NC}"
        curl -fsSL https://raw.githubusercontent.com/wrx861/market/$GITHUB_BRANCH/frontend/craco.config.js -o ./frontend/craco.config.js
    fi
    if [ ! -f "./frontend/jsconfig.json" ]; then
        curl -fsSL https://raw.githubusercontent.com/wrx861/market/$GITHUB_BRANCH/frontend/jsconfig.json -o ./frontend/jsconfig.json 2>/dev/null || true
    fi
    if [ ! -f "./frontend/postcss.config.js" ]; then
        curl -fsSL https://raw.githubusercontent.com/wrx861/market/$GITHUB_BRANCH/frontend/postcss.config.js -o ./frontend/postcss.config.js 2>/dev/null || true
    fi
    if [ ! -f "./frontend/tailwind.config.js" ]; then
        curl -fsSL https://raw.githubusercontent.com/wrx861/market/$GITHUB_BRANCH/frontend/tailwind.config.js -o ./frontend/tailwind.config.js 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ Файлы frontend:${NC}"
    ls -la ./frontend/*.js ./frontend/*.json 2>/dev/null | tail -10
    
    # Создаем простой nginx.conf без SSL
    cat > $APP_DIR/nginx/nginx.conf << 'NGINX_EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8001;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name _;

        # API запросы к backend
        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Увеличенные таймауты для парсинга
            proxy_connect_timeout 300;
            proxy_send_timeout 300;
            proxy_read_timeout 300;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
NGINX_EOF
    
    # Модифицируем docker-compose.yml чтобы убрать SSL
    cat > $APP_DIR/docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: market-mongodb
    restart: unless-stopped
    volumes:
      - ./mongodb/data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=market_db
    networks:
      - market-network
    ports:
      - "27017:27017"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: market-backend
    restart: unless-stopped
    env_file:
      - ./backend/.env
    depends_on:
      - mongodb
    networks:
      - market-network
    ports:
      - "8001:8001"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: market-frontend
    restart: unless-stopped
    env_file:
      - ./frontend/.env
    depends_on:
      - backend
    networks:
      - market-network
    ports:
      - "3001:3000"

  nginx:
    image: nginx:alpine
    container_name: market-nginx
    restart: unless-stopped
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend
    networks:
      - market-network
    ports:
      - "80:80"

networks:
  market-network:
    driver: bridge
COMPOSE_EOF
    
    # Удаляем временную директорию
    rm -rf /tmp/market-clone
    
    # Удаляем старые .env если были в репозитории
    rm -f backend/.env
    rm -f frontend/.env
    
    # Создаем .env заново с введенными данными
    create_env_files
    
    echo -e "${GREEN}✓ Репозиторий склонирован и настроен${NC}"
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
    echo -e "${YELLOW}Логи backend (последние 30 строк):${NC}"
    docker-compose -f $APP_DIR/docker-compose.yml logs --tail=30 backend
}

# Финальная информация
print_info() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}         Установка завершена успешно!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}📱 Приложение:${NC} http://$DOMAIN (БЕЗ SSL)"
    echo -e "${YELLOW}📁 Директория:${NC} $APP_DIR"
    echo ""
    echo -e "${RED}⚠️  ВНИМАНИЕ: SSL отключен - используйте HTTP${NC}"
    echo -e "${YELLOW}Для добавления SSL позже выполните:${NC}"
    echo "  apt-get install certbot"
    echo "  certbot certonly --standalone -d $DOMAIN"
    echo "  # Затем измените docker-compose.yml и nginx.conf"
    echo ""
    echo -e "${YELLOW}Команды управления:${NC}"
    echo "cd $APP_DIR"
    echo "docker-compose ps                    # статус"
    echo "docker-compose logs -f backend       # логи backend"
    echo "docker-compose logs -f frontend      # логи frontend"
    echo "docker-compose restart               # перезапуск"
    echo ""
}

# Основной процесс установки
main() {
    check_root
    check_dns
    check_ports
    install_dependencies
    create_directories
    input_credentials
    clone_repository
    start_project
    check_status
    print_info
}

main
