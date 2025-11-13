import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import logging
import time
import re

logger = logging.getLogger(__name__)


class RosskoParser:
    def __init__(self):
        self.base_url = "https://tmn.rossko.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def parse_car_info_by_vin(self, vin: str) -> Optional[Dict]:
        """
        Парсинг информации об автомобиле по VIN с Rossko
        Возвращает детальную информацию: марка, модель, год, двигатель, КПП и т.д.
        """
        try:
            # Поиск по VIN на Rossko
            search_url = f"{self.base_url}/search/?search={vin}"
            logger.info(f"Parsing car info from: {search_url}")
            
            response = self.session.get(search_url, timeout=20)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch page: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлекаем информацию об автомобиле
            car_info = self._extract_car_details(soup, vin)
            
            if not car_info:
                logger.warning(f"Could not extract car info for VIN: {vin}")
                return None
            
            # Получаем структуру каталога для этого авто
            catalog_structure = self._extract_catalog_structure(soup)
            car_info['catalog_structure'] = catalog_structure
            
            logger.info(f"Successfully parsed car info: {car_info.get('make')} {car_info.get('model')}")
            return car_info
            
        except Exception as e:
            logger.error(f"Error parsing car info: {str(e)}")
            return None
    
    def _extract_car_details(self, soup: BeautifulSoup, vin: str) -> Optional[Dict]:
        """
        Извлечение детальной информации об автомобиле
        """
        try:
            car_info = {
                'vin': vin,
                'make': None,
                'model': None,
                'year': None,
                'production_period': None,
                'engine': None,
                'engine_number': None,
                'engine_details': None,
                'transmission': None,
                'body_color': None,
                'interior_color': None,
                'release_date': None
            }
            
            # Ищем заголовок с информацией об авто
            title_elem = soup.find(['h1', 'h2', 'h3'], text=re.compile(r'VIN|Frame', re.I))
            if not title_elem:
                title_elem = soup.find(text=re.compile(vin, re.I))
                if title_elem:
                    title_elem = title_elem.parent
            
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                parts = title_text.split('·')[0].strip().split()
                if len(parts) >= 2:
                    car_info['make'] = parts[0]
                    car_info['model'] = ' '.join(parts[1:])
            
            # Ищем таблицу с характеристиками
            info_container = soup.find(['table', 'div', 'dl'], class_=re.compile(r'info|detail|vehicle|car', re.I))
            
            if not info_container:
                info_container = soup.find('dl') or soup.find('table')
            
            if info_container:
                text_content = info_container.get_text('\n', strip=True)
                lines = text_content.split('\n')
                
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    
                    if 'дата выпуска' in line_lower and i + 1 < len(lines):
                        car_info['release_date'] = lines[i + 1].strip()
                    
                    elif 'выпущено' in line_lower and i + 1 < len(lines):
                        year_match = re.search(r'(\d{4})', lines[i + 1])
                        if year_match:
                            car_info['year'] = year_match.group(1)
                    
                    elif 'период производства' in line_lower and i + 1 < len(lines):
                        car_info['production_period'] = lines[i + 1].strip()
                    
                    elif line_lower == 'двигатель' and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if len(next_line) < 20 and not any(c in next_line for c in ['/', 'CC', 'hp']):
                            car_info['engine'] = next_line
                    
                    elif 'номер двигателя' in line_lower and i + 1 < len(lines):
                        car_info['engine_number'] = lines[i + 1].strip()
                    
                    elif 'cc' in line_lower or 'hp' in line_lower or 'kw' in line_lower:
                        if '/' in line:
                            car_info['engine_details'] = line.strip()
                    
                    elif 'кпп' in line_lower and i + 1 < len(lines):
                        car_info['transmission'] = lines[i + 1].strip()
                    
                    elif 'цвет кузова' in line_lower and i + 1 < len(lines):
                        car_info['body_color'] = lines[i + 1].strip()
                    
                    elif 'цвет салона' in line_lower and i + 1 < len(lines):
                        car_info['interior_color'] = lines[i + 1].strip()
            
            if not car_info['make'] or not car_info['model']:
                meta_title = soup.find('meta', property='og:title')
                if meta_title:
                    title = meta_title.get('content', '')
                    parts = title.split()
                    if len(parts) >= 2:
                        car_info['make'] = parts[0]
                        car_info['model'] = parts[1]
            
            if not car_info['make']:
                return None
            
            return car_info
            
        except Exception as e:
            logger.error(f"Error extracting car details: {str(e)}")
            return None
    
    def _extract_catalog_structure(self, soup: BeautifulSoup) -> Dict:
        """
        Извлечение структуры каталога запчастей
        """
        try:
            catalog = {
                'groups': [],
                'parts': []
            }
            
            catalog_nav = soup.find(['ul', 'div'], class_=re.compile(r'catalog|category|parts|group', re.I))
            
            if catalog_nav:
                links = catalog_nav.find_all('a')
                for link in links:
                    text = link.get_text(strip=True)
                    href = link.get('href', '')
                    if text and len(text) > 2:
                        catalog['groups'].append({
                            'name': text,
                            'url': href
                        })
            
            parts_table = soup.find('table', class_=re.compile(r'parts|product|item', re.I))
            if not parts_table:
                parts_table = soup.find_all('tr', limit=50)
            
            if parts_table:
                rows = parts_table.find_all('tr') if hasattr(parts_table, 'find_all') else parts_table
                
                for row in rows[:30]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        part_info = {}
                        for cell in cells:
                            text = cell.get_text(strip=True)
                            if re.match(r'^[A-Z0-9\-]{5,20}$', text):
                                part_info['article'] = text
                            elif len(text) > 10 and len(text) < 100:
                                part_info['name'] = text
                        
                        if 'article' in part_info or 'name' in part_info:
                            catalog['parts'].append(part_info)
            
            return catalog
            
        except Exception as e:
            logger.error(f"Error extracting catalog structure: {str(e)}")
            return {'groups': [], 'parts': []}
    
    def get_catalog_page_content(self, vin: str) -> str:
        """
        Получение текстового содержимого страницы каталога
        """
        try:
            search_url = f"{self.base_url}/search/?search={vin}"
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)
            
            return clean_text[:8000]
            
        except Exception as e:
            logger.error(f"Error getting catalog content: {str(e)}")
            return ""
