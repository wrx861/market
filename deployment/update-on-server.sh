#!/bin/bash

# Скрипт для обновления приложения на сервере без полной переустановки

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="/opt/market-auto-parts"

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Market Auto Parts - Обновление на сервере${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Проверка что мы в правильной директории
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}✗ Директория $APP_DIR не найдена!${NC}"
    echo -e "${YELLOW}Сначала установите приложение через install скрипт${NC}"
    exit 1
fi

cd $APP_DIR

echo -e "${YELLOW}[1/5] Сохранение текущих .env файлов...${NC}"
cp backend/.env /tmp/backend.env.backup
cp frontend/.env /tmp/frontend.env.backup
echo -e "${GREEN}✓ .env файлы сохранены${NC}"

echo ""
echo -e "${YELLOW}[2/5] Получение последних изменений...${NC}"
git fetch origin
git reset --hard origin/main
echo -e "${GREEN}✓ Код обновлен${NC}"

echo ""
echo -e "${YELLOW}[3/5] Восстановление .env файлов...${NC}"
cp /tmp/backend.env.backup backend/.env
cp /tmp/frontend.env.backup frontend/.env
echo -e "${GREEN}✓ .env файлы восстановлены${NC}"

echo ""
echo -e "${YELLOW}[4/5] Пересборка контейнеров...${NC}"
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo -e "${GREEN}✓ Контейнеры пересобраны${NC}"

echo ""
echo -e "${YELLOW}[5/5] Ожидание запуска сервисов...${NC}"
sleep 20

echo ""
docker-compose ps

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}         Обновление завершено успешно!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Проверьте логи:${NC}"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f frontend"
echo ""
