# -*- coding: utf-8 -*-
"""
小地图黄点检测测试脚本
用于测试和调试黄点检测功能
"""

import os
import sys
import cv2
import numpy as np
from datetime import datetime

# 添加父目录到路径（因为测试文件在test子目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PARENT_DIR)

from mir2_auto_bot_v2 import Mir2AutoBotV2, MinimapDetector


def create_test_image_with_yellow_dots(width=150, height=150, num_dots=3):
    """创建带有黄点的测试图像"""
    # 创建深色背景（模拟小地图）
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:] = (30, 30, 40)  # 深蓝灰色背景

    # 添加一些随机噪点（绿色，代表怪物或NPC）
    for _ in range(20):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        cv2.circle(image, (x, y), 2, (0, 150, 0), -1)

    # 添加黄点（代表其他玩家）- 使用精确RGB(255,255,0)，即BGR(0,255,255)
    for i in range(num_dots):
        # 避免在中心位置
        while True:
            x = np.random.randint(20, width - 20)
            y = np.random.randint(20, height - 20)
            # 确保不在中心区域
            if np.sqrt((x - width//2)**2 + (y - height//2)**2) > 30:
                break

        # 绘制精确黄色点 BGR(0, 255, 255) = RGB(255, 255, 0)
        cv2.circle(image, (x, y), 3, (0, 255, 255), -1)

    # 在中心添加一个黄点（代表自己）
    cv2.circle(image, (width//2, height//2), 3, (0, 255, 255), -1)

    return image


def test_detector_basic():
    """基本检测测试"""
    print("=" * 50)
    print("测试1: 基本黄点检测")
    print("=" * 50)

    detector = MinimapDetector()

    # 创建测试图像
    test_image = create_test_image_with_yellow_dots(num_dots=3)

    # 保存测试图像
    debug_dir = os.path.join(PARENT_DIR, 'debug_v2')
    os.makedirs(debug_dir, exist_ok=True)
    cv2.imwrite(os.path.join(debug_dir, 'test_image.jpg'), test_image)

    # 检测黄点
    yellow_dots = detector.detect(test_image, method='hsv')

    print(f"检测到 {len(yellow_dots)} 个黄点")
    for i, (x, y, area) in enumerate(yellow_dots):
        print(f"  黄点 {i+1}: 位置({x}, {y}), 面积={area}")

    # 绘制检测结果
    result_img = test_image.copy()
    for x, y, area in yellow_dots:
        cv2.circle(result_img, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(result_img, str(area), (x + 5, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

    cv2.imwrite(os.path.join(debug_dir, 'test_result.jpg'), result_img)
    print(f"结果已保存到: {debug_dir}")

    return len(yellow_dots) > 0


def test_color_range():
    """测试不同颜色范围的检测"""
    print("\n" + "=" * 50)
    print("测试2: 颜色范围测试")
    print("=" * 50)

    detector = MinimapDetector()

    # 创建测试图像，包含不同颜色
    image = np.zeros((100, 300, 3), dtype=np.uint8)
    image[:] = (30, 30, 40)

    # 添加不同颜色的点
    colors = [
        ((0, 255, 255), "纯黄色"),      # BGR纯黄
        ((30, 230, 230), "浅黄色"),      # 浅黄
        ((0, 200, 200), "暗黄色"),       # 暗黄
        ((0, 255, 100), "黄绿色"),       # 黄绿
        ((100, 255, 255), "淡黄色"),     # 淡黄
        ((0, 150, 0), "绿色"),           # 绿色（不应检测到）
        ((255, 0, 0), "红色"),           # 红色（不应检测到）
        ((0, 0, 255), "蓝色"),           # 蓝色（不应检测到）
    ]

    for i, (color, name) in enumerate(colors):
        x = 30 + i * 35
        y = 50
        cv2.circle(image, (x, y), 8, color, -1)
        cv2.putText(image, name, (x - 15, y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

    # 保存测试图像
    debug_dir = os.path.join(PARENT_DIR, 'debug_v2')
    cv2.imwrite(os.path.join(debug_dir, 'color_test.jpg'), image)

    # 检测
    yellow_dots = detector.detect(image, method='hsv')

    print(f"检测到 {len(yellow_dots)} 个黄点")
    print("预期: 应检测到前5个黄色系点，不应检测到绿、红、蓝")

    return True


def test_minimap_capture():
    """测试小地图截图"""
    print("\n" + "=" * 50)
    print("测试3: 小地图截图测试")
    print("=" * 50)

    bot = Mir2AutoBotV2()

    # 查找游戏窗口
    if not bot.find_game_window():
        print("未找到游戏窗口，跳过此测试")
        print("请确保游戏已启动")
        return False

    # 截取小地图
    minimap = bot.capture_minimap()

    if minimap is not None:
        debug_dir = os.path.join(PARENT_DIR, 'debug_v2')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(debug_dir, f'minimap_capture_{timestamp}.jpg')
        cv2.imwrite(filepath, minimap)
        print(f"小地图已保存: {filepath}")
        print(f"小地图尺寸: {minimap.shape[1]}x{minimap.shape[0]}")

        # 检测黄点
        has_players, yellow_dots = bot.detect_yellow_dots(minimap)
        print(f"检测到 {len(yellow_dots)} 个黄点")
        print(f"检测到其他玩家: {has_players}")

        return True
    else:
        print("截取小地图失败")
        return False


def test_full_screen_capture():
    """测试全屏截图并标记小地图区域"""
    print("\n" + "=" * 50)
    print("测试4: 全屏截图测试（标记小地图区域）")
    print("=" * 50)

    bot = Mir2AutoBotV2()

    if not bot.find_game_window():
        print("未找到游戏窗口，跳过此测试")
        return False

    # 截取完整客户区
    full_screen = bot.capture_full_screen()

    if full_screen is not None:
        debug_dir = os.path.join(PARENT_DIR, 'debug_v2')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 绘制小地图区域
        if bot.minimap_region:
            x, y, w, h = bot.minimap_region
            cv2.rectangle(full_screen, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(full_screen, "Minimap", (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        filepath = os.path.join(debug_dir, f'fullscreen_{timestamp}.jpg')
        cv2.imwrite(filepath, full_screen)
        print(f"全屏截图已保存: {filepath}")
        print(f"小地图区域: {bot.minimap_region}")

        return True
    else:
        print("截取全屏失败")
        return False


def interactive_adjust_minimap():
    """交互式调整小地图位置"""
    print("\n" + "=" * 50)
    print("测试5: 交互式小地图位置调整")
    print("=" * 50)
    print("此功能帮助您找到正确的小地图位置")
    print("请按照提示操作...")
    print()

    bot = Mir2AutoBotV2()

    if not bot.find_game_window():
        print("未找到游戏窗口")
        return False

    # 读取当前配置
    print("当前小地图配置:")
    print(f"  offset_x: {bot.config.get('Minimap', 'offset_x')}")
    print(f"  offset_y: {bot.config.get('Minimap', 'offset_y')}")
    print(f"  width: {bot.config.get('Minimap', 'width')}")
    print(f"  height: {bot.config.get('Minimap', 'height')}")
    print(f"  from_right: {bot.config.get('Minimap', 'from_right')}")
    print()

    # 截取全屏
    full_screen = bot.capture_full_screen()

    if full_screen is None:
        print("截图失败")
        return False

    debug_dir = os.path.join(PARENT_DIR, 'debug_v2')

    # 尝试不同的位置
    test_configs = [
        {"offset_x": 5, "offset_y": 5, "width": 150, "height": 150, "from_right": True},
        {"offset_x": 10, "offset_y": 10, "width": 150, "height": 150, "from_right": True},
        {"offset_x": 15, "offset_y": 5, "width": 160, "height": 160, "from_right": True},
        {"offset_x": 5, "offset_y": 30, "width": 150, "height": 150, "from_right": True},
    ]

    for i, cfg in enumerate(test_configs):
        test_img = full_screen.copy()

        client_width = bot.client_rect[2] - bot.client_rect[0]

        if cfg["from_right"]:
            x = client_width - cfg["width"] - cfg["offset_x"]
        else:
            x = cfg["offset_x"]

        y = cfg["offset_y"]
        w = cfg["width"]
        h = cfg["height"]

        # 绘制矩形
        cv2.rectangle(test_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(test_img, f"Config {i+1}: {cfg}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        filepath = os.path.join(debug_dir, f'minimap_adjust_{i+1}.jpg')
        cv2.imwrite(filepath, test_img)
        print(f"配置 {i+1} 已保存: {filepath}")
        print(f"  参数: {cfg}")

    print()
    print(f"请查看 {debug_dir} 目录下的图片，选择最合适的配置")
    print("然后修改 bot_config_v2.ini 中的 [Minimap] 部分")

    return True


def main():
    """主测试函数"""
    print("=" * 60)
    print("小地图黄点检测测试工具")
    print("=" * 60)
    print()

    # 创建调试目录
    debug_dir = os.path.join(PARENT_DIR, 'debug_v2')
    os.makedirs(debug_dir, exist_ok=True)

    while True:
        print("\n请选择测试:")
        print("1. 基本黄点检测测试（使用合成图像）")
        print("2. 颜色范围测试")
        print("3. 小地图截图测试（需要游戏运行）")
        print("4. 全屏截图测试（标记小地图区域）")
        print("5. 交互式调整小地图位置")
        print("6. 运行所有测试")
        print("0. 退出")
        print()

        choice = input("请输入选项 (0-6): ").strip()

        if choice == '0':
            print("退出测试")
            break
        elif choice == '1':
            test_detector_basic()
        elif choice == '2':
            test_color_range()
        elif choice == '3':
            test_minimap_capture()
        elif choice == '4':
            test_full_screen_capture()
        elif choice == '5':
            interactive_adjust_minimap()
        elif choice == '6':
            test_detector_basic()
            test_color_range()
            test_minimap_capture()
            test_full_screen_capture()
        else:
            print("无效选项，请重新选择")

        print()
        input("按回车继续...")


if __name__ == '__main__':
    main()
