@echo off
REM 运行单元测试脚本
REM 使用方法: run_tests.bat [选项]
REM 选项:
REM   -v, --verbose    详细输出
REM   -q, --quiet      简洁输出
REM   --cov            生成覆盖率报告
REM   --html           生成HTML报告

echo ========================================
echo 传奇2自动挂机脚本 - 单元测试
echo ========================================
echo.

REM 检查pytest是否安装
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo [错误] pytest未安装
    echo 正在安装pytest...
    pip install pytest pytest-cov pytest-html
    echo.
)

REM 运行测试
echo 开始运行测试...
echo.

if "%1"=="" (
    REM 默认运行所有测试
    python -m pytest tests/ -v --tb=short
) else (
    REM 使用用户提供的参数
    python -m pytest tests/ %*
)

echo.
echo ========================================
echo 测试完成
echo ========================================
pause
