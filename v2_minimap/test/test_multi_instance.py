# -*- coding: utf-8 -*-
"""
测试多实例窗口选择功能
验证每个bot实例能够选择不同的窗口
"""

import sys
import os

# 添加父目录到路径（因为测试文件在test子目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PARENT_DIR)

from mir2_auto_bot_v2 import Mir2AutoBotV2
import win32gui

def test_window_selection():
    """测试窗口选择功能"""
    print("=" * 60)
    print("测试多实例窗口选择功能")
    print("=" * 60)
    print()
    
    # 创建多个bot实例
    instances = []
    for i in range(3):
        print(f"\n创建Bot实例 {i}...")
        bot = Mir2AutoBotV2(window_index=i)
        
        # 查找窗口
        if bot.find_game_window():
            print(f"  ✓ 窗口句柄: {bot.hwnd}")
            print(f"  ✓ 窗口标题: {bot.window_title}")
            print(f"  ✓ 客户区大小: {bot.client_rect[2]-bot.client_rect[0]}x{bot.client_rect[3]-bot.client_rect[1]}")
            instances.append(bot)
        else:
            print(f"  ✗ 未找到窗口")
            break
    
    print()
    print("=" * 60)
    print("测试结果:")
    print("=" * 60)
    
    if len(instances) == 0:
        print("❌ 未找到任何游戏窗口")
        return False
    
    # 检查每个实例是否选择了不同的窗口
    hwnds = [bot.hwnd for bot in instances]
    unique_hwnds = set(hwnds)
    
    print(f"找到 {len(instances)} 个Bot实例")
    print(f"窗口句柄列表: {hwnds}")
    print(f"唯一窗口句柄: {list(unique_hwnds)}")
    
    if len(unique_hwnds) == len(instances):
        print()
        print("✅ 测试通过！每个Bot实例选择了不同的窗口")
        return True
    else:
        print()
        print("❌ 测试失败！存在多个Bot实例选择了相同的窗口")
        return False

def list_all_windows():
    """列出所有游戏窗口"""
    print()
    print("=" * 60)
    print("所有游戏窗口列表:")
    print("=" * 60)
    
    possible_titles = ['九五沉默', 'Legend of Mir2', '传奇']
    
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            for possible_title in possible_titles:
                if possible_title.lower() in title.lower():
                    try:
                        client_rect = win32gui.GetClientRect(hwnd)
                        client_width = client_rect[2] - client_rect[0]
                        client_height = client_rect[3] - client_rect[1]
                        if client_width > 0 and client_height > 0:
                            windows.append((hwnd, title, client_width, client_height))
                    except:
                        pass
        return True
    
    windows = []
    win32gui.EnumWindows(callback, windows)
    
    if windows:
        for i, (hwnd, title, width, height) in enumerate(windows):
            print(f"  [{i}] HWND: {hwnd} | {title} | {width}x{height}")
    else:
        print("  未找到任何游戏窗口")
    
    return windows

if __name__ == '__main__':
    # 先列出所有窗口
    windows = list_all_windows()
    
    if not windows:
        print("\n请先启动游戏窗口！")
        sys.exit(1)
    
    # 测试窗口选择
    success = test_window_selection()
    
    if success:
        print("\n" + "=" * 60)
        print("使用方法:")
        print("=" * 60)
        print("启动第1个窗口监控: python mir2_auto_bot_v2.py 0")
        print("启动第2个窗口监控: python mir2_auto_bot_v2.py 1")
        print("启动第3个窗口监控: python mir2_auto_bot_v2.py 2")
        print("或使用批处理文件: start_bot_instance.bat")
        sys.exit(0)
    else:
        sys.exit(1)
