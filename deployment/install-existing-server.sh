#!/bin/bash

# Скрипт для установки на сервер где уже есть другие проекты
# Особенности:
# - Не требует чистого сервера
# - Автоматически подбирает свободные порты если стандартные заняты
# - Не конфликтует с существующими проектами
# - Не требует перезагрузки существующих сервисов

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Конфигурация по умолчанию
DOMAIN="miniapp.shopmarketbot.ru"
APP_DIR="/opt/market-auto-parts"
REPO_URL="https://github.com/wrx861/market.git"
REPO_BRANCH="main"

# Порты (будут автоматически изменены если заняты)
BACKEND_PORT="8001"
FRONTEND_PORT="3001"
MONGO_PORT="27017"
HTTP_PORT="80"
HTTPS_PORT="443"

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Market Auto Parts - Установка на существующий сервер${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Этот скрипт безопасен для серверов где уже работают другие проекты${NC}"
echo ""

# Функция для проверки root прав
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}✗ Пожалуйста, запустите скрипт с правами root (sudo)${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Права root подтверждены${NC}"
}

# Функция для поиска свободного порта
find_free_port() {
    local start_port=$1
    local port=$start_port
    
    while ss -tulpn | grep -q ":$port "; do
        port=$((port + 1))
    done
    
    echo $port
}

# Проверка и автоматический подбор портов
check_and_adjust_ports() {
    echo -e "${BLUE}[1/8]${NC} ${YELLOW}Проверка портов...${NC}"
    
    local ports_changed=false
    
    # Backend port
    if ss -tulpn | grep -q ":$BACKEND_PORT "; then
        echo -e "${YELLOW}⚠ Порт $BACKEND_PORT занят, ищу свободный...${NC}"
        BACKEND_PORT=$(find_free_port $BACKEND_PORT)
        echo -e "${GREEN}✓ Использую порт $BACKEND_PORT для backend${NC}"
        ports_changed=true
    else
        echo -e "${GREEN}✓ Порт $BACKEND_PORT свободен (backend)${NC}"
    fi
    
    # Frontend port
    if ss -tulpn | grep -q ":$FRONTEND_PORT "; then
        echo -e "${YELLOW}⚠ Порт $FRONTEND_PORT занят, ищу свободный...${NC}"
        FRONTEND_PORT=$(find_free_port $FRONTEND_PORT)
        echo -e "${GREEN}✓ Использую порт $FRONTEND_PORT для frontend${NC}"
        ports_changed=true
    else
        echo -e "${GREEN}✓ Порт $FRONTEND_PORT свободен (frontend)${NC}"
    fi
    
    # MongoDB port
    if ss -tulpn | grep -q ":$MONGO_PORT "; then
        echo -e "${YELLOW}⚠ Порт $MONGO_PORT занят, ищу свободный...${NC}"
        MONGO_PORT=$(find_free_port $MONGO_PORT)
        echo -e "${GREEN}✓ Использую порт $MONGO_PORT для MongoDB${NC}"
        ports_changed=true
    else
        echo -e "${GREEN}✓ Порт $MONGO_PORT свободен (MongoDB)${NC}"
    fi
    
    # HTTP/HTTPS ports
    if ss -tulpn | grep -q ":$HTTP_PORT " || ss -tulpn | grep -q ":$HTTPS_PORT "; then
        echo -e "${YELLOW}⚠ Порты 80/443 заняты (возможно nginx/apache)${NC}"
        echo -e "${YELLOW}⚠ SSL сертификат будет пропущен, используйте обратный прокси${NC}"
        USE_SSL=false
    else
        echo -e "${GREEN}✓ Порты 80/443 свободны (SSL будет установлен)${NC}"
        USE_SSL=true
    fi
    
    if [ "$ports_changed" = true ]; then
        echo ""
        echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  ВНИМАНИЕ: Порты были изменены!${NC}"
        echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}Backend:  $BACKEND_PORT${NC}"
        echo -e "${YELLOW}Frontend: $FRONTEND_PORT${NC}"
        echo -e "${YELLOW}MongoDB:  $MONGO_PORT${NC}"
        echo ""
        read -p "Продолжить с этими портами? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Установка отменена${NC}"
            exit 1
        fi
    fi
}

