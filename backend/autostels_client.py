import requests
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AutostelsClient:
    def __init__(self):
        self.base_url = "https://services.allautoparts.ru/WebService2"
        self.search_url = f"{self.base_url}/SearchService.svc"
        
        # Учетные данные - преобразуем в base64 как требует API
        import base64
        self.parent_id = "39151"
        login = "car.workshop72@mail.ru"
        password = "Qq23321q"
        self.login_b64 = base64.b64encode(login.encode('utf-8')).decode('utf-8')
        self.password_b64 = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        
        # SessionGUID получается из Step1 и используется в Step2
        self.session_guid = None
    
    def _create_session_info(self) -> str:
        """Создает XML для SessionInfo (используем атрибуты как в документации)"""
        return f'<SessionInfo ParentID="{self.parent_id}" UserLogin="{self.login_b64}" UserPass="{self.password_b64}" />'
    
    def search_step1(self, article: str) -> List[Dict]:
        """
        Шаг 1: Поиск брендов по артикулу
        """
        try:
            # Формируем XML параметры для CDATA (согласно документации v3.6)
            search_params = f"""<root>
   {self._create_session_info()}
   <Search>
      <Key>{article}</Key>
   </Search>
</root>"""
            
            # Формируем SOAP запрос с CDATA (как в документации)
            soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:SearchOfferStep1>
         <tem:SearchParametersXml><![CDATA[{search_params}]]></tem:SearchParametersXml>
      </tem:SearchOfferStep1>
   </soapenv:Body>
