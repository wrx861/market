import asyncio

# Имитация результатов
article = "RARE123"

# Autotrade - ничего не нашел
autotrade_direct = []

# Berg нашел аналоги
berg_results = [
    {"article": "15208AA100", "brand": "Subaru", "price": 500},
    {"article": "ST-15208-AA100", "brand": "SAT", "price": 121},
    {"article": "26300-35503", "brand": "Hyundai", "price": 450}
]

# Теперь имитируем что Autotrade нашел по OEM
autotrade_oem = [
    {"article": "ST-15208-AA100", "brand": "SAT", "price": 121, "in_stock": True, "warehouse": "Тюмень"},
    {"article": "15208-AA100", "brand": "Subaru Original", "price": 550, "in_stock": False, "warehouse": "Склад"}
]

print("="*60)
print("Демонстрация логики поиска по OEM")
print("="*60)
print()
print(f"🔍 Исходный запрос: {article}")
print()
print(f"1️⃣ Прямой поиск Autotrade: {len(autotrade_direct)} результатов")
print()
print(f"2️⃣ Berg нашел аналоги: {len(berg_results)} результатов")
for r in berg_results:
    print(f"   • {r['article']} | {r['brand']}")
print()
print(f"3️⃣ Поиск в Autotrade по OEM номерам из Berg:")

oem_numbers = set()
for part in berg_results:
    oem = part['article']
    if oem != article:
        oem_numbers.add(oem)

print(f"   OEM номера: {oem_numbers}")
print()
print(f"4️⃣ Autotrade нашел по OEM: {len(autotrade_oem)} результатов")
for r in autotrade_oem:
    in_stock = "✅ В НАЛИЧИИ" if r.get('in_stock') else "⏳ Под заказ"
    print(f"   • {r['article']} | {r['brand']} | {r['price']}₽ | {in_stock}")
print()
print("="*60)
print(f"📊 ИТОГО: {len(autotrade_direct) + len(autotrade_oem)} результатов от Autotrade")
print(f"   (из них {len([r for r in autotrade_oem if r.get('in_stock')])} в наличии)")
print("="*60)