# Исправление DNS
fix_dns() {
    echo ""
    echo -e "${BLUE}[1.5/8]${NC} ${YELLOW}Настройка DNS...${NC}"
    
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

# Установка зависимостей (только если не установлены)
install_dependencies() {
    echo ""
    echo -e "${BLUE}[2/8]${NC} ${YELLOW}Проверка зависимостей...${NC}"
    
    # Не обновляем apt если не нужно
    local need_apt_update=false
    
    # Git
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}Установка Git...${NC}"
        need_apt_update=true
        apt-get update -qq
        apt-get install -y git
    fi
    echo -e "${GREEN}✓ Git доступен${NC}"
    
    # Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Установка Docker...${NC}"
        curl -fsSL https://get.docker.com | bash
        systemctl enable docker
        systemctl start docker
        
        # Перезапускаем Docker с DNS настройками
        systemctl restart docker
        sleep 3
    fi
    echo -e "${GREEN}✓ Docker доступен${NC}"
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}Установка Docker Compose...${NC}"
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    echo -e "${GREEN}✓ Docker Compose доступен${NC}"
    
    # Certbot (только если будем устанавливать SSL)
    if [ "$USE_SSL" = true ]; then
        if ! command -v certbot &> /dev/null; then
            echo -e "${YELLOW}Установка Certbot...${NC}"
            if [ "$need_apt_update" = false ]; then
                apt-get update -qq
            fi
            apt-get install -y certbot
        fi
        echo -e "${GREEN}✓ Certbot доступен${NC}"
    fi
}

# Интерактивный ввод credentials
input_credentials() {
    echo ""
    echo -e "${BLUE}[3/8]${NC} ${GREEN}Ввод API ключей и учетных данных${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    
    exec < /dev/tty
    
    echo ""
    echo -e "${YELLOW}Telegram Bot${NC}"
    read -p "TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
    read -p "TELEGRAM_ADMIN_ID: " TELEGRAM_ADMIN_ID
    
    echo ""
    echo -e "${YELLOW}Google AI Studio (Gemini)${NC}"
    read -p "GOOGLE_API_KEY: " GOOGLE_API_KEY
    
    echo ""
    echo -e "${YELLOW}Rossko API${NC}"
    read -p "ROSSKO_API_KEY1: " ROSSKO_API_KEY1
    read -p "ROSSKO_API_KEY2: " ROSSKO_API_KEY2
    
    echo ""
    echo -e "${YELLOW}Autotrade API${NC}"
    read -p "Логин (email): " AUTOTRADE_LOGIN
    read -sp "Пароль: " AUTOTRADE_PASSWORD
    echo ""
    read -p "API ключ: " AUTOTRADE_API_KEY
    
    echo ""
    echo -e "${YELLOW}Berg API${NC}"
    read -p "BERG_API_KEY: " BERG_API_KEY
    echo ""
    
    echo -e "${YELLOW}PartsAPI.ru${NC}"
    read -p "PARTSAPI_KEY: " PARTSAPI_KEY
    
    echo ""
    echo -e "${YELLOW}OpenAI API${NC}"
    read -sp "OPENAI_API_KEY: " OPENAI_API_KEY
    echo ""
    
    echo ""
    echo -e "${GREEN}✓ Все данные получены${NC}"
}

# Клонирование репозитория
clone_repository() {
    echo ""
    echo -e "${BLUE}[4/8]${NC} ${YELLOW}Скачивание проекта с GitHub...${NC}"
    
    # Удаляем старую директорию если есть
    if [ -d "$APP_DIR" ]; then
        echo -e "${YELLOW}Директория $APP_DIR уже существует${NC}"
        read -p "Удалить и пересоздать? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf $APP_DIR
        else
            echo -e "${RED}Установка отменена${NC}"
            exit 1
        fi
    fi
    
    # Клонируем репозиторий
    git clone --depth 1 --branch $REPO_BRANCH $REPO_URL $APP_DIR
    
    # Создаем дополнительные директории
    mkdir -p $APP_DIR/ssl
    mkdir -p $APP_DIR/mongodb/data
    
    echo -e "${GREEN}✓ Проект скачан${NC}"
}

# Создание .env файлов
create_env_files() {
    echo ""
    echo -e "${BLUE}[5/8]${NC} ${YELLOW}Создание конфигурационных файлов...${NC}"
    
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
REACT_APP_ADMIN_ID=${TELEGRAM_ADMIN_ID}
EOF

    echo -e "${GREEN}✓ .env файлы созданы${NC}"
}

