import re

def generate_article_variants(article: str) -> set:
    """Генерирует варианты артикула для поиска"""
    variants = {article}
    
    # Убираем дефисы
    no_dash = article.replace('-', '')
    variants.add(no_dash)
    
    # Добавляем ST- префикс если его нет
    if not article.upper().startswith('ST-') and not article.upper().startswith('ST'):
        variants.add(f'ST-{article}')
        variants.add(f'ST-{no_dash}')
    
    # Пробуем заменить суффиксы
    digits = re.findall(r'\d+', article)
    if digits:
        base_number = digits[0]
        if len(base_number) >= 5:
            common_suffixes = ['H5103', '1PA1A', 'AA100', '35503']
            for suffix in common_suffixes:
                variants.add(f'{base_number}-{suffix}')
                variants.add(f'ST-{base_number}-{suffix}')
    
    return variants

# Тест
test_articles = ['54630-1PA1A', 'SCP10184', '15208AA100']

for article in test_articles:
    print(f"\n{'='*60}")
    print(f"Оригинал: {article}")
    print(f"{'='*60}")
    variants = generate_article_variants(article)
    for i, v in enumerate(sorted(variants), 1):
        print(f"{i}. {v}")
