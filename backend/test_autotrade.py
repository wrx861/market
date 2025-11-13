"""
Тестовый скрипт для проверки ответа Autotrade API
"""
import sys
import json
sys.path.insert(0, '/app/backend')

from autotrade_client import AutotradeClient

# Создаем клиент
client = AutotradeClient()

# Тестируем проблемный артикул
article = "ST-dtw1-395-0"
print(f"Testing article: {article}")
print(f"Auth key: {client.auth_key[:10]}...")
print()

# Делаем запрос
results = client.search_by_article(article, with_stocks_and_prices=True, with_delivery=True)

print(f"Found {len(results)} results")
print()

if results:
    print("=== First result ===")
    print(json.dumps(results[0], indent=2, ensure_ascii=False))
    print()
    
    print("=== All results ===")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['brand']} {result['article']} - {result['price']}р, кол-во: {result['quantity']}, склад: {result['warehouse']}, доставка: {result['delivery_days']} дней")
