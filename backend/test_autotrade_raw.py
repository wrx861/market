"""
Тестовый скрипт для проверки сырого ответа Autotrade API
"""
import os
import hashlib
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path('/app/backend/.env'))

# Credentials
login = os.environ.get('AUTOTRADE_LOGIN')
password = os.environ.get('AUTOTRADE_PASSWORD')
api_key = os.environ.get('AUTOTRADE_API_KEY')
api_url = "https://api2.autotrade.su/?json"
salt = "1>6)/MI~{J"

print(f"Login: {login}")
print(f"API Key from env: {api_key}")
print()

# Попробуем оба варианта auth_key

# Вариант 1: API ключ напрямую
print("=== Вариант 1: API ключ напрямую ===")
auth_key_v1 = api_key

params = {
    "q": "ST-dtw1-395-0",
    "page": 1,
    "limit": 20,
    "cross": 1,
    "replace": 1,
    "with_stocks_and_prices": 1,
    "with_delivery": 1
}

request_data = {
    "auth_key": auth_key_v1,
    "method": "getItemsByQuery",
    "params": params
}

payload = {
    "data": json.dumps(request_data, ensure_ascii=False)
}

headers = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
}

print(f"Auth key: {auth_key_v1}")
print(f"Request: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
print()

response = requests.post(api_url, data=payload, headers=headers, timeout=10)

print(f"Status: {response.status_code}")
print(f"Response:")
try:
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
except:
    print(response.text[:1000])

print("\n" + "="*80 + "\n")

# Вариант 2: Генерация через MD5
print("=== Вариант 2: MD5 хеш ===")
password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
combined = f"{login}{password_hash}{salt}"
auth_key_v2 = hashlib.md5(combined.encode('utf-8')).hexdigest()

request_data["auth_key"] = auth_key_v2
payload = {
    "data": json.dumps(request_data, ensure_ascii=False)
}

print(f"Password MD5: {password_hash}")
print(f"Combined: {combined}")
print(f"Auth key: {auth_key_v2}")
print()

response = requests.post(api_url, data=payload, headers=headers, timeout=10)

print(f"Status: {response.status_code}")
print(f"Response:")
try:
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Если есть результаты, покажем первый
    if result.get('code') == 0 and result.get('items'):
        print("\n=== Первый товар ===")
        print(json.dumps(result['items'][0], indent=2, ensure_ascii=False))
except:
    print(response.text[:1000])
