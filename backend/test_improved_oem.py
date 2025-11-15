import asyncio
import os
import re

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
            common_suffixes = ['H5103', '1PA1A']
            for suffix in common_suffixes:
                variants.add(f'{base_number}-{suffix}')
                variants.add(f'ST-{base_number}-{suffix}')
    
    return variants

async def test():
    article = 'SCP10184'
    
    print("="*80)
    print(f"Улучшенный OEM поиск для: {article}")
    print("="*80)
    
    berg = BergClient()
    berg_results = berg.search_by_article(article, analogs=True)
    print(f"\n📦 Berg: {len(berg_results)} результатов")
    
    # Собираем уникальные артикулы (не сам SCP10184)
    berg_articles = set()
    for part in berg_results:
        art = part.get('article', '').strip()
        if art and art.upper() != article.upper():
            berg_articles.add(art)
            if len(berg_articles) >= 20:
                break
    
    print(f"   Уникальных OEM артикулов: {len(berg_articles)}")
    print(f"   Примеры: {list(berg_articles)[:5]}")
    
    # Генерируем варианты
    all_variants = set()
    for art in berg_articles:
        variants = generate_article_variants(art)
        all_variants.update(variants)
    
    print(f"   Всего вариантов для поиска: {len(all_variants)}")
    
    # Ищем в Autotrade
    print(f"\n🔍 Поиск в Autotrade (топ 10 вариантов):")
    autotrade = AutotradeClient()
    loop = asyncio.get_event_loop()
    total_found = 0
    found_variants = []
    
    for variant in list(all_variants)[:10]:
        results = await loop.run_in_executor(None, lambda v=variant: autotrade.search_by_article(v))
        if results:
            total_found += len(results)
            found_variants.append((variant, len(results)))
            print(f"   ✅ {variant}: {len(results)} шт")
    
    print(f"\n{'='*80}")
    print(f"📊 РЕЗУЛЬТАТ:")
    print(f"   Нашли через варианты: {len(found_variants)}")
    print(f"   Всего предложений: {total_found}")
    print(f"{'='*80}")
    
    if found_variants:
        print(f"\n✅ Успешные варианты:")
        for v, count in found_variants[:3]:
            print(f"   • {v} → {count} предложений")

asyncio.run(test())
