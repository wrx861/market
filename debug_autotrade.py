#!/usr/bin/env python3
"""
Debug script to check raw Autotrade API response for ST-dtw1-395-0
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from autotrade_client import AutotradeClient

def debug_autotrade_response():
    """Debug the raw Autotrade API response"""
    print("=" * 80)
    print("DEBUGGING AUTOTRADE API RESPONSE FOR ST-DTW1-395-0")
    print("=" * 80)
    
    client = AutotradeClient()
    article = "ST-dtw1-395-0"
    
    print(f"Testing article: {article}")
    
    try:
        # Get raw response
        results = client.search_by_article(article, cross=True, replace=True)
        
        print(f"\nTotal results returned: {len(results)}")
        
        # Analyze all warehouses
        warehouses = {}
        delivery_stats = {}
        tyumen_warehouses = []
        
        for i, result in enumerate(results):
            warehouse = result.get('warehouse', 'Unknown')
            delivery_days = result.get('delivery_days', 'Unknown')
            quantity = result.get('quantity', 0)
            in_stock = result.get('in_stock', False)
            
            print(f"\nResult {i+1}:")
            print(f"  Article: {result.get('article', 'Unknown')}")
            print(f"  Brand: {result.get('brand', 'Unknown')}")
            print(f"  Warehouse: {warehouse}")
            print(f"  Delivery days: {delivery_days}")
            print(f"  Quantity: {quantity}")
            print(f"  In stock: {in_stock}")
            print(f"  Price: {result.get('price', 0)} руб")
            
            # Count warehouses
            if warehouse not in warehouses:
                warehouses[warehouse] = []
            warehouses[warehouse].append({
                'delivery_days': delivery_days,
                'quantity': quantity,
                'in_stock': in_stock
            })
            
            # Count delivery days
            if delivery_days not in delivery_stats:
                delivery_stats[delivery_days] = 0
            delivery_stats[delivery_days] += 1
            
            # Check for Tyumen
            if 'тюмень' in warehouse.lower():
                tyumen_warehouses.append({
                    'warehouse': warehouse,
                    'delivery_days': delivery_days,
                    'quantity': quantity,
                    'in_stock': in_stock
                })
        
        print(f"\n{'='*60}")
        print("WAREHOUSE ANALYSIS")
        print(f"{'='*60}")
        
        print(f"Total unique warehouses: {len(warehouses)}")
        for warehouse, items in warehouses.items():
            total_qty = sum(item['quantity'] for item in items)
            delivery_days_list = [item['delivery_days'] for item in items]
            in_stock_count = sum(1 for item in items if item['in_stock'])
            
            print(f"\n{warehouse}:")
            print(f"  Items: {len(items)}")
            print(f"  Total quantity: {total_qty}")
            print(f"  Delivery days: {delivery_days_list}")
            print(f"  In stock items: {in_stock_count}")
        
        print(f"\n{'='*60}")
        print("DELIVERY DAYS ANALYSIS")
        print(f"{'='*60}")
        
        for delivery_days, count in sorted(delivery_stats.items()):
            print(f"Delivery {delivery_days} days: {count} items")
        
        print(f"\n{'='*60}")
        print("TYUMEN WAREHOUSES ANALYSIS")
        print(f"{'='*60}")
        
        if tyumen_warehouses:
            print(f"Found {len(tyumen_warehouses)} items from Tyumen warehouses:")
            for tyumen in tyumen_warehouses:
                print(f"  - {tyumen['warehouse']}")
                print(f"    Delivery: {tyumen['delivery_days']} days")
                print(f"    Quantity: {tyumen['quantity']}")
                print(f"    In stock: {tyumen['in_stock']}")
        else:
            print("❌ NO TYUMEN WAREHOUSES FOUND")
            print("This explains why the filter returns 0 results!")
        
        print(f"\n{'='*60}")
        print("FILTER ANALYSIS")
        print(f"{'='*60}")
        
        # Simulate the filter logic
        filtered_results = []
        for result in results:
            warehouse = result.get('warehouse', '').lower()
            delivery_days = result.get('delivery_days', 999)
            quantity = result.get('quantity', 0)
            
            # Filter criteria: Tyumen warehouse + delivery_days = 0 + quantity > 0
            if 'тюмень' in warehouse and delivery_days == 0 and quantity > 0:
                filtered_results.append(result)
        
        print(f"Items matching 'in_stock_tyumen' filter: {len(filtered_results)}")
        
        if filtered_results:
            print("Filtered results:")
            for result in filtered_results:
                print(f"  - {result.get('warehouse', 'Unknown')} - {result.get('quantity', 0)} шт - {result.get('delivery_days', 'Unknown')} дней")
        else:
            print("✅ FILTER WORKING CORRECTLY: No items match the criteria")
            print("   (Tyumen warehouse + delivery_days = 0 + quantity > 0)")
        
        # Check if there are Tyumen warehouses with delivery_days = 1
        tyumen_with_delivery_1 = []
        for result in results:
            warehouse = result.get('warehouse', '').lower()
            delivery_days = result.get('delivery_days', 999)
            
            if 'тюмень' in warehouse and delivery_days == 1:
                tyumen_with_delivery_1.append(result)
        
        if tyumen_with_delivery_1:
            print(f"\n⚠️  Found {len(tyumen_with_delivery_1)} Tyumen items with delivery_days = 1:")
            for result in tyumen_with_delivery_1:
                print(f"  - {result.get('warehouse', 'Unknown')} - {result.get('quantity', 0)} шт")
            print("These would have been shown with the OLD filter logic (delivery_days <= 1)")
            print("But are correctly EXCLUDED with the NEW filter logic (delivery_days == 0)")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_autotrade_response()