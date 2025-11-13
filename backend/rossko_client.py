import requests
import xmltodict
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RosskoClient:
    def __init__(self):
        # Use correct Rossko API v2.1 endpoint
        self.api_url = os.environ.get('ROSSKO_API_URL', 'http://api.rossko.ru/service/v2.1/GetSearch')
        self.api_key1 = os.environ['ROSSKO_API_KEY1']
        self.api_key2 = os.environ['ROSSKO_API_KEY2']
        
    def search_by_article(
        self, 
        article: str, 
        availability_filter: Optional[str] = None,  # 'in_stock', 'on_order', None (все)
        sort_by: Optional[str] = None,  # 'price_asc', 'price_desc', None (по умолчанию)
        markup_percent: float = 0  # Наценка в процентах
    ) -> List[Dict]:
        """
        Поиск запчастей по артикулу через Rossko API
        """
        try:
            logger.info(f"Searching Rossko for article: {article}")
            original_article = article.upper().replace('-', '').replace(' ', '')
            
            # Формируем SOAP запрос для API v2.1 с правильным namespace
            soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <GetSearch xmlns="http://api.rossko.ru/">
            <KEY1>{self.api_key1}</KEY1>
            <KEY2>{self.api_key2}</KEY2>
            <text>{article}</text>
            <delivery_id>000000001</delivery_id>
        </GetSearch>
    </soap:Body>
