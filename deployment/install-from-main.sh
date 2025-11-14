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
echo -e "${GREEN}    Market Auto Parts - Установка на сервер${NC}"
echo -e "${GREEN}    (Временная версия - качает с ветки main)${NC}"
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
    
    if ! command -v certbot &> /dev/null; then
        echo -e "${YELLOW}Установка certbot...${NC}"
        apt-get install -y certbot git
    fi
    echo -e "${GREEN}✓ Certbot установлен${NC}"
}

# Создание директорий
create_directories() {
    echo -e "${YELLOW}Создание директорий...${NC}"
    
    mkdir -p $APP_DIR
    mkdir -p $APP_DIR/ssl
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

REACT_APP_WEBAPP_URL=https://$DOMAIN
PLAYWRIGHT_BROWSERS_PATH=/pw-browsers
EOF

    cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
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
    cp /tmp/market-clone/deployment/nginx.conf ./nginx/
    
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
    
    # Удаляем временную директорию
    rm -rf /tmp/market-clone
    
    # Удаляем старые .env если были в репозитории
    rm -f backend/.env
    rm -f frontend/.env
    
    # Создаем .env заново с введенными данными
    create_env_files
    
    echo -e "${GREEN}✓ Репозиторий склонирован${NC}"
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
    echo -e "${YELLOW}Команды управления:${NC}"
    echo "cd $APP_DIR"
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
    install_dependencies
    create_directories
    input_credentials
    clone_repository
    install_ssl
    start_project
    check_status
    print_info
}

main
