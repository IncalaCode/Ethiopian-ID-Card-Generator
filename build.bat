@echo off
REM Build script for Ethiopian ID Generator (Windows)

echo ==================================
echo Ethiopian ID Generator - Build
echo ==================================

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
pyinstaller build_app.spec

REM Check if build was successful
if exist "dist\EthiopianIDGenerator.exe" (
    echo.
    echo ==================================
    echo Build successful!
    echo ==================================
    echo Single executable created: dist\EthiopianIDGenerator.exe
    echo.
    echo To run the app:
    echo   dist\EthiopianIDGenerator.exe
    echo.
    echo To distribute:
    echo   Just copy the single file: dist\EthiopianIDGenerator.exe
    echo.
) else (
    echo.
    echo Build failed! Check errors above.
    exit /b 1
)

pause
