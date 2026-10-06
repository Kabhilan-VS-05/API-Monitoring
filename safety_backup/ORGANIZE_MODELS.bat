@echo off
echo ========================================
echo 📁 Model Files Organization Script
echo ========================================
echo.
echo This script will organize model files into proper directories
echo for better maintainability and structure.
echo.
pause

echo 🔄 Starting model organization...
echo.

:: Create organized directories
echo [1/4] Creating organized directory structure...
if not exist "models\lstm" (
    mkdir "models\lstm"
    echo   Created: models\lstm
)
if not exist "models\autoencoder" (
    mkdir "models\autoencoder"
    echo   Created: models\autoencoder
)
if not exist "models\scalers" (
    mkdir "models\scalers"
    echo   Created: models\scalers
)
if not exist "models\configs" (
    mkdir "models\configs"
    echo   Created: models\configs
)

:: Move LSTM model files
echo [2/4] Moving LSTM model files...
move "models\lstm_*.h5" "models\lstm\" 2>nul && echo   Moved LSTM models to models\lstm\

:: Move Autoencoder model files
echo [3/4] Moving Autoencoder model files...
move "models\autoencoder_*.h5" "models\autoencoder\" 2>nul && echo   Moved Autoencoder models to models\autoencoder\

:: Move Scaler files
echo [4/4] Moving scaler and config files...
move "models\scaler_*.pkl" "models\scalers\" 2>nul && echo   Moved scaler files to models\scalers\
move "models\config_*.json" "models\configs\" 2>nul && echo   Moved config files to models\configs\

echo.
echo ✅ Model files organized successfully!
echo.
echo 📊 Organization Summary:
echo   - LSTM models: models\lstm\
echo   - Autoencoder models: models\autoencoder\
echo   - Scalers: models\scalers\
echo   - Configs: models\configs\
echo.
echo 🚀 Next step: Run UPDATE_APPLICATION.bat to update main application
echo.
pause
