import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ['ROSSKO_API_KEY1'] = '18b5c3be3f488acd8af5791a2ae96fc5'
os.environ['ROSSKO_API_KEY2'] = 'e0f20f53362c826845b8a4a2b2fbef8b'
os.environ['AUTOTRADE_LOGIN'] = 'car.workshop72@mail.ru'
os.environ['AUTOTRADE_PASSWORD'] = 'Qq23321q'
os.environ['AUTOTRADE_API_KEY'] = 'd1db0fa6d842bab4186d9c6a511d04d'
os.environ['AUTOTRADE_API_URL'] = 'https://api2.autotrade.su/?json'
os.environ['BERG_API_KEY'] = '0fdaa3d7d2e65cc60f684ea6edb9f8e2a1e37ce5c7059067408a17bdb8d65e44'

from autotrade_client import AutotradeClient
from berg_client import BergClient

async def test_oem_search():
    article = 'SCP10184'
    
    print("="*80)
    print(f"Тест поиска по OEM для артикула: {article}")
    print("="*80)
    print()
    
    # 1. Прямой поиск в Autotrade
    print("📦 Шаг 1: Прямой поиск в Autotrade")
    autotrade = AutotradeClient()
    loop = asyncio.get_event_loop()
    autotrade_direct = await loop.run_in_executor(None, lambda: autotrade.search_by_article(article))
    print(f"   Результатов: {len(autotrade_direct)}")
    print()
    
    # 2. Поиск в Berg для получения OEM
    print("📦 Шаг 2: Поиск в Berg для получения OEM номеров")
    berg = BergClient()
    berg_results = berg.search_by_article(article, analogs=True)
    print(f"   Результатов в Berg: {len(berg_results)}")
    
    # Собираем OEM номера
    oem_numbers = set()
    for part in berg_results[:10]:  # Берем первые 10
        oem = part.get('article', '').strip()
        if oem and oem.upper() != article.upper():
            oem_numbers.add(oem)
    
    print(f"   Найдено уникальных OEM: {len(oem_numbers)}")
    print(f"   OEM номера: {list(oem_numbers)[:5]}")
    print()
    
    # 3. Поиск в Autotrade по OEM номерам
    print("📦 Шаг 3: Поиск в Autotrade по OEM номерам")
    autotrade_oem_results = []
    
    for oem in list(oem_numbers)[:3]:  # Проверяем первые 3 OEM
        print(f"   Ищем: {oem}")
        oem_results = await loop.run_in_executor(None, lambda o=oem: autotrade.search_by_article(o))
        print(f"   Найдено: {len(oem_results)}")
        autotrade_oem_results.extend(oem_results)
    
    print()
    print("="*80)
    print("📊 ИТОГО:")
    print(f"   Прямой поиск Autotrade: {len(autotrade_direct)}")
    print(f"   Поиск по OEM: {len(autotrade_oem_results)}")
    print(f"   Всего в Autotrade: {len(autotrade_direct) + len(autotrade_oem_results)}")
    print("="*80)
    
    if autotrade_oem_results:
        print()
        print("✅ Примеры найденных через OEM (первые 3):")
        for r in autotrade_oem_results[:3]:
            in_stock = "✅ В НАЛИЧИИ" if r.get('in_stock') else "⏳ Под заказ"
            print(f"   • {r['article']} | {r['brand']} | {r['price']}₽ | {r.get('warehouse', 'N/A')} | {in_stock}")

asyncio.run(test_oem_search())
