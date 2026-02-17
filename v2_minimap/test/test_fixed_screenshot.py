# -*- coding: utf-8 -*-
"""
测试修复后的截屏功能
"""

import sys
import os
import cv2
from datetime import datetime

# 添加父目录到路径（因为测试文件在test子目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PARENT_DIR)

from mir2_auto_bot_v2 import Mir2AutoBotV2

def main():
    print("=" * 60)
    print("测试修复后的截屏功能")
    print("=" * 60)
    print()

    # 创建bot实例
    bot = Mir2AutoBotV2()

    # 查找游戏窗口
    print("1. 查找游戏窗口...")
    if not bot.find_game_window():
        print("❌ 未找到游戏窗口")
        print("请确保游戏已启动")
        return

    print(f"✅ 找到游戏窗口: {bot.window_title}")
    print(f"   窗口句柄: {bot.hwnd}")
    print(f"   客户区大小: {bot.client_rect[2]}x{bot.client_rect[3]}")
    print()

    # 截取小地图
    print("2. 截取小地图...")
    minimap = bot.capture_minimap()

    if minimap is None:
        print("❌ 截取小地图失败")
        return

    print(f"✅ 小地图截取成功")
    print(f"   图像大小: {minimap.shape[1]}x{minimap.shape[0]}")
    print(f"   平均亮度: {minimap.mean():.2f}")
    print(f"   最大像素值: {minimap.max()}")
    print()

    # 保存小地图
    debug_dir = os.path.join(PARENT_DIR, 'debug_test')
    os.makedirs(debug_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(debug_dir, f'minimap_fixed_{timestamp}.jpg')
    cv2.imwrite(filepath, minimap)
    print(f"✅ 小地图已保存: {filepath}")
    print()

    # 检测黄点
    print("3. 检测黄点...")
    has_players, yellow_dots = bot.detect_yellow_dots(minimap)

    if has_players:
        print(f"✅ 检测到 {len(yellow_dots)} 个黄点（其他玩家）")
        for i, (x, y, area) in enumerate(yellow_dots, 1):
            print(f"   黄点 {i}: 位置({x}, {y}), 面积={area}")
    else:
        print("ℹ️  未检测到黄点（没有其他玩家）")
    print()

    # 绘制检测结果
    if yellow_dots:
        debug_img = minimap.copy()
        for x, y, area in yellow_dots:
            cv2.circle(debug_img, (x, y), 5, (0, 0, 255), -1)
            cv2.putText(debug_img, str(area), (x + 5, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        detection_filepath = os.path.join(debug_dir, f'detection_fixed_{timestamp}.jpg')
        cv2.imwrite(detection_filepath, debug_img)
        print(f"✅ 检测结果已保存: {detection_filepath}")
    print()

    print("=" * 60)
    print("测试完成！")
    print()
    print("结果分析:")
    if minimap.mean() > 50:
        print("✅ 截屏亮度正常（修复成功）")
    else:
        print("⚠️  截屏仍然较暗，可能需要进一步调整")
    print("=" * 60)

if __name__ == '__main__':
    main()
