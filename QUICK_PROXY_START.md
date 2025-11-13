# 🚀 Быстрый старт с Proxy

## ⚠️ Последнее предупреждение!
Использование proxy для обхода rate limiting PartsAPI - **на ваш риск**. Может привести к блокировке.

---

## Вариант 1: Бесплатные proxy (тестирование)

### Шаг 1: Найти бесплатные proxy
Откройте в браузере: https://free-proxy-list.net/

Скопируйте несколько HTTP proxy (формат: IP:PORT)

Пример:
```
123.45.67.89:8080
98.76.54.32:3128
11.22.33.44:80
```

### Шаг 2: Добавить в .env
Откройте файл `/app/backend/.env` и добавьте:

```bash
USE_PROXY=true
PROXY_LIST=http://123.45.67.89:8080,http://98.76.54.32:3128,http://11.22.33.44:80
```

### Шаг 3: Перезапустить backend
```bash
sudo supervisorctl restart backend
```

### Шаг 4: Проверить логи
```bash
tail -f /var/log/supervisor/backend.err.log
```

Должны увидеть:
```
INFO: Loaded 3 proxies from environment
INFO: ⚠️ Using proxy for request to PartsAPI
```

---

## Вариант 2: Платные proxy (production)

### Рекомендуемые сервисы:

#### 🇷🇺 Proxy-seller.ru (российский)
1. Перейдите на: https://proxy-seller.ru/
2. Купите IPv4 proxy (от 0.5$/месяц)
3. Получите данные:
   ```
   http://username:password@proxy-server.com:8080
   ```

#### 🌍 SmartProxy (международный)
1. Регистрация: https://smartproxy.com/
2. Выберите тариф (от $75/месяц)
3. Получите credentials в личном кабинете

### Добавить в .env:
```bash
USE_PROXY=true
PROXY_LIST=http://username:password@proxy1.com:8080,http://username:password@proxy2.com:8080
```

---

## Тестирование proxy

### Создайте тестовый скрипт:
```bash
cat > /app/test_proxy.py << 'EOF'
import requests

proxy = "http://123.45.67.89:8080"  # Ваш proxy

proxies = {
    'http': proxy,
    'https': proxy
}

try:
    response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
    print(f"✅ Proxy работает! Ваш IP: {response.json()}")
except Exception as e:
    print(f"❌ Proxy не работает: {e}")
EOF

python3 /app/test_proxy.py
```

---

## Проверка работы в приложении

### Тест через API:
```bash
# Получите REACT_APP_BACKEND_URL из .env
BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

# Сделайте тестовый запрос
curl -X POST "$BACKEND_URL/api/search/vin" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "vin": "XW7BF4FK60S145161"
  }'
```

Проверьте логи - должны увидеть использование proxy:
```bash
tail -n 50 /var/log/supervisor/backend.err.log | grep proxy
```

---

## Отключение proxy

Если хотите отключить:

```bash
# Откройте .env
nano /app/backend/.env

# Измените USE_PROXY на false
USE_PROXY=false

# Перезапустите backend
sudo supervisorctl restart backend
```

---

## Troubleshooting

### Proxy не работает:
```bash
# Проверьте, что proxy действительно живой
curl -x http://123.45.67.89:8080 https://httpbin.org/ip

# Попробуйте другой proxy из списка
```

### Все еще блокируют:
1. Используйте residential proxy (не datacenter)
2. Уменьшите частоту запросов
3. Увеличьте время кэширования
4. Свяжитесь с PartsAPI для корпоративного тарифа

### Ошибки в логах:
```bash
# Смотрите полные логи
tail -n 100 /var/log/supervisor/backend.err.log

# Ищите строки с ERROR или WARNING
grep -i error /var/log/supervisor/backend.err.log
```

---

## 💰 Примерные цены на proxy:

| Сервис | Тип | Цена | Количество |
|--------|-----|------|------------|
| Бесплатные | HTTP/HTTPS | $0 | Неограниченно (ненадежно) |
| Proxy-seller | IPv4 | $0.5-2/мес | 1 IP |
| SmartProxy | Residential | $75/мес | 5GB трафика |
| Bright Data | Enterprise | $500+/мес | Безлимит |

---

## 🎯 Рекомендация:

**Для тестирования:** Бесплатные proxy (1-2 дня)
**Для production:** Платные residential proxy + Корпоративный тариф PartsAPI

**Самое надежное:** Rate Limiting + Кэширование (без proxy)

---

Удачи! И помните - мы предупредили о рисках! 🙏
