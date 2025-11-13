# 🚀 Установка Market Auto Parts на сервер

## Автоматическая установка одной командой

### Требования:
- Ubuntu/Debian сервер (20.04+)
- Root доступ
- Домен с настроенными DNS записями

### Быстрая установка:

```bash
wget -qO- https://raw.githubusercontent.com/wrx861/market/main/install.sh | sudo bash
```

**Или скачайте и запустите:**

```bash
wget https://raw.githubusercontent.com/wrx861/market/main/install.sh
chmod +x install.sh
sudo ./install.sh
```

### Что будет запрошено:

1. **Домен для Mini App**: `shop.example.com`
2. **Домен для Backend API**: `api.example.com`
3. **Telegram Bot Token**: `1234567890:AAF8dKndVrui-QOzpDlAyDhPU6UrVaIfHZo`
4. **Telegram Admin ID**: `508352361`
5. **Google AI API Key**: `AIzaSy...`
6. **Rossko API KEY1**: `18b5c3be...`
7. **Rossko API KEY2**: `e0f20f53...`

### Что установится автоматически:

✅ Python 3 + виртуальное окружение  
✅ Node.js + Yarn  
✅ MongoDB  
✅ Nginx  
✅ SSL сертификаты (Let's Encrypt)  
✅ Supervisor для автозапуска  
✅ Playwright браузер для парсинга  
✅ Все зависимости проекта  

### Что настроится:

✅ Backend API на `https://api.example.com`  
✅ Mini App на `https://shop.example.com`  
✅ SSL с автообновлением  
✅ Автозапуск сервисов  
✅ Telegram бот  

---

## 📋 Подробная инструкция

### 1. Подготовка сервера

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите git (если нужно)
sudo apt install -y git
```

### 2. Настройка DNS

Создайте А-записи для ваших доменов:

```
shop.example.com  → IP вашего сервера
api.example.com   → IP вашего сервера
```

Проверьте DNS:
```bash
ping shop.example.com
ping api.example.com
```

### 3. Получение API ключей

**Telegram Bot:**
1. Откройте [@BotFather](https://t.me/BotFather)
2. Создайте бота: `/newbot`
3. Скопируйте токен

**Telegram Admin ID:**
1. Напишите [@userinfobot](https://t.me/userinfobot)
2. Отправьте `/start`
3. Скопируйте ваш ID

**Google AI (Gemini):**
1. Перейдите: https://ai.google.dev/
2. Получите API ключ

**Rossko API:**
- У вас уже есть ключи

### 4. Запуск установки

```bash
wget https://raw.githubusercontent.com/wrx861/market/main/install.sh
chmod +x install.sh
sudo ./install.sh
```

Следуйте инструкциям на экране.

### 5. Настройка Telegram бота

После установки:

1. Откройте [@BotFather](https://t.me/BotFather)
2. Выполните команды:
```
/mybots
[Выберите вашего бота]
Bot Settings → Menu Button

Настройки:
Text: 🛒 Магазин
URL: https://shop.example.com
```

3. Проверьте работу:
```
/start в вашем боте
```

---

## ⚙️ Управление сервисами

### Статус:
```bash
sudo supervisorctl status
```

### Перезапуск:
```bash
# Все сервисы
sudo supervisorctl restart all

# Только backend
sudo supervisorctl restart market-backend

# Только бот
sudo supervisorctl restart market-telegram-bot
```

### Остановка/Запуск:
```bash
sudo supervisorctl stop market-backend
sudo supervisorctl start market-backend
```

---

## 📝 Логи

### Backend:
```bash
tail -f /var/log/market-backend.out.log
tail -f /var/log/market-backend.err.log
```

### Telegram Bot:
```bash
tail -f /var/log/market-telegram-bot.out.log
tail -f /var/log/market-telegram-bot.err.log
```

### Nginx:
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### MongoDB:
```bash
tail -f /var/log/mongodb/mongod.log
```

---

## 🧪 Тестирование

### Проверка API:
```bash
curl https://api.example.com/api/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T20:00:00"
}
```

### Проверка Mini App:
```bash
curl -I https://shop.example.com
```

Должен вернуть `HTTP/2 200`

### Тест VIN поиска:
```bash
curl -X POST https://api.example.com/api/search/vin \
  -H "Content-Type: application/json" \
  -d '{"vin": "JTMKD31V105022682", "telegram_id": 123456789}'
```

---

## 🔧 Обновление приложения

```bash
cd /opt/market-autoparts
git pull
sudo supervisorctl restart all
```

---

## 🔐 Обновление SSL

SSL сертификаты обновляются автоматически через cron.

Ручное обновление:
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## 🛠️ Устранение проблем

### Backend не запускается:
```bash
# Проверьте логи
tail -n 50 /var/log/market-backend.err.log

# Проверьте .env файл
cat /opt/market-autoparts/backend/.env

# Перезапустите
sudo supervisorctl restart market-backend
```

### Mini App не открывается:
```bash
# Проверьте Nginx
sudo nginx -t
sudo systemctl status nginx

# Проверьте SSL
sudo certbot certificates
```

### MongoDB не работает:
```bash
sudo systemctl status mongodb
sudo systemctl restart mongodb
```

### Playwright не работает:
```bash
cd /opt/market-autoparts
source venv/bin/activate
playwright install chromium
```

---

## 📊 Мониторинг

### Использование диска:
```bash
df -h
```

### Использование памяти:
```bash
free -h
```

### Процессы:
```bash
ps aux | grep python
ps aux | grep nginx
```

### Порты:
```bash
netstat -tlnp | grep -E '(80|443|8001|27017)'
```

---

## 🔄 Полная переустановка

```bash
# Остановите сервисы
sudo supervisorctl stop all

# Удалите приложение
sudo rm -rf /opt/market-autoparts

# Запустите установку заново
wget -qO- https://raw.githubusercontent.com/wrx861/market/main/install.sh | sudo bash
```

---

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи (см. раздел Логи)
2. Проверьте статус сервисов
3. Создайте issue на GitHub: https://github.com/wrx861/market

---

**Готово! Ваш магазин автозапчастей работает! 🎉**
