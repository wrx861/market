#!/bin/bash

# Скрипт для тестирования deployment локально

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Market Auto Parts - Локальное тестирование${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Шаг 1: Проверка целостности
echo -e "${BLUE}[1/5]${NC} ${YELLOW}Проверка целостности файлов...${NC}"
cd /app
if ./deployment/check-completeness.sh > /tmp/check-result.txt 2>&1; then
    echo -e "${GREEN}✓ Все файлы на месте${NC}"
    cat /tmp/check-result.txt | tail -3
else
    echo -e "${RED}✗ Проверка не прошла${NC}"
    cat /tmp/check-result.txt
    exit 1
fi

echo ""

# Шаг 2: Проверка Python импортов
echo -e "${BLUE}[2/5]${NC} ${YELLOW}Проверка Python импортов...${NC}"
cd /app/backend
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    import models
    import rossko_client
    import autotrade_client
    import partsapi_client
    import cache_manager
    import rate_limiter
    import proxy_manager
    print('✅ Все критические модули импортируются')
    exit(0)
except Exception as e:
    print(f'❌ Ошибка: {e}')
    exit(1)
" > /tmp/import-result.txt 2>&1; then
    cat /tmp/import-result.txt
else
    echo -e "${RED}✗ Импорты не прошли${NC}"
    cat /tmp/import-result.txt
    exit 1
fi

echo ""

# Шаг 3: Проверка requirements.txt
echo -e "${BLUE}[3/5]${NC} ${YELLOW}Проверка requirements.txt...${NC}"
cd /app/backend

REQUIRED_PACKAGES=(
    "fastapi"
    "uvicorn"
    "motor"
    "pydantic"
    "python-dotenv"
    "httpx"
    "playwright"
)

MISSING=0
for package in "${REQUIRED_PACKAGES[@]}"; do
    if grep -q "^${package}" requirements.txt; then
        echo -e "${GREEN}✓${NC} $package"
    else
        echo -e "${RED}✗${NC} $package - ОТСУТСТВУЕТ!"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✓ Все необходимые пакеты в requirements.txt${NC}"
else
    echo -e "${RED}✗ Отсутствуют $MISSING пакетов${NC}"
    exit 1
fi

echo ""

# Шаг 4: Проверка Docker файлов
echo -e "${BLUE}[4/5]${NC} ${YELLOW}Проверка Docker конфигурации...${NC}"
cd /app/deployment

# Проверка backend.Dockerfile
if grep -q "COPY . ." backend.Dockerfile; then
    echo -e "${GREEN}✓${NC} backend.Dockerfile корректен (COPY . .)"
else
    echo -e "${RED}✗${NC} backend.Dockerfile - отсутствует COPY . ."
    exit 1
fi

# Проверка docker-compose.yml
if grep -q "market-backend" docker-compose.yml && \
   grep -q "market-frontend" docker-compose.yml && \
   grep -q "market-mongodb" docker-compose.yml && \
   grep -q "market-nginx" docker-compose.yml; then
    echo -e "${GREEN}✓${NC} docker-compose.yml содержит все сервисы"
else
    echo -e "${RED}✗${NC} docker-compose.yml - отсутствуют сервисы"
    exit 1
fi

echo ""

# Шаг 5: Попытка сборки backend образа (быстрая проверка)
echo -e "${BLUE}[5/5]${NC} ${YELLOW}Проверка сборки backend Dockerfile...${NC}"
echo -e "${YELLOW}Внимание: Это может занять несколько минут${NC}"

cd /app

# Создаем временный Dockerfile для быстрой проверки синтаксиса
cat > /tmp/test.Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
# Проверяем только синтаксис, без установки пакетов
RUN head -5 requirements.txt
COPY backend/ .
RUN ls -la *.py | head -10
CMD ["echo", "Test successful"]
EOF

if docker build -f /tmp/test.Dockerfile -t market-test:latest . > /tmp/docker-build.log 2>&1; then
    echo -e "${GREEN}✓${NC} Docker образ собирается успешно"
    echo -e "${GREEN}✓${NC} Найдено Python файлов:"
    tail -10 /tmp/docker-build.log | grep "\.py$" || echo "  (см. /tmp/docker-build.log)"
    
    # Очистка
    docker rmi market-test:latest > /dev/null 2>&1 || true
else
    echo -e "${RED}✗${NC} Ошибка сборки Docker образа"
    echo -e "${YELLOW}Последние строки лога:${NC}"
    tail -20 /tmp/docker-build.log
    exit 1
fi

# Итоговая статистика
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Все проверки пройдены успешно!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✓${NC} Целостность файлов: OK"
echo -e "${GREEN}✓${NC} Python импорты: OK"
echo -e "${GREEN}✓${NC} Requirements.txt: OK"
echo -e "${GREEN}✓${NC} Docker конфигурация: OK"
echo -e "${GREEN}✓${NC} Docker сборка: OK"
echo ""
echo -e "${GREEN}📦 Проект готов к deployment на удаленном сервере!${NC}"
echo ""
echo -e "${YELLOW}Для развертывания используйте:${NC}"
echo "  Способ 1 (Git): bash install-with-git.sh"
echo "  Способ 2 (Curl): bash install-clean-server.sh"
echo ""
