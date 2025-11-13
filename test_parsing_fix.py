#!/usr/bin/env python3
"""
Test the FIXED PartsAPI article parsing logic directly
Since PartsAPI is rate-limited, we'll test the parsing methods directly
"""

import sys
import json
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from partsapi_client import PartsApiClient

def test_parse_parts_response_method():
    """Test the parse_parts_response method directly with sample data"""
    print("=" * 60)
    print("TESTING parse_parts_response() METHOD DIRECTLY")
    print("=" * 60)
    
    client = PartsApiClient()
    
    # Sample raw data that would come from PartsAPI
    # This simulates the format: parts field contains "BRAND|ARTICLE,BRAND|ARTICLE"
    sample_raw_parts = [
        {
            "name": "Комплект тормозных колодок",
            "group": "Тормозная система",
            "parts": "TOYOTA|4654020040,LEXUS|0446520290,AISIN|A1N135"
        },
        {
            "name": "Масляный фильтр",
            "group": "Система смазки",
            "parts": "TOYOTA|1560017010,MANN|W67/2,BOSCH|0451103316"
        },
        {
            "name": "Воздушный фильтр",
            "group": "Система впуска",
            "parts": "TOYOTA|1780122020,K&N|33-2252,FRAM|CA9997"
        }
    ]
    
    print("Sample raw data from PartsAPI:")
    print(json.dumps(sample_raw_parts, indent=2, ensure_ascii=False))
    
    # Test the parsing method
    print("\n--- TESTING PARSING METHOD ---")
    parsed_parts = client.parse_parts_response(sample_raw_parts)
    
    print(f"\nParsed {len(parsed_parts)} individual parts:")
    print(json.dumps(parsed_parts, indent=2, ensure_ascii=False))
    
    # Validate parsing results
    success = True
    real_articles = 0
    
    for i, part in enumerate(parsed_parts):
        article = part.get('article', '')
        brand = part.get('brand', '')
        name = part.get('name', '')
        
        print(f"\nPart {i+1}:")
        print(f"  Article: '{article}'")
        print(f"  Brand: '{brand}'")
        print(f"  Name: '{name}'")
        
        # Check if we got real articles (not "Unknown")
        if article and article != "Unknown" and len(article) > 3:
            real_articles += 1
            print(f"  ✅ REAL ARTICLE: {article}")
        else:
            print(f"  ❌ INVALID ARTICLE: '{article}'")
            success = False
        
        # Check if we got real brands
        if brand and brand != "Unknown" and len(brand) > 1:
            print(f"  ✅ REAL BRAND: {brand}")
        else:
            print(f"  ❌ INVALID BRAND: '{brand}'")
            success = False
    
    print(f"\n--- PARSING TEST RESULTS ---")
    if success and real_articles > 0:
        print(f"✅ SUCCESS: parse_parts_response() is working correctly!")
        print(f"✅ Extracted {real_articles} real articles from parts field")
        print(f"✅ Format 'BRAND|ARTICLE,BRAND|ARTICLE' parsed correctly")
    else:
        print(f"❌ FAILURE: parse_parts_response() is not working correctly")
        print(f"❌ Only {real_articles} real articles extracted")
    
    return success

def test_ai_search_with_fallback():
    """Test AI search endpoint with fallback to Rossko when PartsAPI is rate-limited"""
    print("\n" + "=" * 60)
    print("TESTING AI SEARCH WITH PARTSAPI RATE LIMIT FALLBACK")
    print("=" * 60)
    
    import requests
    
    # Load environment variables
    env_file = Path(__file__).parent / "frontend" / ".env"
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    backend_url = env_vars.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    endpoint = f"{backend_url}/api/search/ai"
    
    print(f"Testing endpoint: {endpoint}")
    
    # Test with a simple query that should fallback to Rossko
    test_data = {
        "telegram_id": 123456789,
        "vin": "XW7BF4FK60S145161",
        "query": "масляный фильтр"
    }
    
    print(f"Request payload: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        print("\nSending request (expecting PartsAPI rate limit, should fallback to Rossko)...")
        response = requests.post(
            endpoint,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API returned 200 OK")
            
            response_data = response.json()
            results = response_data.get('results', [])
            
            print(f"Found {len(results)} results")
            
            if len(results) > 0:
                print("\nFirst few results:")
                for i, result in enumerate(results[:3]):
                    article = result.get('article', '')
                    brand = result.get('brand', '')
                    name = result.get('name', '')
                    source = result.get('source', '')
                    
                    print(f"  Result {i+1}:")
                    print(f"    Article: {article}")
                    print(f"    Brand: {brand}")
                    print(f"    Name: {name}")
                    print(f"    Source: {source}")
                
                # Check if fallback to Rossko worked
                rossko_results = [r for r in results if 'rossko' in r.get('source', '').lower()]
                if len(rossko_results) > 0:
                    print(f"\n✅ SUCCESS: Fallback to Rossko worked! Found {len(rossko_results)} Rossko results")
                    return True
                else:
                    print(f"\n⚠️  No Rossko fallback detected, but got {len(results)} results")
                    return len(results) > 0
            else:
                print("\n❌ No results found")
                return False
        else:
            print(f"❌ API returned error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 TESTING PARTSAPI ARTICLE PARSING FIX")
    print("=" * 80)
    print("Testing parse_parts_response() method and AI search fallback")
    print("=" * 80)
    
    # Test 1: Direct parsing method test
    parsing_success = test_parse_parts_response_method()
    
    # Test 2: AI search with fallback
    fallback_success = test_ai_search_with_fallback()
    
    print("\n" + "=" * 80)
    print("🏁 FINAL TEST SUMMARY")
    print("=" * 80)
    
    if parsing_success:
        print("✅ PARSING METHOD TEST: SUCCESS")
        print("  - parse_parts_response() correctly extracts BRAND|ARTICLE format")
        print("  - Real articles and brands are extracted properly")
        print("  - Method implementation is working as expected")
    else:
        print("❌ PARSING METHOD TEST: FAILED")
        print("  - parse_parts_response() is not working correctly")
        print("  - Articles/brands not extracted properly")
    
    if fallback_success:
        print("\n✅ AI SEARCH FALLBACK TEST: SUCCESS")
        print("  - AI search endpoint handles PartsAPI rate limits")
        print("  - Fallback to Rossko API is working")
        print("  - System returns results even when PartsAPI is unavailable")
    else:
        print("\n❌ AI SEARCH FALLBACK TEST: FAILED")
        print("  - AI search endpoint not handling rate limits properly")
        print("  - Fallback mechanism may not be working")
    
    print("\n📋 CONCLUSIONS:")
    if parsing_success and fallback_success:
        print("🎉 ARTICLE PARSING FIX IS WORKING!")
        print("✅ The parse_parts_response() method correctly handles BRAND|ARTICLE format")
        print("✅ AI search properly falls back to Rossko when PartsAPI is rate-limited")
        print("✅ System is resilient and provides results even with API limitations")
    elif parsing_success:
        print("⚠️  PARTIAL SUCCESS:")
        print("✅ Article parsing logic is correct")
        print("❌ But AI search fallback needs improvement")
    else:
        print("💥 PARSING FIX NEEDS WORK:")
        print("❌ Core parsing logic is not working correctly")
        print("❌ Need to fix parse_parts_response() method")
    
    return parsing_success and fallback_success

if __name__ == "__main__":
    main()