@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Legend of Mir 2 Auto Bot V2 - Multi-Window
echo ========================================
echo.
echo This version monitors multiple game windows
echo Each window detects and teleports independently
echo.
echo Starting...
echo.

python mir2_multi_window_bot.py

if errorlevel 1 (
    echo.
    echo Failed to start! Please check:
    echo 1. Python is installed
    echo 2. Dependencies are installed
    echo.
    pause
)
