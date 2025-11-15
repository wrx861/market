import asyncio
import os
import logging
import re

logging.basicConfig(level=logging.INFO)

os.environ['AUTOTRADE_LOGIN'] = 'car.workshop72@mail.ru'
os.environ['AUTOTRADE_PASSWORD'] = 'Qq23321q'
os.environ['AUTOTRADE_API_KEY'] = 'd1db0fa6d842bab4186d9c6a511d04d'
os.environ['AUTOTRADE_API_URL'] = 'https://api2.autotrade.su/?json'
os.environ['BERG_API_KEY'] = '0fdaa3d7d2e65cc60f684ea6edb9f8e2a1e37ce5c7059067408a17bdb8d65e44'

from autotrade_client import AutotradeClient
from berg_client import BergClient

def generate_article_variants(article: str) -> set:
    variants = {article}
    no_dash = article.replace('-', '')
    variants.add(no_dash)
    
    if not article.upper().startswith('ST-') and not article.upper().startswith('ST'):
        variants.add(f'ST-{article}')
        variants.add(f'ST-{no_dash}')
    
    digits = re.findall(r'\d+', article)
    if digits:
        base_number = digits[0]
        if len(base_number) >= 5:
            common_suffixes = ['H5103', '1PA1A', 'AA100', '35503']
            for suffix in common_suffixes:
                variants.add(f'{base_number}-{suffix}')
                variants.add(f'ST-{base_number}-{suffix}')
    
    return variants

async def test():
    article = 'SCP10184'
    
    print("="*80)
    print(f"Полный тест OEM поиска для: {article}")
    print("="*80)
    
    # 1. Прямой поиск Autotrade
    print("\n1️⃣ Прямой поиск Autotrade:")
    autotrade = AutotradeClient()
    loop = asyncio.get_event_loop()
    direct_results = await loop.run_in_executor(None, lambda: autotrade.search_by_article(article))
    print(f"   Найдено: {len(direct_results)} результатов")
    
    # 2. Поиск в Berg
    print("\n2️⃣ Поиск в Berg:")
    berg = BergClient()
    berg_results = berg.search_by_article(article, analogs=True)
    print(f"   Найдено: {len(berg_results)} результатов")
    
    # 3. Собираем OEM и генерируем варианты
    print("\n3️⃣ Сбор OEM и генерация вариантов:")
    oem_numbers = set()
    
    for part in berg_results[:5]:
        article_berg = part.get('article', '').strip()
        if article_berg and article_berg.upper() != article.upper():
            variants = generate_article_variants(article_berg)
            oem_numbers.update(variants)
            print(f"   OEM: {article_berg} → {len(variants)} вариантов")
    
    print(f"\n   Всего уникальных вариантов для поиска: {len(oem_numbers)}")
    
    # 4. Поиск в Autotrade по OEM
    print("\n4️⃣ Поиск в Autotrade по OEM вариантам (топ 5):")
    total_found = 0
    
    for oem in list(oem_numbers)[:5]:
        results = await loop.run_in_executor(None, lambda o=oem: autotrade.search_by_article(o))
        if results:
            total_found += len(results)
            print(f"   ✅ {oem}: {len(results)} результатов")
            for r in results[:1]:
                in_stock = "В НАЛИЧИИ" if r.get('in_stock') else "Под заказ"
                print(f"      • {r['article']} | {r['brand']} | {r['price']}₽ | {in_stock}")
    
    print(f"\n{'='*80}")
    print(f"📊 ИТОГО:")
    print(f"   Прямой поиск: {len(direct_results)}")
    print(f"   OEM поиск: {total_found}")
    print(f"   Всего от Autotrade: {len(direct_results) + total_found}")
    print(f"{'='*80}")

asyncio.run(test())
