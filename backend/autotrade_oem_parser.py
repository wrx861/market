"""
Autotrade OEM Catalog Parser
Парсер для извлечения OEM артикулов из каталога Autotrade через Playwright
"""

import os
import logging
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AutotradeOEMParser:
    """Парсер для работы с OEM каталогом Autotrade"""
    
    def __init__(self):
        self.login = os.environ.get('AUTOTRADE_LOGIN', '')
        self.password = os.environ.get('AUTOTRADE_PASSWORD', '')
        self.auth_url = 'https://sklad.autotrade.su/'
        self.catalog_url = 'https://catalog.autotrade.su/'
        
    async def search_by_vin(self, vin: str, part_name: str) -> Dict:
        """
        Поиск OEM артикулов по VIN и названию запчасти
        
        Args:
            vin: VIN номер автомобиля
            part_name: Название запчасти (например "шаровая опора")
            
        Returns:
            Dict с информацией об автомобиле и найденными артикулами
        """
        logger.info(f"Starting OEM search for VIN: {vin}, part: {part_name}")
        
        async with async_playwright() as p:
            # Запускаем браузер с дефолтными настройками (как в отладочном скрипте)
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Шаг 1: Авторизация
                logger.info("Step 1: Authorizing on sklad.autotrade.su")
                await self._authorize(page)
                
                # Шаг 2: Переход на каталог с VIN
                logger.info(f"Step 2: Opening catalog with VIN: {vin}")
                vehicle_data = await self._open_catalog_with_vin(page, vin)
                
                if not vehicle_data:
                    return {
                        'success': False,
                        'error': 'Vehicle not found by VIN'
                    }
                
                # Шаг 3: Клик на автомобиль из списка результатов
                logger.info("Step 3: Clicking on vehicle from results")
                await self._click_vehicle_from_results(page)
                
                # Шаг 4: Поиск запчасти в каталоге
                logger.info(f"Step 4: Searching for part: {part_name}")
                oem_parts = await self._search_part_in_catalog(page, part_name)
                
                return {
                    'success': True,
                    'vehicle_info': vehicle_data,
                    'oem_parts': oem_parts
                }
                
            except Exception as e:
                logger.error(f"Error during OEM search: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': str(e)
                }
            finally:
                await browser.close()
    
    async def _authorize(self, page):
        """Авторизация на sklad.autotrade.su через форму в шапке"""
        try:
            await page.goto(self.auth_url, wait_until='domcontentloaded', timeout=30000)
            
            # Ждем загрузки страницы и скриптов
            await page.wait_for_timeout(3000)
            
            logger.info("Page loaded, looking for login form in header")
            
            # Форма находится в шапке страницы (правый верхний угол)
            # Ищем поля E-mail и Пароль в шапке
            # Используем простой wait_for_selector вместо locator.wait_for
            await page.wait_for_selector('input#log_u', state='visible', timeout=15000)
            
            logger.info("Login form found in header, filling credentials")
            
            # Вводим email
            login_input = page.locator('input#log_u')
            await login_input.fill(self.login)
            await page.wait_for_timeout(300)
            
            # Вводим пароль
            password_input = page.locator('input#log_p')
            await password_input.fill(self.password)
            await page.wait_for_timeout(300)
            
            logger.info("Credentials filled, clicking login button")
            
            # Нажимаем кнопку входа (кнопка рядом с полями)
            login_button = page.locator('#linkLogIn')
            await login_button.click()
            
            # Ждем успешной авторизации - может быть редирект или обновление страницы
            await page.wait_for_timeout(4000)
            
            logger.info("Authorization successful")
            
        except Exception as e:
            logger.error(f"Authorization failed: {e}")
            # Делаем скриншот для отладки
            try:
                await page.screenshot(path='/tmp/auth_error.png')
                logger.info("Error screenshot saved to /tmp/auth_error.png")
            except:
                pass
            raise Exception(f"Failed to authorize: {e}")
    
    async def _open_catalog_with_vin(self, page, vin: str) -> Optional[Dict]:
        """Открытие каталога с VIN напрямую (после авторизации можно сразу перейти по URL)"""
        try:
            # После авторизации на sklad.autotrade.su можем сразу перейти на catalog с VIN
            catalog_url = f'https://catalog.autotrade.su/index.php?task=vehicles&ft=FindVehicle&c=&identString={vin}&ssd='
            
            logger.info(f"Opening catalog URL: {catalog_url}")
            await page.goto(catalog_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Делаем скриншот для отладки
            try:
                await page.screenshot(path='/tmp/catalog_page.png')
                logger.info("Catalog screenshot saved to /tmp/catalog_page.png")
            except:
                pass
            
            # Проверяем что страница загрузилась и есть результаты
            # После поиска по VIN автомобиль должен отобразиться в таблице
            table_rows = await page.locator('table tr').count()
            
            if table_rows < 2:  # Минимум: заголовок + 1 строка с данными
                logger.warning(f"No vehicle found for VIN: {vin} (rows: {table_rows})")
                return None
            
            logger.info(f"Found table with {table_rows} rows")
            
            # Извлекаем данные автомобиля из таблицы
            # Структура: Бренд | Название | Модель | Дата выпуска | Регион | Двигатель | КПП | Цвет кузова | Цвет салона | Дверей
            vehicle_data = {}
            
            try:
                # Первая строка после заголовка - данные автомобиля
                first_row = page.locator('table tr').nth(1)
                cells = first_row.locator('td')
                
                cell_count = await cells.count()
                logger.info(f"Table has {cell_count} columns")
                
                if cell_count >= 3:
                    vehicle_data['brand'] = (await cells.nth(0).text_content()).strip()
                    vehicle_data['name'] = (await cells.nth(1).text_content()).strip()
                    vehicle_data['model'] = (await cells.nth(2).text_content()).strip()
                    
                    if cell_count >= 4:
                        vehicle_data['release_date'] = (await cells.nth(3).text_content()).strip()
                    
                    if cell_count >= 6:
                        vehicle_data['engine'] = (await cells.nth(5).text_content()).strip()
                    
                    if cell_count >= 7:
                        vehicle_data['transmission'] = (await cells.nth(6).text_content()).strip()
                
                logger.info(f"Vehicle data extracted: {vehicle_data}")
                
            except Exception as e:
                logger.warning(f"Could not extract vehicle data from table: {e}")
                vehicle_data = {
                    'brand': 'Unknown',
                    'model': 'Unknown',
                    'name': 'Unknown'
                }
            
            return vehicle_data
            
        except Exception as e:
            logger.error(f"Failed to open catalog with VIN: {e}")
            return None
    
    async def _click_vehicle_from_results(self, page):
        """Клик на автомобиль из списка результатов"""
        try:
            # Ждем таблицу с результатами
            await page.wait_for_selector('table tr', timeout=10000)
            
            # Ищем первую кликабельную строку с автомобилем (вторая строка, первая - заголовок)
            # Строка может быть кликабельной или содержать ссылку
            vehicle_row = page.locator('table tr').nth(1)
            
            # Пытаемся найти ссылку внутри строки
            link = vehicle_row.locator('a').first
            
            if await link.count() > 0:
                await link.click()
            else:
                # Если нет ссылки, кликаем на саму строку
                await vehicle_row.click()
            
            # Ждем загрузки страницы с деталями автомобиля
            await page.wait_for_load_state('networkidle', timeout=15000)
            await page.wait_for_timeout(2000)
            
            logger.info("Clicked on vehicle from results")
            
        except Exception as e:
            logger.error(f"Failed to click vehicle: {e}")
            raise Exception(f"Failed to select vehicle: {e}")
    
    async def _search_part_in_catalog(self, page, part_name: str) -> List[Dict]:
        """Поиск запчасти в каталоге OEM"""
        try:
            # Ищем поле поиска в каталоге
            search_input = page.locator('input[type="text"][placeholder*="поиск"], input[type="search"], input.search-input').first
            
            await search_input.fill(part_name)
            await search_input.press('Enter')
            
            # Ждем результатов поиска
            await page.wait_for_timeout(3000)
            
            # Извлекаем OEM артикулы из результатов
            oem_parts = []
            
            # Ищем элементы с артикулами (могут быть в разных форматах)
            # Обычно артикулы в таблице или списке
            article_elements = await page.locator('td.article, .part-number, .oem-number, td:has-text("")').all()
            
            for element in article_elements:
                text = await element.text_content()
                text = text.strip()
                
                # Проверяем что это похоже на артикул (буквы и цифры)
                if text and len(text) > 5 and any(c.isalnum() for c in text):
                    # Пытаемся получить название запчасти из соседних элементов
                    parent = element.locator('xpath=..')
                    part_name_elem = parent.locator('td').nth(1)  # Обычно название во второй колонке
                    
                    try:
                        part_desc = await part_name_elem.text_content()
                    except:
                        part_desc = part_name
                    
                    oem_parts.append({
                        'article': text,
                        'name': part_desc.strip(),
                        'source': 'OEM Catalog'
                    })
            
            logger.info(f"Found {len(oem_parts)} OEM parts")
            
            return oem_parts
            
        except Exception as e:
            logger.error(f"Failed to search part in catalog: {e}")
            return []


# Singleton instance
oem_parser = AutotradeOEMParser()


if __name__ == "__main__":
    # Тестирование
    async def test():
        logging.basicConfig(level=logging.INFO)
        
        vin = "XW8BJ21Z6AK253512"
        part_name = "шаровая опора"
        
        result = await oem_parser.search_by_vin(vin, part_name)
        
        print("\n=== Result ===")
        print(result)
    
    asyncio.run(test())
