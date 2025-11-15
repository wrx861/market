import asyncio
import sys
import os

# Устанавливаем переменные окружения
os.environ['ROSSKO_API_KEY1'] = '18b5c3be3f488acd8af5791a2ae96fc5'
os.environ['ROSSKO_API_KEY2'] = 'e0f20f53362c826845b8a4a2b2fbef8b'
os.environ['AUTOTRADE_LOGIN'] = 'car.workshop72@mail.ru'
os.environ['AUTOTRADE_PASSWORD'] = 'Qq23321q'
os.environ['AUTOTRADE_API_KEY'] = 'd1db0fa6d842bab4186d9c6a511d04d'
os.environ['AUTOTRADE_API_URL'] = 'https://api2.autotrade.su/?json'
os.environ['BERG_API_KEY'] = '0fdaa3d7d2e65cc60f684ea6edb9f8e2a1e37ce5c7059067408a17bdb8d65e44'

from rossko_client import RosskoClient
from autotrade_client import AutotradeClient
from berg_client import BergClient
from autostels_client import AutostelsClient

async def test_all_suppliers():
    article = 'SCP10184'
    
    print("="*80)
    print(f"Тестирование поиска артикула: {article}")
    print("="*80)
    print()
    
    # Rossko
    print("📦 ROSSKO:")
    try:
        rossko = RosskoClient()
        rossko_results = rossko.search_by_article(article)
        
        in_stock = [r for r in rossko_results if r.get('in_stock', False)]
        on_order = [r for r in rossko_results if not r.get('in_stock', False)]
        
        print(f"  ✅ Всего найдено: {len(rossko_results)}")
        print(f"  📍 В наличии: {len(in_stock)}")
        print(f"  ⏳ Под заказ: {len(on_order)}")
        
        if in_stock:
            print(f"\n  Примеры В НАЛИЧИИ (первые 3):")
            for r in in_stock[:3]:
                print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r['warehouse']} | {r['quantity']} шт")
        
        if on_order:
            print(f"\n  Примеры ПОД ЗАКАЗ (первые 3):")
            for r in on_order[:3]:
                print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r['warehouse']} | {r['delivery_days']} дн")
                
    except Exception as e:
        print(f"  ❌ Ошибка: {str(e)}")
    
    print()
    
    # Autotrade
    print("📦 AUTOTRADE:")
    try:
        autotrade = AutotradeClient()
        loop = asyncio.get_event_loop()
        autotrade_results = await loop.run_in_executor(
            None, 
            lambda: autotrade.search_by_article(article)
        )
        
        in_stock = [r for r in autotrade_results if r.get('in_stock', False)]
        on_order = [r for r in autotrade_results if not r.get('in_stock', False)]
        
        print(f"  ✅ Всего найдено: {len(autotrade_results)}")
        print(f"  📍 В наличии: {len(in_stock)}")
        print(f"  ⏳ Под заказ: {len(on_order)}")
        
        if in_stock:
            print(f"\n  Примеры В НАЛИЧИИ (первые 3):")
            for r in in_stock[:3]:
                print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r['warehouse']} | {r['quantity']} шт")
        
        if on_order:
            print(f"\n  Примеры ПОД ЗАКАЗ (первые 3):")
            for r in on_order[:3]:
                print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r['warehouse']} | {r['delivery_days']} дн")
                
    except Exception as e:
        print(f"  ❌ Ошибка: {str(e)}")
    
    print()
    
    # Berg
    print("📦 BERG:")
    try:
        berg = BergClient()
        berg_results = berg.search_by_article(article, analogs=True)
        
        in_stock = [r for r in berg_results if r.get('in_stock', False)]
        on_order = [r for r in berg_results if not r.get('in_stock', False)]
        
        print(f"  ✅ Всего найдено: {len(berg_results)}")
        print(f"  📍 В наличии: {len(in_stock)}")
        print(f"  ⏳ Под заказ: {len(on_order)}")
        
        if in_stock:
            print(f"\n  Примеры В НАЛИЧИИ (первые 3):")
            for r in in_stock[:3]:
                print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r['warehouse']} | {r['quantity']} шт")
        
        if on_order:
            print(f"\n  Примеры ПОД ЗАКАЗ (первые 3):")
            for r in on_order[:3]:
                print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r['warehouse']} | {r['delivery_days']} дн")
                
    except Exception as e:
        print(f"  ❌ Ошибка: {str(e)}")
    
    print()
    
    # Autostels
    print("📦 AUTOSTELS:")
    try:
        autostels = AutostelsClient()
        autostels_results = autostels.search_by_article(article, in_stock=1, show_cross=1)
        
        in_stock = [r for r in autostels_results if r.get('in_stock', False)]
        on_order = [r for r in autostels_results if not r.get('in_stock', False)]
        
        print(f"  ✅ Всего найдено: {len(autostels_results)}")
        print(f"  📍 В наличии: {len(in_stock)}")
        print(f"  ⏳ Под заказ: {len(on_order)}")
        
        if in_stock:
            print(f"\n  Примеры В НАЛИЧИИ (первые 3):")
            for r in in_stock[:3]:
                print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r['warehouse']} | {r['quantity']} шт")
        
        if on_order:
            print(f"\n  Примеры ПОД ЗАКАЗ (первые 3):")
            for r in on_order[:3]:
                print(f"    • {r['article']} | {r['brand']} | {r['price']}₽ | {r['warehouse']} | {r['delivery_days']} дн")
                
    except Exception as e:
        print(f"  ❌ Ошибка: {str(e)}")
    
    print()
    print("="*80)
    print("Тестирование завершено")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_all_suppliers())
