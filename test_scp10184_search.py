#!/usr/bin/env python3
"""
Test script for SCP10184 article search issue
Testing why Rossko and Autotrade results are not showing up
"""

import requests
import json
import os
import sys
import time
from pathlib import Path

def load_env_vars():
    """Load environment variables from frontend/.env"""
    env_file = Path(__file__).parent / "frontend" / ".env"
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    return env_vars

def test_scp10184_search():
    """Test search for article SCP10184 as specified in review request"""
    print("=" * 80)
    print("TESTING SEARCH FOR ARTICLE SCP10184")
    print("=" * 80)
    print("🎯 ЗАДАЧА: Протестировать поиск по артикулу SCP10184")
    print("🎯 ПРОБЛЕМА: Не показываются результаты от Rossko и Autotrade")
    print("🎯 ОЖИДАЕТСЯ: Результаты от всех поставщиков (Rossko, Autotrade, Berg)")
    print("🎯 ENDPOINT: POST /api/search с body: {'article': 'SCP10184', 'telegram_id': 508352361}")
    print("=" * 80)
    
    # Load environment variables
    env_vars = load_env_vars()
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    print(f"Backend URL: {backend_url}")
    
    # Test endpoint
    endpoint = f"{backend_url}/api/search/article"
    print(f"Testing endpoint: {endpoint}")
    
    # Test data from review request
    test_data = {
        "article": "SCP10184",
        "telegram_id": 508352361
    }
    
    print(f"Request payload: {json.dumps(test_data, indent=2)}")
    
    try:
        print(f"\n🚀 Отправляем POST запрос для артикула SCP10184...")
        start_time = time.time()
        
        response = requests.post(
            endpoint,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Time: {duration:.2f} seconds")
        
        if response.status_code == 200:
            print("✅ API returned 200 OK")
            
            try:
                response_data = response.json()
                
                # Analyze results by supplier
                success = analyze_scp10184_results(response_data)
                
                if success:
                    print(f"✅ SCP10184 search completed successfully")
                else:
                    print(f"❌ SCP10184 search has issues with supplier results")
                
                return success, response_data
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {response.text}")
                return False, None
                
        else:
            print(f"❌ API returned error status: {response.status_code}")
            print(f"Response text: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False, None

def analyze_scp10184_results(response_data):
    """Analyze SCP10184 search results by supplier"""
    print(f"\n--- АНАЛИЗ РЕЗУЛЬТАТОВ ПОИСКА SCP10184 ---")
    
    # Check basic response structure
    if not isinstance(response_data, dict):
        print(f"❌ Response is not a dictionary: {type(response_data)}")
        return False
    
    if response_data.get('status') != 'success':
        print(f"❌ Status is not 'success': {response_data.get('status')}")
        return False
    
    print("✅ Response status is 'success'")
    
    # Check results array
    results = response_data.get('results', [])
    if not isinstance(results, list):
        print(f"❌ Results is not a list: {type(results)}")
        return False
    
    print(f"✅ Found {len(results)} total results")
    
    if len(results) == 0:
        print("❌ No results found - this indicates all suppliers failed")
        return False
    
    # Analyze by supplier
    suppliers = {}
    rossko_results = []
    autotrade_results = []
    berg_results = []
    
    for result in results:
        provider = result.get('provider', 'unknown')
        if provider not in suppliers:
            suppliers[provider] = 0
        suppliers[provider] += 1
        
        if provider == 'rossko':
            rossko_results.append(result)
        elif provider == 'autotrade':
            autotrade_results.append(result)
        elif provider == 'berg':
            berg_results.append(result)
    
    print(f"\n--- РЕЗУЛЬТАТЫ ПО ПОСТАВЩИКАМ ---")
    for provider, count in suppliers.items():
        print(f"📊 {provider}: {count} результатов")
    
    # Check each supplier
    has_rossko = len(rossko_results) > 0
    has_autotrade = len(autotrade_results) > 0
    has_berg = len(berg_results) > 0
    
    print(f"\n--- ПРОВЕРКА ПОСТАВЩИКОВ ---")
    print(f"🔍 Rossko results: {len(rossko_results)} {'✅' if has_rossko else '❌'}")
    print(f"🔍 Autotrade results: {len(autotrade_results)} {'✅' if has_autotrade else '❌'}")
    print(f"🔍 Berg results: {len(berg_results)} {'✅' if has_berg else '❌'}")
    
    # Show examples from each supplier
    if has_rossko:
        print(f"\n--- ПРИМЕРЫ ОТ ROSSKO ---")
        for i, result in enumerate(rossko_results[:3]):
            print(f"  {i+1}. {result.get('brand', 'Unknown')} {result.get('article', 'Unknown')}")
            print(f"     Название: {result.get('name', 'Unknown')}")
            print(f"     Цена: {result.get('price', 0)} руб")
            print(f"     Доставка: {result.get('delivery_days', 'Unknown')} дней")
            print(f"     Поставщик: {result.get('supplier', 'Unknown')}")
    else:
        print(f"\n❌ ROSSKO НЕ ВЕРНУЛ РЕЗУЛЬТАТОВ")
        print("⚠️  Возможные причины:")
        print("   - Проблемы с Rossko API")
        print("   - Неправильные учетные данные")
        print("   - Артикул не найден в базе Rossko")
        print("   - Rate limiting")
    
    if has_autotrade:
        print(f"\n--- ПРИМЕРЫ ОТ AUTOTRADE ---")
        for i, result in enumerate(autotrade_results[:3]):
            print(f"  {i+1}. {result.get('brand', 'Unknown')} {result.get('article', 'Unknown')}")
            print(f"     Название: {result.get('name', 'Unknown')}")
            print(f"     Цена: {result.get('price', 0)} руб")
            print(f"     Склад: {result.get('warehouse', 'Unknown')}")
            print(f"     Доставка: {result.get('delivery_days', 'Unknown')} дней")
    else:
        print(f"\n❌ AUTOTRADE НЕ ВЕРНУЛ РЕЗУЛЬТАТОВ")
        print("⚠️  Возможные причины:")
        print("   - Проблемы с Autotrade API")
        print("   - Неправильная аутентификация")
        print("   - Артикул не найден в базе Autotrade")
        print("   - Rate limiting (1 запрос в секунду)")
    
    if has_berg:
        print(f"\n--- ПРИМЕРЫ ОТ BERG ---")
        for i, result in enumerate(berg_results[:3]):
            print(f"  {i+1}. {result.get('brand', 'Unknown')} {result.get('article', 'Unknown')}")
            print(f"     Название: {result.get('name', 'Unknown')}")
            print(f"     Цена: {result.get('price', 0)} руб")
            print(f"     Склад: {result.get('warehouse', 'Unknown')}")
            print(f"     Доставка: {result.get('delivery_days', 'Unknown')} дней")
    else:
        print(f"\n❌ BERG НЕ ВЕРНУЛ РЕЗУЛЬТАТОВ")
        print("⚠️  Возможные причины:")
        print("   - Проблемы с Berg API")
        print("   - Неправильный API ключ")
        print("   - Артикул не найден в базе Berg")
    
    # Summary
    working_suppliers = sum([has_rossko, has_autotrade, has_berg])
    
    print(f"\n--- ИТОГОВАЯ ОЦЕНКА ---")
    print(f"✅ Работающих поставщиков: {working_suppliers}/3")
    print(f"✅ Общее количество результатов: {len(results)}")
    
    if working_suppliers == 0:
        print(f"\n❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: НИ ОДИН ПОСТАВЩИК НЕ РАБОТАЕТ")
        print(f"   ❌ Требуется проверка всех API интеграций")
        return False
    elif working_suppliers == 1:
        print(f"\n⚠️  ЧАСТИЧНАЯ ПРОБЛЕМА: РАБОТАЕТ ТОЛЬКО 1 ПОСТАВЩИК")
        if has_berg and not has_rossko and not has_autotrade:
            print(f"   ❌ Rossko и Autotrade не работают (основная проблема из review request)")
        return False
    elif working_suppliers == 2:
        print(f"\n⚠️  ЧАСТИЧНАЯ ПРОБЛЕМА: РАБОТАЕТ 2 ИЗ 3 ПОСТАВЩИКОВ")
        if not has_rossko or not has_autotrade:
            print(f"   ❌ Проблема с Rossko или Autotrade (основная проблема из review request)")
        return False
    else:
        print(f"\n✅ ВСЕ ПОСТАВЩИКИ РАБОТАЮТ КОРРЕКТНО")
        print(f"   ✅ Rossko, Autotrade и Berg возвращают результаты")
        return True

def test_st_54630_h5103_search():
    """Test search for article ST-54630-H5103 mentioned in review request"""
    print("\n" + "=" * 80)
    print("TESTING SEARCH FOR ARTICLE ST-54630-H5103")
    print("=" * 80)
    print("🎯 КОНТЕКСТ: Пользователь говорит что ST-54630-H5103 есть в Autotrade")
    print("🎯 ОЖИДАЕТСЯ: Результаты от Autotrade в Тюмени по лучшей цене чем Berg")
    print("=" * 80)
    
    # Load environment variables
    env_vars = load_env_vars()
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    # Test endpoint
    endpoint = f"{backend_url}/api/search/article"
    
    # Test data
    test_data = {
        "article": "ST-54630-H5103",
        "telegram_id": 508352361
    }
    
    print(f"Request payload: {json.dumps(test_data, indent=2)}")
    
    try:
        print(f"\n🚀 Отправляем POST запрос для артикула ST-54630-H5103...")
        start_time = time.time()
        
        response = requests.post(
            endpoint,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Time: {duration:.2f} seconds")
        
        if response.status_code == 200:
            print("✅ API returned 200 OK")
            
            try:
                response_data = response.json()
                
                # Analyze results specifically for Autotrade vs Berg comparison
                success = analyze_st_54630_results(response_data)
                
                return success, response_data
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                return False, None
                
        else:
            print(f"❌ API returned error status: {response.status_code}")
            print(f"Response text: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False, None

def analyze_st_54630_results(response_data):
    """Analyze ST-54630-H5103 results to compare Autotrade vs Berg prices"""
    print(f"\n--- АНАЛИЗ РЕЗУЛЬТАТОВ ST-54630-H5103 ---")
    
    results = response_data.get('results', [])
    print(f"✅ Found {len(results)} total results")
    
    if len(results) == 0:
        print("❌ No results found")
        return False
    
    # Filter by supplier
    autotrade_results = [r for r in results if r.get('provider') == 'autotrade']
    berg_results = [r for r in results if r.get('provider') == 'berg']
    
    print(f"\n--- СРАВНЕНИЕ AUTOTRADE VS BERG ---")
    print(f"📊 Autotrade results: {len(autotrade_results)}")
    print(f"📊 Berg results: {len(berg_results)}")
    
    if len(autotrade_results) == 0:
        print("❌ Autotrade не вернул результатов для ST-54630-H5103")
        print("   Это подтверждает проблему из review request")
        return False
    
    if len(berg_results) == 0:
        print("⚠️  Berg не вернул результатов для ST-54630-H5103")
    
    # Show Autotrade results
    print(f"\n--- РЕЗУЛЬТАТЫ ОТ AUTOTRADE ---")
    autotrade_tyumen_results = []
    
    for i, result in enumerate(autotrade_results):
        warehouse = result.get('warehouse', '')
        price = result.get('price', 0)
        quantity = result.get('quantity', 0)
        delivery_days = result.get('delivery_days', 'Unknown')
        
        print(f"  {i+1}. {result.get('brand', 'Unknown')} {result.get('article', 'Unknown')}")
        print(f"     Цена: {price} руб")
        print(f"     Склад: {warehouse}")
        print(f"     Количество: {quantity} шт")
        print(f"     Доставка: {delivery_days} дней")
        
        # Check if it's Tyumen warehouse
        if 'тюмень' in warehouse.lower():
            autotrade_tyumen_results.append(result)
    
    # Show Berg results for comparison
    if berg_results:
        print(f"\n--- РЕЗУЛЬТАТЫ ОТ BERG ---")
        for i, result in enumerate(berg_results):
            warehouse = result.get('warehouse', '')
            price = result.get('price', 0)
            quantity = result.get('quantity', 0)
            delivery_days = result.get('delivery_days', 'Unknown')
            
            print(f"  {i+1}. {result.get('brand', 'Unknown')} {result.get('article', 'Unknown')}")
            print(f"     Цена: {price} руб")
            print(f"     Склад: {warehouse}")
            print(f"     Количество: {quantity} шт")
            print(f"     Доставка: {delivery_days} дней")
    
    # Price comparison
    if autotrade_tyumen_results and berg_results:
        print(f"\n--- СРАВНЕНИЕ ЦЕН ТЮМЕНЬ (AUTOTRADE) VS BERG ---")
        
        tyumen_prices = [r.get('price', 0) for r in autotrade_tyumen_results if r.get('price', 0) > 0]
        berg_prices = [r.get('price', 0) for r in berg_results if r.get('price', 0) > 0]
        
        if tyumen_prices and berg_prices:
            min_tyumen_price = min(tyumen_prices)
            min_berg_price = min(berg_prices)
            
            print(f"💰 Лучшая цена Autotrade (Тюмень): {min_tyumen_price} руб")
            print(f"💰 Лучшая цена Berg: {min_berg_price} руб")
            
            if min_tyumen_price < min_berg_price:
                print(f"✅ Autotrade в Тюмени дешевле на {min_berg_price - min_tyumen_price:.2f} руб")
                print(f"   Это подтверждает утверждение пользователя")
            else:
                print(f"❌ Berg дешевле на {min_tyumen_price - min_berg_price:.2f} руб")
                print(f"   Это противоречит утверждению пользователя")
    
    # Final assessment
    if len(autotrade_results) > 0:
        print(f"\n✅ ST-54630-H5103 найден в Autotrade")
        if len(autotrade_tyumen_results) > 0:
            print(f"✅ Есть предложения из Тюмени")
        else:
            print(f"⚠️  Нет предложений из Тюмени")
        return True
    else:
        print(f"\n❌ ST-54630-H5103 НЕ найден в Autotrade")
        print(f"   Это подтверждает проблему из review request")
        return False

def check_backend_logs_for_scp10184():
    """Check backend logs for SCP10184 search activity"""
    print(f"\n--- ПРОВЕРКА ЛОГОВ BACKEND ДЛЯ SCP10184 ---")
    
    try:
        import subprocess
        
        # Check for SCP10184 in logs
        log_command = ["docker", "logs", "market-backend", "--tail=200"]
        
        print(f"Выполняем команду: {' '.join(log_command)}")
        
        result = subprocess.run(
            log_command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logs = result.stdout
            
            # Search for SCP10184 related entries
            scp_lines = []
            for line in logs.split('\n'):
                if 'SCP10184' in line.upper():
                    scp_lines.append(line)
            
            if scp_lines:
                print(f"✅ Найдено {len(scp_lines)} записей с SCP10184:")
                for line in scp_lines[-10:]:  # Show last 10
                    print(f"   {line}")
            else:
                print(f"⚠️  Записи с SCP10184 не найдены в последних 200 строках")
            
            # Search for supplier-specific activity
            suppliers = ['rossko', 'autotrade', 'berg']
            for supplier in suppliers:
                supplier_lines = []
                for line in logs.split('\n'):
                    if supplier.lower() in line.lower():
                        supplier_lines.append(line)
                
                if supplier_lines:
                    print(f"\n📊 {supplier.upper()} активность (последние 5 записей):")
                    for line in supplier_lines[-5:]:
                        print(f"   {line}")
                else:
                    print(f"\n⚠️  {supplier.upper()} активность не найдена")
        
        else:
            print(f"❌ Ошибка выполнения docker logs: {result.stderr}")
            
            # Fallback to supervisor logs
            print(f"\n--- FALLBACK: ПРОВЕРКА SUPERVISOR ЛОГОВ ---")
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    print(f"\n--- {log_file} (поиск SCP10184) ---")
                    
                    # Search for SCP10184
                    grep_result = subprocess.run(
                        ["grep", "-i", "scp10184", log_file],
                        capture_output=True,
                        text=True
                    )
                    
                    if grep_result.stdout:
                        print(f"🔍 Найдено SCP10184:")
                        for line in grep_result.stdout.strip().split('\n')[-10:]:
                            print(f"   {line}")
                    else:
                        print(f"⚠️  SCP10184 не найден в {log_file}")
                else:
                    print(f"❌ Log file not found: {log_file}")
                    
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

def main():
    """Main test function"""
    print("🚀 STARTING SCP10184 SEARCH TESTING")
    print("=" * 80)
    
    # Test 1: SCP10184 search
    print("\n📋 TEST 1: SCP10184 SEARCH")
    scp_success, scp_data = test_scp10184_search()
    
    # Test 2: ST-54630-H5103 search
    print("\n📋 TEST 2: ST-54630-H5103 SEARCH")
    st_success, st_data = test_st_54630_h5103_search()
    
    # Test 3: Check backend logs
    print("\n📋 TEST 3: BACKEND LOGS ANALYSIS")
    check_backend_logs_for_scp10184()
    
    # Summary
    print("\n" + "=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)
    
    if scp_success:
        print("✅ SCP10184: Поиск работает, все поставщики возвращают результаты")
    else:
        print("❌ SCP10184: Проблемы с поставщиками Rossko и/или Autotrade")
    
    if st_success:
        print("✅ ST-54630-H5103: Найден в Autotrade")
    else:
        print("❌ ST-54630-H5103: НЕ найден в Autotrade (подтверждает проблему)")
    
    print("\n🎯 РЕКОМЕНДАЦИИ:")
    if not scp_success or not st_success:
        print("1. Проверить API ключи и учетные данные для Rossko и Autotrade")
        print("2. Проверить rate limiting и таймауты")
        print("3. Проверить логи на наличие ошибок аутентификации")
        print("4. Проверить что артикулы существуют в базах поставщиков")
    else:
        print("Все тесты прошли успешно!")

if __name__ == "__main__":
    main()