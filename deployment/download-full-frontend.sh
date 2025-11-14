#!/bin/bash

# Скрипт для полного скачивания frontend с GitHub
# Используйте когда git clone не работает корректно

set -e

GITHUB_BRANCH="main"
BASE_URL="https://raw.githubusercontent.com/wrx861/market/$GITHUB_BRANCH"
TARGET_DIR="/opt/market-auto-parts/frontend"

echo "Скачивание всех файлов frontend с GitHub..."
echo "Целевая директория: $TARGET_DIR"
echo ""

# Создаем структуру директорий
mkdir -p "$TARGET_DIR/src/pages"
mkdir -p "$TARGET_DIR/src/utils"
mkdir -p "$TARGET_DIR/src/components/ui"
mkdir -p "$TARGET_DIR/public"

cd "$TARGET_DIR"

# Dockerfile
echo "Скачиваю Dockerfile..."
curl -fsSL "$BASE_URL/deployment/frontend.Dockerfile" -o Dockerfile

# Корневые файлы frontend
echo "Скачиваю конфигурационные файлы..."
curl -fsSL "$BASE_URL/frontend/package.json" -o package.json
curl -fsSL "$BASE_URL/frontend/yarn.lock" -o yarn.lock
curl -fsSL "$BASE_URL/frontend/craco.config.js" -o craco.config.js
curl -fsSL "$BASE_URL/frontend/jsconfig.json" -o jsconfig.json 2>/dev/null || true
curl -fsSL "$BASE_URL/frontend/postcss.config.js" -o postcss.config.js 2>/dev/null || true
curl -fsSL "$BASE_URL/frontend/tailwind.config.js" -o tailwind.config.js 2>/dev/null || true
curl -fsSL "$BASE_URL/frontend/components.json" -o components.json 2>/dev/null || true

# src/ файлы
echo "Скачиваю src файлы..."
curl -fsSL "$BASE_URL/frontend/src/index.js" -o src/index.js
curl -fsSL "$BASE_URL/frontend/src/index.css" -o src/index.css
curl -fsSL "$BASE_URL/frontend/src/App.js" -o src/App.js
curl -fsSL "$BASE_URL/frontend/src/App.css" -o src/App.css

# utils
echo "Скачиваю utils..."
curl -fsSL "$BASE_URL/frontend/src/utils/telegram.js" -o src/utils/telegram.js

# pages
echo "Скачиваю pages..."
curl -fsSL "$BASE_URL/frontend/src/pages/Home.js" -o src/pages/Home.js
curl -fsSL "$BASE_URL/frontend/src/pages/SearchArticle.js" -o src/pages/SearchArticle.js
curl -fsSL "$BASE_URL/frontend/src/pages/SearchVIN.js" -o src/pages/SearchVIN.js
curl -fsSL "$BASE_URL/frontend/src/pages/Cart.js" -o src/pages/Cart.js
curl -fsSL "$BASE_URL/frontend/src/pages/Orders.js" -o src/pages/Orders.js
curl -fsSL "$BASE_URL/frontend/src/pages/Diagnostics.js" -o src/pages/Diagnostics.js
curl -fsSL "$BASE_URL/frontend/src/pages/Garage.js" -o src/pages/Garage.js
curl -fsSL "$BASE_URL/frontend/src/pages/VehicleDetail.js" -o src/pages/VehicleDetail.js
curl -fsSL "$BASE_URL/frontend/src/pages/AddVehicle.js" -o src/pages/AddVehicle.js
curl -fsSL "$BASE_URL/frontend/src/pages/ServiceLog.js" -o src/pages/ServiceLog.js
curl -fsSL "$BASE_URL/frontend/src/pages/AddService.js" -o src/pages/AddService.js
curl -fsSL "$BASE_URL/frontend/src/pages/BoardJournal.js" -o src/pages/BoardJournal.js
curl -fsSL "$BASE_URL/frontend/src/pages/AddLog.js" -o src/pages/AddLog.js
curl -fsSL "$BASE_URL/frontend/src/pages/Reminders.js" -o src/pages/Reminders.js
curl -fsSL "$BASE_URL/frontend/src/pages/AddReminder.js" -o src/pages/AddReminder.js
curl -fsSL "$BASE_URL/frontend/src/pages/Expenses.js" -o src/pages/Expenses.js
curl -fsSL "$BASE_URL/frontend/src/pages/Admin.js" -o src/pages/Admin.js

# UI components
echo "Скачиваю UI компоненты..."
for component in accordion alert-dialog alert aspect-ratio avatar badge breadcrumb button calendar card carousel checkbox collapsible command context-menu dialog drawer dropdown-menu form hover-card input-otp input label menubar navigation-menu pagination popover progress radio-group resizable scroll-area select separator sheet skeleton slider sonner switch table tabs textarea toast toaster toggle-group toggle tooltip; do
    curl -fsSL "$BASE_URL/frontend/src/components/ui/${component}.jsx" -o "src/components/ui/${component}.jsx" 2>/dev/null || true
done

# public файлы
echo "Скачиваю public файлы..."
curl -fsSL "$BASE_URL/frontend/public/index.html" -o public/index.html 2>/dev/null || true
curl -fsSL "$BASE_URL/frontend/public/manifest.json" -o public/manifest.json 2>/dev/null || true
curl -fsSL "$BASE_URL/frontend/public/robots.txt" -o public/robots.txt 2>/dev/null || true

# .env файл (должен быть создан с правильными данными)
if [ ! -f ".env" ]; then
    echo "Создаю .env файл..."
    cat > .env << 'EOF'
REACT_APP_BACKEND_URL=https://miniapp.shopmarketbot.ru
EOF
fi

echo ""
echo "✓ Все файлы скачаны!"
echo ""
echo "Структура frontend:"
find . -type f -name "*.js" -o -name "*.jsx" -o -name "*.json" -o -name "*.css" | head -20
echo "..."
echo ""
echo "Файлов всего: $(find . -type f | wc -l)"
