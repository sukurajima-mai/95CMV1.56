@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Legend of Mir 2 Auto Bot V2 - Minimap Yellow Dot Detection
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
python -c "import keyboard, win32gui, cv2, numpy" >nul 2>&1
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
echo Features:
echo   - Detect yellow dots in minimap (other players)
echo   - Auto teleport when other players detected
echo.
echo Tips:
echo   - F10: Stop bot
echo   - Ctrl+C: Force exit
echo.
echo First time? Run test_detection.bat to adjust
echo minimap position and color range
echo ========================================
echo.

python mir2_auto_bot_v2.py

echo.
echo Bot script stopped
pause
