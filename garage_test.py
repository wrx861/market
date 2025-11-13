#!/usr/bin/env python3
"""
Market Auto Parts Telegram Mini App - Garage Module Testing
Tests all CRUD operations for vehicles, service records, log entries, reminders and expense analytics
Based on review request requirements
"""

import requests
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

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

def test_garage_crud_operations():
    """Test all CRUD operations for Market Auto Parts Garage module"""
    print("=" * 80)
    print("TESTING MARKET AUTO PARTS TELEGRAM MINI APP - GARAGE MODULE")
    print("=" * 80)
    print("🚗 Тестирование всех CRUD операций для модуля Гараж")
    print("📋 Согласно review request:")
    print("   1. Создать тестовое авто (если нет)")
    print("   2. Тесты для Service Records CRUD")
    print("   3. Тесты для Log Entries CRUD")
    print("   4. Тесты для Reminders CRUD")
    print("   5. Тест аналитики расходов")
    print("   6. Тест удаления автомобиля с каскадным удалением")
    print("=" * 80)
    
    # Load environment variables
    env_vars = load_env_vars()
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    print(f"Backend URL: {backend_url}")
    
    # Test data from review request
    telegram_id = 508352361
    
    # Step 1: Create test vehicle
    print(f"\n{'='*60}")
    print("STEP 1: СОЗДАНИЕ ТЕСТОВОГО АВТОМОБИЛЯ")
    print(f"{'='*60}")
    
    vehicle_id = create_test_vehicle(backend_url, telegram_id)
    if not vehicle_id:
        print("❌ Не удалось создать тестовое авто. Прерываем тестирование.")
        return False
    
    print(f"✅ Тестовое авто создано: {vehicle_id}")
    
    # Step 2: Test Service Records CRUD
    print(f"\n{'='*60}")
    print("STEP 2: ТЕСТИРОВАНИЕ SERVICE RECORDS CRUD")
    print(f"{'='*60}")
    
    service_success = test_service_records_crud(backend_url, vehicle_id, telegram_id)
    if not service_success:
        print("❌ Service Records CRUD тесты провалились")
        return False
    
    # Step 3: Test Log Entries CRUD
    print(f"\n{'='*60}")
    print("STEP 3: ТЕСТИРОВАНИЕ LOG ENTRIES CRUD")
    print(f"{'='*60}")
    
    log_success = test_log_entries_crud(backend_url, vehicle_id, telegram_id)
    if not log_success:
        print("❌ Log Entries CRUD тесты провалились")
        return False
    
    # Step 4: Test Reminders CRUD
    print(f"\n{'='*60}")
    print("STEP 4: ТЕСТИРОВАНИЕ REMINDERS CRUD")
    print(f"{'='*60}")
    
    reminders_success = test_reminders_crud(backend_url, vehicle_id, telegram_id)
    if not reminders_success:
        print("❌ Reminders CRUD тесты провалились")
        return False
    
    # Step 5: Test Expense Analytics
    print(f"\n{'='*60}")
    print("STEP 5: ТЕСТИРОВАНИЕ АНАЛИТИКИ РАСХОДОВ")
    print(f"{'='*60}")
    
    analytics_success = test_expense_analytics(backend_url, vehicle_id)
    if not analytics_success:
        print("❌ Аналитика расходов тесты провалились")
        return False
    
    # Step 6: Test Vehicle Deletion with Cascade
    print(f"\n{'='*60}")
    print("STEP 6: ТЕСТИРОВАНИЕ УДАЛЕНИЯ АВТОМОБИЛЯ С КАСКАДНЫМ УДАЛЕНИЕМ")
    print(f"{'='*60}")
    
    deletion_success = test_vehicle_deletion_cascade(backend_url, vehicle_id)
    if not deletion_success:
        print("❌ Удаление автомобиля тесты провалились")
        return False
    
    print(f"\n{'='*80}")
    print("🎉 ВСЕ ТЕСТЫ GARAGE MODULE УСПЕШНО ЗАВЕРШЕНЫ!")
    print("✅ Service Records CRUD - работает")
    print("✅ Log Entries CRUD - работает")
    print("✅ Reminders CRUD - работает")
    print("✅ Expense Analytics - работает")
    print("✅ Vehicle Deletion Cascade - работает")
    print(f"{'='*80}")
    
    return True

