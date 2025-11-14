# 🔔 Система уведомлений

## Архитектура (без n8n)

Уведомления отправляются **напрямую через Telegram Bot API** - просто и надежно!

```
Пользователь создает заказ
         ↓
    Backend API
         ↓
   Сохранение в MongoDB
         ↓
Telegram Bot API → Админ получает уведомление
```

## 📱 Что получает админ

При каждом новом заказе админ получает сообщение в Telegram:

```
🆕 НОВЫЙ ЗАКАЗ №abc12345

💰 Сумма: 3,000 ₽

👤 Клиент: Иван Иванов
📞 Телефон: +79001234567
📍 Адрес: г. Москва, ул. Ленина, д. 1

📦 Товары:
1. Шаровая опора (VAG)
   Артикул: 1K0505435Q
   Цена: 1,500 ₽ × 2 шт. = 3,000 ₽

🆔 Telegram ID: 123456789
⏰ Дата: 10.11.2025 19:00
```

## ⚙️ Настройка

### 1. Получите Telegram Admin ID

Отправьте `/start` боту [@userinfobot](https://t.me/userinfobot) - он покажет ваш ID.

### 2. Обновите .env файл

```bash
TELEGRAM_ADMIN_ID=ваш_telegram_id
```

### 3. Перезапустите backend

```bash
sudo supervisorctl restart backend
```

## 🧪 Тестирование

### Создайте тестовый заказ:

```bash
curl -X POST https://partfinder-app-1.preview.emergentagent.com/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "user_info": {
      "name": "Test User",
      "phone": "+79001234567",
      "address": "Москва, ул. Ленина, д. 1"
    }
  }'
```

**Результат:** Админ получит уведомление в Telegram.

## 📊 Что отправляется

Backend отправляет POST запрос к Telegram Bot API:

```bash
POST https://api.telegram.org/bot<TOKEN>/sendMessage
{
  "chat_id": "508352361",
  "text": "🆕 НОВЫЙ ЗАКАЗ...",
  "parse_mode": "HTML"
}
```

## 🔧 Кастомизация

### Изменить формат сообщения

Отредактируйте `/app/backend/n8n_client.py`:

```python
message = f"""🆕 <b>НОВЫЙ ЗАКАЗ №{order_data.get('order_id', '')[:8]}</b>

💰 <b>Сумма: {order_data.get('total', 0):,} ₽</b>
...
"""
```

### Отправлять уведомления нескольким админам

```python
admin_ids = [508352361, 123456789, 987654321]

for admin_id in admin_ids:
    telegram_notifier.send_message_to_user(admin_id, message)
```

### Добавить кнопки (Inline Keyboard)

```python
response = requests.post(
    f"{self.api_url}/sendMessage",
    json={
        "chat_id": self.admin_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ Принять", "callback_data": f"accept_{order_id}"},
                {"text": "❌ Отменить", "callback_data": f"cancel_{order_id}"}
            ]]
        }
    }
)
```

## 🚀 Расширения (опционально)

### 1. Уведомления клиенту

Отправка статуса заказа клиенту:

```python
# В server.py после создания заказа
telegram_notifier.send_message_to_user(
    telegram_id=request.telegram_id,
    message="✅ Ваш заказ принят! Мы свяжемся с вами в ближайшее время."
)
```

### 2. Обновление статуса заказа

Создайте endpoint для обновления статуса:

```python
@api_router.post("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    # Обновить в БД
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"status": status}}
    )
    
    # Уведомить клиента
    order = await db.orders.find_one({"id": order_id})
    if order:
        status_text = {
            "processing": "⏳ В обработке",
            "shipped": "📦 Отправлен",
            "completed": "✅ Выполнен"
        }
        telegram_notifier.send_message_to_user(
            telegram_id=order['telegram_id'],
            message=f"Статус вашего заказа изменен: {status_text.get(status)}"
        )
```

### 3. Ежедневный отчет

Добавьте в cron (опционально):

```python
# daily_report.py
async def send_daily_report():
    today_orders = await db.orders.find({
        "created_at": {"$gte": datetime.now().replace(hour=0, minute=0)}
    }).to_list(1000)
    
    total = sum(o['total'] for o in today_orders)
    
    message = f"""📊 <b>ОТЧЕТ ЗА СЕГОДНЯ</b>

Заказов: {len(today_orders)}
Сумма: {total:,} ₽"""
    
    telegram_notifier.send_message_to_user(508352361, message)
```

## ❓ FAQ

**Q: Админ не получает уведомления?**
- Проверьте `TELEGRAM_ADMIN_ID` в `.env`
- Убедитесь, что админ написал `/start` боту
- Проверьте логи: `tail -f /var/log/supervisor/backend.err.log`

**Q: Как добавить второго админа?**
- Измените код в `n8n_client.py` на отправку списку админов

**Q: Можно ли отправлять в группу?**
- Да! Добавьте бота в группу, сделайте админом
- Получите Group ID через [@userinfobot](https://t.me/userinfobot)
- Используйте Group ID вместо Admin ID

**Q: Форматирование не работает?**
- Используйте HTML теги: `<b>`, `<i>`, `<code>`
- Убедитесь, что `parse_mode: "HTML"` установлен

## 🔍 Отладка

```bash
# Проверка логов
tail -f /var/log/supervisor/backend.err.log | grep "notification"

# Тест отправки напрямую
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "508352361",
    "text": "Test notification"
  }'
```

---

**Просто и без лишних инструментов! 🚀**
