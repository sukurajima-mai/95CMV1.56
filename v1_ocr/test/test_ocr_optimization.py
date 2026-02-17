# -*- coding: utf-8 -*-
"""
测试OCR识别优化效果
"""

import sys
import os

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mir2_bot_gui import Mir2AutoBot
import cv2

def test_ocr_optimization():
    """测试OCR识别优化效果"""
    print("=" * 60)
    print("测试OCR识别优化效果")
    print("=" * 60)
    print()

    # 创建机器人实例
    bot = Mir2AutoBot(screenshot_mode='win32')

    # 查找窗口
    if not bot.find_game_window():
        print("✗ 无法找到游戏窗口")
        return

    print("✓ 找到游戏窗口")

    # 截图
    image = bot.capture_game_screen()

    if image is None:
        print("✗ 截图失败")
        return

    print(f"✓ 截图成功！图像大小: {image.shape}")
    print()

    # 启用调试模式
    bot.config.set('Detection', 'debug', 'true')

    # 执行OCR检测
    print("正在执行OCR检测...")
    print("-" * 60)

    target_rects = bot.detect_players_opencv(image)

    print()
    print("=" * 60)
    print("检测结果")
    print("=" * 60)
    print(f"检测到的目标文字数量: {len(target_rects)}")

    if target_rects:
        print("✓ 检测到目标文字！")
        for i, (x, y, w, h) in enumerate(target_rects):
            print(f"  目标 {i+1}: 位置 ({x}, {y}), 大小 ({w}x{h})")
    else:
        print("✗ 未检测到目标文字")

    print()
    print("调试图片已保存到 debug 目录:")
    print("  - 00_full_screen_*.jpg (完整截图)")
    print("  - 01_detection_region_*.jpg (检测区域)")
    print("  - 02_preprocessed_*.jpg (预处理后的图像)")
    print("  - 03_detection_result_*.jpg (检测结果)")
    print()
    print("说明:")
    print("  - 蓝色框: 所有识别到的文字")
    print("  - 绿色框: 匹配到的目标文字")
    print("  - 黄色框: 检测范围")

if __name__ == '__main__':
    test_ocr_optimization()
