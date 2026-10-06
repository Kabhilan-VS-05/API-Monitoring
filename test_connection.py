#!/usr/bin/env python3
"""
Test connection to Community Guardian APIs
"""

import requests
import json
import time

def test_api_connection():
    """Test if the Community Guardian APIs are working"""
    
    print("🏥 Community Guardian - Connection Test")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    
    # Test basic connection
    print("📡 Testing basic connection...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Basic connection: {response.status_code}")
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
        print("💡 Make sure the application is running: python src/app.py")
        return False
    
    # Test advanced monitors endpoint
    print("\n📊 Testing healthcare monitors API...")
    try:
        response = requests.get(f"{base_url}/api/advanced/monitors", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Monitors API: {len(data)} APIs found")
            
            # Show healthcare categories
            categories = {}
            for monitor in data:
                cat = monitor.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            print("🏥 Healthcare APIs by category:")
            for cat, count in categories.items():
                icons = {
                    'emergency_dispatch': '🚨',
                    'life_support': '❤️',
                    'emergency_alerts': '📢',
                    'hospital_operations': '🏥',
                    'telemedicine': '💻',
                    'vaccination': '💉',
                    'health_records': '📋',
                    'supply_chain': '🚚',
                    'public_health': '📊'
                }
                icon = icons.get(cat, '⚕️')
                print(f"   {icon} {cat}: {count}")
                
        else:
            print(f"❌ Monitors API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Monitors API error: {e}")
    
    # Test healthcare categories endpoint
    print("\n📋 Testing healthcare categories API...")
    try:
        response = requests.get(f"{base_url}/api/healthcare/categories", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Categories API: {len(data['categories'])} categories found")
        else:
            print(f"❌ Categories API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Categories API error: {e}")
    
    # Test healthcare stats endpoint
    print("\n📊 Testing healthcare stats API...")
    try:
        response = requests.get(f"{base_url}/api/healthcare/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats API: {data['total_apis']} total APIs")
            print(f"   🚨 Critical: {data['by_priority']['critical']}")
            print(f"   ⚕️ High: {data['by_priority']['high']}")
            print(f"   ✅ Up: {data['by_status']['up']}")
            print(f"   ❌ Down: {data['by_status']['down']}")
        else:
            print(f"❌ Stats API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats API error: {e}")
    
    print("\n🎯 Browser Test Instructions:")
    print("1. Open browser to: http://localhost:5000/advanced_monitor")
    print("2. Open Developer Tools (F12)")
    print("3. Check Console for JavaScript errors")
    print("4. Check Network tab for API requests")
    print("5. Look for requests to /api/advanced/monitors")
    
    print("\n✅ Connection test completed!")
    return True

if __name__ == "__main__":
    test_api_connection()
