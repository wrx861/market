# 🚀 Market Auto Parts - Развертывание и Обновление

## 📋 Содержание

- [Первичная установка](#первичная-установка)
- [Автообновление с GitHub](#автообновление-с-github)
- [Управление приложением](#управление-приложением)
- [Устранение неполадок](#устранение-неполадок)

---

## 🎯 Первичная установка

### Вариант 1: Установка с Git (рекомендуется)

Используйте если у вас уже есть Git репозиторий:

```bash
wget https://raw.githubusercontent.com/ваш-username/market/main/deployment/install-with-git.sh
chmod +x install-with-git.sh
sudo ./install-with-git.sh
```

Скрипт запросит:
- Доменное имя
- API ключи (Rossko, Autotrade, Berg, Google, Telegram)
- Настройки SSL сертификата

### Вариант 2: Установка на чистый сервер

Если Git репозитория еще нет:

```bash
wget https://raw.githubusercontent.com/ваш-username/market/main/deployment/install-clean-server.sh
chmod +x install-clean-server.sh
sudo ./install-clean-server.sh
```

После установки создайте Git репозиторий:

```bash
cd /opt/market-auto-parts
git init
git remote add origin https://github.com/ваш-username/market.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### Вариант 3: Установка на существующий сервер

Если на сервере уже есть другие приложения:

```bash
wget https://raw.githubusercontent.com/ваш-username/market/main/deployment/install-existing-server.sh
chmod +x install-existing-server.sh
sudo ./install-existing-server.sh
```

Скрипт запросит порты для избежания конфликтов.

---

## 🔄 Автообновление с GitHub

### Быстрое обновление

После того как вы сохранили изменения в GitHub (`git push`):

```bash
cd /opt/market-auto-parts
bash deployment/update.sh
```

**Что делает скрипт:**
- ✅ Загружает последний код с GitHub
- ✅ Пересобирает Docker образы
- ✅ Перезапускает все сервисы
- ✅ Показывает статус контейнеров

### Создание быстрой команды

Для удобства создайте alias:

```bash
echo 'alias update-app="cd /opt/market-auto-parts && bash deployment/update.sh"' >> ~/.bashrc
source ~/.bashrc
```

Теперь просто:
```bash
update-app
```

### Процесс обновления

1. **На локальной машине / Emergent:**
   ```bash
   git add .
   git commit -m "Описание изменений"
   git push origin main
   ```

2. **На сервере:**
   ```bash
   cd /opt/market-auto-parts
   bash deployment/update.sh
   ```

3. **Проверка:**
   ```bash
   docker-compose ps
   docker-compose logs -f backend
   ```

---

## 🛠 Управление приложением

### Основные команды

```bash
cd /opt/market-auto-parts/deployment

# Статус контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f                # все сервисы
docker-compose logs -f backend        # только backend
docker-compose logs -f frontend       # только frontend

# Перезапуск
docker-compose restart                # все сервисы
docker-compose restart backend        # только backend

# Остановка и запуск
docker-compose down                   # остановить все
docker-compose up -d                  # запустить все

# Полная пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Просмотр логов

```bash
# Последние 100 строк
docker-compose logs --tail=100 backend

# Логи в реальном времени
docker-compose logs -f backend

# Логи за последние 10 минут
docker-compose logs --since 10m backend

# Фильтр по слову
docker-compose logs backend | grep "ERROR"
```

### Вход в контейнер

```bash
# Backend
docker-compose exec backend bash

# Frontend
docker-compose exec frontend sh

# MongoDB
docker-compose exec mongodb mongosh
```

### Проверка работы

```bash
# Проверка backend
curl https://ваш-домен.ru/api/health

# Проверка frontend
curl https://ваш-домен.ru

# Проверка статуса всех сервисов
docker-compose ps
```

---

## 🔧 Устранение неполадок

### Backend не запускается

```bash
# Проверьте логи
docker-compose logs backend

# Проверьте .env файл
cat /opt/market-auto-parts/backend/.env

# Пересоберите контейнер
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Frontend не загружается

```bash
# Проверьте логи
docker-compose logs frontend

# Проверьте Nginx конфигурацию
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# Пересоберите
docker-compose down
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### MongoDB не подключается

```bash
# Проверьте что MongoDB запущен
docker-compose ps mongodb

# Проверьте логи
docker-compose logs mongodb

# Перезапустите
docker-compose restart mongodb

# Проверьте соединение
docker-compose exec backend python -c "from pymongo import MongoClient; print(MongoClient('mongodb://mongodb:27017').server_info())"
```

### Проблемы с SSL

```bash
# Проверьте сертификаты
sudo certbot certificates

# Обновите сертификаты
sudo certbot renew

# Перезапустите Nginx
docker-compose restart nginx
```

### Недостаточно места

```bash
# Проверьте свободное место
df -h

# Очистите старые Docker образы
docker system prune -a

# Очистите логи
sudo truncate -s 0 /var/log/nginx/*.log
sudo truncate -s 0 /var/log/supervisor/*.log
```

### Откат к предыдущей версии

```bash
cd /opt/market-auto-parts

# Посмотрите историю
git log --oneline

# Откатитесь к нужному коммиту
git reset --hard <commit-hash>

# Примените изменения
bash deployment/update.sh
```

---

## 📊 Мониторинг

### Использование ресурсов

```bash
# CPU и память
docker stats

# Место на диске
df -h

# Размер контейнеров
docker system df
```

### Автоматические обновления (опционально)

Настройте cron для автоматического обновления:

```bash
crontab -e

# Добавьте (обновление каждую ночь в 3:00)
0 3 * * * cd /opt/market-auto-parts && bash deployment/update.sh >> /var/log/market-update.log 2>&1
```

### Резервное копирование

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /backup
docker cp market-auto-parts-mongodb-1:/backup ./mongodb-backup-$(date +%Y%m%d)

# Backup .env файлов
tar -czf env-backup-$(date +%Y%m%d).tar.gz backend/.env frontend/.env

# Backup всего проекта
tar -czf market-backup-$(date +%Y%m%d).tar.gz /opt/market-auto-parts
```

---

## 📚 Дополнительная документация

- **Подробная инструкция по обновлению:** `deployment/UPDATE_INSTRUCTIONS.md`
- **Краткая шпаргалка:** `deployment/QUICK_UPDATE.md`
- **Конфигурация Docker:** `deployment/docker-compose.yml`

---

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи контейнеров
2. Проверьте статус сервисов: `docker-compose ps`
3. Проверьте свободное место: `df -h`
4. Проверьте что Docker запущен: `systemctl status docker`

**Полезные ссылки:**
- Docker документация: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Nginx: https://nginx.org/ru/docs/
- MongoDB: https://docs.mongodb.com/

---

**Версия:** 1.0  
**Последнее обновление:** Ноябрь 2024
