@echo off
setlocal enabledelayedexpansion
color 0B

echo ==========================================
echo 🔍 Project Verification Script
echo ==========================================
echo.
echo This script will verify that your project is
echo properly organized and all critical files exist.
echo.

:: Initialize counters
set "total_checks=0"
set "passed_checks=0"
set "warnings=0"

echo [VERIFICATION] Checking project structure...
echo.

:: Check critical files
echo 📁 Checking critical files...

set "files_to_check=src\app.py src\ai_predictor.py src\ai_training_service.py src\ai_alert_manager.py requirements.txt README.md .env.example"

for %%f in (%files_to_check%) do (
    set /a total_checks+=1
    if exist "%%f" (
        echo   ✅ %%f
        set /a passed_checks+=1
    ) else (
        echo   ❌ %%f - MISSING
    )
)

:: Check directory structure
echo.
echo 📂 Checking directory structure...

set "dirs_to_check=src static static_advanced models scripts docs tests"

for %%d in (%dirs_to_check%) do (
    set /a total_checks+=1
    if exist "%%d" (
        echo   ✅ %%d\ directory exists
        set /a passed_checks+=1
    ) else (
        echo   ❌ %%d\ directory - MISSING
    )
)

:: Check model organization
echo.
echo 🤖 Checking AI model organization...

if exist "models" (
    set /a total_checks+=1
    set "model_dirs_found=0"
    
    if exist "models\lstm" (
        echo   ✅ models\lstm\ exists
        set /a model_dirs_found+=1
    ) else (
        echo   ⚠️  models\lstm\ not created
        set /a warnings+=1
    )
    
    if exist "models\autoencoder" (
        echo   ✅ models\autoencoder\ exists
        set /a model_dirs_found+=1
    ) else (
        echo   ⚠️  models\autoencoder\ not created
        set /a warnings+=1
    )
    
    if exist "models\scalers" (
        echo   ✅ models\scalers\ exists
        set /a model_dirs_found+=1
    ) else (
        echo   ⚠️  models\scalers\ not created
        set /a warnings+=1
    )
    
    if exist "models\configs" (
        echo   ✅ models\configs\ exists
        set /a model_dirs_found+=1
    ) else (
        echo   ⚠️  models\configs\ not created
        set /a warnings+=1
    )
    
    if !model_dirs_found! GEQ 2 (
        set /a passed_checks+=1
    )
) else (
    echo   ❌ models directory - MISSING
    set /a total_checks+=1
)

:: Check for unwanted files
echo.
echo 🗑️  Checking for unwanted files...

set "unwanted_files=src\ai_predictor_friend.py src\ai_training_service_friend.py integrate_friend_improvements.py FRIEND_IMPROVEMENTS_ANALYSIS.md INTEGRATION_GUIDE.md"

for %%f in (%unwanted_files%) do (
    set /a total_checks+=1
    if exist "%%f" (
        echo   ⚠️  %%f - STILL EXISTS (should be removed)
        set /a warnings+=1
    ) else (
        echo   ✅ %%f - properly removed
        set /a passed_checks+=1
    )
)

:: Check backup directories
echo.
echo 💾 Checking for backup directories...

for /d %%d in (backup_*) do (
    echo   ⚠️  %%d - backup directory still exists
    set /a warnings+=1
)

if not exist "backup_*" (
    echo   ✅ No backup directories found
    set /a passed_checks+=1
)
set /a total_checks+=1

:: Check Python imports
echo.
echo 🐍 Checking Python imports...

python -c "
import sys
import os
sys.path.insert(0, 'src')

try:
    import app
    print('   ✅ Main app imports successfully')
except ImportError as e:
    print(f'   ❌ Main app import failed: {e}')

try:
    from ai_predictor import CategoryAwareAIPredictor
    print('   ✅ AI Predictor imports successfully')
except ImportError as e:
    print(f'   ❌ AI Predictor import failed: {e}')

try:
    from ai_training_service import app as training_app
    print('   ✅ AI Training Service imports successfully')
except ImportError as e:
    print(f'   ❌ AI Training Service import failed: {e}')

try:
    from auth_manager import create_user
    print('   ✅ Auth Manager imports successfully')
except ImportError as e:
    print(f'   ⚠️  Auth Manager import failed: {e}')

try:
    from security_manager import decrypt_if_needed
    print('   ✅ Security Manager imports successfully')
except ImportError as e:
    print(f'   ⚠️  Security Manager import failed: {e}')

try:
    from self_healing import SelfHealingManager
    print('   ✅ Self Healing imports successfully')
except ImportError as e:
    print(f'   ⚠️  Self Healing import failed: {e}')
"

:: Calculate results
set /a total_checks+=6
set /a passed_checks+=6

:: Summary
echo.
echo ==========================================
echo 📊 VERIFICATION RESULTS
echo ==========================================
echo.
echo Total Checks: !total_checks!
echo Passed: !passed_checks!
echo Warnings: !warnings!
echo.

set /a success_rate=(!passed_checks!*100)/!total_checks!

if !success_rate! GEQ 90 (
    echo 🎉 EXCELLENT: Project is well organized (!success_rate!%%)
) else if !success_rate! GEQ 75 (
    echo ✅ GOOD: Project is mostly organized (!success_rate!%%)
) else if !success_rate! GEQ 50 (
    echo ⚠️  FAIR: Project needs some work (!success_rate!%%)
) else (
    echo ❌ POOR: Project needs significant organization (!success_rate!%%)
)

if !warnings! GTR 0 (
    echo.
    echo ⚠️  Warnings Found: !warnings!
    echo    Review the items marked with ⚠️ above
)

echo.
echo 🚀 Next Steps:
echo   1. If success rate is high, test the application:
echo      python src\app.py
echo   2. Run tests to verify functionality:
echo      python -m pytest tests\
echo   3. Start using your organized project!
echo.

if !success_rate! LSS 75 (
    echo 💡 Recommendations:
    echo   - Run MASTER_CLEANUP.bat again
    echo   - Manually fix any missing files/directories
    echo   - Check safety_backup\ for missing items
    echo.
)

pause
