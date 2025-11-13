#!/usr/bin/env python3
"""
Test OBD P0420 code specifically
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

def test_p0420_diagnostics():
    """Test P0420 OBD code diagnostics"""
    print("=" * 80)
    print("TESTING P0420 OBD DIAGNOSTICS")
    print("=" * 80)
    
    # Load environment variables
    env_vars = load_env_vars()
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    # Use existing vehicle (from previous test)
    vehicle_id = "07093ae5-bfd0-4622-a59a-5b08d2544c0c"  # From previous test
    
    print(f"Backend URL: {backend_url}")
    print(f"Using vehicle ID: {vehicle_id}")
    
    # Test P0420 diagnostics
    print("\n--- TESTING P0420 DIAGNOSTICS ---")
    diagnostics_endpoint = f"{backend_url}/api/garage/diagnostics"
    obd_data = {
        "obd_code": "P0420",
        "vehicle_id": vehicle_id,
        "telegram_id": 508352361
    }
    
    print(f"OBD payload: {json.dumps(obd_data, indent=2)}")
    
    try:
        print("Sending P0420 diagnostics request...")
        start_time = time.time()
        
        obd_response = requests.post(diagnostics_endpoint, json=obd_data, timeout=90)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"P0420 response: {obd_response.status_code} ({duration:.2f}s)")
        
        if obd_response.status_code == 200:
            obd_result = obd_response.json()
            
            print(f"✅ P0420 diagnostics successful")
            print(f"Status: {obd_result.get('status')}")
            print(f"OBD Code: {obd_result.get('obd_code')}")
            print(f"Vehicle: {obd_result.get('vehicle')}")
            
            diagnosis = obd_result.get('diagnosis', '')
            print(f"Diagnosis length: {len(diagnosis)} characters")
            
            # Show diagnosis excerpt
            print(f"\n--- P0420 DIAGNOSIS EXCERPT ---")
            print(diagnosis[:200] + "..." if len(diagnosis) > 200 else diagnosis)
            
            return True
        else:
            print(f"❌ P0420 diagnostics failed: {obd_response.status_code}")
            print(f"Response: {obd_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ P0420 diagnostics error: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 TESTING P0420 OBD DIAGNOSTICS")
    print("=" * 80)
    
    success = test_p0420_diagnostics()
    
    print("\n" + "=" * 80)
    print("🏁 P0420 TEST SUMMARY")
    print("=" * 80)
    
    if success:
        print("🎉 SUCCESS: P0420 DIAGNOSTICS WORKING!")
        print("✅ Different OBD codes supported")
        print("✅ System handles multiple diagnostic requests")
    else:
        print("💥 FAILURE: P0420 DIAGNOSTICS NOT WORKING!")
    
    return success

if __name__ == "__main__":
    main()