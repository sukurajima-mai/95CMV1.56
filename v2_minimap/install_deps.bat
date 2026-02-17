@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Legend of Mir 2 Auto Bot V2 - Install Dependencies
echo ========================================
echo.

echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.x
    pause
    exit /b 1
)

echo [Success] Python environment OK
echo.

echo Installing dependencies...
echo This may take a few minutes, please wait...
echo.

pip install -r ..\requirements.txt

if errorlevel 1 (
    echo.
    echo [Error] Failed to install dependencies
    echo.
    echo Possible solutions:
    echo 1. Check network connection
    echo 2. Update pip: python -m pip install --upgrade pip
    echo 3. Use mirror: pip install -r ..\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    pause
    exit /b 1
)

echo.
echo ========================================
echo [Success] Dependencies installed!
echo ========================================
echo.
echo Run test tool:
echo   test_detection.bat
echo.
echo Run the bot:
echo   start_bot.bat
echo.
pause
