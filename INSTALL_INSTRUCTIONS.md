# 📋 Инструкция по установке Market Auto Parts

## Для вас (владелец проекта)

### 🚀 Установка на ваш хостинг 144.31.84.74

**Одна команда - и все готово:**

```bash
ssh root@144.31.84.74
wget -qO- https://raw.githubusercontent.com/wrx861/market/main/deployment/install.sh | sudo bash
```

**Скрипт автоматически:**
1. ✅ Проверит что порты 8001, 3001, 27017 свободны (не трогает ваши VPN порты)
2. ✅ Установит Docker (если еще нет)
3. ✅ Запросит по очереди все API ключи:
   - Rossko API ключи (KEY1, KEY2)
   - Autotrade Email
   - Autotrade Пароль  
   - Autotrade API ключ
   - PartsAPI ключ
   - OpenAI API ключ
   - N8N Webhook (можно пропустить)
4. ✅ Создаст .env файлы автоматически
5. ✅ Установит SSL сертификат для miniapp.shopmarketbot.ru
6. ✅ Настроит Nginx
7. ✅ Запустит MongoDB, Backend, Frontend
8. ✅ Настроит автообновление SSL

**Время установки:** ~5-10 минут

**После установки:**
- Приложение: https://miniapp.shopmarketbot.ru
- Логи: `cd /opt/market-auto-parts && docker-compose logs -f`

---

## Подготовьте эти данные:

Во время установки скрипт попросит ввести:

### 1. Rossko API
```
ROSSKO_KEY1: (ваш ключ)
ROSSKO_KEY2: (ваш ключ)
```

### 2. Autotrade API
```
Email: car.workshop72@mail.ru
Пароль: Qq23321q
API ключ: d1db0fa6d842bab4186d9c6a511d04da
```

### 3. PartsAPI
```
PARTSAPI_KEY: (ваш ключ)
```

### 4. OpenAI
```
OpenAI API ключ: (ваш ключ)
```

### 5. N8N Webhook (опционально)
```
URL: (можно нажать Enter для пропуска)
```

---

## Управление после установки

### Просмотр логов
```bash
cd /opt/market-auto-parts
docker-compose logs -f
```

### Перезапуск
```bash
cd /opt/market-auto-parts
docker-compose restart
```

### Остановка
```bash
cd /opt/market-auto-parts
docker-compose down
```

### Обновление после изменений в GitHub
```bash
cd /opt/market-auto-parts
git pull https://github.com/wrx861/market.git
docker-compose up --build -d
```

---

## Проверка работы

После установки проверьте:

```bash
# Backend
curl http://localhost:8001/api/health

# Frontend  
curl http://localhost:3001

# HTTPS
curl https://miniapp.shopmarketbot.ru
```

---

## Telegram Bot настройка

1. Откройте [@BotFather](https://t.me/botfather)
2. Создайте нового бота или используйте существующего
3. Настройте Web App:
   - Команда: `/newapp`
   - Выберите бота
   - Название: Market Auto Parts
   - Описание: Поиск автозапчастей
   - Web App URL: `https://miniapp.shopmarketbot.ru`
4. Готово!

---

## 🔧 Troubleshooting

### Backend не запускается
```bash
docker logs market-auto-parts-backend
```

### Frontend ошибки
```bash
docker logs market-auto-parts-frontend
```

### MongoDB проблемы
```bash
docker logs market-auto-parts-mongodb
docker exec -it market-auto-parts-mongodb mongosh
```

### SSL не установился
Проверьте что DNS настроен:
```bash
dig +short miniapp.shopmarketbot.ru
# Должен вернуть: 144.31.84.74
```

---

## ✅ Чеклист перед запуском

- [ ] DNS запись для miniapp.shopmarketbot.ru → 144.31.84.74
- [ ] Порты 80, 443 открыты в firewall
- [ ] Подготовлены все API ключи
- [ ] Есть root доступ к серверу

---

## 📞 Если что-то пошло не так

1. Проверьте логи: `docker-compose logs`
2. Проверьте .env файлы: `cat /opt/market-auto-parts/backend/.env`
3. Проверьте DNS: `dig +short miniapp.shopmarketbot.ru`
4. Проверьте порты: `ss -tulpn | grep -E ':(8001|3001|27017)'`

---

**Все готово! Скрипт сделает все сам, вам нужно только ввести API ключи! 🚀**
