@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 🧹 API Downtime Project Cleanup Script
echo ========================================
echo.
echo This script will clean up and organize your project
echo by removing unwanted files and organizing the structure.
echo.
pause

echo 🔄 Starting cleanup process...
echo.

:: Phase 1: Remove backup directories
echo [1/6] Removing backup directories...
for /d %%i in (backup_*) do (
    echo   Removing: %%i
    rmdir /s /q "%%i" 2>nul
)

:: Phase 2: Remove debug files
echo [2/6] Removing debug files...
del /q "debug_css.html" 2>nul && echo   Removed: debug_css.html
del /q "debug_email_config.py" 2>nul && echo   Removed: debug_email_config.py

:: Phase 3: Remove duplicate friend files
echo [3/6] Removing duplicate friend files...
del /q "src\ai_predictor_friend.py" 2>nul && echo   Removed: src\ai_predictor_friend.py
del /q "src\ai_training_service_friend.py" 2>nul && echo   Removed: src\ai_training_service_friend.py

:: Phase 4: Remove integration scripts
echo [4/6] Removing integration scripts...
del /q "integrate_friend_improvements.py" 2>nul && echo   Removed: integrate_friend_improvements.py
del /q "FRIEND_IMPROVEMENTS_ANALYSIS.md" 2>nul && echo   Removed: FRIEND_IMPROVEMENTS_ANALYSIS.md
del /q "INTEGRATION_GUIDE.md" 2>nul && echo   Removed: INTEGRATION_GUIDE.md

:: Phase 5: Remove email setup files
echo [5/6] Removing email setup files...
del /q "EMAIL_*.bat" 2>nul && echo   Removed email setup batch files
del /q "CONFIGURE_*.bat" 2>nul && echo   Removed configuration batch files
del /q "SETUP_*.bat" 2>nul && echo   Removed setup batch files
del /q "EMAIL_CONFIG_GUIDE.txt" 2>nul && echo   Removed: EMAIL_CONFIG_GUIDE.txt

:: Phase 6: Remove cleanup guide (optional)
echo [6/6] Removing temporary cleanup guide...
del /q "CLEANUP_AND_ORGANIZE.md" 2>nul && echo   Removed: CLEANUP_AND_ORGANIZE.md

echo.
echo ✅ Cleanup completed successfully!
echo.
echo 📁 Next step: Run ORGANIZE_MODELS.bat to organize model files
echo.
pause
