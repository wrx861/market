import asyncio
import os

os.environ['ROSSKO_API_KEY1'] = '18b5c3be3f488acd8af5791a2ae96fc5'
os.environ['ROSSKO_API_KEY2'] = 'e0f20f53362c826845b8a4a2b2fbef8b'
os.environ['AUTOTRADE_LOGIN'] = 'car.workshop72@mail.ru'
os.environ['AUTOTRADE_PASSWORD'] = 'Qq23321q'
os.environ['AUTOTRADE_API_KEY'] = 'd1db0fa6d842bab4186d9c6a511d04d'
os.environ['AUTOTRADE_API_URL'] = 'https://api2.autotrade.su/?json'
os.environ['BERG_API_KEY'] = '0fdaa3d7d2e65cc60f684ea6edb9f8e2a1e37ce5c7059067408a17bdb8d65e44'

from autotrade_client import AutotradeClient
from berg_client import BergClient

async def test():
    article = '15208AA100'
    
    print(f"\n{'='*60}")
    print(f"Поиск по артикулу: {article}")
    print(f"{'='*60}\n")
    
    # Autotrade
    print("📦 AUTOTRADE:")
    autotrade = AutotradeClient()
    loop = asyncio.get_event_loop()
    at_results = await loop.run_in_executor(None, lambda: autotrade.search_by_article(article))
    
    at_in_stock = [r for r in at_results if r.get('in_stock', False)]
    at_on_order = [r for r in at_results if not r.get('in_stock', False)]
    
    print(f"  ✅ Всего: {len(at_results)}")
    print(f"  📍 В наличии: {len(at_in_stock)}")
    print(f"  ⏳ Под заказ: {len(at_on_order)}")
    
    if at_in_stock:
        print(f"\n  Примеры В НАЛИЧИИ:")
        for r in at_in_stock[:3]:
            print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r.get('warehouse', 'N/A')}")
    
    # Berg
    print(f"\n📦 BERG:")
    berg = BergClient()
    berg_results = berg.search_by_article(article, analogs=True)
    
    berg_in_stock = [r for r in berg_results if r.get('in_stock', False)]
    berg_on_order = [r for r in berg_results if not r.get('in_stock', False)]
    
    print(f"  ✅ Всего: {len(berg_results)}")
    print(f"  📍 В наличии: {len(berg_in_stock)}")
    print(f"  ⏳ Под заказ: {len(berg_on_order)}")
    
    if berg_in_stock:
        print(f"\n  Примеры В НАЛИЧИИ:")
        for r in berg_in_stock[:3]:
            print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r.get('warehouse', 'N/A')}")

asyncio.run(test())
