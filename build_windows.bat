@echo off
REM Build script for Ethiopian ID Generator (Windows)

echo ==================================
echo Ethiopian ID Generator - Build
echo ==================================

REM Check if Tesseract is installed
where tesseract >nul 2>&1
if errorlevel 1 (
    echo ERROR: Tesseract is not installed or not in PATH!
    echo.
    echo Please install Tesseract OCR from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Make sure to:
    echo 1. Install to C:\Program Files\Tesseract-OCR
    echo 2. Select "Additional language data" during installation
    echo 3. Choose "Amharic" language pack
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
pyinstaller build_app_windows.spec

REM Check if build was successful
if exist "dist\EthiopianIDGenerator\EthiopianIDGenerator.exe" (
    echo.
    echo ==================================
    echo Build successful!
    echo ==================================
    echo Executable created: dist\EthiopianIDGenerator\EthiopianIDGenerator.exe
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
