@echo off
echo ========================================
echo Clean Restart - Clearing Cache
echo ========================================
echo.

echo Step 1: Killing Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Step 2: Clearing Python cache...
del /S /Q __pycache__ 2>nul
del /S /Q *.pyc 2>nul
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo Step 3: Starting fresh...
echo.
call START_HERE.bat
