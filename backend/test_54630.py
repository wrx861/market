import asyncio
import os

os.environ['AUTOTRADE_LOGIN'] = 'car.workshop72@mail.ru'
os.environ['AUTOTRADE_PASSWORD'] = 'Qq23321q'
os.environ['AUTOTRADE_API_KEY'] = 'd1db0fa6d842bab4186d9c6a511d04d'
os.environ['AUTOTRADE_API_URL'] = 'https://api2.autotrade.su/?json'
os.environ['BERG_API_KEY'] = '0fdaa3d7d2e65cc60f684ea6edb9f8e2a1e37ce5c7059067408a17bdb8d65e44'

from autotrade_client import AutotradeClient
from berg_client import BergClient

async def test():
    print("="*80)
    print("Тест: что возвращает Berg для SCP10184")
    print("="*80)
    
    berg = BergClient()
    berg_results = berg.search_by_article('SCP10184', analogs=True)
    
    print(f"\nBerg нашел: {len(berg_results)} результатов")
    print("\nПервые 10 артикулов из Berg:")
    
    oem_set = set()
    for i, r in enumerate(berg_results[:10], 1):
        article = r.get('article', '')
        print(f"{i}. {article} | {r.get('brand', 'N/A')}")
        oem_set.add(article)
    
    print("\n" + "="*80)
    print("Тест: поиск в Autotrade по этим артикулам")
    print("="*80)
    
    autotrade = AutotradeClient()
    loop = asyncio.get_event_loop()
    
    # Тестируем разные варианты артикулов
    test_articles = [
        '54630-1PA1A',  # Как написано на скрине
        '546301PA1A',   # Без дефиса
        '54630-H5103',  # Вариант с H5103
        'ST-54630-H5103'  # С префиксом ST
    ]
    
    for article in test_articles:
        print(f"\n🔍 Поиск: {article}")
        results = await loop.run_in_executor(None, lambda a=article: autotrade.search_by_article(a))
        print(f"   Найдено: {len(results)} результатов")
        
        if results:
            for r in results[:2]:
                in_stock = "✅ В НАЛИЧИИ" if r.get('in_stock') else "⏳ Под заказ"
                print(f"   • {r['article']} | {r['brand']} | {r['price']}₽ | {in_stock}")

asyncio.run(test())
