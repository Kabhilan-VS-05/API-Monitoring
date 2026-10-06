#!/usr/bin/env python3
"""
Diagnose loading issues with Community Guardian
"""

import sys
import os

print("🏥 Community Guardian - Loading Issue Diagnosis")
print("=" * 50)

# Check Python version
print(f"Python version: {sys.version}")

# Check required modules
required_modules = ['flask', 'pymongo', 'requests', 'pycurl']
missing_modules = []

for module in required_modules:
    try:
        __import__(module)
        print(f"✅ {module} - OK")
    except ImportError as e:
        print(f"❌ {module} - MISSING: {e}")
        missing_modules.append(module)

if missing_modules:
    print(f"\n❌ Missing modules: {missing_modules}")
    print("Install with: pip install flask pymongo requests pycurl cryptography idna")
    sys.exit(1)

# Check MongoDB connection
print("\n📊 Checking MongoDB connection...")
try:
    from pymongo import MongoClient
    
    # Try to connect with timeout
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
    
    # Test connection
    client.server_info()
    print("✅ MongoDB connection - OK")
    
    # Check database
    db = client['api_monitoring']
    collections = db.list_collection_names()
    print(f"📋 Collections found: {collections}")
    
    # Check if monitored_apis exists and has data
    if 'monitored_apis' in collections:
        count = db.monitored_apis.count_documents({})
        print(f"🏥 Healthcare APIs in database: {count}")
        
        if count == 0:
            print("⚠️ No healthcare APIs found. Running setup...")
            # Run setup
            sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
            try:
                import setup_healthcare_apis
                if setup_healthcare_apis.setup_healthcare_apis():
                    print("✅ Healthcare APIs setup completed")
                else:
                    print("❌ Healthcare APIs setup failed")
            except Exception as e:
                print(f"❌ Setup error: {e}")
        else:
            print("✅ Healthcare APIs already exist")
    else:
        print("⚠️ monitored_apis collection not found")
        
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("\n🔧 MongoDB troubleshooting:")
    print("1. Make sure MongoDB is installed")
    print("2. Start MongoDB service: net start MongoDB")
    print("3. Check if MongoDB is running on port 27017")

# Check Flask app
print("\n🌐 Checking Flask application...")
try:
    from src.app import app
    print("✅ Flask app loaded successfully")
    
    # Check routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(rule.rule)
    
    healthcare_routes = [r for r in routes if 'healthcare' in r or 'advanced' in r]
    print(f"🛣️ Healthcare-related routes: {len(healthcare_routes)}")
    
    for route in healthcare_routes[:5]:  # Show first 5
        print(f"   {route}")
    
    if len(healthcare_routes) > 5:
        print(f"   ... and {len(healthcare_routes) - 5} more")
        
except Exception as e:
    print(f"❌ Flask app error: {e}")

print("\n🚀 Starting recommendations:")
print("1. If MongoDB is not running, start it with: net start MongoDB")
print("2. If no healthcare APIs exist, run: python scripts/setup_healthcare_apis.py")
print("3. Start the application: python src/app.py")
print("4. Open browser to: http://localhost:5000/advanced_monitor")

print("\n🔍 Browser debugging:")
print("- Open browser developer tools (F12)")
print("- Check Console tab for JavaScript errors")
print("- Check Network tab for failed API requests")
print("- Look for 404 or 500 errors on /api/advanced/monitors")

print("\n✅ Diagnosis complete!")