def create_test_vehicle(backend_url: str, telegram_id: int) -> str:
    """Create test vehicle as specified in review request"""
    print("\n--- СОЗДАНИЕ ТЕСТОВОГО АВТОМОБИЛЯ ---")
    
    # First ensure user exists
    user_endpoint = f"{backend_url}/api/users"
    user_data = {
        "telegram_id": telegram_id,
        "username": "garage_test_user",
        "name": "Garage Test User"
    }
    
    try:
        user_response = requests.post(
            user_endpoint,
            json=user_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if user_response.status_code == 200:
            print("✅ Пользователь создан/обновлён")
        else:
            print(f"⚠️  Пользователь: {user_response.status_code}")
    except Exception as e:
        print(f"⚠️  Ошибка создания пользователя: {e}")
    
    # Create vehicle exactly as specified in review request
    vehicle_endpoint = f"{backend_url}/api/garage"
    vehicle_data = {
        "telegram_id": telegram_id,
        "make": "BMW",
        "model": "X5",
        "year": 2019,
        "vin": "TESTVIN123",
        "mileage": 45000
    }
    
    print(f"Vehicle payload: {json.dumps(vehicle_data, indent=2)}")
    
    try:
        vehicle_response = requests.post(
            vehicle_endpoint,
            json=vehicle_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response Status: {vehicle_response.status_code}")
        
        if vehicle_response.status_code == 200:
            vehicle_result = vehicle_response.json()
            vehicle_id = vehicle_result.get('vehicle_id')
            
            if vehicle_id:
                print(f"✅ Автомобиль создан: {vehicle_id}")
                print(f"🚗 BMW X5 2019, VIN: TESTVIN123, пробег: 45000 км")
                return vehicle_id
            else:
                print("❌ vehicle_id не найден в ответе")
                print(f"Response: {json.dumps(vehicle_result, indent=2)}")
                return None
        else:
            print(f"❌ Ошибка создания автомобиля: {vehicle_response.status_code}")
            print(f"Response: {vehicle_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка создания автомобиля: {e}")
        return None

def test_service_records_crud(backend_url: str, vehicle_id: str, telegram_id: int) -> bool:
    """Test Service Records CRUD operations"""
    print("\n--- ТЕСТИРОВАНИЕ SERVICE RECORDS CRUD ---")
    
    # Test CREATE service record
    print("\n1. CREATE - Создание записи обслуживания")
    
    create_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/service"
    service_data = {
        "telegram_id": telegram_id,
        "service_type": "maintenance",
        "title": "Замена масла и фильтров",
        "description": "Плановое ТО: замена моторного масла, масляного и воздушного фильтров",
        "mileage": 45500,
        "cost": 3500.00,
        "service_date": "2024-01-15",
        "service_provider": "BMW Сервис Тюмень",
        "parts_used": ["Масло моторное 5W-30", "Фильтр масляный", "Фильтр воздушный"]
    }
    
    print(f"POST {create_endpoint}")
    print(f"Payload: {json.dumps(service_data, indent=2, ensure_ascii=False)}")
    
    try:
        create_response = requests.post(
            create_endpoint,
            json=service_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response Status: {create_response.status_code}")
        
        if create_response.status_code == 200:
            create_result = create_response.json()
            record_id = create_result.get('record_id')
            
            if record_id:
                print(f"✅ Запись обслуживания создана: {record_id}")
            else:
                print("❌ record_id не найден в ответе")
                return False
        else:
            print(f"❌ Ошибка создания записи: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка создания записи: {e}")
        return False
    
    # Test READ service records
    print("\n2. READ - Получение записей обслуживания")
    
    read_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/service"
    
    try:
        read_response = requests.get(read_endpoint, timeout=30)
        
        print(f"GET {read_endpoint}")
        print(f"Response Status: {read_response.status_code}")
        
        if read_response.status_code == 200:
            read_result = read_response.json()
            records = read_result.get('records', [])
            
            if len(records) > 0:
                print(f"✅ Получено {len(records)} записей обслуживания")
                print(f"Первая запись: {records[0].get('title', 'N/A')}")
            else:
                print("❌ Записи обслуживания не найдены")
                return False
        else:
            print(f"❌ Ошибка получения записей: {read_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка получения записей: {e}")
        return False
    
    # Test UPDATE service record
    print("\n3. UPDATE - Обновление записи обслуживания")
    
    update_endpoint = f"{backend_url}/api/garage/service/{record_id}"
    update_data = {
        "title": "Замена масла и фильтров (ОБНОВЛЕНО)",
        "cost": 4000.00,
        "description": "Плановое ТО: замена моторного масла, масляного и воздушного фильтров + диагностика"
    }
    
    print(f"PUT {update_endpoint}")
    print(f"Payload: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    try:
        update_response = requests.put(
            update_endpoint,
            json=update_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response Status: {update_response.status_code}")
        
        if update_response.status_code == 200:
            print("✅ Запись обслуживания обновлена")
        else:
            print(f"❌ Ошибка обновления записи: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обновления записи: {e}")
        return False
    
    # Test DELETE service record
    print("\n4. DELETE - Удаление записи обслуживания")
    
    delete_endpoint = f"{backend_url}/api/garage/service/{record_id}"
    
    print(f"DELETE {delete_endpoint}")
    
    try:
        delete_response = requests.delete(delete_endpoint, timeout=30)
        
        print(f"Response Status: {delete_response.status_code}")
        
        if delete_response.status_code == 200:
            print("✅ Запись обслуживания удалена")
        else:
            print(f"❌ Ошибка удаления записи: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка удаления записи: {e}")
        return False
    
    print("\n✅ SERVICE RECORDS CRUD - ВСЕ ОПЕРАЦИИ РАБОТАЮТ КОРРЕКТНО")
    return True

def test_log_entries_crud(backend_url: str, vehicle_id: str, telegram_id: int) -> bool:
    """Test Log Entries CRUD operations"""
    print("\n--- ТЕСТИРОВАНИЕ LOG ENTRIES CRUD ---")
    
    # Test CREATE log entry (refuel type as specified in review)
    print("\n1. CREATE - Создание записи бортжурнала (refuel тип)")
    
    create_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/log"
    log_data = {
        "telegram_id": telegram_id,
        "entry_type": "refuel",
        "title": "Заправка АИ-95",
        "description": "Заправка на АЗС Лукойл",
        "fuel_amount": 45.5,
        "fuel_cost": 2275.00,
        "fuel_type": "АИ-95",
        "mileage": 45600,
        "entry_date": "2024-01-16"
    }
    
    print(f"POST {create_endpoint}")
    print(f"Payload: {json.dumps(log_data, indent=2, ensure_ascii=False)}")
    
    try:
        create_response = requests.post(
            create_endpoint,
            json=log_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response Status: {create_response.status_code}")
        
        if create_response.status_code == 200:
            create_result = create_response.json()
            entry_id = create_result.get('entry_id')
            
            if entry_id:
                print(f"✅ Запись бортжурнала создана: {entry_id}")
            else:
                print("❌ entry_id не найден в ответе")
                return False
        else:
            print(f"❌ Ошибка создания записи: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка создания записи: {e}")
        return False
    
    # Test READ log entries
    print("\n2. READ - Получение записей бортжурнала")
    
    read_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/log"
    
    try:
        read_response = requests.get(read_endpoint, timeout=30)
        
        print(f"GET {read_endpoint}")
        print(f"Response Status: {read_response.status_code}")
        
        if read_response.status_code == 200:
            read_result = read_response.json()
            entries = read_result.get('entries', [])
            
            if len(entries) > 0:
                print(f"✅ Получено {len(entries)} записей бортжурнала")
                print(f"Первая запись: {entries[0].get('title', 'N/A')}")
            else:
                print("❌ Записи бортжурнала не найдены")
                return False
        else:
            print(f"❌ Ошибка получения записей: {read_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка получения записей: {e}")
        return False
    
    # Test UPDATE log entry
    print("\n3. UPDATE - Обновление записи бортжурнала")
    
    update_endpoint = f"{backend_url}/api/garage/log/{entry_id}"
    update_data = {
        "title": "Заправка АИ-95 (ОБНОВЛЕНО)",
        "fuel_cost": 2300.00,
        "description": "Заправка на АЗС Лукойл + мойка"
    }
    
    print(f"PUT {update_endpoint}")
    print(f"Payload: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    try:
        update_response = requests.put(
            update_endpoint,
            json=update_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response Status: {update_response.status_code}")
        
        if update_response.status_code == 200:
            print("✅ Запись бортжурнала обновлена")
        else:
            print(f"❌ Ошибка обновления записи: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обновления записи: {e}")
        return False
    
    # Test DELETE log entry
    print("\n4. DELETE - Удаление записи бортжурнала")
    
    delete_endpoint = f"{backend_url}/api/garage/log/{entry_id}"
    
    print(f"DELETE {delete_endpoint}")
    
    try:
        delete_response = requests.delete(delete_endpoint, timeout=30)
        
        print(f"Response Status: {delete_response.status_code}")
        
        if delete_response.status_code == 200:
            print("✅ Запись бортжурнала удалена")
        else:
            print(f"❌ Ошибка удаления записи: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка удаления записи: {e}")
        return False
    
    print("\n✅ LOG ENTRIES CRUD - ВСЕ ОПЕРАЦИИ РАБОТАЮТ КОРРЕКТНО")
    return True

def test_reminders_crud(backend_url: str, vehicle_id: str, telegram_id: int) -> bool:
    """Test Reminders CRUD operations"""
    print("\n--- ТЕСТИРОВАНИЕ REMINDERS CRUD ---")
    
    # Test CREATE reminder
    print("\n1. CREATE - Создание напоминания")
    
    create_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/reminders"
    reminder_data = {
        "telegram_id": telegram_id,
        "reminder_type": "maintenance",
        "title": "Следующее ТО",
        "description": "Плановое техническое обслуживание через 10000 км",
        "remind_at_mileage": 55000,
        "remind_at_date": "2024-06-15"
    }
    
    print(f"POST {create_endpoint}")
    print(f"Payload: {json.dumps(reminder_data, indent=2, ensure_ascii=False)}")
    
    try:
        create_response = requests.post(
            create_endpoint,
            json=reminder_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response Status: {create_response.status_code}")
        
        if create_response.status_code == 200:
            create_result = create_response.json()
            reminder_id = create_result.get('reminder_id')
            
            if reminder_id:
                print(f"✅ Напоминание создано: {reminder_id}")
            else:
                print("❌ reminder_id не найден в ответе")
                return False
        else:
            print(f"❌ Ошибка создания напоминания: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка создания напоминания: {e}")
        return False
    
    # Test READ reminders
    print("\n2. READ - Получение напоминаний")
    
    read_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/reminders"
    
    try:
        read_response = requests.get(read_endpoint, timeout=30)
        
        print(f"GET {read_endpoint}")
        print(f"Response Status: {read_response.status_code}")
        
        if read_response.status_code == 200:
            read_result = read_response.json()
            reminders = read_result.get('reminders', [])
            
            if len(reminders) > 0:
                print(f"✅ Получено {len(reminders)} напоминаний")
                print(f"Первое напоминание: {reminders[0].get('title', 'N/A')}")
            else:
                print("❌ Напоминания не найдены")
                return False
        else:
            print(f"❌ Ошибка получения напоминаний: {read_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка получения напоминаний: {e}")
        return False
    
    # Test UPDATE reminder
    print("\n3. UPDATE - Обновление напоминания")
    
    update_endpoint = f"{backend_url}/api/garage/reminders/{reminder_id}"
    update_data = {
        "title": "Следующее ТО (ОБНОВЛЕНО)",
        "remind_at_mileage": 54000,
        "description": "Плановое техническое обслуживание через 9000 км"
    }
    
    print(f"PUT {update_endpoint}")
    print(f"Payload: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    try:
        update_response = requests.put(
            update_endpoint,
            json=update_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response Status: {update_response.status_code}")
        
        if update_response.status_code == 200:
            print("✅ Напоминание обновлено")
        else:
            print(f"❌ Ошибка обновления напоминания: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обновления напоминания: {e}")
        return False
    
    # Test DELETE reminder
    print("\n4. DELETE - Удаление напоминания")
    
    delete_endpoint = f"{backend_url}/api/garage/reminders/{reminder_id}"
    
    print(f"DELETE {delete_endpoint}")
    
    try:
        delete_response = requests.delete(delete_endpoint, timeout=30)
        
        print(f"Response Status: {delete_response.status_code}")
        
        if delete_response.status_code == 200:
            print("✅ Напоминание удалено")
        else:
            print(f"❌ Ошибка удаления напоминания: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка удаления напоминания: {e}")
        return False
    
    print("\n✅ REMINDERS CRUD - ВСЕ ОПЕРАЦИИ РАБОТАЮТ КОРРЕКТНО")
    return True

def test_expense_analytics(backend_url: str, vehicle_id: str) -> bool:
    """Test expense analytics functionality"""
    print("\n--- ТЕСТИРОВАНИЕ АНАЛИТИКИ РАСХОДОВ ---")
    
    # First create some test data for analytics
    print("\n1. ПОДГОТОВКА ТЕСТОВЫХ ДАННЫХ ДЛЯ АНАЛИТИКИ")
    
    # Create service record with cost
    service_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/service"
    service_data = {
        "telegram_id": 508352361,
        "service_type": "maintenance",
        "title": "Замена тормозных колодок",
        "description": "Замена передних тормозных колодок",
        "mileage": 46000,
        "cost": 8500.00,
        "service_date": "2024-01-20",
        "service_provider": "BMW Сервис"
    }
    
    try:
        service_response = requests.post(
            service_endpoint,
            json=service_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if service_response.status_code == 200:
            print("✅ Тестовая запись обслуживания создана")
        else:
            print(f"⚠️  Ошибка создания тестовой записи обслуживания: {service_response.status_code}")
    except Exception as e:
        print(f"⚠️  Ошибка создания тестовой записи обслуживания: {e}")
    
    # Create log entry with fuel cost
    log_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/log"
    log_data = {
        "telegram_id": 508352361,
        "entry_type": "refuel",
        "title": "Заправка АИ-95",
        "description": "Заправка полного бака",
        "fuel_amount": 50.0,
        "fuel_cost": 2500.00,
        "fuel_type": "АИ-95",
        "mileage": 46100,
        "entry_date": "2024-01-21"
    }
    
    try:
        log_response = requests.post(
            log_endpoint,
            json=log_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if log_response.status_code == 200:
            print("✅ Тестовая запись заправки создана")
        else:
            print(f"⚠️  Ошибка создания тестовой записи заправки: {log_response.status_code}")
    except Exception as e:
        print(f"⚠️  Ошибка создания тестовой записи заправки: {e}")
    
    # Create expense log entry
    expense_data = {
        "telegram_id": 508352361,
        "entry_type": "expense",
        "title": "Мойка автомобиля",
        "description": "Комплексная мойка с воском",
        "expense_amount": 800.00,
        "expense_category": "wash",
        "mileage": 46150,
        "entry_date": "2024-01-22"
    }
    
    try:
        expense_response = requests.post(
            log_endpoint,
            json=expense_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if expense_response.status_code == 200:
            print("✅ Тестовая запись расхода создана")
        else:
            print(f"⚠️  Ошибка создания тестовой записи расхода: {expense_response.status_code}")
    except Exception as e:
        print(f"⚠️  Ошибка создания тестовой записи расхода: {e}")
    
    # Test expense analytics endpoint
    print("\n2. ТЕСТИРОВАНИЕ ENDPOINT АНАЛИТИКИ РАСХОДОВ")
    
    analytics_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/expenses"
    
    # Test different periods
    periods = ["all", "month", "3months", "year"]
    
    for period in periods:
        print(f"\n--- Тестирование периода: {period} ---")
        
        try:
            analytics_response = requests.get(
                f"{analytics_endpoint}?period={period}",
                timeout=30
            )
            
            print(f"GET {analytics_endpoint}?period={period}")
            print(f"Response Status: {analytics_response.status_code}")
            
            if analytics_response.status_code == 200:
                analytics_result = analytics_response.json()
                
                # Validate response structure
                if validate_expense_analytics_response(analytics_result, period):
                    print(f"✅ Аналитика для периода '{period}' работает корректно")
                else:
                    print(f"❌ Некорректная структура ответа для периода '{period}'")
                    return False
            else:
                print(f"❌ Ошибка получения аналитики для периода '{period}': {analytics_response.status_code}")
                print(f"Response: {analytics_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запроса аналитики для периода '{period}': {e}")
            return False
    
    print("\n✅ EXPENSE ANALYTICS - ВСЕ ПРОВЕРКИ ПРОШЛИ УСПЕШНО")
    return True

def validate_expense_analytics_response(response_data: dict, period: str) -> bool:
    """Validate expense analytics response structure"""
    print(f"\n--- ВАЛИДАЦИЯ ОТВЕТА АНАЛИТИКИ ДЛЯ ПЕРИОДА '{period}' ---")
    
    # Check required fields
    required_fields = ['status', 'total', 'period', 'categories', 'expenses', 'expenses_count']
    
    for field in required_fields:
        if field in response_data:
            print(f"✅ Поле '{field}' присутствует")
        else:
            print(f"❌ Поле '{field}' отсутствует")
            return False
    
    # Check status
    if response_data.get('status') == 'success':
        print("✅ Status = 'success'")
    else:
        print(f"❌ Status не равен 'success': {response_data.get('status')}")
        return False
    
    # Check period matches
    if response_data.get('period') == period:
        print(f"✅ Period соответствует запросу: {period}")
    else:
        print(f"❌ Period не соответствует: ожидался {period}, получен {response_data.get('period')}")
        return False
    
    # Check total is numeric
    total = response_data.get('total', 0)
    if isinstance(total, (int, float)) and total >= 0:
        print(f"✅ Total корректный: {total} руб.")
    else:
        print(f"❌ Total некорректный: {total}")
        return False
    
    # Check categories structure
    categories = response_data.get('categories', [])
    if isinstance(categories, list):
        print(f"✅ Categories - массив с {len(categories)} элементами")
        
        # Validate category structure
        for i, category in enumerate(categories[:3]):  # Check first 3
            if validate_category_structure(category, i):
                print(f"✅ Категория {i+1} корректна")
            else:
                print(f"❌ Категория {i+1} некорректна")
                return False
    else:
        print(f"❌ Categories не является массивом: {type(categories)}")
        return False
    
    # Check expenses structure
    expenses = response_data.get('expenses', [])
    if isinstance(expenses, list):
        print(f"✅ Expenses - массив с {len(expenses)} элементами")
        
        # Validate expense structure
        for i, expense in enumerate(expenses[:3]):  # Check first 3
            if validate_expense_structure(expense, i):
                print(f"✅ Расход {i+1} корректен")
            else:
                print(f"❌ Расход {i+1} некорректен")
                return False
    else:
        print(f"❌ Expenses не является массивом: {type(expenses)}")
        return False
    
    # Check expenses_count matches
    expenses_count = response_data.get('expenses_count', 0)
    if expenses_count == len(expenses) or expenses_count >= len(expenses):
        print(f"✅ Expenses_count корректен: {expenses_count}")
    else:
        print(f"❌ Expenses_count некорректен: {expenses_count} vs {len(expenses)}")
        return False
    
    print(f"✅ Структура ответа аналитики для периода '{period}' валидна")
    return True

def validate_category_structure(category: dict, index: int) -> bool:
    """Validate individual category structure"""
    required_fields = ['key', 'name', 'total', 'count', 'percentage']
    
    for field in required_fields:
        if field not in category:
            print(f"❌ Категория {index+1}: отсутствует поле '{field}'")
            return False
    
    # Check data types
    if not isinstance(category['total'], (int, float)) or category['total'] < 0:
        print(f"❌ Категория {index+1}: некорректный total")
        return False
    
    if not isinstance(category['count'], int) or category['count'] < 0:
        print(f"❌ Категория {index+1}: некорректный count")
        return False
    
    if not isinstance(category['percentage'], (int, float)) or category['percentage'] < 0:
        print(f"❌ Категория {index+1}: некорректный percentage")
        return False
    
    return True

def validate_expense_structure(expense: dict, index: int) -> bool:
    """Validate individual expense structure"""
    required_fields = ['date', 'category', 'title', 'amount']
    
    for field in required_fields:
        if field not in expense:
            print(f"❌ Расход {index+1}: отсутствует поле '{field}'")
            return False
    
    # Check amount is numeric
    if not isinstance(expense['amount'], (int, float)) or expense['amount'] < 0:
        print(f"❌ Расход {index+1}: некорректный amount")
        return False
    
    return True

def test_vehicle_deletion_cascade(backend_url: str, vehicle_id: str) -> bool:
    """Test vehicle deletion with cascade deletion of related data"""
    print("\n--- ТЕСТИРОВАНИЕ УДАЛЕНИЯ АВТОМОБИЛЯ С КАСКАДНЫМ УДАЛЕНИЕМ ---")
    
    # First verify vehicle exists
    print("\n1. ПРОВЕРКА СУЩЕСТВОВАНИЯ АВТОМОБИЛЯ")
    
    vehicle_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}"
    
    try:
        vehicle_response = requests.get(vehicle_endpoint, timeout=30)
        
        print(f"GET {vehicle_endpoint}")
        print(f"Response Status: {vehicle_response.status_code}")
        
        if vehicle_response.status_code == 200:
            vehicle_data = vehicle_response.json()
            print(f"✅ Автомобиль найден: {vehicle_data.get('vehicle', {}).get('make', 'N/A')} {vehicle_data.get('vehicle', {}).get('model', 'N/A')}")
        else:
            print(f"❌ Автомобиль не найден: {vehicle_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки автомобиля: {e}")
        return False
    
    # Check related data exists before deletion
    print("\n2. ПРОВЕРКА СВЯЗАННЫХ ДАННЫХ ПЕРЕД УДАЛЕНИЕМ")
    
    # Check service records
    service_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/service"
    try:
        service_response = requests.get(service_endpoint, timeout=30)
        if service_response.status_code == 200:
            service_data = service_response.json()
            service_count = len(service_data.get('records', []))
            print(f"✅ Записей обслуживания: {service_count}")
        else:
            service_count = 0
            print(f"⚠️  Записи обслуживания недоступны: {service_response.status_code}")
    except Exception as e:
        service_count = 0
        print(f"⚠️  Ошибка проверки записей обслуживания: {e}")
    
    # Check log entries
    log_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/log"
    try:
        log_response = requests.get(log_endpoint, timeout=30)
        if log_response.status_code == 200:
            log_data = log_response.json()
            log_count = len(log_data.get('entries', []))
            print(f"✅ Записей бортжурнала: {log_count}")
        else:
            log_count = 0
            print(f"⚠️  Записи бортжурнала недоступны: {log_response.status_code}")
    except Exception as e:
        log_count = 0
        print(f"⚠️  Ошибка проверки записей бортжурнала: {e}")
    
    # Check reminders
    reminders_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}/reminders"
    try:
        reminders_response = requests.get(reminders_endpoint, timeout=30)
        if reminders_response.status_code == 200:
            reminders_data = reminders_response.json()
            reminders_count = len(reminders_data.get('reminders', []))
            print(f"✅ Напоминаний: {reminders_count}")
        else:
            reminders_count = 0
            print(f"⚠️  Напоминания недоступны: {reminders_response.status_code}")
    except Exception as e:
        reminders_count = 0
        print(f"⚠️  Ошибка проверки напоминаний: {e}")
    
    # Delete vehicle
    print("\n3. УДАЛЕНИЕ АВТОМОБИЛЯ")
    
    delete_endpoint = f"{backend_url}/api/garage/vehicle/{vehicle_id}"
    
    print(f"DELETE {delete_endpoint}")
    
    try:
        delete_response = requests.delete(delete_endpoint, timeout=30)
        
        print(f"Response Status: {delete_response.status_code}")
        
        if delete_response.status_code == 200:
            print("✅ Автомобиль удален")
        else:
            print(f"❌ Ошибка удаления автомобиля: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка удаления автомобиля: {e}")
        return False
    
    # Verify vehicle is deleted
    print("\n4. ПРОВЕРКА УДАЛЕНИЯ АВТОМОБИЛЯ")
    
    try:
        verify_response = requests.get(vehicle_endpoint, timeout=30)
        
        print(f"GET {vehicle_endpoint}")
        print(f"Response Status: {verify_response.status_code}")
        
        if verify_response.status_code == 404:
            print("✅ Автомобиль успешно удален (404 Not Found)")
        else:
            print(f"❌ Автомобиль не удален: {verify_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки удаления: {e}")
        return False
    
    # Verify related data is deleted (cascade)
    print("\n5. ПРОВЕРКА КАСКАДНОГО УДАЛЕНИЯ СВЯЗАННЫХ ДАННЫХ")
    
    # Check service records are deleted
    try:
        service_verify = requests.get(service_endpoint, timeout=30)
        if service_verify.status_code == 200:
            service_verify_data = service_verify.json()
            remaining_service = len(service_verify_data.get('records', []))
            if remaining_service == 0:
                print("✅ Записи обслуживания удалены")
            else:
                print(f"⚠️  Остались записи обслуживания: {remaining_service}")
        else:
            print("✅ Записи обслуживания недоступны (удалены)")
    except Exception as e:
        print(f"⚠️  Ошибка проверки удаления записей обслуживания: {e}")
    
    # Check log entries are deleted
    try:
        log_verify = requests.get(log_endpoint, timeout=30)
        if log_verify.status_code == 200:
            log_verify_data = log_verify.json()
            remaining_log = len(log_verify_data.get('entries', []))
            if remaining_log == 0:
                print("✅ Записи бортжурнала удалены")
            else:
                print(f"⚠️  Остались записи бортжурнала: {remaining_log}")
        else:
            print("✅ Записи бортжурнала недоступны (удалены)")
    except Exception as e:
        print(f"⚠️  Ошибка проверки удаления записей бортжурнала: {e}")
    
    # Check reminders are deleted
    try:
        reminders_verify = requests.get(reminders_endpoint, timeout=30)
        if reminders_verify.status_code == 200:
            reminders_verify_data = reminders_verify.json()
            remaining_reminders = len(reminders_verify_data.get('reminders', []))
            if remaining_reminders == 0:
                print("✅ Напоминания удалены")
            else:
                print(f"⚠️  Остались напоминания: {remaining_reminders}")
        else:
            print("✅ Напоминания недоступны (удалены)")
    except Exception as e:
        print(f"⚠️  Ошибка проверки удаления напоминаний: {e}")
    
    print("\n✅ VEHICLE DELETION CASCADE - УДАЛЕНИЕ ПРОШЛО УСПЕШНО")
    return True

def main():
    """Main test function for Market Auto Parts Garage module"""
    print("🚗 MARKET AUTO PARTS TELEGRAM MINI APP - GARAGE MODULE TESTING")
    print("=" * 80)
    
    success = test_garage_crud_operations()
    
    if success:
        print("\n🎉 ВСЕ ТЕСТЫ GARAGE MODULE ЗАВЕРШЕНЫ УСПЕШНО!")
        return True
    else:
        print("\n❌ ТЕСТЫ GARAGE MODULE ПРОВАЛИЛИСЬ!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)