# 🔌 Интеграция Berg.ru

## Обзор

Berg.ru добавлен как третий поставщик запчастей наряду с Rossko и Autotrade.

**API ключ:** `0fdaa3d7d2e65cc60f684ea6edb9f8e2a1e37ce5c7059067408a17bdb8d65e44`

---

## Возможности

### ✅ Поиск по артикулу
- Поиск по точному артикулу
- Поиск аналогов (cross/analogs)
- Фильтрация по брендам
- Информация о наличии и ценах

### ✅ Типы складов
- **Филиал БЕРГ** (type=1)
- **ЦС БЕРГ** (Центральный склад, type=2)
- **Дополнительный склад** (type=3)

### ✅ Параметры надежности
- `reliability` - показатель надежности предложения
- `average_period` - средний срок доставки
- `assured_period` - гарантированный срок доставки
- `is_transit` - товар в пути

---

## Архитектура

### Файлы

```
backend/
├── berg_client.py          # Клиент Berg API
└── server.py               # Интеграция в поиск
```

### Класс BergClient

```python
class BergClient:
    def __init__(self):
        self.api_key = os.getenv('BERG_API_KEY')
        self.base_url = "https://api.berg.ru/v1.0"
    
    def search_by_article(
        self,
        article: str,
        brand_name: Optional[str] = None,
        analogs: bool = True,
        warehouse_types: Optional[List[int]] = None
    ) -> List[Dict]:
        """Поиск запчастей по артикулу"""
```

---

## API Berg

### Endpoint

```
GET https://api.berg.ru/v1.0/ordering/get_stock.json
```

### Параметры

```python
{
    "key": "0fdaa3d7...",                          # API ключ
    "items[0][resource_article]": "A2761800009",   # Артикул
    "items[0][brand_name]": "MERCEDES-BENZ",       # Бренд (опционально)
    "analogs": 1,                                  # 1=с аналогами, 0=только точные
    "warehouse_types[0]": 1,                       # Тип склада (опционально)
    "warehouse_types[1]": 2,
}
```

### Ответ

```json
{
  "resources": [
    {
      "id": 123456,
      "article": "A2761800009",
      "name": "Фильтр масляный",
      "brand": {
        "id": 789,
        "name": "MERCEDES-BENZ"
      },
      "offers": [
        {
          "price": 1250.50,
          "quantity": 5,
          "available_more": true,
          "reliability": 95.5,
          "average_period": 1,
          "assured_period": 2,
          "is_transit": false,
          "multiplication_factor": 1,
          "warehouse": {
            "id": 1,
            "name": "Тюмень",
            "type": 1
          }
        }
      ]
    }
  ]
}
```

---

## Интеграция в поиск

### Параллельный поиск

Поиск Berg запускается параллельно с Rossko и Autotrade:

```python
# server.py
async def search_article(request: SearchArticleRequest):
    # Запускаем все три поиска параллельно
    rossko_parts, autotrade_parts, berg_parts = await asyncio.gather(
        search_rossko(),
        search_autotrade(),
        search_berg(),
        return_exceptions=True
    )
    
    # Объединяем результаты
    all_parts = rossko_parts + autotrade_parts + berg_parts
```

### Дедупликация

Одинаковые артикулы от разных поставщиков автоматически объединяются:

```python
def deduplicate_parts(parts):
    """Дедупликация по артикулу + бренд + цена"""
    seen = set()
    unique_parts = []
    
    for part in parts:
        # Нормализуем артикул
        article = part['article'].upper().replace(' ', '').replace('-', '')
        brand = part['brand'].upper()
        price = round(part['price'], 2)
        
        key = (article, brand, price)
        if key not in seen:
            seen.add(key)
            unique_parts.append(part)
    
    return unique_parts
```

---

## Формат данных

### Унифицированный формат

Berg возвращает данные в том же формате что Rossko и Autotrade:

```python
{
    'supplier': 'Berg',
    'article': 'A2761800009',
    'brand': 'MERCEDES-BENZ',
    'name': 'Фильтр масляный',
    'price': 1250.50,
    'quantity': 5,
    'available_more': True,
    'delivery_days': 1,
    'delivery_days_max': 2,
    'warehouse': 'Тюмень',
    'warehouse_type': 'Филиал БЕРГ',
    'reliability': 95.5,
    'is_transit': False,
    'multiplication_factor': 1,
    'resource_id': 123456
}
```

### Специфичные поля Berg

- `reliability` - процент надежности (0-100)
- `average_period` - средний срок поставки
- `assured_period` - гарантированный срок
- `multiplication_factor` - минимальная кратность заказа
- `warehouse_type` - тип склада (Филиал/ЦС/Доп)
- `is_transit` - товар в транзите

---

## Настройка

### Переменные окружения

Добавьте в `backend/.env`:

```bash
BERG_API_KEY=0fdaa3d7d2e65cc60f684ea6edb9f8e2a1e37ce5c7059067408a17bdb8d65e44
```

### Установочные скрипты

Все три установочных скрипта обновлены для запроса Berg API ключа:

- `deployment/install-with-git.sh`
- `deployment/install-existing-server.sh`
- `deployment/install-clean-server.sh`

