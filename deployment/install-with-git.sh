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
REPO_URL="https://github.com/wrx861/market.git"
REPO_BRANCH="main"

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Market Auto Parts - Установка на сервер (с Git)${NC}"
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

# Исправление DNS (критически важно для Docker)
fix_dns() {
    echo -e "${YELLOW}Настройка DNS...${NC}"
    
    # Проверяем есть ли проблемы с DNS
    if ! nslookup google.com > /dev/null 2>&1; then
        echo -e "${YELLOW}Обнаружены проблемы с DNS, исправляем...${NC}"
    fi
    
    # Добавляем Google DNS в систему
    if ! grep -q "8.8.8.8" /etc/resolv.conf; then
        # Создаем бэкап
        cp /etc/resolv.conf /etc/resolv.conf.backup 2>/dev/null || true
        
        # Добавляем Google DNS в начало
        echo "nameserver 8.8.8.8" | cat - /etc/resolv.conf > /tmp/resolv.conf.tmp
        echo "nameserver 8.8.4.4" >> /tmp/resolv.conf.tmp
        echo "nameserver 1.1.1.1" >> /tmp/resolv.conf.tmp
        cat /etc/resolv.conf >> /tmp/resolv.conf.tmp
        mv /tmp/resolv.conf.tmp /etc/resolv.conf
    fi
    
    # Настраиваем DNS для Docker (до установки Docker)
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
    
    # Git
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}Установка Git...${NC}"
        apt-get install -y git
    fi
    echo -e "${GREEN}✓ Git установлен${NC}"
    
    # Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Установка Docker...${NC}"
        curl -fsSL https://get.docker.com | bash
        systemctl enable docker
        systemctl start docker
        
        # Перезапускаем Docker с новыми DNS настройками
        echo -e "${YELLOW}Применение DNS настроек для Docker...${NC}"
        systemctl restart docker
        sleep 3
    fi
    echo -e "${GREEN}✓ Docker установлен${NC}"
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}Установка Docker Compose...${NC}"
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    echo -e "${GREEN}✓ Docker Compose установлен${NC}"
    
    # Certbot
    if ! command -v certbot &> /dev/null; then
        echo -e "${YELLOW}Установка certbot...${NC}"
        apt-get install -y certbot
    fi
    echo -e "${GREEN}✓ Certbot установлен${NC}"
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
    
    echo -e "${YELLOW}PartsAPI.ru (поиск по VIN)${NC}"
    read -p "Введите PARTSAPI_KEY: " PARTSAPI_KEY
    echo ""
    
    echo -e "${YELLOW}OpenAI API (AI диагностика)${NC}"
    read -sp "Введите OpenAI API ключ: " OPENAI_API_KEY
    echo ""
    echo ""
    
    echo -e "${GREEN}✓ Все данные получены${NC}"
}

# Клонирование репозитория
clone_repository() {
    echo -e "${YELLOW}Клонирование репозитория с GitHub...${NC}"
    
    # Удаляем старую директорию если есть
    if [ -d "$APP_DIR" ]; then
        echo -e "${YELLOW}Удаление старой директории...${NC}"
        rm -rf $APP_DIR
    fi
    
    # Клонируем репозиторий
    git clone --depth 1 --branch $REPO_BRANCH $REPO_URL $APP_DIR
    
    # Создаем дополнительные директории
    mkdir -p $APP_DIR/ssl
    mkdir -p $APP_DIR/mongodb/data
    
    echo -e "${GREEN}✓ Репозиторий клонирован${NC}"
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
REACT_APP_ADMIN_ID=${TELEGRAM_ADMIN_ID}
EOF

    echo -e "${GREEN}✓ .env файлы созданы${NC}"
}

# Копирование deployment файлов
setup_deployment() {
    echo -e "${YELLOW}Настройка deployment файлов...${NC}"
    
    cd $APP_DIR
    
    # Копируем docker-compose.yml в корень
    cp deployment/docker-compose.yml ./
    
    # Копируем Dockerfiles
    cp deployment/backend.Dockerfile backend/Dockerfile
    cp deployment/frontend.Dockerfile frontend/Dockerfile
    
    # Создаем директорию nginx и копируем конфиг
    mkdir -p nginx
    cp deployment/nginx.conf nginx/
    
    echo -e "${GREEN}✓ Deployment файлы настроены${NC}"
}

# Установка SSL сертификата
install_ssl() {
    echo -e "${YELLOW}Установка SSL сертификата для $DOMAIN...${NC}"
    
    # Открытие порта 80 временно
    ufw allow 80 2>/dev/null || true
    
    # Остановка всех контейнеров которые могут занимать порт 80
    cd $APP_DIR
    docker-compose down 2>/dev/null || true
    
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
    echo -e "${YELLOW}Логи backend (последние 30 строк):${NC}"
    docker-compose -f $APP_DIR/docker-compose.yml logs --tail=30 backend
    
    echo ""
    echo -e "${YELLOW}Логи frontend (последние 10 строк):${NC}"
    docker-compose -f $APP_DIR/docker-compose.yml logs --tail=10 frontend
    
    # Финальная проверка
    echo ""
    echo -e "${YELLOW}Выполнение финальной проверки...${NC}"
    sleep 10
    
    # Проверяем что все контейнеры работают
    RUNNING=$(docker-compose -f $APP_DIR/docker-compose.yml ps --format json 2>/dev/null | grep -c '"State":"running"' || docker-compose -f $APP_DIR/docker-compose.yml ps | grep -c "Up")
    
    if [ "$RUNNING" -ge 4 ]; then
        echo -e "${GREEN}✓ Все контейнеры запущены успешно${NC}"
    else
        echo -e "${YELLOW}⚠ Внимание: запущено только $RUNNING контейнеров${NC}"
        echo -e "${YELLOW}Проверьте логи: docker-compose -f $APP_DIR/docker-compose.yml logs${NC}"
    fi
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
    fix_dns                    # Исправляем DNS ДО установки зависимостей
    install_dependencies
    input_credentials
    clone_repository
    create_env_files
    setup_deployment
    install_ssl
    start_project
    check_status
    print_info
}

main
