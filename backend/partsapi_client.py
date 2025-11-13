import requests
import logging
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from cache_manager import CacheManager
from rate_limiter import RateLimiter
from proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

class PartsApiClient:
    """
    Клиент для работы с API partsapi.ru
    Документация: https://api.partsapi.ru
    
    Основной метод API: getPartsbyVIN
    Возвращает список оригинальных и/или неоригинальных запчастей по VIN и категории
    """
    
    def __init__(self):
        load_dotenv()
        self.base_url = "https://api.partsapi.ru"
        self.api_key = os.environ.get('PARTSAPI_KEY', '')
        
        # Инициализируем кэш-менеджер (кэш на 1 час)
        self.cache = CacheManager(ttl=3600)
        
        # Инициализируем rate limiter (максимум 10 запросов в минуту)
        self.rate_limiter = RateLimiter(max_requests=10, time_window=60)
        
        # ⚠️ Инициализируем proxy manager (использовать на свой риск!)
        self.proxy_manager = ProxyManager()
        
        # Основные категории запчастей для быстрого поиска
        self.category_keywords = {
            'масло': ['7', '3353'],  # Масляный фильтр
            'фильтр масляный': ['7'],
            'фильтр воздушный': ['8'],
            'фильтр топливный': ['9'],
            'тормоз': ['70', '78', '82', '83', '281'],  
            'колодки': ['70', '281'],  # Тормозные колодки
            'диск тормозной': ['82'],
            'суппорт': ['78'],
            'амортизатор': ['198'],
            'стойка': ['198', '274'],
            'свеча': ['243'],
            'аккумулятор': ['1'],
            'ремень': ['10', '305', '306'],
            'подшипник': ['48'],
            'шаровая': ['176'],
        }
        
        if not self.api_key:
            logger.warning("PARTSAPI_KEY not found in environment variables")
    
    def get_parts_by_vin_and_category(self, vin: str, category_id: str, parts_type: str = "oem") -> List[Dict]:
        """
        Получение списка запчастей по VIN и категории с кэшированием и rate limiting
        
        Args:
            vin: VIN номер автомобиля
            category_id: ID категории запчастей (из справочника категорий)
            parts_type: Тип запчастей ("oem" для оригинальных, пустая строка для всех)
            
        Returns:
            Список запчастей с информацией
        """
        try:
            # Проверяем кэш
            cached_data = self.cache.get(vin, category_id, parts_type)
            if cached_data is not None:
                logger.info(f"Using cached data for VIN: {vin}, category: {category_id}")
                return cached_data
            
            # Проверяем rate limit
            if not self.rate_limiter.wait_if_needed(key="partsapi", timeout=30):
                logger.error("Rate limit timeout - too many requests")
                return []
            
            params = {
                'method': 'getPartsbyVIN',
                'key': self.api_key,
                'vin': vin,
                'cat': category_id
            }
            
            # Добавляем type только если нужны оригинальные
            if parts_type == "oem":
                params['type'] = 'oem'
            
            remaining = self.rate_limiter.get_remaining_requests("partsapi")
            logger.info(
                f"Getting parts for VIN: {vin}, category: {category_id}, type: {parts_type} "
                f"(Remaining requests: {remaining})"
            )
            
            # Получаем proxy если включено
            proxies = self.proxy_manager.get_proxy()
            
            if proxies:
                logger.info(f"⚠️ Using proxy for request to PartsAPI")
            
            response = requests.get(
                self.base_url, 
                params=params, 
                proxies=proxies,
                timeout=15
            )
            
            # Проверяем статус ответа
            if response.status_code == 401:
                logger.error(f"API key unauthorized (401)")
                return []
            
            if response.status_code == 429:
                logger.error(f"Too many requests (429) - rate limited by API")
                return []
            
            if response.status_code != 200:
                logger.error(f"API returned status {response.status_code}")
                return []
            
            data = response.json()
            
            if not isinstance(data, list):
                logger.error(f"Unexpected response format: {type(data)}")
                return []
            
            # Сохраняем в кэш
            self.cache.set(vin, category_id, data, parts_type)
            
            logger.info(f"Found {len(data)} parts for category {category_id}")
            return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting parts: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return []
    
    def parse_parts_response(self, raw_parts: List[Dict]) -> List[Dict]:
        """
        Парсит ответ от PartsAPI и извлекает артикулы из поля 'parts'
        Формат поля parts: "BRAND|ARTICLE,BRAND|ARTICLE,..."
        
        Args:
            raw_parts: Сырые данные от API
            
        Returns:
            Список запчастей с извлеченными артикулами и брендами
        """
        parsed_parts = []
        
        for part_group in raw_parts:
            parts_string = part_group.get('parts', '')
            name = part_group.get('name', 'Unknown')
            group = part_group.get('group', 'Unknown')
            
            if not parts_string:
                continue
            
            # Разбираем строку с артикулами: "BRAND|ARTICLE,BRAND|ARTICLE"
            parts_list = parts_string.split(',')
            
            for part_str in parts_list[:10]:  # Ограничиваем 10 артикулами на группу
                part_str = part_str.strip()
                if '|' in part_str:
                    brand, article = part_str.split('|', 1)
                    parsed_parts.append({
                        'article': article,
                        'brand': brand,
                        'name': name,
                        'group': group,
                        'source': 'partsapi'
                    })
        
        logger.info(f"Parsed {len(parsed_parts)} individual parts from {len(raw_parts)} groups")
        return parsed_parts
    
    def search_parts_by_query(self, vin: str, query: str, parts_type: str = "oem") -> List[Dict]:
        """
        Поиск запчастей по текстовому запросу
        Автоматически определяет подходящие категории и ищет в них
        
        Args:
            vin: VIN номер автомобиля
            query: Поисковый запрос (например, "масляный фильтр", "тормозные колодки")
            parts_type: Тип запчастей
            
        Returns:
            Список найденных запчастей с распарсенными артикулами
        """
        try:
            query_lower = query.lower()
            
            # Определяем подходящие категории
            categories = []
            for keyword, cat_ids in self.category_keywords.items():
                if keyword in query_lower:
                    categories.extend(cat_ids)
            
            # Если не нашли подходящих категорий, используем базовые
            if not categories:
                logger.info(f"No specific categories found for query '{query}', using common categories")
                # Используем самые популярные категории
                categories = ['7', '8', '9', '70', '82', '198']  # Фильтры, тормоза, амортизаторы
            
            # Убираем дубликаты
            categories = list(set(categories))
            logger.info(f"Searching in {len(categories)} categories: {categories}")
            
            all_raw_parts = []
            for category_id in categories[:10]:  # Ограничиваем 10 категориями
                raw_parts = self.get_parts_by_vin_and_category(vin, category_id, parts_type)
                if raw_parts:
                    all_raw_parts.extend(raw_parts)
            
            # Парсим артикулы из ответа
            parsed_parts = self.parse_parts_response(all_raw_parts)
            
            logger.info(f"Total parts found: {len(parsed_parts)}")
            return parsed_parts
            
        except Exception as e:
            logger.error(f"Error searching parts: {str(e)}")
            return []
    
    def get_car_info_by_vin(self, vin: str) -> Optional[Dict]:
        """
        Получение информации об автомобиле по VIN
        
        Используем рабочую категорию для проверки VIN
        
        Args:
            vin: VIN номер автомобиля
            
        Returns:
            Информация об автомобиле или None
        """
        try:
            # Пробуем несколько популярных категорий для проверки VIN
            test_categories = ['1191', '7', '8', '70', '82']  # Кузов, фильтры, тормоза
            
            for category in test_categories:
                logger.info(f"Testing VIN {vin} with category {category}")
                test_parts = self.get_parts_by_vin_and_category(vin, category, 'oem')
                
                if test_parts and len(test_parts) > 0:
                    # Если получили данные, значит VIN валиден
                    logger.info(f"VIN {vin} is valid, found {len(test_parts)} parts in category {category}")
                    
                    # Извлекаем информацию об автомобиле из первой запчасти
                    first_part = test_parts[0]
                    
                    # Возвращаем информацию об автомобиле
                    return {
                        'vin': vin,
                        'make': 'Unknown',  # PartsAPI не возвращает марку напрямую
                        'model': 'Unknown',  # PartsAPI не возвращает модель напрямую  
                        'year': 'Unknown',   # PartsAPI не возвращает год напрямую
                        'status': 'valid',
                        'parts_available': True,
                        'test_category': category,
                        'parts_found': len(test_parts),
                        'sample_part': first_part.get('name', 'Unknown')
                    }
            
            logger.warning(f"No data found for VIN: {vin} in any test category")
            return None
                
        except Exception as e:
            logger.error(f"Error getting car info: {str(e)}")
            return None
    
    def get_catalog_groups(self, vin: str) -> List[Dict]:
        """
        Возвращает список основных групп каталога запчастей
        
        Args:
            vin: VIN номер автомобиля
            
        Returns:
            Список групп каталога
        """
        # Возвращаем основные группы из нашего справочника
        basic_groups = [
            {"id": "1", "name": "Система стартера (Аккумулятор)"},
            {"id": "2", "name": "Стартер"},
            {"id": "4", "name": "Генератор"},
            {"id": "7", "name": "Масляный фильтр"},
            {"id": "8", "name": "Воздушный фильтр"},
            {"id": "9", "name": "Топливный фильтр"},
            {"id": "10", "name": "Клиновой ремень"},
            {"id": "48", "name": "Выжимной подшипник"},
            {"id": "70", "name": "Комплект тормозных колодок"},
            {"id": "78", "name": "Тормозной суппорт"},
            {"id": "82", "name": "Тормозной диск"},
            {"id": "83", "name": "Тормозной шланг"},
            {"id": "176", "name": "Болт с шаровой головкой"},
            {"id": "198", "name": "Стойка амортизатора"},
            {"id": "243", "name": "Свеча накаливания"},
            {"id": "274", "name": "Рычаг независимой подвески колеса"},
            {"id": "281", "name": "Тормозные колодки"},
            {"id": "305", "name": "Поликлиновой ремень"},
            {"id": "306", "name": "Ремень ГРМ"},
            {"id": "307", "name": "Комплект ремня ГРМ"}
        ]
        
        logger.info(f"Returning {len(basic_groups)} catalog groups for VIN: {vin}")
        return basic_groups
    
    def get_full_catalog_text(self, vin: str) -> str:
        """
        Генерирует текстовое представление каталога для AI анализа
        Получает запчасти из основных категорий и извлекает артикулы
        
        Args:
            vin: VIN номер автомобиля
            
        Returns:
            Текстовое представление каталога с артикулами
        """
        try:
            catalog_text = f"Каталог запчастей для VIN: {vin}\n\n"
            
            # Используем рабочие категории для каталога
            working_categories = ['7', '8', '9', '70', '82', '198', '1191']
            category_names = {
                '7': 'Масляный фильтр',
                '8': 'Воздушный фильтр',
                '9': 'Топливный фильтр',
                '70': 'Тормозные колодки',
                '82': 'Тормозной диск',
                '198': 'Стойка амортизатора',
                '1191': 'Кузовные детали'
            }
            
            for category_id in working_categories:
                category_name = category_names.get(category_id, 'Unknown')
                
                catalog_text += f"\nГруппа: {category_name} (ID: {category_id})\n"
                
                # Получаем запчасти в группе
                raw_parts = self.get_parts_by_vin_and_category(vin, category_id, 'oem')
                
                if not raw_parts:
                    catalog_text += "  (нет данных)\n"
                    continue
                
                # Парсим артикулы
                for part_group in raw_parts[:3]:  # Ограничиваем 3 группами на категорию
                    part_name = part_group.get('name', 'Unknown')
                    parts_string = part_group.get('parts', '')
                    
                    if not parts_string:
                        continue
                    
                    # Извлекаем первые несколько артикулов
                    parts_list = parts_string.split(',')[:5]  # Первые 5 артикулов
                    
                    catalog_text += f"  - {part_name}:\n"
                    for part_str in parts_list:
                        part_str = part_str.strip()
                        if '|' in part_str:
                            brand, article = part_str.split('|', 1)
                            catalog_text += f"    * {brand} {article}\n"
            
            logger.info(f"Generated catalog text with {len(catalog_text)} characters")
            return catalog_text
            
        except Exception as e:
            logger.error(f"Error generating catalog text: {str(e)}")
            return ""
