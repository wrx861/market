"""
Autotrade API Client
Клиент для работы с API autotrade.su для поиска автозапчастей
"""

import os
import hashlib
import requests
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)


class AutotradeClient:
    """Клиент для работы с Autotrade API"""
    
    def __init__(self):
        self.api_url = os.environ.get('AUTOTRADE_API_URL', 'https://api2.autotrade.su/?json')
        self.login = os.environ.get('AUTOTRADE_LOGIN', '')
        self.password = os.environ.get('AUTOTRADE_PASSWORD', '')
        self.api_key = os.environ.get('AUTOTRADE_API_KEY', '')
        self.salt = "1>6)/MI~{J"  # SALT из документации
        
        # API ключ из .env И ЕСТЬ auth_key (MD5 хеш уже сгенерирован на стороне Autotrade)
        # Не нужно генерировать MD5 повторно
        if self.api_key and len(self.api_key) == 32:
            # Если есть API ключ и он похож на MD5 хеш (32 символа) - используем его напрямую
            self.auth_key = self.api_key
            logger.info("Using provided API key as auth_key")
        else:
            # Иначе генерируем через MD5
            self.auth_key = self._generate_auth_key()
            logger.info("Generated auth_key via MD5")
        
    def _generate_auth_key(self) -> str:
        """
        Генерация auth_key по формуле: MD5(login + MD5(password) + SALT)
        """
        try:
            password_hash = hashlib.md5(self.password.encode('utf-8')).hexdigest()
            combined = f"{self.login}{password_hash}{self.salt}"
            auth_key = hashlib.md5(combined.encode('utf-8')).hexdigest()
            logger.info(f"Generated auth_key for Autotrade")
            return auth_key
        except Exception as e:
            logger.error(f"Error generating auth_key: {e}")
            return ""
    
    def search_by_article(
        self,
        article: str,
        with_stocks_and_prices: bool = True,
        with_delivery: bool = True,
        cross: bool = True,
        replace: bool = False,
        strict: bool = False,
        limit: int = 100
    ) -> List[Dict]:
        """
        Поиск запчастей по артикулу через метод getItemsByQuery
        
        Args:
            article: Артикул для поиска
            with_stocks_and_prices: Получить информацию о наличии и ценах
            with_delivery: Получить информацию о сроках доставки
            cross: Искать по кроссам (аналогам) - TRUE для показа аналогов
            replace: Искать по заменам
            strict: Точный поиск (0 = с аналогами, 1 = только точное совпадение)
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных запчастей
        """
        logger.info(f"Searching Autotrade for article: {article}, strict={strict}, cross={cross}, replace={replace}")
        
        try:
            # Формируем параметры запроса
            params = {
                "q": article,
                "strict": 1 if strict else 0,  # Точный поиск по артикулу
                "page": 1,
                "limit": limit,
                "cross": 1 if cross else 0,
                "replace": 1 if replace else 0,
                "discount": 1,
                "related": 1,
                "component": 1,
                "with_stocks_and_prices": 1 if with_stocks_and_prices else 0,
                "with_delivery": 1 if with_delivery else 0,
                "check_transit": 0
            }
            
            # Формируем JSON запрос
            request_data = {
                "auth_key": self.auth_key,
                "method": "getItemsByQuery",
                "params": params
            }
            
            # Важно: добавляем префикс "data=" согласно документации
            payload = {
                "data": json.dumps(request_data, ensure_ascii=False)
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }
            
            logger.info(f"Sending request to Autotrade API: {self.api_url}")
            
            response = requests.post(
                self.api_url,
                data=payload,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"Autotrade API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Autotrade API error: status {response.status_code}, body: {response.text[:500]}")
                return []
            
            result = response.json()
            
            # Проверяем код ответа
            if result.get('code') != 0:
                logger.error(f"Autotrade API error: code {result.get('code')}, message: {result.get('message')}")
                return []
            
            # Парсим результаты
            items = result.get('items', [])
            logger.info(f"Autotrade returned {len(items)} items")
            
            # Нормализуем артикул для сравнения (убираем пробелы, переводим в верхний регистр)
            search_article_normalized = article.replace(' ', '').replace('-', '').upper()
            
            # Преобразуем в единый формат
            parts = []
            for item in items:
                # Фильтрация по точному совпадению артикула (если strict=True)
                if strict:
                    item_article = item.get('article', '')
                    item_article_normalized = item_article.replace(' ', '').replace('-', '').upper()
                    
                    # Пропускаем если артикул не совпадает точно
                    if item_article_normalized != search_article_normalized:
                        logger.debug(f"Skipping item with non-matching article: {item_article} vs {article}")
                        continue
                
                # Получаем информацию о складах (stocks, не stocks_and_prices!)
                stocks_info = item.get('stocks', {})
                
                # Если есть информация о складах, создаем записи для каждого склада
                if with_stocks_and_prices and stocks_info:
                    for stock_id, stock in stocks_info.items():
                        part = self._format_part(item, stock)
                        if part:
                            parts.append(part)
                else:
                    # Если нет информации о складах, создаем базовую запись
                    part = self._format_part(item, None)
                    if part:
                        parts.append(part)
            
            logger.info(f"Formatted {len(parts)} parts from Autotrade (after filtering)")
            return parts
            
        except requests.exceptions.Timeout:
            logger.error(f"Autotrade API timeout for article: {article}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Autotrade API request error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Autotrade search: {e}", exc_info=True)
            return []
    
    def _format_part(self, item: Dict, stock: Optional[Dict]) -> Optional[Dict]:
        """
        Форматирование данных запчасти в единый формат
        
        Args:
            item: Данные о запчасти от API
            stock: Информация о складе (может быть None)
            
        Returns:
            Отформатированная запчасть или None
        """
        try:
            # Базовая информация о запчасти
            article = item.get('article', '')
            brand = item.get('brand_name', '')
            name = item.get('name', '')
            
            if not article or not brand:
                return None
            
            # Цена берется с верхнего уровня item
            price = float(item.get('price', 0))
            
            # Информация о складе
            if stock:
                # Количество распакованное + упакованное
                quantity = int(stock.get('quantity_unpacked', 0)) + int(stock.get('quantity_packed', 0))
                warehouse = stock.get('name', 'Неизвестно')
                delivery_days = int(stock.get('delivery_period', 0))
            else:
                quantity = 0
                warehouse = 'Неизвестно'
                delivery_days = 0
            
            # Если количество = 0, не показываем эту запись
            # (товара нет на этом складе)
            if quantity == 0:
                return None
            
            # Определяем статус наличия: есть количество и быстрая доставка (0-1 день)
            # delivery_period = 1 означает что склад закрыт сейчас, откроется завтра
            # Для складов Тюмени это считается "в наличии"
            is_tyumen = 'тюмень' in warehouse.lower()
            in_stock = quantity > 0 and (delivery_days <= 1 if is_tyumen else delivery_days == 0)
            
            return {
                'article': article,
                'brand': brand,
                'name': name,
                'price': price,
                'quantity': quantity,
                'warehouse': warehouse,
                'delivery_days': delivery_days,
                'in_stock': in_stock,
                'provider': 'autotrade',
                'availability': 'В наличии' if in_stock else 'Под заказ'
            }
            
        except Exception as e:
            logger.error(f"Error formatting part from Autotrade: {e}")
            return None


# Singleton instance
autotrade_client = AutotradeClient()


if __name__ == "__main__":
    # Тестирование клиента
    logging.basicConfig(level=logging.INFO)
    
    client = AutotradeClient()
    print(f"Auth key: {client.auth_key}")
    
    # Тест поиска
    results = client.search_by_article("51750A6000")
    print(f"Found {len(results)} parts")
    
    if results:
        print("\nПервая запчасть:")
        print(json.dumps(results[0], indent=2, ensure_ascii=False))
