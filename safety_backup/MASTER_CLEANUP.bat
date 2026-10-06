@echo off
setlocal enabledelayedexpansion
color 0A

echo ==========================================
echo 🚀 API Downtime - Master Cleanup & Organization
echo ==========================================
echo.
echo This master script will perform complete project cleanup
echo and organization in the correct sequence.
echo.
echo ⚠️  IMPORTANT: Make sure you have committed your changes
echo    to git before running this cleanup script!
echo.
pause

:: Create backup before cleanup
echo.
echo [PREPARATION] Creating safety backup...
if not exist "safety_backup" mkdir "safety_backup"
xcopy "src" "safety_backup\src\" /E /I /H /Y >nul 2>&1
xcopy "static" "safety_backup\static\" /E /I /H /Y >nul 2>&1
xcopy "static_advanced" "safety_backup\static_advanced\" /E /I /H /Y >nul 2>&1
copy "*.md" "safety_backup\" >nul 2>&1
copy "*.bat" "safety_backup\" >nul 2>&1
copy "*.py" "safety_backup\" >nul 2>&1
copy "requirements.txt" "safety_backup\" >nul 2>&1
if exist ".env" copy ".env" "safety_backup\" >nul 2>&1
echo ✅ Safety backup created in safety_backup\

:: Phase 1: Cleanup unwanted files
echo.
echo [PHASE 1/4] Cleaning up unwanted files...
call CLEANUP_PROJECT.bat

:: Phase 2: Organize model files
echo.
echo [PHASE 2/4] Organizing model files...
call ORGANIZE_MODELS.bat

:: Phase 3: Update application
echo.
echo [PHASE 3/4] Updating application files...
call UPDATE_APPLICATION.bat

:: Phase 4: Final verification
echo.
echo [PHASE 4/4] Final verification...

:: Check if main files exist
set "errors=0"

if not exist "src\app.py" (
    echo ❌ ERROR: src\app.py not found
    set /a errors+=1
)

if not exist "requirements.txt" (
    echo ❌ ERROR: requirements.txt not found
    set /a errors+=1
)

if not exist "README.md" (
    echo ❌ ERROR: README.md not found
    set /a errors+=1
)

if not exist "src\ai_predictor.py" (
    echo ❌ ERROR: src\ai_predictor.py not found
    set /a errors+=1
)

if not exist "src\ai_training_service.py" (
    echo ❌ ERROR: src\ai_training_service.py not found
    set /a errors+=1
)

:: Check if unwanted files are removed
if exist "src\ai_predictor_friend.py" (
    echo ❌ WARNING: src\ai_predictor_friend.py still exists
)

if exist "src\ai_training_service_friend.py" (
    echo ❌ WARNING: src\ai_training_service_friend.py still exists
)

:: Check model organization
if not exist "models\lstm" (
    echo ❌ WARNING: models\lstm directory not created
)

if not exist "models\autoencoder" (
    echo ❌ WARNING: models\autoencoder directory not created
)

if !errors! EQU 0 (
    echo.
    echo ✅ VERIFICATION PASSED: All critical files are present
) else (
    echo.
    echo ❌ VERIFICATION FAILED: !errors! critical files missing
)

:: Summary
echo.
echo ==========================================
echo 📊 CLEANUP SUMMARY
echo ==========================================
echo.
echo ✅ Completed Operations:
echo   - Removed backup directories
echo   - Removed debug and temporary files
echo   - Removed duplicate friend files
echo   - Removed integration scripts
echo   - Organized model files into directories
echo   - Updated application imports
echo   - Updated documentation
echo.
echo 📁 Final Structure:
echo   - src\ (clean source code)
echo   - static\ (basic frontend)
echo   - static_advanced\ (advanced dashboard)
echo   - models\ (organized AI models)
echo   - scripts\ (training scripts)
echo   - docs\ (documentation)
echo   - tests\ (test files)
echo.

if !errors! EQU 0 (
    echo 🎉 CLEANUP COMPLETED SUCCESSFULLY!
    echo.
    echo 🚀 Next Steps:
    echo   1. Test the application: python src\app.py
    echo   2. Verify all functionality works
    echo   3. Run tests: python -m pytest tests/
    echo   4. Commit cleaned project to git
    echo.
    echo 💡 If any issues occur, restore from safety_backup\
) else (
    echo ⚠️  CLEANUP COMPLETED WITH ISSUES
    echo.
    echo 🔧 Troubleshooting:
    echo   1. Check safety_backup\ for missing files
    echo   2. Restore from backup if needed
    echo   3. Manually fix any reported issues
    echo.
    echo 💡 Safety backup available in safety_backup\
)

echo.
echo 🗑️  To remove safety backup (if everything works):
echo    rmdir /s /q safety_backup
echo.
pause
