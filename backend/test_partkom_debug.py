#!/usr/bin/env python3
"""
Детальная отладка парсера Part-Kom
"""
import sys
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_partkom_login():
    """Тест авторизации на Part-Kom с детальной отладкой"""
    
    print("=" * 80)
    print("ТЕСТ ПАРСЕРА PART-KOM")
    print("=" * 80)
    
    base_url = "https://b2b.part-kom.ru"
    username = "carworkshop"
    password = "Qq23321q"
    test_vin = "JTMKD31V105022682"
    
    playwright = None
    browser = None
    
    try:
        print(f"\n📋 Параметры:")
        print(f"  URL: {base_url}")
        print(f"  Логин: {username}")
        print(f"  VIN: {test_vin}")
        
        print("\n🚀 Запуск браузера...")
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=True,  # Headless для облака
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # Шаг 1: Переход на главную
        print(f"\n📍 Шаг 1: Переход на {base_url}")
        page.goto(base_url, timeout=30000, wait_until='domcontentloaded')
        time.sleep(3)
        page.screenshot(path='/tmp/partkom_1_homepage.png')
        print("  ✅ Скриншот: /tmp/partkom_1_homepage.png")
        
        # Проверяем текущий URL
        current_url = page.url
        print(f"  Текущий URL: {current_url}")
        
        # Шаг 2: Поиск формы входа
        print("\n🔍 Шаг 2: Поиск формы входа")
        
        # Проверяем различные варианты
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем все input поля
        inputs = soup.find_all('input')
        print(f"  Найдено input полей: {len(inputs)}")
        for inp in inputs[:10]:
            print(f"    - type={inp.get('type')}, name={inp.get('name')}, placeholder={inp.get('placeholder')}")
        
        # Ищем все кнопки
        buttons = soup.find_all('button')
        print(f"  Найдено кнопок: {len(buttons)}")
        for btn in buttons[:5]:
            print(f"    - text={btn.get_text(strip=True)[:30]}, type={btn.get('type')}")
        
        # Ищем ссылки на вход
        links = soup.find_all('a')
        login_links = [link for link in links if 'вход' in link.get_text().lower() or 'login' in link.get_text().lower()]
        print(f"  Найдено ссылок на вход: {len(login_links)}")
        for link in login_links:
            print(f"    - {link.get_text(strip=True)} -> {link.get('href')}")
        
        # Пробуем кликнуть на ссылку входа
        if login_links:
            print("\n🖱️ Шаг 3: Клик на ссылку входа")
            login_selectors = [
                'a:has-text("Вход")',
                'a:has-text("Войти")',
                'button:has-text("Войти")',
                '.login-link',
                '#login-btn'
            ]
            
            clicked = False
            for selector in login_selectors:
                try:
                    elem = page.query_selector(selector)
                    if elem and elem.is_visible():
                        print(f"  Кликаем: {selector}")
                        elem.click()
                        clicked = True
                        time.sleep(3)
                        page.screenshot(path='/tmp/partkom_2_after_click.png')
                        print("  ✅ Скриншот: /tmp/partkom_2_after_click.png")
                        break
                except Exception as e:
                    print(f"  ❌ Ошибка с {selector}: {e}")
                    continue
            
            if not clicked:
                print("  ⚠️ Не удалось кликнуть, пробуем прямой переход на /login")
                page.goto(f"{base_url}/login", timeout=30000)
                time.sleep(3)
        else:
            print("\n🔗 Шаг 3: Прямой переход на /login")
            page.goto(f"{base_url}/login", timeout=30000)
            time.sleep(3)
        
        page.screenshot(path='/tmp/partkom_3_login_page.png')
        print("  ✅ Скриншот: /tmp/partkom_3_login_page.png")
        
        # Шаг 4: Заполнение формы
        print("\n✍️ Шаг 4: Заполнение формы входа")
        
        # Получаем актуальный HTML
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем поля ввода
        username_filled = False
        password_filled = False
        
        # Варианты селекторов для логина
        username_selectors = [
            'input[name="username"]',
            'input[name="login"]',
            'input[name="email"]',
            'input[id="username"]',
            'input[id="login"]',
            'input[placeholder*="огин"]',
            'input[type="text"]'
        ]
        
        for selector in username_selectors:
            try:
                elem = page.query_selector(selector)
                if elem and elem.is_visible():
                    print(f"  Заполняем логин: {selector}")
                    elem.fill(username)
                    username_filled = True
                    time.sleep(1)
                    break
            except Exception as e:
                print(f"  ⚠️ {selector}: {e}")
        
        # Варианты селекторов для пароля
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[id="password"]',
            'input[placeholder*="ароль"]'
        ]
        
        for selector in password_selectors:
            try:
                elem = page.query_selector(selector)
                if elem and elem.is_visible():
                    print(f"  Заполняем пароль: {selector}")
                    elem.fill(password)
                    password_filled = True
                    time.sleep(1)
                    break
            except Exception as e:
                print(f"  ⚠️ {selector}: {e}")
        
        if username_filled and password_filled:
            print("  ✅ Форма заполнена")
        else:
            print(f"  ❌ Проблема: логин={username_filled}, пароль={password_filled}")
        
        page.screenshot(path='/tmp/partkom_4_form_filled.png')
        print("  ✅ Скриншот: /tmp/partkom_4_form_filled.png")
        
        # Шаг 5: Отправка формы
        print("\n🚀 Шаг 5: Отправка формы")
        
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Войти")',
            'button:has-text("Вход")',
            '.btn-login',
            '.submit-btn'
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                elem = page.query_selector(selector)
                if elem and elem.is_visible():
                    print(f"  Кликаем submit: {selector}")
                    elem.click()
                    submitted = True
                    time.sleep(4)
                    break
            except Exception as e:
                print(f"  ⚠️ {selector}: {e}")
        
        if not submitted:
            print("  ⚠️ Не нашли кнопку, пробуем Enter")
            try:
                page.keyboard.press('Enter')
                time.sleep(4)
            except:
                pass
        
        page.screenshot(path='/tmp/partkom_5_after_submit.png')
        print("  ✅ Скриншот: /tmp/partkom_5_after_submit.png")
        
        # Шаг 6: Проверка авторизации
        print("\n✔️ Шаг 6: Проверка авторизации")
        current_url = page.url
        print(f"  Текущий URL: {current_url}")
        
        if 'login' not in current_url.lower():
            print("  ✅ ВХОД ВЫПОЛНЕН УСПЕШНО!")
            
            # Шаг 7: Поиск по VIN
            print(f"\n🔍 Шаг 7: Поиск по VIN {test_vin}")
            
            # Ищем поле поиска
            search_selectors = [
                'input[type="search"]',
                'input[name="search"]',
                'input[placeholder*="Поиск"]',
                'input[placeholder*="VIN"]',
                'input.search',
                '#search-input'
            ]
            
            search_found = False
            for selector in search_selectors:
                try:
                    elem = page.query_selector(selector)
                    if elem and elem.is_visible():
                        print(f"  Вводим VIN в: {selector}")
                        elem.fill(test_vin)
                        time.sleep(1)
                        elem.press('Enter')
                        search_found = True
                        time.sleep(5)
                        break
                except Exception as e:
                    print(f"  ⚠️ {selector}: {e}")
            
            if search_found:
                page.screenshot(path='/tmp/partkom_6_search_result.png')
                print("  ✅ Скриншот результата: /tmp/partkom_6_search_result.png")
                
                # Анализ результатов
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                print("\n📊 Анализ результатов:")
                # Ищем информацию об авто
                text = soup.get_text()
                if test_vin in text:
                    print("  ✅ VIN найден на странице")
                
                # Ищем таблицы
                tables = soup.find_all('table')
                print(f"  Найдено таблиц: {len(tables)}")
                
                # Ищем ссылки/категории
                links = soup.find_all('a', limit=50)
                part_links = [l for l in links if len(l.get_text(strip=True)) > 5]
                print(f"  Найдено ссылок: {len(part_links)}")
                if part_links:
                    print("  Первые 5 ссылок:")
                    for link in part_links[:5]:
                        print(f"    - {link.get_text(strip=True)[:50]}")
                
            else:
                print("  ❌ Не нашли поле поиска")
                page.screenshot(path='/tmp/partkom_6_no_search.png')
        else:
            print("  ❌ ВХОД НЕ ВЫПОЛНЕН - все еще на странице логина")
            
            # Проверяем ошибки
            html = page.content()
            if 'ошибка' in html.lower() or 'error' in html.lower():
                print("  ⚠️ Обнаружена ошибка входа")
        
        print("\n✅ Тест завершен")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
    
    print("\n" + "=" * 80)
    print("ТЕСТ ЗАВЕРШЕН")
    print("Проверьте скриншоты в /tmp/partkom_*.png")
    print("=" * 80)

if __name__ == "__main__":
    test_partkom_login()
