@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Legend of Mir 2 Auto Bot V2 - Detection Test Tool
echo ========================================
echo.
echo This tool is for testing and debugging yellow dot detection
echo.
echo Test options:
echo   1. Basic yellow dot detection test (synthetic image)
echo   2. Color range test
echo   3. Minimap screenshot test (requires game running)
echo   4. Full screen screenshot test (mark minimap area)
echo   5. Interactive minimap position adjustment
echo.
echo For first time use, run tests 1-5 in order
echo.
pause

python test\test_yellow_dot_detection.py

echo.
pause
