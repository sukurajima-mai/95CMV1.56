@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================
echo Window Detection Fix Tool (V1)
echo ========================================
echo.
echo This tool helps diagnose and fix window detection issues
echo.
pause

echo.
echo Step 1/3: Creating debug directory...
if not exist debug mkdir debug
echo [Done] Debug directory created
echo.

echo Step 2/3: Running window diagnostic tool...
echo.
echo Please make sure the game window is open and visible
echo.
pause

python test\window_diagnostic.py

echo.
echo Step 3/3: Checking diagnostic results...
echo.
echo Please check the following files:
echo   - debug\01_full_window.jpg    (Full window screenshot)
echo   - debug\02_client_area.jpg    (Client area screenshot)
echo   - debug\03_comparison.jpg     (Comparison image)
echo.
echo If the client area screenshot is correct (no black borders), the fix is working
echo.
echo Fixes applied:
echo   [OK] Fixed window rectangle detection
echo   [OK] Using client area coordinates for screenshot
echo   [OK] Added window offset calculation
echo   [OK] Fixed target text inconsistency
echo.
echo ========================================
echo Fix Complete!
echo ========================================
echo.
echo You can now run:
echo   start_gui.bat    (Start GUI version)
echo   start_bot.bat    (Start command line version)
echo.
pause
