#!/usr/bin/env python3
"""
Focused test for PartsAPI.ru integration with the corrected API method
Testing the specific VIN from the request: XW7BF4FK60S145161
"""

import requests
import json
import os
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

def test_direct_partsapi():
    """Test direct PartsAPI.ru call with the corrected method"""
    print("=" * 80)
    print("TESTING DIRECT PARTSAPI.RU CALL")
    print("=" * 80)
    
    # Test parameters from the request
    api_key = "5c52f6e4db91259648e10e3dfab5828e"
    test_vin = "XW7BF4FK60S145161"
    category_id = "7"  # Oil filter category
    
    # Direct API URL with corrected method
    url = f"https://api.partsapi.ru?method=getPartsbyVIN&key={api_key}&vin={test_vin}&type=oem&cat={category_id}"
    
    print(f"Testing URL: {url}")
    print(f"VIN: {test_vin}")
    print(f"Category: {category_id} (масляный фильтр)")
    print(f"API Key: {api_key}")
    
    try:
        print("\nSending direct API request...")
        response = requests.get(url, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ API returned 200 OK")
            try:
                data = response.json()
                print(f"Response JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ Found {len(data)} parts")
                    
                    # Check first part structure
                    first_part = data[0]
                    print(f"\nFirst part details:")
                    for key, value in first_part.items():
                        print(f"  {key}: {value}")
                    
                    return True, data
                else:
                    print("⚠️  No parts found or invalid response format")
                    return False, data
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Raw response: {response.text}")
                return False, None
                
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - API key is invalid")
            print(f"Response: {response.text}")
            return False, None
        else:
            print(f"❌ API returned error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False, None

def test_backend_vin_endpoint():
    """Test the backend VIN endpoint with the test VIN"""
    print("\n" + "=" * 80)
    print("TESTING BACKEND VIN ENDPOINT")
    print("=" * 80)
    
    env_vars = load_env_vars()
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    endpoint = f"{backend_url}/api/search/vin"
    test_vin = "XW7BF4FK60S145161"
    
    print(f"Backend URL: {backend_url}")
    print(f"Endpoint: {endpoint}")
    print(f"Test VIN: {test_vin}")
    
    test_data = {
        "vin": test_vin,
        "telegram_id": 123456789
    }
    
    try:
        print("\nSending POST request to backend...")
        response = requests.post(
            endpoint,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Backend returned 200 OK")
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # Check response structure
                if data.get('status') == 'success':
                    print("✅ Status is success")
                    
                    car_info = data.get('car_info', {})
                    if car_info:
                        print(f"✅ Car info: {car_info}")
                    
                    catalog_groups = data.get('catalog_groups', [])
                    print(f"✅ Catalog groups: {len(catalog_groups)} found")
                    
                    return True, data
                else:
                    print(f"❌ Status is not success: {data.get('status')}")
                    return False, data
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Raw response: {response.text}")
                return False, None
        else:
            print(f"❌ Backend returned error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False, None

def test_backend_ai_endpoint():
    """Test the backend AI search endpoint"""
    print("\n" + "=" * 80)
    print("TESTING BACKEND AI SEARCH ENDPOINT")
    print("=" * 80)
    
    env_vars = load_env_vars()
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    endpoint = f"{backend_url}/api/search/ai"
    test_vin = "XW7BF4FK60S145161"
    test_query = "масляный фильтр"
    
    print(f"Backend URL: {backend_url}")
    print(f"Endpoint: {endpoint}")
    print(f"Test VIN: {test_vin}")
    print(f"Test Query: {test_query}")
    
    test_data = {
        "vin": test_vin,
        "query": test_query,
        "telegram_id": 123456789
    }
    
    try:
        print("\nSending POST request to AI endpoint...")
        response = requests.post(
            endpoint,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=90
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ AI endpoint returned 200 OK")
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # Check AI response structure
                if data.get('status') == 'success':
                    print("✅ AI search status is success")
                    
                    articles_found = data.get('articles_found', [])
                    print(f"✅ AI found articles: {articles_found}")
                    
                    results = data.get('results', [])
                    print(f"✅ Parts found: {len(results)}")
                    
                    return True, data
                else:
                    print(f"❌ AI search status is not success: {data.get('status')}")
                    return False, data
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Raw response: {response.text}")
                return False, None
        else:
            print(f"❌ AI endpoint returned error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False, None

def check_backend_logs():
    """Check backend logs for errors"""
    print("\n" + "=" * 80)
    print("CHECKING BACKEND LOGS")
    print("=" * 80)
    
    try:
        import subprocess
        
        log_files = [
            "/var/log/supervisor/backend.out.log",
            "/var/log/supervisor/backend.err.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n--- {log_file} (last 30 lines) ---")
                result = subprocess.run(
                    ["tail", "-n", "30", log_file],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(f"Error reading log: {result.stderr}")
            else:
                print(f"Log file not found: {log_file}")
                
    except Exception as e:
        print(f"Error checking logs: {e}")

def main():
    """Main test function"""
    print("PARTSAPI.RU INTEGRATION TEST")
    print("Testing corrected API method: getPartsbyVIN")
    print("API Key: 5c52f6e4db91259648e10e3dfab5828e")
    print("Test VIN: XW7BF4FK60S145161")
    
    # Test 1: Direct API call
    direct_success, direct_data = test_direct_partsapi()
    
    # Test 2: Backend VIN endpoint
    vin_success, vin_data = test_backend_vin_endpoint()
    
    # Test 3: Backend AI endpoint
    ai_success, ai_data = test_backend_ai_endpoint()
    
    # Check logs
    check_backend_logs()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n🔗 DIRECT PARTSAPI CALL:")
    if direct_success:
        print("✅ Direct API call successful")
        if direct_data and len(direct_data) > 0:
            print(f"✅ Found {len(direct_data)} parts")
        else:
            print("⚠️  No parts returned")
    else:
        print("❌ Direct API call failed")
    
    print(f"\n🚀 BACKEND VIN ENDPOINT:")
    if vin_success:
        print("✅ Backend VIN endpoint working")
        if vin_data:
            car_info = vin_data.get('car_info', {})
            catalog_groups = vin_data.get('catalog_groups', [])
            print(f"✅ Car info available: {bool(car_info)}")
            print(f"✅ Catalog groups: {len(catalog_groups)}")
    else:
        print("❌ Backend VIN endpoint failed")
    
    print(f"\n🤖 BACKEND AI ENDPOINT:")
    if ai_success:
        print("✅ Backend AI endpoint working")
        if ai_data:
            articles = ai_data.get('articles_found', [])
            results = ai_data.get('results', [])
            print(f"✅ AI found {len(articles)} articles")
            print(f"✅ Returned {len(results)} parts")
    else:
        print("❌ Backend AI endpoint failed")
    
    print(f"\n📋 OVERALL STATUS:")
    if direct_success and vin_success and ai_success:
        print("🎉 ALL TESTS PASSED - PartsAPI integration is working!")
    elif direct_success:
        print("⚠️  Direct API works but backend integration has issues")
    else:
        print("❌ PartsAPI integration has critical issues")
    
    return direct_success and vin_success and ai_success

if __name__ == "__main__":
    main()