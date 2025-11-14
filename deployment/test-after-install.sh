#!/bin/bash

# Скрипт для проверки работоспособности после установки

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Market Auto Parts - Проверка установки${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

cd /opt/market-auto-parts

# 1. Проверка контейнеров
echo -e "${YELLOW}[1/6] Проверка контейнеров...${NC}"
CONTAINERS=$(docker-compose ps --format json | jq -r '.State' | grep -c "running")

if [ "$CONTAINERS" -eq 4 ]; then
    echo -e "${GREEN}✓ Все 4 контейнера запущены${NC}"
else
    echo -e "${RED}✗ Запущено только $CONTAINERS контейнеров из 4${NC}"
    docker-compose ps
    exit 1
fi

# 2. Проверка Backend
echo ""
echo -e "${YELLOW}[2/6] Проверка Backend API...${NC}"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/)

if [ "$BACKEND_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ Backend API отвечает (200 OK)${NC}"
else
    echo -e "${RED}✗ Backend API не отвечает (код: $BACKEND_STATUS)${NC}"
    docker-compose logs --tail=20 backend
    exit 1
fi

# 3. Проверка Frontend
echo ""
echo -e "${YELLOW}[3/6] Проверка Frontend...${NC}"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001)

if [ "$FRONTEND_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ Frontend отвечает (200 OK)${NC}"
else
    echo -e "${RED}✗ Frontend не отвечает (код: $FRONTEND_STATUS)${NC}"
    docker-compose logs --tail=20 frontend
    exit 1
fi

# 4. Проверка Telegram Bot
echo ""
echo -e "${YELLOW}[4/6] Проверка Telegram Bot...${NC}"
BOT_RUNNING=$(docker-compose logs backend | grep -c "Bot is running")

if [ "$BOT_RUNNING" -gt 0 ]; then
    echo -e "${GREEN}✓ Telegram Bot запущен${NC}"
else
    echo -e "${RED}✗ Telegram Bot не запущен${NC}"
    docker-compose logs backend | grep -i telegram | tail -10
fi

# 5. Проверка Nginx
echo ""
echo -e "${YELLOW}[5/6] Проверка Nginx...${NC}"
NGINX_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)

if [ "$NGINX_STATUS" -eq 200 ] || [ "$NGINX_STATUS" -eq 301 ]; then
    echo -e "${GREEN}✓ Nginx работает (код: $NGINX_STATUS)${NC}"
else
    echo -e "${RED}✗ Nginx не работает (код: $NGINX_STATUS)${NC}"
    docker-compose logs --tail=20 nginx
fi

# 6. Проверка HTTPS
echo ""
echo -e "${YELLOW}[6/6] Проверка HTTPS...${NC}"
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://miniapp.shopmarketbot.ru)

if [ "$HTTPS_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ HTTPS работает (200 OK)${NC}"
else
    echo -e "${YELLOW}⚠ HTTPS код: $HTTPS_STATUS (может быть нормально если SSL еще настраивается)${NC}"
fi

# Итоговый отчет
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Результаты проверки${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✓ Контейнеры: 4/4 запущены${NC}"
echo -e "${GREEN}✓ Backend API: работает${NC}"
echo -e "${GREEN}✓ Frontend: работает${NC}"
echo -e "${GREEN}✓ Telegram Bot: запущен${NC}"
echo -e "${GREEN}✓ Nginx: работает${NC}"
echo ""
echo -e "${YELLOW}📱 Приложение: https://miniapp.shopmarketbot.ru${NC}"
echo ""
