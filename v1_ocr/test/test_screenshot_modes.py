# -*- coding: utf-8 -*-
"""
测试两种截图模式
"""

import sys
import os

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mir2_bot_gui import Mir2AutoBot

def test_screenshot_modes():
    """测试两种截图模式"""
    print("=" * 60)
    print("测试两种截图模式")
    print("=" * 60)
    print()

    # 测试Win32模式
    print("1. 测试 Win32 API 截图模式")
    print("-" * 60)
    bot_win32 = Mir2AutoBot(screenshot_mode='win32')

    if bot_win32.find_game_window():
        print("✓ 找到游戏窗口")
        image_win32 = bot_win32.capture_game_screen()

        if image_win32 is not None:
            print(f"✓ Win32截图成功！图像大小: {image_win32.shape}")

            # 保存截图
            import cv2
            debug_dir = os.path.join(os.path.dirname(__file__), 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            win32_path = os.path.join(debug_dir, 'test_win32_mode.jpg')
            cv2.imwrite(win32_path, image_win32)
            print(f"✓ 已保存: {win32_path}")
        else:
            print("✗ Win32截图失败")
    else:
        print("✗ 无法找到游戏窗口")

    print()

    # 测试PyAutoGUI模式
    print("2. 测试 PyAutoGUI 截图模式")
    print("-" * 60)
    print("注意: 此模式需要游戏窗口在最前端")
    bot_pyautogui = Mir2AutoBot(screenshot_mode='pyautogui')

    if bot_pyautogui.find_game_window():
        print("✓ 找到游戏窗口")
        image_pyautogui = bot_pyautogui.capture_game_screen()

        if image_pyautogui is not None:
            print(f"✓ PyAutoGUI截图成功！图像大小: {image_pyautogui.shape}")

            # 保存截图
            import cv2
            debug_dir = os.path.join(os.path.dirname(__file__), 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            pyautogui_path = os.path.join(debug_dir, 'test_pyautogui_mode.jpg')
            cv2.imwrite(pyautogui_path, image_pyautogui)
            print(f"✓ 已保存: {pyautogui_path}")
        else:
            print("✗ PyAutoGUI截图失败")
    else:
        print("✗ 无法找到游戏窗口")

    print()
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
    print()
    print("请检查 debug 目录下的截图文件:")
    print("  - test_win32_mode.jpg (Win32 API模式)")
    print("  - test_pyautogui_mode.jpg (PyAutoGUI模式)")
    print()
    print("对比两种模式的截图效果:")
    print("  - Win32模式: 后台截图，窗口可被遮挡，但可能有黑边")
    print("  - PyAutoGUI模式: 前台截图，窗口需在最前，无黑边")

if __name__ == '__main__':
    test_screenshot_modes()
