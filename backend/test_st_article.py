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

async def test():
    article = 'ST-54630-H5103'
    print(f"Поиск Autotrade: {article}")
    
    autotrade = AutotradeClient()
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, lambda: autotrade.search_by_article(article))
    
    print(f"Найдено: {len(results)} результатов")
    for r in results[:5]:
        print(f"  • {r['article']} | {r['brand']} | {r['price']}₽ | В наличии: {r.get('in_stock', False)}")

asyncio.run(test())
