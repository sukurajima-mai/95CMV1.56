@echo off
chcp 65001 >nul
echo ========================================
echo 传奇2自动挂机脚本 V2 - 多实例启动器
echo ========================================
echo.

set /p window_index="请输入窗口索引 (0=第1个窗口, 1=第2个窗口...): "

echo.
echo 正在启动Bot实例，监控第 %window_index% 个窗口...
echo 按 F10 停止挂机
echo.

python mir2_auto_bot_v2.py %window_index%

pause