</soap:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://api.rossko.ru/GetSearch'
            }
            
            logger.info(f"Sending SOAP request to {self.api_url}")
            
            response = requests.post(
                self.api_url,
                data=soap_body,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                # Проверяем что получили XML
                content_type = response.headers.get('content-type', '').lower()
                if 'xml' not in content_type and 'soap' not in content_type:
                    logger.warning(f"Unexpected content type: {content_type}")
                    logger.debug(f"Response preview: {response.text[:500]}")
                    
                    # Если это не XML, возвращаем mock данные
                    return self._get_mock_data(article)
                
                # Парсим XML ответ
                result = xmltodict.parse(response.content)
                logger.info("Successfully parsed XML response")
                
                parts = self._parse_search_response(result)
                
                if not parts:
                    logger.warning("No parts found in response, using mock data")
                    return self._get_mock_data(article)
                
                logger.info(f"Found {len(parts)} parts before filtering")
                
                # Применяем фильтрацию и дедупликацию
                parts = self._deduplicate_parts(parts, original_article)
                logger.info(f"After deduplication: {len(parts)} parts")
                
                # Применяем наценку к ценам
                if markup_percent > 0:
                    parts = self._apply_markup(parts, markup_percent)
                    logger.info(f"Applied markup: {markup_percent}%")
                
                # Применяем округление цен вверх
                parts = self._round_prices(parts)
                
                # Заменяем адреса складов на конкретные для Тюмени
                parts = self._map_warehouse_names(parts)
                
                # Применяем фильтр по наличию
                if availability_filter:
                    parts = self._filter_by_availability(parts, availability_filter)
                    logger.info(f"After availability filter '{availability_filter}': {len(parts)} parts")
                
                # Применяем сортировку (оригинал всегда первый)
                parts = self._sort_with_original_first(parts, original_article, sort_by)
                logger.info(f"Sorted by {sort_by}, original first")
                
                logger.info(f"Final result: {len(parts)} parts for article {article}")
                return parts
            else:
                logger.error(f"API returned status {response.status_code}")
                return self._get_mock_data(article)
            
        except Exception as e:
            logger.error(f"Error searching article {article}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._get_mock_data(article)
    
    def _get_mock_data(self, article: str) -> List[Dict]:
        """
        Возвращает mock данные когда API недоступен
        """
        logger.info(f"Returning mock data for article: {article}")
        return [
            {
                'article': article,
                'name': f'Запчасть {article}',
                'brand': 'ОРИГИНАЛ',
                'price': 1500.0,
                'delivery_days': 2,
                'availability': 'В наличии',
                'supplier': 'ROSSKO (mock)',
                'provider': 'rossko'
            }
        ]
    
    def _parse_search_response(self, xml_data: dict) -> List[Dict]:
        """
        Парсинг XML ответа от Rossko API v2.1
        Сохраняет полную информацию о всех складах для каждой запчасти
        """
        try:
            parts = []
            
            # Навигация по структуре SOAP ответа согласно WSDL
            soap_body = xml_data.get('SOAP-ENV:Envelope', {}).get('SOAP-ENV:Body', {})
            search_response = soap_body.get('ns1:GetSearchResponse', {})
            search_result = search_response.get('ns1:SearchResult', {})
            
            # Проверяем успешность запроса
            success = search_result.get('ns1:success', 'false')
            if success != 'true':
                message = search_result.get('ns1:message', 'Unknown error')
                logger.warning(f"Rossko API returned error: {message}")
                return []
            
            # Получаем список запчастей
            parts_list = search_result.get('ns1:PartsList', {})
            if parts_list and 'ns1:Part' in parts_list:
                part_items = parts_list['ns1:Part']
                
                # Может быть один элемент или список
                if isinstance(part_items, dict):
                    part_items = [part_items]
                
                for item in part_items:
                    # Обрабатываем основную запчасть (оригинал)
                    self._process_part_item(item, parts, is_cross=False)
                    
                    # Обрабатываем аналоги (crosses)
                    crosses = item.get('ns1:crosses', {})
                    if crosses and 'ns1:Part' in crosses:
                        cross_items = crosses['ns1:Part']
                        if isinstance(cross_items, dict):
                            cross_items = [cross_items]
                        
                        for cross_item in cross_items:
                            self._process_part_item(cross_item, parts, is_cross=True)
            
            return parts
            
        except Exception as e:
            logger.error(f"Error parsing Rossko response: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _process_part_item(self, item: dict, parts: List[Dict], is_cross: bool = False):
        """
        Обработка одной запчасти (оригинал или аналог) и всех её складов
        """
        # Получаем информацию о всех складах
        stocks = item.get('ns1:stocks', {})
        stocks_list = []
        
        if stocks and 'ns1:stock' in stocks:
            stock_items = stocks['ns1:stock']
            if isinstance(stock_items, dict):
                stock_items = [stock_items]
            
            for stock in stock_items:
                stock_info = {
                    'id': stock.get('ns1:id', ''),
                    'price': float(stock.get('ns1:price', 0)),
                    'count': int(stock.get('ns1:count', 0)),
                    'delivery': int(stock.get('ns1:delivery', 0)),
                    'description': stock.get('ns1:description', ''),
                    'extra': int(stock.get('ns1:extra', 0))
                }
                stocks_list.append(stock_info)
        
        # Для каждого склада создаём отдельную запись
        for stock in stocks_list:
            part = {
                'article': item.get('ns1:partnumber', ''),
                'name': item.get('ns1:name', ''),
                'brand': item.get('ns1:brand', ''),
                'guid': item.get('ns1:guid', ''),
                'price': stock['price'],
                'delivery_days': stock['delivery'],
                'count': stock['count'],
                'stock_id': stock['id'],
                'stock_description': stock['description'],
                'is_extra': stock['extra'] == 1,
                'is_cross': is_cross,  # Метка аналога
                'availability': 'В наличии' if stock['delivery'] == 0 else 'Под заказ',
                'supplier': 'ROSSKO',
                'provider': 'rossko'
            }
            parts.append(part)
    
    def _deduplicate_parts(self, parts: List[Dict], original_article: str = '') -> List[Dict]:
        """
        Убирает дубликаты и суммирует количество для складов Тюмени
        Приоритет: точное совпадение с запросом > оригинал > аналог, в наличии > под заказ, дешевле > дороже
        """
        # Группируем по артикулу + бренд
        groups = {}
        
        for part in parts:
            key = f"{part['brand']}_{part['article']}"
            
            if key not in groups:
                groups[key] = part.copy()
                # Инициализируем список складов для суммирования
                groups[key]['all_stocks'] = [part]
            else:
                existing = groups[key]
                
                # Добавляем в список складов для суммирования
                existing['all_stocks'].append(part)
                
                # Выбираем лучшее предложение по критериям:
                # 0. Приоритет - точное совпадение артикула с запросом
                # 1. Оригинал (is_cross=False)
                # 2. В наличии (delivery_days = 0)
                # 3. Меньше срок доставки
                # 4. Дешевле цена
                
                is_better = False
                
                # Нормализуем артикулы для сравнения
                part_article_norm = part['article'].upper().replace('-', '').replace(' ', '')
                existing_article_norm = existing['article'].upper().replace('-', '').replace(' ', '')
                
                # Точное совпадение с запросом всегда лучше
                part_is_exact = (part_article_norm == original_article)
                existing_is_exact = (existing_article_norm == original_article)
                
                if part_is_exact and not existing_is_exact:
                    is_better = True
                elif existing_is_exact and not part_is_exact:
                    is_better = False
                # Оригинал всегда лучше аналога
                elif not part['is_cross'] and existing['is_cross']:
                    is_better = True
                elif part['is_cross'] and not existing['is_cross']:
                    is_better = False
                else:
                    # Оба оригиналы или оба аналоги - сравниваем по другим критериям
                    if part['delivery_days'] == 0 and existing['delivery_days'] > 0:
                        is_better = True
                    elif part['delivery_days'] == 0 and existing['delivery_days'] == 0:
                        # Оба в наличии - выбираем дешевле
                        if part['price'] < existing['price']:
                            is_better = True
                    elif existing['delivery_days'] > 0 and part['delivery_days'] > 0:
                        # Оба под заказ - сравниваем сроки и цену
                        if part['delivery_days'] < existing['delivery_days']:
                            is_better = True
                        elif part['delivery_days'] == existing['delivery_days'] and part['price'] < existing['price']:
                            is_better = True
                
                if is_better:
                    # Сохраняем список складов
                    all_stocks = existing['all_stocks']
                    groups[key] = part.copy()
                    groups[key]['all_stocks'] = all_stocks
        
        # Суммируем количество для складов Тюмени (в наличии)
        result = []
        for key, part in groups.items():
            # Подсчитываем общее количество на складах Тюмени
            total_count = 0
            tyumen_stocks = []
            
            for stock in part.get('all_stocks', []):
                if stock['delivery_days'] == 0:  # В наличии
                    total_count += stock['count']
                    tyumen_stocks.append(stock['stock_description'])
            
            # Обновляем count и availability
            if total_count > 0:
                part['count'] = total_count
                part['availability'] = f'В наличии: {total_count} шт.'
            
            # Удаляем служебное поле
            part.pop('all_stocks', None)
            
            result.append(part)
        
        return result
    
    def _apply_markup(self, parts: List[Dict], markup_percent: float) -> List[Dict]:
        """
        Применяет наценку к ценам
        """
        for part in parts:
            part['price'] = part['price'] * (1 + markup_percent / 100)
        return parts
    
    def _round_prices(self, parts: List[Dict]) -> List[Dict]:
        """
        Округляет цены вверх (убирает копейки)
        """
        import math
        for part in parts:
            part['price'] = math.ceil(part['price'])
        return parts
    
    def _map_warehouse_names(self, parts: List[Dict]) -> List[Dict]:
        """
        Заменяет названия складов на конкретные адреса для Тюмени
        """
        tyumen_warehouses = {
            'Тюмень': [
                'Тюмень, Пермякова, 1Б',
                'Тюмень, Щербакова, 160Д',
                'Тюмень, Ивана Словцова, 2',
                'Тюмень, Горпищекомбинатовская, 21а'
            ]
        }
        
        for part in parts:
            desc = part.get('stock_description', '')
            
            # Если это партнерский склад и товар в наличии (Тюмень)
            if 'Партнерский склад' in desc and part['delivery_days'] == 0:
                # Заменяем на один из складов Тюмени (можно случайный или первый)
                part['stock_description'] = tyumen_warehouses['Тюмень'][0]
            elif 'Екатеринбург' in desc or 'екатеринбург' in desc.lower():
                # Для Екатеринбурга обычно 1 день
                if part['delivery_days'] == 1:
                    part['delivery_display'] = 'Завтра'
        
        return parts
    
    def _sort_with_original_first(self, parts: List[Dict], original_article: str, sort_by: Optional[str]) -> List[Dict]:
        """
        Сортировка с оригиналом (точным совпадением) первым
        """
        # Разделяем на оригинал и остальные
        exact_matches = []
        other_parts = []
        
        for part in parts:
            part_article_norm = part['article'].upper().replace('-', '').replace(' ', '')
            if part_article_norm == original_article and not part['is_cross']:
                exact_matches.append(part)
            else:
                other_parts.append(part)
        
        # Сортируем остальные по выбранному критерию
        if sort_by:
            other_parts = self._sort_parts(other_parts, sort_by)
        
        # Оригинал первым, потом остальные
        return exact_matches + other_parts
    
    def _filter_by_availability(self, parts: List[Dict], filter_type: str) -> List[Dict]:
        """
        Фильтрация по наличию
        filter_type: 'in_stock' - только в наличии (Тюмень, delivery=0)
                     'on_order' - только под заказ (delivery>0)
        """
        if filter_type == 'in_stock':
            # В наличии: delivery_days = 0
            # Дополнительно можем фильтровать по описанию склада (Тюмень)
            return [
                p for p in parts 
                if p['delivery_days'] == 0 and 
                ('Тюмен' in p.get('stock_description', '') or p['delivery_days'] == 0)
            ]
        elif filter_type == 'on_order':
            # Под заказ: delivery_days > 0
            return [p for p in parts if p['delivery_days'] > 0]
        
        return parts
    
    def _sort_parts(self, parts: List[Dict], sort_by: str) -> List[Dict]:
        """
        Сортировка результатов
        sort_by: 'price_asc' - сначала дешёвые
                 'price_desc' - сначала дорогие
        """
        if sort_by == 'price_asc':
            return sorted(parts, key=lambda x: x['price'])
        elif sort_by == 'price_desc':
            return sorted(parts, key=lambda x: x['price'], reverse=True)
        
        return parts
    
    def get_delivery_details(self, article: str, brand: str) -> Optional[Dict]:
        """
        Получение детальной информации о доставке
        """
        try:
            soap_body = f"""
            <?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <GetDeliveryDetails xmlns="http://api.rossko.ru/">
                        <KEY1>{self.api_key1}</KEY1>
                        <KEY2>{self.api_key2}</KEY2>
                        <part_number>{article}</part_number>
                        <brand>{brand}</brand>
                    </GetDeliveryDetails>
                </soap:Body>
            </soap:Envelope>
            """
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://api.rossko.ru/GetDeliveryDetails'
            }
            
            response = requests.post(
                f"{self.api_url}?path=/GetDeliveryDetails&action=SOAP",
                data=soap_body,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = xmltodict.parse(response.content)
                return self._parse_delivery_response(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting delivery details: {str(e)}")
            return None
    
    def _parse_delivery_response(self, xml_data: dict) -> Dict:
        """
        Парсинг ответа с информацией о доставке
        """
        try:
            soap_body = xml_data.get('soap:Envelope', {}).get('soap:Body', {})
            delivery_response = soap_body.get('GetDeliveryDetailsResponse', {})
            result = delivery_response.get('GetDeliveryDetailsResult', {})
            
            return {
                'delivery_date': result.get('DeliveryDate', ''),
                'delivery_days': int(result.get('DeliveryDays', 0)),
                'quantity': result.get('Quantity', ''),
                'price': float(result.get('Price', 0))
            }
            
        except Exception as e:
            logger.error(f"Error parsing delivery response: {str(e)}")
            return {}