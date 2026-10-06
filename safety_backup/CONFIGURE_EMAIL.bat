@echo off
echo ========================================
echo Email Configuration Setup
echo ========================================
echo.
echo Setting up email for: formsreg61@gmail.com
echo.

echo [1/4] Creating .env file with email settings...
if exist ".env" (
    echo ✅ .env file exists, backing up...
    copy ".env" ".env.backup" >nul 2>&1
)

echo.
echo [2/4] Adding email configuration...
(
echo # Email Configuration
echo EMAIL_SMTP_SERVER=smtp.gmail.com
echo EMAIL_SMTP_PORT=587
echo EMAIL_USERNAME=formsreg61@gmail.com
echo EMAIL_PASSWORD=ibkr fjec pgue aflb
echo EMAIL_FROM_ADDRESS=formsreg61@gmail.com
echo.
echo # Other existing settings...
) > .env

if exist ".env.example" (
    echo ✅ Appending existing configuration...
    type ".env.example" >> .env
)

echo.
echo [3/4] Configuration added:
echo ----------------------------------------
echo ✅ Email Server: smtp.gmail.com:587
echo ✅ Username: formsreg61@gmail.com
echo ✅ Password: ibkr fjec pgue aflb
echo ✅ From Address: formsreg61@gmail.com
echo ----------------------------------------

echo.
echo [4/4] Next steps:
echo 1. Restart the application: python src/app.py
echo 2. Open Settings panel in dashboard
echo 3. Test email notifications
echo.
echo ========================================
echo Email Configuration Complete!
echo ========================================
echo.
pause
