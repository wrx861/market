#!/usr/bin/env python3
"""
Direct test of Autotrade API parsing for ST-dtw1-395-0
"""

import requests
import json
import time

def test_direct_autotrade():
    """Test the article directly and show full response"""
    
    backend_url = "https://car-garage-app.preview.emergentagent.com"
    endpoint = f"{backend_url}/api/search/article"
    
    # Test the main article multiple times to see different warehouses
    test_articles = ["ST-dtw1-395-0"] * 3  # Test 3 times
    
    all_autotrade_results = []
    
    for i, article in enumerate(test_articles):
        print(f"\n{'='*60}")
        print(f"TEST RUN {i+1}: {article}")
        print(f"{'='*60}")
        
        test_data = {
            "telegram_id": 123456789,
            "article": article
        }
        
        try:
            print(f"Sending request for: {article}")
            start_time = time.time()
            
            response = requests.post(
                endpoint,
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            duration = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Duration: {duration:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"Status: {data.get('status')}")
                print(f"Query: {data.get('query')}")
                print(f"Count: {data.get('count')}")
                
                results = data.get('results', [])
                print(f"Total results: {len(results)}")
                
                # Check providers
                providers = {}
                for result in results:
                    provider = result.get('provider', 'unknown')
                    if provider not in providers:
                        providers[provider] = 0
                    providers[provider] += 1
                
                print(f"Providers: {providers}")
                
                # Show Autotrade results specifically
                autotrade_results = [r for r in results if r.get('provider') == 'autotrade']
                print(f"Autotrade results: {len(autotrade_results)}")
                
                if autotrade_results:
                    print("\n--- AUTOTRADE RESULTS ---")
                    for i, result in enumerate(autotrade_results[:3]):
                        print(f"  Result {i+1}:")
                        print(f"    Article: {result.get('article')}")
                        print(f"    Brand: {result.get('brand')}")
                        print(f"    Name: {result.get('name')}")
                        print(f"    Price: {result.get('price')} руб")
                        print(f"    Quantity: {result.get('quantity')} шт")
                        print(f"    Warehouse: {result.get('warehouse')}")
                        print(f"    Delivery: {result.get('delivery_days')} дней")
                        print(f"    In stock: {result.get('in_stock')}")
                        print(f"    Provider: {result.get('provider')}")
                
                # Show all results for comparison
                print(f"\n--- ALL RESULTS ---")
                for i, result in enumerate(results):
                    print(f"  {i+1}. {result.get('provider', 'unknown')} - {result.get('brand', 'Unknown')} {result.get('article', 'Unknown')} - {result.get('price', 0)} руб")
                
                if autotrade_results:
                    print(f"\n✅ SUCCESS: Found {len(autotrade_results)} Autotrade results for {article}")
                    all_autotrade_results.extend(autotrade_results)
                else:
                    print(f"\n⚠️  No Autotrade results for {article}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")
    
    # Summary of all Autotrade results
    print(f"\n{'='*80}")
    print(f"SUMMARY OF ALL AUTOTRADE RESULTS")
    print(f"{'='*80}")
    print(f"Total Autotrade results collected: {len(all_autotrade_results)}")
    
    # Unique warehouses
    warehouses = set()
    prices = []
    quantities = []
    
    for result in all_autotrade_results:
        warehouses.add(result.get('warehouse', 'Unknown'))
        prices.append(result.get('price', 0))
        quantities.append(result.get('quantity', 0))
    
    print(f"Unique warehouses: {len(warehouses)}")
    for warehouse in sorted(warehouses):
        print(f"  - {warehouse}")
    
    if prices:
        print(f"Price range: {min(prices)} - {max(prices)} руб")
        print(f"Average price: {sum(prices)/len(prices):.2f} руб")
    
    if quantities:
        print(f"Quantity range: {min(quantities)} - {max(quantities)} шт")
        print(f"Total quantity: {sum(quantities)} шт")
    
    return len(all_autotrade_results) > 0

if __name__ == "__main__":
    test_direct_autotrade()