# Настройка deployment с учетом портов
setup_deployment() {
    echo ""
    echo -e "${BLUE}[6/8]${NC} ${YELLOW}Настройка deployment...${NC}"
    
    cd $APP_DIR
    
    # Копируем docker-compose.yml
    cp deployment/docker-compose.yml ./
    
    # Обновляем порты в docker-compose.yml если они изменились
    if [ "$BACKEND_PORT" != "8001" ] || [ "$FRONTEND_PORT" != "3001" ] || [ "$MONGO_PORT" != "27017" ]; then
        echo -e "${YELLOW}Обновление портов в docker-compose.yml...${NC}"
        sed -i "s/\"8001:8001\"/\"$BACKEND_PORT:8001\"/g" docker-compose.yml
        sed -i "s/\"3001:3000\"/\"$FRONTEND_PORT:3000\"/g" docker-compose.yml
        sed -i "s/\"27017:27017\"/\"$MONGO_PORT:27017\"/g" docker-compose.yml
    fi
    
    # Копируем Dockerfiles
    cp deployment/backend.Dockerfile backend/Dockerfile
    cp deployment/frontend.Dockerfile frontend/Dockerfile
    
    # Копируем nginx конфиг
    mkdir -p nginx
    cp deployment/nginx.conf nginx/
    
    echo -e "${GREEN}✓ Deployment настроен${NC}"
}

# Установка SSL (опционально)
install_ssl() {
    if [ "$USE_SSL" = false ]; then
        echo ""
        echo -e "${BLUE}[7/8]${NC} ${YELLOW}SSL сертификаты пропущены (порты 80/443 заняты)${NC}"
        echo -e "${YELLOW}Настройте обратный прокси вручную:${NC}"
        echo -e "  Backend: http://localhost:$BACKEND_PORT"
        echo -e "  Frontend: http://localhost:$FRONTEND_PORT"
        
        # Создаем самоподписанный сертификат для тестирования
        mkdir -p $APP_DIR/ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout $APP_DIR/ssl/privkey.pem \
            -out $APP_DIR/ssl/fullchain.pem \
            -subj "/CN=$DOMAIN" 2>/dev/null
        
        echo -e "${GREEN}✓ Создан самоподписанный сертификат для тестирования${NC}"
        return
    fi
    
    echo ""
    echo -e "${BLUE}[7/8]${NC} ${YELLOW}Установка SSL сертификата...${NC}"
    
    # Временно останавливаем приложение если оно запущено
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
    
    # Настройка автоматического обновления
    (crontab -l 2>/dev/null | grep -v "certbot renew"; echo "0 5 * * 0 certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/*.pem $APP_DIR/ssl/ && docker-compose -f $APP_DIR/docker-compose.yml restart nginx") | crontab -
    
    echo -e "${GREEN}✓ SSL сертификат установлен${NC}"
}

# Запуск проекта
start_project() {
    echo ""
    echo -e "${BLUE}[8/8]${NC} ${YELLOW}Запуск приложения...${NC}"
    
    cd $APP_DIR
    docker-compose down 2>/dev/null || true
    docker-compose up --build -d
    
    echo -e "${GREEN}✓ Приложение запущено${NC}"
    
    # Ждем запуска
    echo ""
    echo -e "${YELLOW}Ожидание запуска сервисов (60 сек)...${NC}"
    sleep 60
    
    # Проверка статуса
    echo ""
    echo -e "${YELLOW}Статус контейнеров:${NC}"
    docker-compose ps
    
    echo ""
    echo -e "${YELLOW}Логи backend (последние 20 строк):${NC}"
    docker-compose logs --tail=20 backend
}

# Финальная информация
print_info() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}         Установка завершена успешно!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    
    if [ "$USE_SSL" = true ]; then
        echo -e "${YELLOW}📱 Приложение:${NC} https://$DOMAIN"
    else
        echo -e "${YELLOW}📱 Backend:${NC} http://$DOMAIN:$BACKEND_PORT"
        echo -e "${YELLOW}📱 Frontend:${NC} http://$DOMAIN:$FRONTEND_PORT"
        echo -e "${YELLOW}⚠  Настройте обратный прокси для SSL${NC}"
    fi
    
    echo -e "${YELLOW}📁 Директория:${NC} $APP_DIR"
    echo ""
    echo -e "${YELLOW}🔧 Используемые порты:${NC}"
    echo -e "  Backend:  $BACKEND_PORT"
    echo -e "  Frontend: $FRONTEND_PORT"
    echo -e "  MongoDB:  $MONGO_PORT"
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
    echo "  cd $APP_DIR"
    echo "  bash deployment/update.sh      # обновление с GitHub"
    echo "  docker-compose ps              # статус"
    echo "  docker-compose logs -f backend # логи"
    echo "  docker-compose restart         # перезапуск"
    echo "  docker-compose down            # остановка"
    echo ""
}

# Основной процесс
main() {
    check_root
    check_and_adjust_ports
    fix_dns                      # Исправляем DNS перед установкой
    install_dependencies
    input_credentials
    clone_repository
    create_env_files
    setup_deployment
    install_ssl
    start_project
    print_info
}

main
