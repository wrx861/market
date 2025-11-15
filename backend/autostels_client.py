import requests
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AutostelsClient:
    def __init__(self):
        self.base_url = "https://services.allautoparts.ru/WebService2"
        self.search_url = f"{self.base_url}/SearchService.svc"
        
        # Учетные данные (уже в base64 формате как требует API)
        self.parent_id = "39151"
        self.login_b64 = "Y2FyLndvcmtzaG9wNzJAbWFpbC5ydQ=="
        self.password_b64 = "UXEyMzMyMXE="
    
    def _create_session_info(self) -> str:
        """Создает XML для SessionInfo (используем атрибуты как в документации)"""
        return f'<SessionInfo ParentID="{self.parent_id}" UserLogin="{self.login_b64}" UserPass="{self.password_b64}" />'
    
    def search_step1(self, article: str) -> List[Dict]:
        """
        Шаг 1: Поиск брендов по артикулу
        """
        try:
            # XML параметры (внутренний XML)
            xml_params = f"""<root>
  {self._create_session_info()}
  <Search>
    <Key>{article}</Key>
  </Search>
</root>"""
            
            # Формируем SOAP запрос (XML передается через CDATA)
            soap_body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
  <soapenv:Header/>
  <soapenv:Body>
    <tem:SearchOfferStep1>
      <tem:SearchParametersXml><![CDATA[{xml_params}]]></tem:SearchParametersXml>
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
        """Парсит ответ Step1 и возвращает список брендов"""
        try:
            root = ET.fromstring(xml_text)
            
            # Находим результат (вложенный XML в виде строки)
            ns = {'s': 'http://schemas.xmlsoap.org/soap/envelope/',
                  't': 'http://tempuri.org/'}
            
            result_elem = root.find('.//t:SearchOfferStep1Result', ns)
            if result_elem is None or not result_elem.text:
                logger.info("No result element found")
                return []
            
            # Парсим вложенный XML
            inner_root = ET.fromstring(result_elem.text)
            
            brands = []
            for row in inner_root.findall('.//row'):
                product_id = row.findtext('ProductID', '')
                producer_name = row.findtext('ProducerName', '')
                
                if product_id and producer_name:
                    brands.append({
                        'product_id': product_id,
                        'producer_name': producer_name,
                        'stocks_only': row.findtext('StocksOnly', '0')
                    })
            
            logger.info(f"Found {len(brands)} brands for article")
            return brands
            
        except Exception as e:
            logger.error(f"Error parsing step1 response: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def search_step2(self, product_id: str, stocks_only: int = 0, in_stock: int = 1, show_cross: int = 1) -> List[Dict]:
        """
        Шаг 2: Получение предложений по product_id
        in_stock: 1 - все предложения, 2 - только в наличии
        show_cross: 0 - без аналогов, 1 - с аналогами
        """
        try:
            # XML параметры
            xml_params = f"""<root>
  {self._create_session_info()}
  <Search ResultFilter="0">
    <ProductID>{product_id}</ProductID>
    <StocksOnly>{stocks_only}</StocksOnly>
    <InStock>{in_stock}</InStock>
    <ShowCross>{show_cross}</ShowCross>
    <PeriodMin>-1</PeriodMin>
    <PeriodMax>-1</PeriodMax>
  </Search>
</root>"""
            
            soap_body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
  <soapenv:Header/>
  <soapenv:Body>
    <tem:SearchOfferStep2>
      <tem:SearchParametersXml><![CDATA[{xml_params}]]></tem:SearchParametersXml>
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
            
            ns = {'s': 'http://schemas.xmlsoap.org/soap/envelope/',
                  't': 'http://tempuri.org/'}
            
            result_elem = root.find('.//t:SearchOfferStep2Result', ns)
            if result_elem is None or not result_elem.text:
                logger.info("No result element found in step2")
                return []
            
            # Парсим вложенный XML
            inner_root = ET.fromstring(result_elem.text)
            
            offers = []
            for row in inner_root.findall('.//row'):
                try:
                    offer = {
                        'article': row.findtext('CodeAsIs', ''),
                        'brand': row.findtext('ManufacturerName', ''),
                        'name': row.findtext('ProductName', ''),
                        'price': float(row.findtext('Price', '0')),
                        'quantity': int(row.findtext('Quantity', '0')),
                        'delivery_days': int(row.findtext('PeriodMin', '0')),
                        'delivery_days_max': int(row.findtext('PeriodMax', '0')),
                        'warehouse': row.findtext('OfferName', 'Autostels'),
                        'is_cross': int(row.findtext('IsCross', '0')) == 1,
                        'in_stock': int(row.findtext('IsAvailability', '0')) == 1,
                        'provider': 'autostels'
                    }
                    
                    offers.append(offer)
                    
                except Exception as e:
                    logger.warning(f"Error parsing row element: {str(e)}")
                    continue
            
            logger.info(f"Parsed {len(offers)} offers from step2")
            return offers
            
        except Exception as e:
            logger.error(f"Error parsing step2 response: {str(e)}")
            return []
    
    def search_joint(self, article: str, brand: str = "", in_stock: int = 0, show_cross: int = 1) -> List[Dict]:
        """
        Комбинированный поиск (SearchOfferJoint) когда известен бренд
        in_stock: 0 - все, 1 - только в наличии
        show_cross: 0 - без аналогов, 1 - с аналогами
        """
        try:
            # XML параметры
            xml_params = f"""<root>
  {self._create_session_info()}
  <Search ResultFilter="0">
    <ProductCode>{article}</ProductCode>
    <ProducerName>{brand}</ProducerName>
    <StocksOnly>0</StocksOnly>
    <InStock>{in_stock}</InStock>
    <ShowCross>{show_cross}</ShowCross>
    <PeriodMin>-1</PeriodMin>
    <PeriodMax>-1</PeriodMax>
  </Search>
</root>"""
            
            soap_body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
  <soapenv:Header/>
  <soapenv:Body>
    <tem:SearchOfferJoint>
      <tem:SearchParametersXml><![CDATA[{xml_params}]]></tem:SearchParametersXml>
    </tem:SearchOfferJoint>
  </soapenv:Body>
</soapenv:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IAS2CSearch/SearchOfferJoint'
            }
            
            response = requests.post(
                self.search_url,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"SearchJoint failed with status {response.status_code}")
                logger.error(f"Response text: {response.text[:500]}")
                return []
            
            # Парсим ответ
            return self._parse_joint_response(response.text)
            
        except Exception as e:
            logger.error(f"Error in search_joint: {str(e)}")
            return []
    
    def _parse_joint_response(self, xml_text: str) -> List[Dict]:
        """Парсит ответ SearchOfferJoint"""
        try:
            root = ET.fromstring(xml_text)
            
            ns = {'s': 'http://schemas.xmlsoap.org/soap/envelope/',
                  't': 'http://tempuri.org/'}
            
            result_elem = root.find('.//t:SearchOfferJointResult', ns)
            if result_elem is None or not result_elem.text:
                logger.info("No result element found in SearchJoint")
                return []
            
            # Парсим вложенный XML
            inner_root = ET.fromstring(result_elem.text)
            
            offers = []
            for row in inner_root.findall('.//row'):
                try:
                    offer = {
                        'article': row.findtext('CodeAsIs', ''),
                        'brand': row.findtext('ManufacturerName', ''),
                        'name': row.findtext('ProductName', ''),
                        'price': float(row.findtext('Price', '0')),
                        'quantity': int(row.findtext('Quantity', '0')),
                        'delivery_days': int(row.findtext('PeriodMin', '0')),
                        'delivery_days_max': int(row.findtext('PeriodMax', '0')),
                        'warehouse': row.findtext('OfferName', 'Autostels'),
                        'is_cross': int(row.findtext('IsCross', '0')) == 1,
                        'in_stock': int(row.findtext('IsAvailability', '0')) == 1,
                        'provider': 'autostels'
                    }
                    
                    offers.append(offer)
                    
                except Exception as e:
                    logger.warning(f"Error parsing row element: {str(e)}")
                    continue
            
            logger.info(f"Parsed {len(offers)} offers from SearchJoint")
            return offers
            
        except Exception as e:
            logger.error(f"Error parsing joint response: {str(e)}")
            return []
    
    def search_by_article(self, article: str, brand: str = "", in_stock: int = 0, show_cross: int = 1) -> List[Dict]:
        """
        Полный поиск по артикулу
        Если бренд известен - использует SearchOfferJoint
        Иначе - пробует Step1 + Step2
        """
        logger.info(f"Searching Autostels for article: {article}")
        
        # Если бренд известен - используем SearchOfferJoint
        if brand:
            return self.search_joint(article, brand, in_stock, show_cross)
        
        # Иначе пробуем двухшаговый поиск
        # Шаг 1: Получаем список брендов
        brands = self.search_step1(article)
        
        if not brands:
            logger.info("No brands found in step1")
            # Пробуем поискать с пустым брендом через SearchOfferJoint
            return self.search_joint(article, "", in_stock, show_cross)
        
        # Шаг 2: Получаем предложения для каждого бренда
        all_offers = []
        for brand_info in brands:
            stocks_only = int(brand_info.get('stocks_only', 0))
            offers = self.search_step2(brand_info['product_id'], stocks_only, in_stock, show_cross)
            all_offers.extend(offers)
        
        logger.info(f"Found total {len(all_offers)} offers from Autostels")
        return all_offers
