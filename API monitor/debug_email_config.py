#!/usr/bin/env python3
"""
Debug email configuration loading
"""
import os
from dotenv import load_dotenv

def debug_email_config():
    print("=== Email Configuration Debug ===")
    
    # Load .env file
    load_dotenv()
    
    # Check each email config variable
    email_vars = {
        'EMAIL_SMTP_SERVER': os.getenv('EMAIL_SMTP_SERVER'),
        'EMAIL_SMTP_PORT': os.getenv('EMAIL_SMTP_PORT'),
        'EMAIL_USERNAME': os.getenv('EMAIL_USERNAME'),
        'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD'),
        'EMAIL_FROM_ADDRESS': os.getenv('EMAIL_FROM_ADDRESS')
    }
    
    print("Email Configuration Status:")
    print("-" * 30)
    
    all_set = True
    for var_name, value in email_vars.items():
        if value:
            if 'PASSWORD' in var_name:
                print(f"✅ {var_name}: {'*' * len(value)}")
            else:
                print(f"✅ {var_name}: {value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_set = False
    
    print("-" * 30)
    
    if all_set:
        print("✅ All email configuration is set!")
        print("The issue might be in the application restart.")
        print("\nTry:")
        print("1. Stop the application")
        print("2. Run: CONFIGURE_EMAIL.bat")
        print("3. Restart: python src/app.py")
    else:
        print("❌ Missing email configuration!")
        print("\nTo fix:")
        print("1. Run: CONFIGURE_EMAIL.bat")
        print("2. Or manually add to .env file:")
        print("   EMAIL_SMTP_SERVER=smtp.gmail.com")
        print("   EMAIL_SMTP_PORT=587")
        print("   EMAIL_USERNAME=formsreg61@gmail.com")
        print("   EMAIL_PASSWORD=ibkr fjec pgue aflb")
        print("   EMAIL_FROM_ADDRESS=formsreg61@gmail.com")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print(f"\n✅ .env file exists ({os.path.getsize('.env')} bytes)")
        print("First few lines:")
        with open('.env', 'r') as f:
            lines = f.readlines()[:5]
            for i, line in enumerate(lines, 1):
                print(f"   {i}: {line.strip()}")
    else:
        print("\n❌ .env file does not exist!")
        print("Run CONFIGURE_EMAIL.bat to create it.")

if __name__ == "__main__":
    debug_email_config()
