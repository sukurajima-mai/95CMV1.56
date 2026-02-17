@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Legend of Mir 2 Auto Bot V2 - Multi-Window GUI
echo ========================================
echo.
echo Starting Multi-Window GUI...
echo.

python mir2_multi_window_gui.py

if errorlevel 1 (
    echo.
    echo Failed to start! Please check:
    echo 1. Python is installed
    echo 2. Dependencies are installed
    echo.
    pause
)
