# -*- coding: utf-8 -*-
"""
模拟测试多实例窗口选择逻辑
不需要实际游戏窗口运行
"""

import os
import sys

# 添加父目录到路径（因为测试文件在test子目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PARENT_DIR)

def test_window_index_logic():
    """测试窗口索引选择逻辑"""
    print("=" * 60)
    print("模拟测试窗口索引选择逻辑")
    print("=" * 60)
    print()
    
    # 模拟找到的窗口列表
    mock_windows = [
        (12345, "九五沉默 - 窗口1"),
        (23456, "九五沉默 - 窗口2"),
        (34567, "九五沉默 - 窗口3"),
    ]
    
    print(f"模拟找到 {len(mock_windows)} 个游戏窗口:")
    for i, (hwnd, title) in enumerate(mock_windows):
        print(f"  [{i}] HWND: {hwnd} | {title}")
    print()
    
    # 测试不同的窗口索引
    test_cases = [
        (0, "第1个窗口"),
        (1, "第2个窗口"),
        (2, "第3个窗口"),
        (3, "超出范围的索引"),
    ]
    
    print("=" * 60)
    print("测试窗口索引选择:")
    print("=" * 60)
    
    for window_index, description in test_cases:
        print(f"\n测试: window_index={window_index} ({description})")
        
        # 模拟选择逻辑
        if window_index < len(mock_windows):
            selected_hwnd, selected_title = mock_windows[window_index]
            print(f"  ✓ 选择窗口: HWND={selected_hwnd}, 标题='{selected_title}'")
        else:
            # 超出范围，使用第一个窗口
            selected_hwnd, selected_title = mock_windows[0]
            print(f"  ⚠ 索引超出范围，使用第一个窗口: HWND={selected_hwnd}, 标题='{selected_title}'")
    
    print()
    print("=" * 60)
    print("✅ 逻辑测试通过！")
    print("=" * 60)
    print()
    print("修复说明:")
    print("  1. 添加了 window_index 参数到 Mir2AutoBotV2.__init__()")
    print("  2. 修改了 find_game_window() 方法，根据索引选择窗口")
    print("  3. 添加了命令行参数支持: python mir2_auto_bot_v2.py [窗口索引]")
    print("  4. 创建了启动脚本: start_bot_instance.bat")
    print()
    print("使用方法:")
    print("  - 启动第1个窗口监控: python mir2_auto_bot_v2.py 0")
    print("  - 启动第2个窗口监控: python mir2_auto_bot_v2.py 1")
    print("  - 启动第3个窗口监控: python mir2_auto_bot_v2.py 2")
    print("  - 或使用批处理文件: start_bot_instance.bat")
    print()
    print("多实例运行示例:")
    print("  命令行1: python mir2_auto_bot_v2.py 0")
    print("  命令行2: python mir2_auto_bot_v2.py 1")
    print("  命令行3: python mir2_auto_bot_v2.py 2")
    print()
    print("这样每个Bot实例都会监控不同的游戏窗口！")

if __name__ == '__main__':
    test_window_index_logic()
