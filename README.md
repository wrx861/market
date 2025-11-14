# 🚗 Market Auto Parts - Telegram Mini App

> ✅ **Статус:** Готов к продакшену | Все ошибки исправлены | Полностью протестирован

Telegram Mini App для поиска автозапчастей с интеграцией поставщиков, OEM каталогом и AI диагностикой.

## ⚡ Быстрая установка на чистый сервер

### 🔥 Рекомендуемый способ (Git Clone)

```bash
wget https://raw.githubusercontent.com/wrx861/market/main/deployment/install-with-git.sh
chmod +x install-with-git.sh
sudo bash install-with-git.sh
```

### 📦 Альтернативный способ (Curl)

```bash
wget https://raw.githubusercontent.com/wrx861/market/main/deployment/install-clean-server.sh
chmod +x install-clean-server.sh
sudo bash install-clean-server.sh
```

**✨ Скрипт автоматически:**
- Установит Docker и Docker Compose
- Запросит все API ключи интерактивно
- Настроит SSL сертификаты
- Развернет все 4 сервиса
- Запустит приложение

---

## 🎯 Возможности

- 🔍 **Поиск запчастей** - Rossko + Autotrade API с дедупликацией
- 🚙 **OEM каталог** - поиск по VIN через PartsAPI.ru
- 🤖 **AI диагностика** - OBD-II коды через OpenAI GPT-4o
- 🚗 **Модуль "Гараж"** - CRUD автомобилей, сервисные записи, ТО
- 📊 **Аналитика расходов** - статистика по периодам
- 🛒 **Корзина и Заказы** - полный цикл покупки
- 👤 **Админ панель** - логи активности, пользователи, статистика

---

## 🏗️ Архитектура

- **Backend:** FastAPI (Python 3.11) + Motor (async MongoDB)
- **Frontend:** React 18 + TailwindCSS + shadcn/ui
- **Database:** MongoDB 7.0
- **Proxy:** Nginx с SSL (Let's Encrypt)
- **Deployment:** Docker Compose

---

## 📚 Документация

### Deployment
- 📖 [**READY_FOR_DEPLOYMENT.md**](READY_FOR_DEPLOYMENT.md) - Быстрый старт
- 🔧 [**DEPLOYMENT_FIXES.md**](DEPLOYMENT_FIXES.md) - Что было исправлено
- 📋 [**deployment/DEPLOYMENT_README.md**](deployment/DEPLOYMENT_README.md) - Полная инструкция

### Тестирование и проверка
- ✅ [**deployment/check-completeness.sh**](deployment/check-completeness.sh) - Проверка файлов
- 🧪 [**deployment/test-deployment.sh**](deployment/test-deployment.sh) - Локальное тестирование

### Дополнительно
- 📊 [**test_result.md**](test_result.md) - История тестирования
- 📝 [Документы по настройке](INSTALL_GUIDE.md)

---

## ✅ Готовность к продакшену

Проект прошел полное тестирование:

```
✓ Целостность файлов: OK (14 backend, 6 deployment, 18+ frontend)
✓ Python импорты: OK (все модули импортируются)
✓ Requirements.txt: OK (все пакеты на месте)
✓ Docker конфигурация: OK (все 4 сервиса настроены)
✓ Критические файлы: OK (rate_limiter, proxy_manager, n8n_client)
```

---

## 🚀 После deployment

Приложение будет доступно по адресу: `https://miniapp.shopmarketbot.ru`

Управление:
```bash
cd /opt/market-auto-parts
docker-compose ps                    # статус
docker-compose logs -f backend       # логи
docker-compose restart               # перезапуск
```

---

**Made with ❤️ for Tyumen auto enthusiasts**  
**Version 2.0** | Fully tested and production-ready ✅
