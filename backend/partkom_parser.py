from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import logging
import asyncio
import re
import os

logger = logging.getLogger(__name__)


class PartKomParser:
    """
    Парсер каталога part-kom.ru с авторизацией (ASYNC VERSION)
    """
    def __init__(self):
        self.base_url = "https://b2b.part-kom.ru"
        self.login_url = f"{self.base_url}/login"
        self.username = "carworkshop"
        self.password = "Qq23321q"
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        
    async def __aenter__(self):
        """Async контекстный менеджер"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие браузера"""
        await self.close()
    
    async def login(self) -> bool:
        """
        Авторизация на part-kom.ru с сохранением cookies (ASYNC)
        """
        try:
            logger.info("Starting Part-Kom login (async)...")
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            # Проверяем есть ли сохраненная сессия
            session_file = '/tmp/partkom_session.json'
            if os.path.exists(session_file):
                logger.info("Loading saved session...")
                try:
                    self.context = await self.browser.new_context(
                        storage_state=session_file,
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        viewport={'width': 1920, 'height': 1080}
                    )
                    self.page = await self.context.new_page()
                    
                    # Проверяем что сессия валидна
                    await self.page.goto(self.base_url, timeout=30000)
                    await asyncio.sleep(3)
                    
                    content = await self.page.content()
                    if 'вход' not in content.lower() and 'login' not in content.lower():
                        logger.info("Session is valid, using saved cookies")
                        return True
                    else:
                        logger.info("Session expired, re-login needed")
                        await self.page.close()
                        await self.context.close()
                except Exception as e:
                    logger.warning(f"Could not load session: {e}")
            
            # Создаем новую сессию
            logger.info("Creating new session...")
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            self.page = await self.context.new_page()
            
            # Переходим на главную
            logger.info(f"Navigating to {self.base_url}")
            await self.page.goto(self.base_url, timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # Ищем форму входа
            # Part-kom может иметь разные варианты формы входа
            login_selectors = [
                'a:has-text("Вход")',
                'a:has-text("Войти")',
                'button:has-text("Войти")',
                '.login-button',
                '#login-link'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    if await self.page.query_selector(selector):
                        await self.page.click(selector)
                        login_clicked = True
                        logger.info(f"Clicked login button: {selector}")
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            if not login_clicked:
                # Пробуем прямо перейти на страницу логина
                logger.info("Trying direct login URL")
                await self.page.goto(self.login_url, timeout=30000)
                await asyncio.sleep(2)
            
            # Заполняем форму
            username_selectors = [
                'input[name="username"]',
                'input[name="login"]',
                'input[name="email"]',
                'input[type="text"]',
                'input[placeholder*="логин"]',
                'input[placeholder*="Логин"]'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="пароль"]',
                'input[placeholder*="Пароль"]'
            ]
            
            # Заполняем логин
            for selector in username_selectors:
                try:
                    if await self.page.query_selector(selector):
                        await self.page.fill(selector, self.username)
                        logger.info(f"Filled username with selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Failed selector {selector}: {e}")
                    continue
            
            # Заполняем пароль
            for selector in password_selectors:
                try:
                    if await self.page.query_selector(selector):
                        await self.page.fill(selector, self.password)
                        logger.info(f"Filled password with selector: {selector}")
                        break
                except:
                    continue
            
            # Нажимаем кнопку входа
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Войти")',
                'button:has-text("Вход")',
                '.btn-login',
                '.login-submit'
            ]
            
            for selector in submit_selectors:
                try:
                    if await self.page.query_selector(selector):
                        await self.page.click(selector)
                        logger.info(f"Clicked submit: {selector}")
                        break
                except:
                    continue
            
            # Ждем перенаправления
            logger.info("Waiting for login redirect...")
            await asyncio.sleep(7)  # Увеличиваем время ожидания
            
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=20000)
            except:
                logger.warning("Timeout waiting for load, continuing...")
            
            await asyncio.sleep(2)
            
            current_url = self.page.url
            logger.info(f"Current URL after login: {current_url}")
            
            # Проверяем успешность входа - ищем элементы личного кабинета
            page_content = (await self.page.content()).lower()
            
            # Сохраняем скриншот после логина для проверки
            try:
                await self.page.screenshot(path='/tmp/partkom_after_login.png')
                logger.info("Screenshot after login saved")
            except:
                pass
            
            # Признаки успешного входа
            logged_in_indicators = [
                'выход' in page_content,
                'личный кабинет' in page_content,
                'logout' in page_content,
                'профиль' in page_content,
                'корзина' in page_content and 'регистрация' not in page_content,
                'мой аккаунт' in page_content
            ]
            
            # Дополнительная проверка - ищем элементы которые доступны только после логина
            login_success = any(logged_in_indicators)
            
            # Проверяем что мы не на странице логина
            not_on_login_page = 'login' not in current_url.lower() and 'вход' not in page_content[:500]
            
            logger.info(f"Login indicators found: {sum(logged_in_indicators)}/{len(logged_in_indicators)}")
            logger.info(f"Not on login page: {not_on_login_page}")
            
            if login_success or not_on_login_page:
                logger.info("✅ Successfully logged in to Part-Kom")
                
                # Сохраняем сессию для повторного использования
                try:
                    storage_state = await self.context.storage_state()
                    # Сохраняем только если есть cookies
                    if storage_state.get('cookies'):
                        with open('/tmp/partkom_session.json', 'w') as f:
                            import json
                            json.dump(storage_state, f)
                        logger.info(f"Session saved with {len(storage_state['cookies'])} cookies")
                    else:
                        logger.warning("No cookies to save")
                except Exception as e:
                    logger.warning(f"Could not save session: {e}")
                
                # Переходим на главную чтобы убедиться что сессия активна
                try:
                    await self.page.goto(self.base_url, timeout=30000)
                    await asyncio.sleep(2)
                    logger.info(f"Navigated to home page: {self.page.url}")
                except Exception as e:
                    logger.warning(f"Could not navigate to home: {e}")
                
                return True
            else:
                logger.error("❌ Login failed - still on login page or indicators not found")
                logger.info(f"Page content preview: {page_content[:300]}")
                try:
                    await self.page.screenshot(path='/tmp/partkom_login_failed.png')
                    logger.info("Login failed screenshot saved")
                except:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    async def search_by_vin(self, vin: str) -> Optional[Dict]:
        """
        Поиск автомобиля по VIN и получение каталога (ASYNC)
        """
        try:
            if not self.page:
                logger.info("Page not initialized, performing login...")
                if not await self.login():
                    logger.error("Login failed, cannot search by VIN")
                    return None
            
            logger.info(f"Starting VIN search for: {vin}")
            logger.info(f"Current URL before search: {self.page.url}")
            
            # Делаем скриншот перед поиском
            try:
                await self.page.screenshot(path='/tmp/partkom_before_search.png')
                logger.info("Screenshot before search saved")
            except:
                pass
            
            # Множественные варианты селекторов для поля VIN поиска
            search_selectors = [
                'input[placeholder*="VIN"]',
                'input[placeholder*="vin"]',
                'input[name*="vin"]',
                'input[id*="vin"]',
                'input[type="search"]',
                'input[type="text"]'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for elem in elements:
                        if await elem.is_visible():
                            search_input = elem
                            logger.info(f"Found search input with selector: {selector}")
                            break
                    if search_input:
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not search_input:
                logger.error("Search input not found with any selector")
                await self.page.screenshot(path='/tmp/partkom_no_search.png')
                
                # Пробуем найти любой input поле на странице для диагностики
                all_inputs = await self.page.query_selector_all('input')
                logger.info(f"Found {len(all_inputs)} input fields on page")
                for i, inp in enumerate(all_inputs[:5]):
                    try:
                        logger.info(f"Input {i}: type={await inp.get_attribute('type')}, name={await inp.get_attribute('name')}, placeholder={await inp.get_attribute('placeholder')}")
                    except:
                        pass
                
                return None
            
            # Очищаем и вводим VIN
            logger.info(f"Clearing search field and entering VIN: {vin}")
            await search_input.click()
            await asyncio.sleep(0.5)
            await search_input.fill('')  # Очищаем поле
            await asyncio.sleep(0.5)
            await search_input.type(vin, delay=100)  # Медленный ввод для имитации человека
            await asyncio.sleep(1)
            
            # Делаем скриншот после ввода VIN
            try:
                await self.page.screenshot(path='/tmp/partkom_after_vin_input.png')
                logger.info("Screenshot after VIN input saved")
            except:
                pass
            
            # Пробуем разные способы подтверждения поиска
            search_submitted = False
            
            # Способ 1: Нажимаем Enter
            logger.info("Trying to submit search with Enter key")
            await search_input.press('Enter')
            await asyncio.sleep(2)
            search_submitted = True
            
            # Способ 2: Ищем кнопку поиска
            if not search_submitted:
                search_button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Найти")',
                    'button:has-text("Поиск")',
                    'input[type="submit"]',
                    '.search-button',
                    'button[class*="search"]'
                ]
                
                for selector in search_button_selectors:
                    try:
                        btn = await self.page.query_selector(selector)
                        if btn and await btn.is_visible():
                            logger.info(f"Clicking search button: {selector}")
                            await btn.click()
                            await asyncio.sleep(2)
                            search_submitted = True
                            break
                    except:
                        continue
            
            if not search_submitted:
                logger.warning("Could not submit search, but continuing...")
            
            # Ждем загрузки результатов с увеличенным временем
            logger.info("Waiting for search results to load...")
            await asyncio.sleep(5)
            
            # Ждем сетевой активности
            try:
                await self.page.wait_for_load_state('networkidle', timeout=20000)
                logger.info("Network idle detected")
            except Exception as e:
                logger.warning(f"Timeout waiting for networkidle: {e}, but continuing...")
            
            await asyncio.sleep(3)  # Дополнительное время для рендеринга
            
            # Проверяем изменился ли URL (признак что поиск отработал)
            current_url = self.page.url
            logger.info(f"Current URL after search: {current_url}")
            
            # Делаем скриншот результатов
            try:
                await self.page.screenshot(path='/tmp/partkom_search_results.png')
                logger.info("Screenshot of search results saved")
            except:
                pass
            
            # Получаем HTML после поиска
            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            page_text = soup.get_text()
            
            # Проверяем что VIN найден на странице
            vin_found = vin.upper() in page_text.upper() or vin.lower() in page_text.lower()
            logger.info(f"VIN found in page text: {vin_found}")
            
            if not vin_found:
                logger.error(f"VIN {vin} not found in results")
                logger.info(f"Page text preview (first 500 chars): {page_text[:500]}")
                return None
            
            logger.info("VIN found on page, looking for car selection...")
            
            # Ищем варианты выбора автомобиля
            car_selection_keywords = [r'выбрать', r'catalog', r'каталог', r'перейти', r'открыть']
            car_links = []
            
            for keyword in car_selection_keywords:
                links = soup.find_all(['a', 'button', 'div'], text=re.compile(keyword, re.I), limit=10)
                car_links.extend(links)
            
            if car_links:
                logger.info(f"Found {len(car_links)} potential car selection elements")
                
                # Пробуем кликнуть на первый подходящий элемент
                for keyword in car_selection_keywords:
                    try:
                        clickable = await self.page.query_selector(f'a:has-text("{keyword}"), button:has-text("{keyword}")')
                        if clickable and await clickable.is_visible():
                            logger.info(f"Clicking on car selection: {keyword}")
                            await clickable.click()
                            await asyncio.sleep(5)
                            
                            try:
                                await self.page.wait_for_load_state('networkidle', timeout=20000)
                            except:
                                logger.warning("Timeout after click, continuing...")
                            
                            await asyncio.sleep(2)
                            logger.info(f"URL after selection: {self.page.url}")
                            break
                    except Exception as e:
                        logger.debug(f"Could not click {keyword}: {e}")
                        continue
            else:
                logger.info("No car selection links found, possibly already in catalog")
            
            # Получаем финальный HTML
            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Сохраняем скриншот каталога
            try:
                await self.page.screenshot(path='/tmp/partkom_catalog.png')
                logger.info("Final catalog screenshot saved")
            except:
                pass
            
            # Извлекаем информацию об автомобиле
            car_info = self._extract_car_info(soup, vin)
            
            if not car_info:
                # Пробуем извлечь из текста страницы
                logger.info("Trying to extract car info from page text")
                page_text = soup.get_text()
                car_info = self._extract_car_from_text(page_text, vin)
            
            if not car_info:
                logger.warning(f"Could not extract full car info for VIN: {vin}")
                # Базовая структура
                car_info = {
                    'vin': vin,
                    'make': 'Unknown',
                    'model': 'Unknown',
                    'year': None
                }
            
            # Получаем структуру каталога
            catalog = self._extract_catalog_structure(soup)
            car_info['catalog'] = catalog
            
            # Получаем текстовое содержимое для AI
            car_info['catalog_text'] = self._get_catalog_text(soup)
            
            logger.info(f"Successfully parsed: {car_info.get('make')} {car_info.get('model')}")
            logger.info(f"Catalog: {len(catalog['groups'])} groups, {len(catalog['parts'])} parts")
            logger.info(f"Catalog text: {len(car_info['catalog_text'])} chars")
            
            return car_info
            
        except Exception as e:
            logger.error(f"Error searching by VIN: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Финальный скриншот для отладки
            try:
                if self.page:
                    await self.page.screenshot(path='/tmp/partkom_error.png')
                    logger.info("Error screenshot saved")
            except:
                pass
            
            return None
    
    def _extract_car_from_text(self, text: str, vin: str) -> Optional[Dict]:
        """
        Извлечение информации об авто из текста страницы
        """
        try:
            car_info = {
                'vin': vin,
                'make': None,
                'model': None,
                'year': None
            }
            
            # Ищем популярные марки в тексте
            brands = {
                'TOYOTA': ['Camry', 'RAV4', 'Corolla', 'Land Cruiser', 'Highlander'],
                'HONDA': ['Accord', 'Civic', 'CR-V', 'Pilot'],
                'NISSAN': ['Qashqai', 'X-Trail', 'Juke', 'Patrol'],
                'MAZDA': ['CX-5', 'Mazda3', 'Mazda6', 'CX-9'],
                'BMW': ['X5', 'X3', '5 Series', '3 Series'],
                'MERCEDES': ['E-Class', 'C-Class', 'GLE', 'GLC']
            }
            
            text_upper = text.upper()
            
            for brand, models in brands.items():
                if brand in text_upper:
                    car_info['make'] = brand.title()
                    # Ищем модель
                    for model in models:
                        if model.upper() in text_upper:
                            car_info['model'] = model
                            break
                    if car_info['model']:
                        break
            
            # Ищем год
            year_match = re.search(r'(20\d{2}|19\d{2})', text)
            if year_match:
                car_info['year'] = year_match.group(1)
            
            if car_info['make']:
                logger.info(f"Extracted from text: {car_info['make']} {car_info['model']} {car_info['year']}")
                return car_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting from text: {e}")
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
                'transmission': None,
                'modification': None
            }
            
            # Ищем блок с информацией об авто (различные варианты классов)
            car_block_selectors = [
                '.vehicle-info', '.car-info', '.auto-info',
                '.product-vehicle', '.search-result-vehicle',
                'div[class*="vehicle"]', 'div[class*="car"]'
            ]
            
            car_block = None
            for selector in car_block_selectors:
                car_block = soup.select_one(selector)
                if car_block:
                    logger.info(f"Found car block with selector: {selector}")
                    break
            
            # Если не нашли блок, ищем в заголовках
            if not car_block:
                headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
                for header in headers:
                    text = header.get_text(strip=True)
                    # Паттерны типа "Toyota Camry 2015" или "TOYOTA CAMRY XV70 2017-"
                    patterns = [
                        r'([A-Z][a-z]+)\s+([A-Z][\w\s]+?)\s+(\d{4})',
                        r'([A-Z]+)\s+([A-Z]+[\w\s]*?)\s+[A-Z0-9]+\s+(\d{4})',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, text)
                        if match:
                            car_info['make'] = match.group(1).title()
                            car_info['model'] = match.group(2).strip().title()
                            car_info['year'] = match.group(3)
                            logger.info(f"Extracted from header: {car_info['make']} {car_info['model']} {car_info['year']}")
                            break
                    if car_info['make']:
                        break
            
            # Если нашли блок, парсим детально
            if car_block:
                text = car_block.get_text('\n', strip=True)
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    
                    # Марка
                    if any(word in line_lower for word in ['марка', 'make', 'brand']):
                        if ':' in line:
                            car_info['make'] = line.split(':')[-1].strip()
                        elif i + 1 < len(lines):
                            car_info['make'] = lines[i + 1].strip()
                    
                    # Модель
                    elif any(word in line_lower for word in ['модель', 'model']):
                        if ':' in line:
                            car_info['model'] = line.split(':')[-1].strip()
                        elif i + 1 < len(lines):
                            car_info['model'] = lines[i + 1].strip()
                    
                    # Год
                    elif any(word in line_lower for word in ['год', 'year']):
                        year_match = re.search(r'(\d{4})', line)
                        if year_match:
                            car_info['year'] = year_match.group(1)
                    
                    # Двигатель
                    elif any(word in line_lower for word in ['двигатель', 'engine', 'мотор']):
                        if ':' in line:
                            car_info['engine'] = line.split(':')[-1].strip()
                        elif i + 1 < len(lines):
                            car_info['engine'] = lines[i + 1].strip()
                    
                    # Модификация
                    elif any(word in line_lower for word in ['модификация', 'modification', 'поколение']):
                        if ':' in line:
                            car_info['modification'] = line.split(':')[-1].strip()
                        elif i + 1 < len(lines):
                            car_info['modification'] = lines[i + 1].strip()
            
            # Дополнительный поиск в тексте всей страницы
            if not car_info['make']:
                page_text = soup.get_text()
                # Ищем популярные марки
                brands = ['Toyota', 'Honda', 'Nissan', 'Mazda', 'BMW', 'Mercedes', 'Audi', 
                         'Ford', 'Chevrolet', 'Volkswagen', 'Hyundai', 'Kia', 'Lexus',
                         'Mitsubishi', 'Subaru', 'Suzuki', 'Skoda', 'Volvo']
                for brand in brands:
                    if brand.lower() in page_text.lower():
                        car_info['make'] = brand
                        logger.info(f"Found brand in page text: {brand}")
                        break
            
            return car_info if car_info['make'] else None
            
        except Exception as e:
            logger.error(f"Error extracting car info: {str(e)}")
            return None
    
    def _extract_catalog_structure(self, soup: BeautifulSoup) -> Dict:
        """
        Извлечение структуры каталога
        """
        try:
            catalog = {
                'groups': [],
                'parts': []
            }
            
            # Ищем категории запчастей
            category_selectors = [
                '.catalog-category', '.parts-category', '.category-list',
                'ul.categories', 'div.catalog-nav', '.parts-groups'
            ]
            
            for selector in category_selectors:
                categories = soup.select(f'{selector} a')
                if categories:
                    for link in categories[:50]:  # Ограничиваем
                        text = link.get_text(strip=True)
                        href = link.get('href', '')
                        if text and len(text) > 2:
                            catalog['groups'].append({
                                'name': text,
                                'url': href
                            })
                    if catalog['groups']:
                        logger.info(f"Found {len(catalog['groups'])} groups via {selector}")
                        break
            
            # Если не нашли через селекторы, ищем все ссылки с ключевыми словами
            if not catalog['groups']:
                all_links = soup.find_all('a', limit=100)
                keywords = ['двигател', 'подвеск', 'тормоз', 'кузов', 'фильтр', 
                           'масло', 'свеч', 'колод', 'диск', 'амортизатор']
                for link in all_links:
                    text = link.get_text(strip=True).lower()
                    if any(keyword in text for keyword in keywords):
                        catalog['groups'].append({
                            'name': link.get_text(strip=True),
                            'url': link.get('href', '')
                        })
            
            # Ищем таблицы с запчастями
            tables = soup.find_all('table', limit=10)
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[:50]:  # Ограничиваем
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # Извлекаем текст
                        row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                        
                        # Ищем артикулы (обычно буквенно-цифровая комбинация)
                        articles = re.findall(r'\b[A-Z0-9]{5,20}\b', row_text)
                        
                        if articles:
                            catalog['parts'].append({
                                'article': articles[0],
                                'name': row_text[:200],
                                'raw_text': row_text
                            })
            
            # Также ищем в div'ах с классами товаров
            product_divs = soup.find_all(['div', 'li'], class_=re.compile(r'product|item|part', re.I), limit=50)
            for div in product_divs:
                text = div.get_text(strip=True)
                articles = re.findall(r'\b[A-Z0-9]{5,20}\b', text)
                if articles and len(text) > 20:
                    catalog['parts'].append({
                        'article': articles[0],
                        'name': text[:200],
                        'raw_text': text
                    })
            
            logger.info(f"Extracted {len(catalog['groups'])} groups and {len(catalog['parts'])} parts")
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
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                element.decompose()
            
            # Получаем текст
            text = soup.get_text(separator='\n', strip=True)
            
            # Очищаем от лишних пробелов
            lines = []
            for line in text.split('\n'):
                line = line.strip()
                if line and len(line) > 3:  # Игнорируем совсем короткие строки
                    lines.append(line)
            
            clean_text = '\n'.join(lines)
            
            # Ограничиваем размер для AI (оставляем самое релевантное)
            if len(clean_text) > 12000:
                clean_text = clean_text[:12000]
            
            return clean_text
            
        except Exception as e:
            logger.error(f"Error getting catalog text: {str(e)}")
            return ""
    
    async def close(self):
        """Закрытие браузера (ASYNC)"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Part-Kom parser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
