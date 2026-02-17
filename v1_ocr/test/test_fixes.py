# -*- coding: utf-8 -*-
"""
测试修复功能
"""

import sys
import os

# 添加script目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mir2_bot_gui import Mir2AutoBot
import win32gui
import numpy as np

def test_initialization():
    """测试初始化"""
    print("=" * 50)
    print("测试1: 初始化")
    print("=" * 50)
    
    bot = Mir2AutoBot()
    print(f"✓ 初始化成功")
    print(f"✓ 目标文字: {bot.target_text}")
    print()
    return bot

def test_window_finding(bot):
    """测试窗口查找"""
    print("=" * 50)
    print("测试2: 窗口查找")
    print("=" * 50)
    
    result = bot.find_game_window()
    
    if result:
        print(f"✓ 找到窗口: {win32gui.GetWindowText(bot.hwnd)}")
        print(f"✓ 窗口位置: {bot.window_rect}")
        print(f"✓ 客户区大小: {bot.client_rect}")
        
        client_width = bot.client_rect[2] - bot.client_rect[0]
        client_height = bot.client_rect[3] - bot.client_rect[1]
        
        print(f"✓ 客户区宽度: {client_width}")
        print(f"✓ 客户区高度: {client_height}")
        
        if client_width > 0 and client_height > 0:
            print("✓ 窗口有效，可以截图")
            return True
        else:
            print("✗ 窗口无效，客户区为0")
            return False
    else:
        print("✗ 未找到游戏窗口")
        print("提示: 请确保游戏窗口已打开且未最小化")
        return False

def test_screenshot(bot):
    """测试截图"""
    print("=" * 50)
    print("测试3: 截图功能")
    print("=" * 50)
    
    if not bot.hwnd:
        print("✗ 没有有效的窗口句柄，跳过截图测试")
        return False
    
    image = bot.capture_game_screen()
    
    if image is not None:
        print(f"✓ 截图成功！")
        print(f"✓ 图像大小: {image.shape}")
        print(f"✓ 图像类型: {type(image)}")
        print(f"✓ 图像数据类型: {image.dtype}")
        
        # 保存测试截图
        import cv2
        test_dir = os.path.join(os.path.dirname(__file__), 'debug')
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, 'test_screenshot.jpg')
        cv2.imwrite(test_file, image)
        print(f"✓ 测试截图已保存: {test_file}")
        
        return True
    else:
        print("✗ 截图失败")
        return False

def main():
    """主测试函数"""
    print("\n")
    print("=" * 50)
    print("开始测试修复功能")
    print("=" * 50)
    print()
    
    # 测试1: 初始化
    bot = test_initialization()
    
    # 测试2: 窗口查找
    window_found = test_window_finding(bot)
    
    # 测试3: 截图
    if window_found:
        screenshot_ok = test_screenshot(bot)
    else:
        print("\n跳过截图测试（未找到有效窗口）")
        screenshot_ok = False
    
    # 总结
    print("\n")
    print("=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"初始化: ✓")
    print(f"窗口查找: {'✓' if window_found else '✗'}")
    print(f"截图功能: {'✓' if screenshot_ok else '✗ (需要有效窗口)'}")
    print("=" * 50)
    
    if window_found and screenshot_ok:
        print("\n✓ 所有测试通过！")
    elif window_found:
        print("\n⚠ 窗口查找成功，但截图失败")
    else:
        print("\n⚠ 请打开游戏窗口后重新测试")

if __name__ == '__main__':
    main()