</soapenv:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IAS2CSearch/SearchOfferStep1'
            }
            
            response = requests.post(
                self.search_url,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Step1 failed with status {response.status_code}")
                logger.error(f"Response text: {response.text[:500]}")
                return []
            
            # Парсим ответ
            return self._parse_step1_response(response.text)
            
        except Exception as e:
            logger.error(f"Error in search_step1: {str(e)}")
            return []
    
    def _parse_step1_response(self, xml_text: str) -> List[Dict]:
        """Парсит ответ Step1 и возвращает список брендов + SessionGUID"""
        try:
            root = ET.fromstring(xml_text)
            
            # Извлекаем результат из SOAP envelope
            ns = {'s': 'http://schemas.xmlsoap.org/soap/envelope/',
                  't': 'http://tempuri.org/'}
            
            # Находим SearchOfferStep1Result
            result_elem = root.find('.//t:SearchOfferStep1Result', ns)
            
            if result_elem is None or not result_elem.text:
                logger.warning("No SearchOfferStep1Result found in response")
                return []
            
            # Парсим внутренний XML из результата
            result_xml = result_elem.text
            result_root = ET.fromstring(result_xml)
            
            # ВАЖНО: Извлекаем SessionGUID для использования в Step2
            session_guid = result_root.findtext('.//SessionGUID', '')
            if session_guid:
                self.session_guid = session_guid
                logger.info(f"Got SessionGUID from Step1: {session_guid[:20]}...")
            
            brands = []
            # Ищем все элементы row внутри rows
            for row in result_root.findall('.//row'):
                product_id = row.findtext('ProductID', '')
                producer_name = row.findtext('ProducerName', '')
                
                if product_id and producer_name:
                    brands.append({
                        'product_id': product_id,
                        'producer_name': producer_name,
                        'article': row.findtext('CodeAsIs', ''),
                        'name': row.findtext('ProductName', '')
                    })
            
            logger.info(f"Found {len(brands)} brands for article")
            return brands
            
        except Exception as e:
            logger.error(f"Error parsing step1 response: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def search_step2(self, product_id: str, in_stock: int = 1, show_cross: int = 2) -> List[Dict]:
        """
        Шаг 2: Получение предложений по product_id
        in_stock: 1 - все предложения, 2 - только в наличии
        show_cross: 1 - без аналогов, 2 - с аналогами
        """
        try:
            # Формируем XML параметры для CDATA (согласно документации v3.6)
            # ResultFilter: 0 - старый формат, 2 - новый формат (используем 2)
            search_params = f"""<root>
   {self._create_session_info()}
   <Search ResultFilter="2">
      <ProductID>{product_id}</ProductID>
      <StocksOnly>0</StocksOnly>
      <InStock>{in_stock}</InStock>
      <ShowCross>{show_cross}</ShowCross>
      <PeriodMin>-1</PeriodMin>
      <PeriodMax>-1</PeriodMax>
   </Search>
</root>"""
            
            # Формируем SOAP запрос с CDATA (как в документации)
            soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:SearchOfferStep2>
         <tem:SearchParametersXml><![CDATA[{search_params}]]></tem:SearchParametersXml>
      </tem:SearchOfferStep2>
   </soapenv:Body>
</soapenv:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IAS2CSearch/SearchOfferStep2'
            }
            
            response = requests.post(
                self.search_url,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Step2 failed with status {response.status_code}")
                logger.error(f"Response text: {response.text[:500]}")
                return []
            
            # Парсим ответ
            return self._parse_step2_response(response.text)
            
        except Exception as e:
            logger.error(f"Error in search_step2: {str(e)}")
            return []
    
    def _parse_step2_response(self, xml_text: str) -> List[Dict]:
        """Парсит ответ Step2 и возвращает список предложений"""
        try:
            root = ET.fromstring(xml_text)
            
            # Извлекаем результат из SOAP envelope
            ns = {'s': 'http://schemas.xmlsoap.org/soap/envelope/',
                  't': 'http://tempuri.org/'}
            
            # Находим SearchOfferStep2Result
            result_elem = root.find('.//t:SearchOfferStep2Result', ns)
            
            if result_elem is None or not result_elem.text:
                logger.warning("No SearchOfferStep2Result found in response")
                return []
            
            # Парсим внутренний XML из результата
            result_xml = result_elem.text
            logger.debug(f"Step2 result XML: {result_xml[:500]}")
            result_root = ET.fromstring(result_xml)
            
            # Проверяем на ошибки в результате
            error_elem = result_root.find('.//error')
            if error_elem is not None:
                error_state = error_elem.get('state', 'unknown')
                error_msg = error_elem.findtext('message', 'Unknown error')
                logger.warning(f"Step2 returned error: state={error_state}, message={error_msg}")
                return []
            
            offers = []
            # Ищем все элементы row внутри rows
            rows = result_root.findall('.//row')
            logger.debug(f"Found {len(rows)} rows in Step2 response")
            
            for row in rows:
                try:
                    # Извлекаем данные из row
                    price = row.findtext('Price', '0')
                    quantity = row.findtext('Quantity', '0')
                    period_min = row.findtext('PeriodMin', '0')
                    period_max = row.findtext('PeriodMax', '0')
                    is_cross = row.findtext('IsCross', '0')
                    is_availability = row.findtext('IsAvailability', '0')
                    
                    offer = {
                        'article': row.findtext('ProductCode', ''),
                        'brand': row.findtext('ProducerName', ''),
                        'name': row.findtext('ProductName', ''),
                        'price': float(price) if price else 0.0,
                        'quantity': int(quantity) if quantity else 0,
                        'delivery_days': int(period_min) if period_min else 0,
                        'delivery_days_max': int(period_max) if period_max else 0,
                        'warehouse': row.findtext('ProviderName', 'Autostels'),
                        'is_cross': int(is_cross) == 1 if is_cross else False,
                        'in_stock': int(is_availability) == 1 if is_availability else False,
                        'provider': 'autostels'
                    }
                    
                    offers.append(offer)
                    
                except Exception as e:
                    logger.warning(f"Error parsing offer element: {str(e)}")
                    continue
            
            logger.info(f"Parsed {len(offers)} offers from step2")
            return offers
            
        except Exception as e:
            logger.error(f"Error parsing step2 response: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def search_by_article(self, article: str, in_stock: int = 1, show_cross: int = 2) -> List[Dict]:
        """
        Полный поиск по артикулу (Step1 + Step2)
        in_stock: 1 - все предложения, 2 - только в наличии
        show_cross: 1 - без аналогов, 2 - с аналогами
        """
        logger.info(f"Searching Autostels for article: {article}")
        
        # Шаг 1: Получаем список брендов
        brands = self.search_step1(article)
        
        if not brands:
            logger.info("No brands found in step1")
            return []
        
        logger.info(f"Found {len(brands)} brands in step1, proceeding to step2")
        
        # Шаг 2: Получаем предложения для каждого бренда
        all_offers = []
        for brand in brands[:5]:  # Ограничиваем 5 брендами для оптимизации
            logger.info(f"Searching step2 for brand: {brand['producer_name']}")
            offers = self.search_step2(brand['product_id'], in_stock, show_cross)
            all_offers.extend(offers)
        
        logger.info(f"Found total {len(all_offers)} offers from Autostels")
        return all_offers
