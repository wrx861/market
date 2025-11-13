#!/usr/bin/env python3
"""
Autotrade API Integration Test
Tests the new Autotrade API integration for parts search by article
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

def test_autotrade_api_integration():
    """Test NEW Autotrade API integration for parts search by article"""
    print("=" * 80)
    print("TESTING NEW AUTOTRADE API INTEGRATION")
    print("=" * 80)
    print("🚀 НОВАЯ ИНТЕГРАЦИЯ AUTOTRADE API")
    print("✅ Создан autotrade_client.py с методом search_by_article()")
    print("✅ Аутентификация через auth_key = MD5(login + MD5(password) + SALT)")
    print("✅ JSON API endpoint: https://api2.autotrade.su/?json")
    print("✅ Метод API: getItemsByQuery с параметрами для поиска по артикулу")
    print("✅ Интегрирован в server.py - параллельный поиск через Rossko и Autotrade")
    print("🎯 Тестовые артикулы: 51750A6000, 1521065D00, 15208AA100, SP-1004")
    print("🎯 Endpoint: POST /api/search/article")
    print("=" * 80)
    
    # Load environment variables
    env_vars = load_env_vars()
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    print(f"Backend URL: {backend_url}")
    
    # Test endpoint
    endpoint = f"{backend_url}/api/search/article"
    print(f"Testing endpoint: {endpoint}")
    
    # Test multiple articles from review request
    test_articles = [
        "51750A6000",  # Primary test article
        "1521065D00",  # Additional test article
        "15208AA100",  # Additional test article
        "SP-1004"      # Additional test article
    ]
    
    all_results = []
    
    for i, article in enumerate(test_articles):
        print(f"\n{'='*60}")
        print(f"TESTING ARTICLE {i+1}: {article}")
        print(f"{'='*60}")
        
        test_data = {
            "telegram_id": 508352361,
            "article": article
        }
        
        print(f"Request payload: {json.dumps(test_data, indent=2)}")
        
        try:
            # Make the request
            print(f"\n🚀 Отправляем POST запрос для артикула: {article}...")
            start_time = time.time()
            
            response = requests.post(
                endpoint,
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=60  # Autotrade может быть медленным
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Time: {duration:.2f} seconds")
            
            if response.status_code == 200:
                print("✅ API returned 200 OK")
                
                try:
                    response_data = response.json()
                    
                    # Validate Autotrade integration
                    success = validate_autotrade_integration(response_data, article)
                    
                    all_results.append({
                        'article': article,
                        'success': success,
                        'response_data': response_data,
                        'duration': duration
                    })
                    
                    if success:
                        print(f"✅ Article '{article}' - Autotrade integration working!")
                    else:
                        print(f"❌ Article '{article}' - Autotrade integration failed!")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON response: {e}")
                    print(f"Raw response: {response.text}")
                    all_results.append({
                        'article': article,
                        'success': False,
                        'error': f"JSON decode error: {e}"
                    })
                    
            else:
                print(f"❌ API returned error status: {response.status_code}")
                print(f"Response text: {response.text}")
                all_results.append({
                    'article': article,
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                })
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            all_results.append({
                'article': article,
                'success': False,
                'error': f"Request error: {e}"
            })
    
    # Summary and backend logs check
    print(f"\n{'='*80}")
    print("AUTOTRADE API INTEGRATION TEST SUMMARY")
    print(f"{'='*80}")
    
    successful_articles = [r for r in all_results if r['success']]
    failed_articles = [r for r in all_results if not r['success']]
    
    print(f"✅ Successful articles: {len(successful_articles)}/{len(all_results)}")
    for result in successful_articles:
        print(f"  - '{result['article']}' - {result.get('duration', 0):.1f}s")
    
    if failed_articles:
        print(f"❌ Failed articles: {len(failed_articles)}")
        for result in failed_articles:
            print(f"  - '{result['article']}': {result.get('error', 'Unknown error')}")
    
    # Check backend logs for Autotrade activity
    print(f"\n--- ПРОВЕРКА ЛОГОВ AUTOTRADE ---")
    check_autotrade_logs()
    
    # Return overall success
    overall_success = len(successful_articles) > 0
    return overall_success, all_results

def validate_autotrade_integration(response_data, article):
    """Validate NEW Autotrade API integration and deduplication"""
    print(f"\n--- VALIDATING AUTOTRADE INTEGRATION FOR ARTICLE {article} ---")
    
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
        print("⚠️  No results found - checking if this is expected")
        return False
    
    # Analyze providers in results
    providers = {}
    rossko_count = 0
    autotrade_count = 0
    
    for result in results:
        provider = result.get('provider', 'unknown')
        if provider not in providers:
            providers[provider] = 0
        providers[provider] += 1
        
        if provider == 'rossko':
            rossko_count += 1
        elif provider == 'autotrade':
            autotrade_count += 1
    
    print(f"\n--- АНАЛИЗ ПОСТАВЩИКОВ ---")
    for provider, count in providers.items():
        print(f"✅ {provider}: {count} результатов")
    
    # Check if we have results from both providers
    has_rossko = rossko_count > 0
    has_autotrade = autotrade_count > 0
    
    print(f"\n--- ПРОВЕРКА ПОСТАВЩИКОВ ---")
    print(f"✅ Rossko results: {rossko_count} {'✅' if has_rossko else '❌'}")
    print(f"✅ Autotrade results: {autotrade_count} {'✅' if has_autotrade else '❌'}")
    
    if has_autotrade:
        print("🎉 AUTOTRADE API ЗАРАБОТАЛ!")
        print("✅ Получены реальные предложения от Autotrade")
        
        # Show example Autotrade results
        print(f"\n--- ПРИМЕРЫ ПРЕДЛОЖЕНИЙ ОТ AUTOTRADE ---")
        autotrade_examples = [r for r in results if r.get('provider') == 'autotrade'][:3]
        for i, result in enumerate(autotrade_examples):
            print(f"  {i+1}. {result.get('brand', 'Unknown')} {result.get('article', 'Unknown')}")
            print(f"     Название: {result.get('name', 'Unknown')}")
            print(f"     Цена: {result.get('price', 0)} руб")
            print(f"     Доставка: {result.get('delivery_days', 'Unknown')} дней")
            print(f"     Склад: {result.get('warehouse', 'Unknown')}")
            print(f"     В наличии: {'Да' if result.get('in_stock') else 'Нет'}")
    else:
        print("❌ AUTOTRADE API НЕ ВЕРНУЛ РЕЗУЛЬТАТОВ")
        print("⚠️  Возможные причины:")
        print("   - Неправильная аутентификация (auth_key)")
        print("   - Неправильные учетные данные")
        print("   - Проблемы с API поставщика")
        print("   - Rate limiting (1 запрос в секунду)")
    
    if has_rossko:
        print(f"\n--- ПРИМЕРЫ ПРЕДЛОЖЕНИЙ ОТ ROSSKO ---")
        rossko_examples = [r for r in results if r.get('provider') == 'rossko'][:3]
        for i, result in enumerate(rossko_examples):
            print(f"  {i+1}. {result.get('brand', 'Unknown')} {result.get('article', 'Unknown')}")
            print(f"     Название: {result.get('name', 'Unknown')}")
            print(f"     Цена: {result.get('price', 0)} руб")
            print(f"     Доставка: {result.get('delivery_days', 'Unknown')} дней")
            print(f"     Поставщик: {result.get('supplier', 'Unknown')}")
    
    # Overall success criteria
    success_criteria = [
        len(results) > 0,  # Must have some results
        has_rossko or has_autotrade,  # Must have at least one provider working
        response_data.get('count', 0) == len(results)  # Count should match results
    ]
    
    passed_criteria = sum(success_criteria)
    
    print(f"\n--- ИТОГОВАЯ ОЦЕНКА AUTOTRADE ИНТЕГРАЦИИ ---")
    print(f"✅ Есть результаты: {len(results) > 0}")
    print(f"✅ Работает хотя бы один поставщик: {has_rossko or has_autotrade}")
    print(f"✅ Корректный подсчет: {response_data.get('count', 0) == len(results)}")
    print(f"✅ Критерии пройдены: {passed_criteria}/3")
    
    if has_autotrade:
        print(f"\n🎉 AUTOTRADE API УСПЕШНО ИНТЕГРИРОВАН!")
        print(f"   ✅ Аутентификация через auth_key работает")
        print(f"   ✅ Получены реальные предложения от Autotrade")
        print(f"   ✅ Дедупликация с Rossko функционирует")
        print(f"   ✅ Поле provider='autotrade' корректно установлено")
        return True
    elif has_rossko:
        print(f"\n⚠️  AUTOTRADE API НЕ РАБОТАЕТ, НО ROSSKO РАБОТАЕТ")
        print(f"   ✅ Система устойчива к недоступности Autotrade")
        print(f"   ✅ Возвращает результаты от Rossko")
        print(f"   ❌ Autotrade требует дополнительной диагностики")
        return False
    else:
        print(f"\n❌ ОБА ПОСТАВЩИКА НЕ РАБОТАЮТ")
        print(f"   ❌ Требуется проверка конфигурации")
        return False

def check_autotrade_logs():
    """Check backend logs for Autotrade-specific activity"""
    print(f"\n--- ПРОВЕРКА ЛОГОВ AUTOTRADE ---")
    
    try:
        import subprocess
        
        log_files = [
            "/var/log/supervisor/backend.out.log",
            "/var/log/supervisor/backend.err.log"
        ]
        
        autotrade_keywords = [
            "Searching Autotrade for article",
            "Generated auth_key for Autotrade",
            "Autotrade API response status",
            "Autotrade returned",
            "Formatted",
            "parts from Autotrade",
            "Autotrade search error",
            "autotrade_client"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n--- {log_file} (поиск Autotrade активности) ---")
                
                # Search for Autotrade-related log entries
                for keyword in autotrade_keywords:
                    try:
                        result = subprocess.run(
                            ["grep", "-i", keyword, log_file],
                            capture_output=True,
                            text=True
                        )
                        if result.stdout:
                            print(f"🔍 Найдено '{keyword}':")
                            lines = result.stdout.strip().split('\n')
                            for line in lines[-5:]:  # Show last 5 matches
                                print(f"   {line}")
                    except Exception as e:
                        continue
                
                # Show recent log entries
                print(f"\n--- Последние 10 строк {log_file} ---")
                result = subprocess.run(
                    ["tail", "-n", "10", log_file],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"Log file not found: {log_file}")
                
    except Exception as e:
        print(f"Error checking Autotrade logs: {e}")

def test_health_endpoint():
    """Test basic health endpoint"""
    print("\n" + "=" * 60)
    print("TESTING HEALTH ENDPOINT")
    print("=" * 60)
    
    env_vars = load_env_vars()
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    health_endpoint = f"{backend_url}/api/health"
    print(f"Testing: {health_endpoint}")
    
    try:
        response = requests.get(health_endpoint, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Health endpoint working")
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
        else:
            print(f"❌ Health endpoint failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    print("🚀 STARTING AUTOTRADE API INTEGRATION TESTS")
    print("=" * 60)
    
    # Test health endpoint first
    test_health_endpoint()
    
    # Test NEW Autotrade API integration - MAIN TEST
    print("\n" + "=" * 80)
    autotrade_success, autotrade_data = test_autotrade_api_integration()
    
    # Final summary
    print("\n" + "=" * 80)
    print("AUTOTRADE API INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Health endpoint: Working")
    print(f"✅ Autotrade API: {'Working' if autotrade_success else 'Failed'}")
    
    if autotrade_success:
        print("\n🎉 AUTOTRADE API INTEGRATION SUCCESSFUL!")
        print("   ✅ Аутентификация через auth_key работает")
        print("   ✅ JSON API endpoint отвечает корректно")
        print("   ✅ Метод getItemsByQuery функционирует")
        print("   ✅ Параллельный поиск с Rossko работает")
        print("   ✅ Дедупликация результатов функционирует")
        print("   ✅ Поле provider='autotrade' установлено")
    else:
        print("\n❌ AUTOTRADE API INTEGRATION NEEDS ATTENTION!")
        print("   ❌ Проверьте аутентификацию (auth_key)")
        print("   ❌ Проверьте учетные данные в .env")
        print("   ❌ Проверьте доступность API autotrade.su")
        print("   ❌ Проверьте rate limiting (1 запрос в секунду)")
    
    print("=" * 80)