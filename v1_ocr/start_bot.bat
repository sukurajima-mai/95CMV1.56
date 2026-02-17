@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Legend of Mir 2 Auto Bot V1 - OCR Version
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python first
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Checking dependencies...
python -c "import keyboard, mouse, win32gui" >nul 2>&1
if errorlevel 1 (
    echo [Info] Installing dependencies...
    pip install -r ..\requirements.txt
    if errorlevel 1 (
        echo [Error] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [Success] Dependencies installed
) else (
    echo [Success] Dependencies already installed
)
echo.

echo [2/2] Starting bot script...
echo.
echo ========================================
echo Tips:
echo   - F10: Stop bot
echo   - Ctrl+C: Force exit
echo ========================================
echo.

python mir2_auto_bot.py

echo.
echo Bot script stopped
pause
