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
    
    def _create_session_info(self) -> str:
        """Создает XML для SessionInfo (используем атрибуты как в документации)"""
        return f'<SessionInfo ParentID="{self.parent_id}" UserLogin="{self.login_b64}" UserPass="{self.password_b64}" />'
    
    def search_step1(self, article: str) -> List[Dict]:
        """
        Шаг 1: Поиск брендов по артикулу
        """
        try:
            # Формируем SOAP запрос (атрибуты как в документации)
            soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SearchOfferStep1 xmlns="http://tempuri.org/">
      <request>
        <root>
          {self._create_session_info()}
          <Search>
            <Key>{article}</Key>
          </Search>
        </root>
      </request>
    </SearchOfferStep1>
  </soap:Body>
</soap:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/ISearchService/SearchOfferStep1'
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
        """Парсит ответ Step1 и возвращает список брендов"""
        try:
            root = ET.fromstring(xml_text)
            
            # Находим все Brand элементы
            ns = {'s': 'http://schemas.xmlsoap.org/soap/envelope/',
                  't': 'http://tempuri.org/'}
            
            brands = []
            for brand_elem in root.findall('.//t:Brand', ns):
                product_id = brand_elem.findtext('t:ProductID', '', ns)
                producer_name = brand_elem.findtext('t:ProducerName', '', ns)
                
                if product_id and producer_name:
                    brands.append({
                        'product_id': product_id,
                        'producer_name': producer_name
                    })
            
            logger.info(f"Found {len(brands)} brands for article")
            return brands
            
        except Exception as e:
            logger.error(f"Error parsing step1 response: {str(e)}")
            return []
    
    def search_step2(self, product_id: str, in_stock: int = 1, show_cross: int = 1) -> List[Dict]:
        """
        Шаг 2: Получение предложений по product_id
        in_stock: 1 - все предложения, 2 - только в наличии
        show_cross: 0 - без аналогов, 1 - с аналогами
        """
        try:
            soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SearchOfferStep2 xmlns="http://tempuri.org/">
      <request>
        <root>
          {self._create_session_info()}
          <Search>
            <ProductID>{product_id}</ProductID>
            <StocksOnly>0</StocksOnly>
            <InStock>{in_stock}</InStock>
            <ShowCross>{show_cross}</ShowCross>
          </Search>
        </root>
      </request>
    </SearchOfferStep2>
  </soap:Body>
</soap:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/ISearchService/SearchOfferStep2'
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
            
            ns = {'s': 'http://schemas.xmlsoap.org/soap/envelope/',
                  't': 'http://tempuri.org/'}
            
            offers = []
            for offer_elem in root.findall('.//t:Offer', ns):
                try:
                    offer = {
                        'article': offer_elem.findtext('t:ProductCode', '', ns),
                        'brand': offer_elem.findtext('t:ProducerName', '', ns),
                        'name': offer_elem.findtext('t:ProductName', '', ns),
                        'price': float(offer_elem.findtext('t:Price', '0', ns)),
                        'quantity': int(offer_elem.findtext('t:Quantity', '0', ns)),
                        'delivery_days': int(offer_elem.findtext('t:PeriodMin', '0', ns)),
                        'delivery_days_max': int(offer_elem.findtext('t:PeriodMax', '0', ns)),
                        'warehouse': offer_elem.findtext('t:ProviderName', 'Autostels', ns),
                        'is_cross': int(offer_elem.findtext('t:IsCross', '0', ns)) == 1,
                        'in_stock': int(offer_elem.findtext('t:IsAvailability', '0', ns)) == 1,
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
            return []
    
    def search_by_article(self, article: str, in_stock: int = 1, show_cross: int = 1) -> List[Dict]:
        """
        Полный поиск по артикулу (Step1 + Step2)
        """
        logger.info(f"Searching Autostels for article: {article}")
        
        # Шаг 1: Получаем список брендов
        brands = self.search_step1(article)
        
        if not brands:
            logger.info("No brands found in step1")
            return []
        
        # Шаг 2: Получаем предложения для каждого бренда
        all_offers = []
        for brand in brands:
            offers = self.search_step2(brand['product_id'], in_stock, show_cross)
            all_offers.extend(offers)
        
        logger.info(f"Found total {len(all_offers)} offers from Autostels")
        return all_offers
