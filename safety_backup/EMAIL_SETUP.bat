@echo off
echo ========================================
echo Email Notification Setup Guide
echo ========================================
echo.
echo This will help you configure email notifications
echo for the API Downtime Monitor.
echo.
echo Required Email Configuration:
echo ----------------------------------------
echo 1. Gmail Account (recommended)
echo 2. App Password (not regular password)
echo 3. SMTP settings
echo.
echo Steps to setup Gmail App Password:
echo ----------------------------------------
echo 1. Enable 2-Step Verification on your Gmail
echo 2. Go to: https://myaccount.google.com/apppasswords
echo 3. Select "Mail" on "Windows computer"
echo 4. Generate 16-character app password
echo 5. Copy this password for the setup
echo.
echo Creating your .env file...
echo.

if not exist ".env" (
    echo Creating .env file from template...
    copy ".env.example" ".env"
    echo ✅ .env file created
) else (
    echo ✅ .env file already exists
)

echo.
echo Please edit your .env file with these settings:
echo ----------------------------------------
echo EMAIL_SMTP_SERVER=smtp.gmail.com
echo EMAIL_SMTP_PORT=587
echo EMAIL_USERNAME=your_email@gmail.com
echo EMAIL_PASSWORD=your_16_char_app_password
echo EMAIL_FROM_ADDRESS=alerts@yourdomain.com
echo.
echo Replace:
echo - your_email@gmail.com with your Gmail address
echo - your_16_char_app_password with the app password
echo - alerts@yourdomain.com with your from address
echo.
echo After configuration:
echo 1. Restart the application
echo 2. Test email notifications in the dashboard
echo.
echo ========================================
echo Email Setup Complete!
echo ========================================
echo.
echo Note: WhatsApp has been removed from this application.
echo Only email notifications are supported.
echo.
pause
