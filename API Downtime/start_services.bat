@echo off
echo ========================================
echo Starting API Monitoring System
echo ========================================
echo.
echo Starting AI Training Service (Port 5001)...
start "AI Training Service" cmd /k "cd /d %~dp0src && python ai_training_service.py"
timeout /t 3 /nobreak >nul
echo.
echo Starting Main Application (Port 5000)...
start "Main Application" cmd /k "cd /d %~dp0src && python app.py"
echo.
echo ========================================
echo Both services started!
echo ========================================
echo Main App: http://localhost:5000
echo AI Training Service: http://localhost:5001
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul
