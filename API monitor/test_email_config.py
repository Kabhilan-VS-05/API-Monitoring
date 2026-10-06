#!/usr/bin/env python3
"""
Test email configuration and basic functionality
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_email_config():
    print("=== Email Configuration Test ===")
    
    try:
        from app import EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT
        print(f"✅ Email Server: {EMAIL_SMTP_SERVER}:{EMAIL_SMTP_PORT}")
        print(f"✅ Email Username: {EMAIL_USERNAME}")
        print(f"✅ Email Password: {'*' * len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 'Not set'}")
        
        if not EMAIL_USERNAME or not EMAIL_PASSWORD:
            print("❌ Email credentials not configured")
            return False
        return True
    except Exception as e:
        print(f"❌ Error loading email config: {e}")
        return False

def test_smtp_connection():
    print("\n=== SMTP Connection Test ===")
    try:
        import smtplib
        from app import EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD
        
        print(f"Connecting to {EMAIL_SMTP_SERVER}:{EMAIL_SMTP_PORT}...")
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.quit()
        print("✅ SMTP connection successful")
        return True
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        print("   Check your email and app password")
        return False

def test_email_sending():
    print("\n=== Email Sending Test ===")
    try:
        from app import dispatch_email_message
        
        test_payload = {
            "api_name": "Test API",
            "status": "Testing",
            "risk_percentage": "50",
            "cause_summary": "Test cause",
            "recommendation": "Test recommendation"
        }
        
        success, result = dispatch_email_message(EMAIL_USERNAME, test_payload)
        if success:
            print("✅ Test email sent successfully")
            print(f"   Result: {result}")
            return True
        else:
            print(f"❌ Email sending failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Email test error: {e}")
        return False

if __name__ == "__main__":
    print("Email Configuration Test Tool")
    print("=" * 40)
    
    config_ok = test_email_config()
    
    if config_ok:
        smtp_ok = test_smtp_connection()
        if smtp_ok:
            test_email_sending()
    
    print("\n" + "=" * 40)
    print("Test complete!")
    print("\nIf tests fail:")
    print("1. Check your .env file has correct email settings")
    print("2. Verify Gmail app password (not regular password)")
    print("3. Ensure 2-step verification is enabled on Gmail")
    print("4. Run SETUP_EMAIL.bat to configure automatically")