При установке скрипт спросит:

```
Berg API (поставщик запчастей)
Введите BERG_API_KEY: [вставьте ключ]
```

---

## Логирование

Berg клиент логирует все операции:

```python
logger.info(f"Searching Berg for article: {article}, analogs={analogs}")
logger.info(f"Berg returned {len(resources)} resources")
logger.info(f"Formatted {len(parts)} parts from Berg")
logger.error(f"Berg API error: {error_message}")
```

Проверка логов:

```bash
docker-compose logs backend | grep Berg
# Должно показать:
# Searching Berg for article: A2761800009, analogs=True
# Berg returned 5 resources
# Formatted 12 parts from Berg
```

---

## Тестирование

### 1. Проверка API напрямую

```bash
curl "https://api.berg.ru/v1.0/ordering/get_stock.json?key=0fdaa3d7...&items[0][resource_article]=A2761800009&analogs=1"
```

### 2. Проверка через наше API

```bash
curl "https://miniapp.shopmarketbot.ru/api/search/article?q=A2761800009"
```

Должны увидеть результаты от трех поставщиков:
- `"supplier": "Rossko"`
- `"supplier": "Autotrade"`
- `"supplier": "Berg"` ✨

### 3. Проверка в приложении

1. Откройте https://miniapp.shopmarketbot.ru
2. Перейдите в поиск по артикулу
3. Введите: `A2761800009`
4. Должны показаться результаты от Berg с пометкой "Berg"

---

## Приоритизация результатов

### Сортировка

Результаты сортируются по приоритету:

1. **Локальные склады** (Тюмень)
2. **Цена** (от меньшей к большей)
3. **Срок доставки** (от быстрого к медленному)
4. **Наличие** (в наличии → под заказ)

### Логика приоритета для Berg

```python
def get_priority(part):
    priority = 0
    
    # Локальный склад Тюмень
    if 'тюмень' in part['warehouse'].lower():
        priority += 1000
    
    # Филиал БЕРГ (type=1) выше чем ЦС
    if part['warehouse_type'] == 'Филиал БЕРГ':
        priority += 100
    
    # Высокая надежность
    if part.get('reliability', 0) > 90:
        priority += 50
    
    # В наличии
    if part['quantity'] > 0:
        priority += 500
    
    return priority
```

---

## Обработка ошибок

### Таймауты

```python
try:
    response = requests.get(url, params=params, timeout=10)
except requests.exceptions.Timeout:
    logger.error(f"Berg API timeout for article: {article}")
    return []
```

### API ошибки

```python
result = response.json()
if "error" in result:
    logger.error(f"Berg API error: {result.get('error')}")
    return []
```

### Graceful degradation

Если Berg недоступен, поиск продолжает работать с Rossko и Autotrade:

```python
if isinstance(berg_parts, Exception):
    logger.error(f"Berg search failed: {str(berg_parts)}")
    berg_parts = []  # Просто пустой список
```

---

## Особенности Berg API

### 1. Множитель заказа (multiplication_factor)

Некоторые товары можно заказать только кратно определенному числу:

```python
if part['multiplication_factor'] > 1:
    # Показываем пользователю
    quantity_text = f"Кратность: {part['multiplication_factor']}"
```

### 2. Надежность (reliability)

Показатель того, насколько вероятна поставка:

- **95-100%** - очень надежно ✅
- **80-95%** - надежно ⚠️
- **<80%** - менее надежно ❌

### 3. Доступно больше (available_more)

Если `available_more=True`, можно заказать больше чем `quantity`:

```python
if part['available_more']:
    quantity_text = f"{part['quantity']}+ шт"
else:
    quantity_text = f"{part['quantity']} шт"
```

---

## Обновление на сервере

После добавления Berg в код, обновите на сервере:

```bash
cd /opt/market-auto-parts

# Получить изменения
git pull origin main

# Обновить .env
echo "BERG_API_KEY=0fdaa3d7d2e65cc60f684ea6edb9f8e2a1e37ce5c7059067408a17bdb8d65e44" >> backend/.env

# Пересобрать backend
docker-compose stop backend
docker-compose build --no-cache backend
docker-compose up -d backend

# Проверить
docker-compose logs -f backend | grep Berg
```

---

## FAQ

**Q: Почему Berg может не вернуть результаты?**

A: Возможные причины:
- Артикул не найден в базе Berg
- API ключ неверный
- Timeout сервера
- Артикул есть но нет в наличии

**Q: Как отключить Berg если нужно?**

A: Закомментируйте в `server.py`:
```python
# berg_parts = []  # Отключить Berg
rossko_parts, autotrade_parts = await asyncio.gather(...)
all_parts = rossko_parts + autotrade_parts  # Без berg_parts
```

**Q: Можно ли искать только на определенных складах?**

A: Да, используйте `warehouse_types`:
```python
berg_client.search_by_article(
    article="A2761800009",
    warehouse_types=[1, 2]  # Только филиалы и ЦС
)
```

---

**Версия:** 2.4  
**Дата:** 2025-11-14  
**Статус:** ✅ Готово к продакшену
