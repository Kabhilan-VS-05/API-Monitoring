@echo off
setlocal

echo ========================================
echo Stopping existing Python processes
echo ========================================
Taskkill /IM python.exe /F >nul 2>&1
echo Any running python.exe processes have been terminated.

echo.
echo ========================================
echo Launching Services
echo ========================================

set "PROJECT_ROOT=%~dp0"

echo Starting AI Training Service (port 5001)...
start "AI Training 5001" cmd /k "cd /d "%PROJECT_ROOT%src" && python ai_training_service.py"
timeout /t 2 /nobreak >nul

echo Starting Main Application (port 5000)...
start "Main App 5000" cmd /k "cd /d "%PROJECT_ROOT%src" && python app.py"
timeout /t 2 /nobreak >nul

echo Starting Test API (port 7000)...
start "Test API 7000" cmd /k "cd /d "%PROJECT_ROOT%running API" && python api_testing.py"

echo.
echo ========================================
echo Services launched.
echo   - Flask Dashboard : http://localhost:5000
echo   - AI Training API: http://localhost:5001/health
echo   - Test API       : http://localhost:7000
echo ========================================
echo You can close this window. Individual terminals stay open for logs.
pause >nul
