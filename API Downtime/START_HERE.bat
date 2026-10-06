@echo off
echo ========================================
echo Starting API Monitoring System
echo ========================================
echo.
echo Starting AI Training Service in a new window...
start "AI Training Service" cmd /c "python ""d:\Users\Desktop\The Project\API Downtime\src\ai_training_service.py"""
echo.
echo Starting Flask application in the current window...
python "d:\Users\Desktop\The Project\API Downtime\src\app.py"
pause