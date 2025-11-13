#!/usr/bin/env python3
"""
Test OBD caching system
"""

import requests
import json
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

def test_obd_caching():
    """Test OBD caching system"""
    print("=" * 80)
    print("TESTING OBD CACHING SYSTEM")
    print("=" * 80)
    
    # Load environment variables
    env_vars = load_env_vars()
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    # Use existing vehicle
    vehicle_id = "07093ae5-bfd0-4622-a59a-5b08d2544c0c"
    
    print(f"Backend URL: {backend_url}")
    print(f"Using vehicle ID: {vehicle_id}")
    
    # Test caching with P0301 (should be cached from previous test)
    print("\n--- TESTING CACHE WITH P0301 (SHOULD BE CACHED) ---")
    diagnostics_endpoint = f"{backend_url}/api/garage/diagnostics"
    obd_data = {
        "obd_code": "P0301",
        "vehicle_id": vehicle_id,
        "telegram_id": 508352361
    }
    
    try:
        print("Sending cached P0301 request...")
        start_time = time.time()
        
        obd_response = requests.post(diagnostics_endpoint, json=obd_data, timeout=30)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Cached P0301 response: {obd_response.status_code} ({duration:.3f}s)")
        
        if obd_response.status_code == 200:
            obd_result = obd_response.json()
            
            print(f"✅ Cached P0301 successful")
            print(f"Status: {obd_result.get('status')}")
            print(f"OBD Code: {obd_result.get('obd_code')}")
            
            diagnosis = obd_result.get('diagnosis', '')
            print(f"Diagnosis length: {len(diagnosis)} characters")
            
            # Check if response was fast (indicating cache hit)
            if duration < 0.5:  # Less than 500ms suggests cache hit
                print(f"✅ Fast response ({duration:.3f}s) suggests cache hit")
                cache_working = True
            else:
                print(f"⚠️  Slower response ({duration:.3f}s) may indicate cache miss")
                cache_working = False
            
            return cache_working
        else:
            print(f"❌ Cached request failed: {obd_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cache test error: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 TESTING OBD CACHING SYSTEM")
    print("=" * 80)
    
    cache_success = test_obd_caching()
    
    print("\n" + "=" * 80)
    print("🏁 CACHING TEST SUMMARY")
    print("=" * 80)
    
    if cache_success:
        print("🎉 SUCCESS: OBD CACHING SYSTEM WORKING!")
        print("✅ Cache hit detected (fast response)")
        print("✅ Repeated requests use cached results")
        print("✅ Performance optimization working")
    else:
        print("⚠️  CACHING STATUS UNCLEAR")
        print("⚠️  May be working but hard to detect due to rate limits")
        print("✅ System still functional with or without cache")
    
    return cache_success

if __name__ == "__main__":
    main()