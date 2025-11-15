"""
Berg API Client
Клиент для работы с API поставщика Berg.ru
"""

import requests
import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)

class BergClient:
    """Клиент для работы с API Berg"""
    
    def __init__(self):
        self.api_key = os.getenv('BERG_API_KEY')
        self.base_url = "https://api.berg.ru/v1.0"
        
        if not self.api_key:
            logger.warning("BERG_API_KEY not found in environment variables")
    
    def search_by_article(
        self,
        article: str,
        brand_name: Optional[str] = None,
        analogs: bool = True,
        warehouse_types: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Поиск запчастей по артикулу через Berg API
        
        Args:
            article: Артикул для поиска
            brand_name: Название бренда (опционально для точного поиска)
            analogs: Искать аналоги (True/False)
            warehouse_types: Типы складов [1=филиал, 2=ЦС, 3=доп]
            
        Returns:
            Список найденных запчастей
        """
        if not self.api_key:
            logger.error("Berg API key not configured")
            return []
        
        logger.info(f"Searching Berg for article: {article}, analogs={analogs}, brand={brand_name}")
        
        try:
            # Формируем параметры запроса
            params = {
                "key": self.api_key,
                "items[0][resource_article]": article,
                "analogs": 1 if analogs else 0
            }
            
            # Добавляем бренд если указан
            if brand_name:
                params["items[0][brand_name]"] = brand_name
            
            # Добавляем фильтр по складам если указан
            if warehouse_types:
                for idx, wh_type in enumerate(warehouse_types):
                    params[f"warehouse_types[{idx}]"] = wh_type
            
            # Отправляем первый запрос
            url = f"{self.base_url}/ordering/get_stock.json"
            response = requests.get(
                url,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Проверяем наличие ошибок
            if "error" in result:
                logger.error(f"Berg API error: {result.get('error')}")
                return []
            
            # Проверяем Status 300 (WARN_ARTICLE_IS_AMBIGUOUS) - нужно указать бренд
            warnings = result.get('warnings', [])
            is_ambiguous = any(w.get('code') == 'WARN_ARTICLE_IS_AMBIGUOUS' for w in warnings)
            
            all_parts = []
            
            if is_ambiguous and not brand_name:
                # Артикул неоднозначный - делаем запросы для каждого бренда
                resources = result.get('resources', [])
                logger.info(f"Article is ambiguous, found {len(resources)} brands")
                
                for resource in resources:
                    brand = resource.get('brand', {})
                    brand_name_from_resource = brand.get('name')
                    
                    if brand_name_from_resource:
                        # Запрашиваем с конкретным брендом
                        logger.info(f"Requesting Berg for brand: {brand_name_from_resource}")
                        brand_parts = self._request_with_brand(article, brand_name_from_resource, analogs, warehouse_types)
                        all_parts.extend(brand_parts)
            else:
                # Обычный ответ - парсим сразу
                resources = result.get('resources', [])
                logger.info(f"Berg returned {len(resources)} resources")
                
                for resource in resources:
                    offers = resource.get('offers', [])
                    
                    if offers:
                        for offer in offers:
                            part = self._format_part(resource, offer)
                            if part:
                                all_parts.append(part)
                    else:
                        # Создаем базовую запись без offer (цена = 0)
                        part = self._format_part(resource, None)
                        if part:
                            all_parts.append(part)
            
            logger.info(f"Formatted {len(all_parts)} parts from Berg")
            return all_parts
            
        except requests.exceptions.Timeout:
            logger.error(f"Berg API timeout for article: {article}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Berg API request error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Berg search: {e}", exc_info=True)
            return []
    
    def _request_with_brand(self, article: str, brand_name: str, analogs: bool, warehouse_types: Optional[List[int]] = None) -> List[Dict]:
        """Запрос к Berg API с указанием конкретного бренда"""
        try:
            params = {
                "key": self.api_key,
                "items[0][resource_article]": article,
                "items[0][brand_name]": brand_name,
                "analogs": 1 if analogs else 0
            }
            
            if warehouse_types:
                for idx, wh_type in enumerate(warehouse_types):
                    params[f"warehouse_types[{idx}]"] = wh_type
            
            url = f"{self.base_url}/ordering/get_stock.json"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            parts = []
            resources = result.get('resources', [])
            
            for resource in resources:
                offers = resource.get('offers', [])
                if offers:
                    for offer in offers:
                        part = self._format_part(resource, offer)
                        if part:
                            parts.append(part)
            
            return parts
            
        except Exception as e:
            logger.error(f"Error in _request_with_brand for {brand_name}: {e}")
            return []
    
    def _format_part(self, resource: Dict, offer: Optional[Dict]) -> Optional[Dict]:
        """
        Форматирование данных о запчасти в единый формат
        
        Args:
            resource: Данные о товаре из Berg API
            offer: Данные о предложении (наличие/цена)
            
        Returns:
            Словарь с данными о запчасти или None
        """
        try:
            article = resource.get('article', '')
            if not article:
                return None
            
            brand = resource.get('brand', {})
            brand_name = brand.get('name', 'Неизвестно')
            
            # Базовая информация
            part_data = {
                'supplier': 'Berg',
                'provider': 'berg',  # Required for frontend filtering
                'article': article,
                'brand': brand_name,
                'name': resource.get('name', ''),
                'resource_id': resource.get('id'),
            }
            
            if offer:
                # Информация о наличии и цене
                warehouse = offer.get('warehouse', {})
                warehouse_name = warehouse.get('name', 'Неизвестно')
                warehouse_type = warehouse.get('type', 0)
                
                # Определяем тип склада
                warehouse_type_name = {
                    1: 'Филиал БЕРГ',
                    2: 'ЦС БЕРГ',
                    3: 'Дополнительный склад'
                }.get(warehouse_type, 'Неизвестно')
                
                quantity = int(offer.get('quantity', 0))
                delivery_days = int(offer.get('average_period', 0))
                
                part_data.update({
                    'price': float(offer.get('price', 0)),
                    'quantity': quantity,
                    'available_more': offer.get('available_more', False),
                    'reliability': float(offer.get('reliability', 0)),
                    'delivery_days': delivery_days,
                    'delivery_days_max': int(offer.get('assured_period', 0)),
                    'is_transit': offer.get('is_transit', False),
                    'warehouse': warehouse_name,
                    'warehouse_type': warehouse_type_name,
                    'multiplication_factor': int(offer.get('multiplication_factor', 1)),
                    'in_stock': quantity > 0 and delivery_days <= 1,  # Required for frontend
                })
            else:
                # Нет информации о наличии
                part_data.update({
                    'price': 0,
                    'quantity': 0,
                    'available_more': False,
                    'reliability': 0,
                    'delivery_days': 0,
                    'delivery_days_max': 0,
                    'is_transit': False,
                    'warehouse': 'Нет в наличии',
                    'warehouse_type': 'Неизвестно',
                    'multiplication_factor': 1,
                    'in_stock': False,  # Required for frontend
                })
            
            return part_data
            
        except Exception as e:
            logger.error(f"Error formatting Berg part: {e}")
            return None


# Singleton instance
_berg_client = None

def get_berg_client() -> BergClient:
    """Получить экземпляр клиента Berg"""
    global _berg_client
    if _berg_client is None:
        _berg_client = BergClient()
    return _berg_client
