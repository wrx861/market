#!/bin/bash

# Скрипт для проверки целостности проекта перед deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Проверка целостности Market Auto Parts${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Проверка backend файлов
echo -e "${YELLOW}Проверка backend файлов...${NC}"

BACKEND_FILES=(
    "server.py"
    "models.py"
    "requirements.txt"
    "rossko_client.py"
    "autotrade_client.py"
    "autotrade_oem_parser.py"
    "autostels_client.py"
    "partsapi_client.py"
    "openai_client.py"
    "gemini_client.py"
    "cache_manager.py"
    "rate_limiter.py"
    "proxy_manager.py"
    "n8n_client.py"
)

for file in "${BACKEND_FILES[@]}"; do
    if [ -f "backend/$file" ]; then
        echo -e "${GREEN}✓${NC} backend/$file"
    else
        echo -e "${RED}✗${NC} backend/$file - ОТСУТСТВУЕТ!"
        ERRORS=$((ERRORS + 1))
    fi
done

# Проверка deployment файлов
echo ""
echo -e "${YELLOW}Проверка deployment файлов...${NC}"

DEPLOYMENT_FILES=(
    "docker-compose.yml"
    "backend.Dockerfile"
    "frontend.Dockerfile"
    "nginx.conf"
    "install-clean-server.sh"
    "install-with-git.sh"
)

for file in "${DEPLOYMENT_FILES[@]}"; do
    if [ -f "deployment/$file" ]; then
        echo -e "${GREEN}✓${NC} deployment/$file"
    else
        echo -e "${RED}✗${NC} deployment/$file - ОТСУТСТВУЕТ!"
        ERRORS=$((ERRORS + 1))
    fi
done

# Проверка frontend конфигурации
echo ""
echo -e "${YELLOW}Проверка frontend конфигурации...${NC}"

FRONTEND_CONFIG=(
    "package.json"
    "yarn.lock"
    "craco.config.js"
    "tailwind.config.js"
    "postcss.config.js"
)

for file in "${FRONTEND_CONFIG[@]}"; do
    if [ -f "frontend/$file" ]; then
        echo -e "${GREEN}✓${NC} frontend/$file"
    else
        echo -e "${RED}✗${NC} frontend/$file - ОТСУТСТВУЕТ!"
        ERRORS=$((ERRORS + 1))
    fi
done

# Проверка frontend src файлов
echo ""
echo -e "${YELLOW}Проверка frontend src файлов...${NC}"

FRONTEND_PAGES=(
    "Home.js"
    "SearchArticle.js"
    "SearchVIN.js"
    "Garage.js"
    "Cart.js"
    "Orders.js"
)

for file in "${FRONTEND_PAGES[@]}"; do
    if [ -f "frontend/src/pages/$file" ]; then
        echo -e "${GREEN}✓${NC} frontend/src/pages/$file"
    else
        echo -e "${YELLOW}⚠${NC} frontend/src/pages/$file - отсутствует"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Проверка Python импортов
echo ""
echo -e "${YELLOW}Проверка Python импортов в server.py...${NC}"

cd backend

IMPORTS_TO_CHECK=(
    "rossko_client"
    "autotrade_client"
    "partsapi_client"
    "openai_client"
)

for import in "${IMPORTS_TO_CHECK[@]}"; do
    if grep -q "from ${import} import" server.py; then
        # Проверяем что файл существует
        if [ -f "${import}.py" ]; then
            echo -e "${GREEN}✓${NC} Импорт ${import} → файл ${import}.py существует"
        else
            echo -e "${RED}✗${NC} Импорт ${import} → файл ${import}.py ОТСУТСТВУЕТ!"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

# Проверка зависимостей в partsapi_client.py
echo ""
echo -e "${YELLOW}Проверка зависимостей partsapi_client.py...${NC}"

PARTSAPI_DEPS=("rate_limiter" "proxy_manager" "cache_manager")

for dep in "${PARTSAPI_DEPS[@]}"; do
    if grep -q "from ${dep} import" partsapi_client.py; then
        if [ -f "${dep}.py" ]; then
            echo -e "${GREEN}✓${NC} Зависимость ${dep} → файл ${dep}.py существует"
        else
            echo -e "${RED}✗${NC} Зависимость ${dep} → файл ${dep}.py ОТСУТСТВУЕТ!"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

cd ..

# Итоговая статистика
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    Результаты проверки${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ Проект готов к deployment!${NC}"
    echo -e "${GREEN}  Все критические файлы на месте.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Проект готов к deployment с предупреждениями${NC}"
    echo -e "${YELLOW}  Предупреждений: $WARNINGS${NC}"
    exit 0
else
    echo -e "${RED}✗ Обнаружены критические ошибки!${NC}"
    echo -e "${RED}  Ошибок: $ERRORS${NC}"
    echo -e "${YELLOW}  Предупреждений: $WARNINGS${NC}"
    echo ""
    echo -e "${RED}Проект НЕ ГОТОВ к deployment!${NC}"
    exit 1
fi
