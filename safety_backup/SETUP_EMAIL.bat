@echo off
echo ========================================
echo Email Configuration Setup
echo ========================================
echo.
echo Setting up email notifications for:
echo formsreg61@gmail.com
echo.
echo Creating .env file with your configuration...

echo.
echo [1/3] Creating .env file...
if not exist ".env" (
    copy ".env.example" ".env"
    echo ✅ .env file created from template
) else (
    echo ✅ .env file already exists
)

echo.
echo [2/3] Adding email configuration...
(
echo.
echo # Email Configuration
echo EMAIL_SMTP_SERVER=smtp.gmail.com
echo EMAIL_SMTP_PORT=587
echo EMAIL_USERNAME=formsreg61@gmail.com
echo EMAIL_PASSWORD=ibkr fjec pgue aflb
echo EMAIL_FROM_ADDRESS=formsreg61@gmail.com
) >> .env

echo.
echo [3/3] Configuration complete!
echo.
echo Your email settings have been added to .env file:
echo ----------------------------------------
echo ✅ Email: formsreg61@gmail.com
echo ✅ SMTP: smtp.gmail.com:587
echo ✅ App Password: ibkr fjec pgue aflb
echo.
echo Next steps:
echo 1. Restart the application: python src/app.py
echo 2. Open Settings panel in the dashboard
echo 3. Add email contacts
echo 4. Test email notifications
echo.
echo ========================================
echo Email Setup Complete!
echo ========================================
echo.
pause
