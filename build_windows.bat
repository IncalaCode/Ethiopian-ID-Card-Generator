@echo off
REM Build script for Ethiopian ID Generator (Windows)

echo ==================================
echo Ethiopian ID Generator - Build
echo ==================================

REM Check if EasyOCR is installed
python -c "import easyocr" >nul 2>&1
if errorlevel 1 (
    echo ERROR: EasyOCR is not installed!
    echo.
    echo Installing EasyOCR...
    pip install easyocr
    echo.
    echo Please run the app once to download models before building:
    echo   python web_server.py
    echo.
    pause
    exit /b 1
)

REM Check if EasyOCR models are downloaded
python -c "import os; exit(0 if os.path.exists(os.path.expanduser('~/.EasyOCR/model')) else 1)" >nul 2>&1
if errorlevel 1 (
    echo WARNING: EasyOCR models not downloaded yet!
    echo.
    echo Please run the app once to download models:
    echo   python web_server.py
    echo.
    echo This will download ~100MB of models.
    echo.
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build the application
echo Building application...
echo This will bundle EasyOCR models (~100MB)
pyinstaller build_app_windows.spec

REM Check if build was successful
if exist "dist\EthiopianIDGenerator\EthiopianIDGenerator.exe" (
    echo.
    echo ==================================
    echo Build successful!
    echo ==================================
    echo Executable created: dist\EthiopianIDGenerator\EthiopianIDGenerator.exe
    echo.
    echo The executable includes:
    echo   - EasyOCR models (no installation needed)
    echo   - All dependencies
    echo.
    echo To run the app:
    echo   cd dist\EthiopianIDGenerator
    echo   EthiopianIDGenerator.exe
    echo.
    echo To distribute:
    echo   Zip the entire folder: dist\EthiopianIDGenerator
    echo.
) else (
    echo.
    echo Build failed! Check errors above.
    exit /b 1
)

pause
