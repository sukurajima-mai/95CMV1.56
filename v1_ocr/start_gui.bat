@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Legend of Mir 2 Auto Bot V1 - GUI Version
echo ========================================
echo.
echo Starting GUI...
echo.

python mir2_bot_gui.py

if errorlevel 1 (
    echo.
    echo Failed to start! Please check:
    echo 1. Python is installed
    echo 2. Dependencies are installed (run install_deps.bat)
    echo 3. Tesseract OCR is installed
    echo.
    pause
)
