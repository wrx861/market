from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import logging
import time
import re

logger = logging.getLogger(__name__)


class BergParser:
    """
    Парсер каталога berg.ru с авторизацией
    """
    def __init__(self):
        self.base_url = "https://berg.ru"
        self.login_url = f"{self.base_url}/login"
        self.username = "carworkshop"
        self.password = "Qq23321q"
        self.browser = None
        self.context = None
        self.page = None
        
    def __enter__(self):
        """Контекстный менеджер для автоматического закрытия браузера"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие браузера"""
        self.close()
    
    def login(self) -> bool:
        """
        Авторизация на berg.ru
        """
        try:
            logger.info("Starting Berg.ru login...")
            
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(headless=True)
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = self.context.new_page()
            
            # Переходим на страницу логина
            self.page.goto(self.login_url, timeout=30000)
            time.sleep(2)
            
            # Заполняем форму
            self.page.fill('input[name="username"], input[name="login"], input[type="text"]', self.username)
            self.page.fill('input[name="password"], input[type="password"]', self.password)
            
            # Нажимаем кнопку входа
            self.page.click('button[type="submit"], input[type="submit"], button:has-text("Войти")')
            
            # Ждем перенаправления
            self.page.wait_for_load_state('networkidle', timeout=15000)
            
            # Проверяем успешность авторизации
            if 'login' not in self.page.url.lower():
                logger.info("Successfully logged in to Berg.ru")
                return True
            else:
                logger.error("Login failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def search_by_vin(self, vin: str) -> Optional[Dict]:
        """
        Поиск автомобиля по VIN и получение каталога
        """
        try:
            if not self.page:
                if not self.login():
                    return None
            
            logger.info(f"Searching for VIN: {vin}")
            
            # Ищем поле поиска по VIN
            search_selectors = [
                'input[placeholder*="VIN"]',
                'input[name*="vin"]',
                'input[id*="vin"]',
                'input[type="search"]',
                'input.search'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.page.query_selector(selector)
                    if search_input:
                        break
                except:
                    continue
            
            if not search_input:
                logger.error("Search input not found")
                return None
            
            # Вводим VIN
            search_input.fill(vin)
            search_input.press('Enter')
            
            # Ждем загрузки результатов
            time.sleep(3)
            self.page.wait_for_load_state('networkidle', timeout=20000)
            
            # Получаем HTML страницы
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Извлекаем информацию об автомобиле
            car_info = self._extract_car_info(soup, vin)
            
            if not car_info:
                logger.warning(f"No car info found for VIN: {vin}")
                return None
            
            # Получаем структуру каталога
            catalog = self._extract_catalog_structure(soup)
            car_info['catalog'] = catalog
            
            # Получаем текстовое содержимое для AI
            car_info['catalog_text'] = self._get_catalog_text(soup)
            
            logger.info(f"Successfully parsed car: {car_info.get('make')} {car_info.get('model')}")
            return car_info
            
        except Exception as e:
            logger.error(f"Error searching by VIN: {str(e)}")
            return None
    
    def _extract_car_info(self, soup: BeautifulSoup, vin: str) -> Optional[Dict]:
        """
        Извлечение информации об автомобиле
        """
        try:
            car_info = {
                'vin': vin,
                'make': None,
                'model': None,
                'year': None,
                'engine': None,
                'body': None,
                'transmission': None
            }
            
            # Ищем блок с информацией об авто
            car_block = soup.find(['div', 'section'], class_=re.compile(r'vehicle|car|auto|info', re.I))
            
            if not car_block:
                # Пробуем найти через заголовки
                headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])
                for header in headers:
                    text = header.get_text(strip=True)
                    # Ищем паттерн типа "Toyota Camry 2015"
                    match = re.search(r'([A-Z][a-z]+)\s+([A-Z][\w\s]+?)\s+(\d{4})', text)
                    if match:
                        car_info['make'] = match.group(1)
                        car_info['model'] = match.group(2).strip()
                        car_info['year'] = match.group(3)
                        break
            else:
                # Извлекаем из блока
                text = car_block.get_text('\n', strip=True)
                lines = text.split('\n')
                
                for line in lines:
                    line_lower = line.lower()
                    
                    if 'марка' in line_lower or 'make' in line_lower:
                        car_info['make'] = line.split(':')[-1].strip() if ':' in line else line
                    elif 'модель' in line_lower or 'model' in line_lower:
                        car_info['model'] = line.split(':')[-1].strip() if ':' in line else line
                    elif 'год' in line_lower or 'year' in line_lower:
                        year_match = re.search(r'(\d{4})', line)
                        if year_match:
                            car_info['year'] = year_match.group(1)
                    elif 'двигатель' in line_lower or 'engine' in line_lower:
                        car_info['engine'] = line.split(':')[-1].strip() if ':' in line else line
                    elif 'кузов' in line_lower or 'body' in line_lower:
                        car_info['body'] = line.split(':')[-1].strip() if ':' in line else line
                    elif 'кпп' in line_lower or 'transmission' in line_lower:
                        car_info['transmission'] = line.split(':')[-1].strip() if ':' in line else line
            
            # Валидация
            if not car_info['make']:
                return None
            
            return car_info
            
        except Exception as e:
            logger.error(f"Error extracting car info: {str(e)}")
            return None
    
    def _extract_catalog_structure(self, soup: BeautifulSoup) -> Dict:
        """
        Извлечение структуры каталога (группы запчастей)
        """
        try:
            catalog = {
                'groups': [],
                'parts': []
            }
            
            # Ищем навигацию по категориям
            nav_selectors = [
                'div.catalog', 'div.categories', 'nav.parts',
                'ul.catalog-list', 'div.parts-list'
            ]
            
            catalog_nav = None
            for selector in nav_selectors:
                catalog_nav = soup.select_one(selector)
                if catalog_nav:
                    break
            
            if catalog_nav:
                # Извлекаем категории
                links = catalog_nav.find_all('a', limit=50)
                for link in links:
                    text = link.get_text(strip=True)
                    href = link.get('href', '')
                    if text and len(text) > 2:
                        catalog['groups'].append({
                            'name': text,
                            'url': href
                        })
            
            # Ищем таблицу с запчастями
            tables = soup.find_all('table', limit=5)
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        part_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                        # Ищем артикулы в тексте
                        articles = re.findall(r'\b[A-Z0-9]{5,20}\b', part_text)
                        if articles:
                            catalog['parts'].append({
                                'article': articles[0],
                                'text': part_text[:200]
                            })
            
            logger.info(f"Found {len(catalog['groups'])} groups and {len(catalog['parts'])} parts")
            return catalog
            
        except Exception as e:
            logger.error(f"Error extracting catalog: {str(e)}")
            return {'groups': [], 'parts': []}
    
    def _get_catalog_text(self, soup: BeautifulSoup) -> str:
        """
        Получение текстового содержимого каталога для AI
        """
        try:
            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Получаем текст
            text = soup.get_text(separator='\n', strip=True)
            
            # Очищаем
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)
            
            # Ограничиваем размер
            return clean_text[:10000]
            
        except Exception as e:
            logger.error(f"Error getting catalog text: {str(e)}")
            return ""
    
    def search_part_in_catalog(self, part_query: str) -> List[str]:
        """
        Поиск конкретной запчасти в открытом каталоге
        """
        try:
            if not self.page:
                logger.error("No active page session")
                return []
            
            logger.info(f"Searching for part: {part_query}")
            
            # Ищем поле поиска
            search_selectors = [
                'input[type="search"]',
                'input.search',
                'input[placeholder*="Поиск"]',
                'input[name="search"]'
            ]
            
            for selector in search_selectors:
                try:
                    search_input = self.page.query_selector(selector)
                    if search_input:
                        search_input.fill(part_query)
                        search_input.press('Enter')
                        break
                except:
                    continue
            
            # Ждем результатов
            time.sleep(2)
            self.page.wait_for_load_state('networkidle', timeout=15000)
            
            # Парсим результаты
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Извлекаем артикулы
            articles = []
            article_pattern = r'\b[A-Z0-9]{5,20}\b'
            
            # Ищем в таблицах
            tables = soup.find_all('table')
            for table in tables:
                text = table.get_text()
                found = re.findall(article_pattern, text)
                articles.extend(found)
            
            # Уникальные артикулы
            articles = list(set(articles))[:10]
            
            logger.info(f"Found {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error searching part: {str(e)}")
            return []
    
    def close(self):
        """Закрытие браузера"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
