# -*- coding: utf-8 -*-
"""
工具函数单元测试
测试各种辅助功能
"""

import pytest
import numpy as np
import cv2
import time
import sys
import os

# 添加父目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PARENT_DIR)


class TestImageUtils:
    """图像处理工具测试类"""

    def test_image_creation(self):
        """测试图像创建"""
        # 创建测试图像
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        assert image.shape == (100, 100, 3), "图像尺寸应该为100x100x3"
        assert image.dtype == np.uint8, "图像类型应该为uint8"

    def test_color_conversion(self):
        """测试颜色转换"""
        # 创建BGR图像
        bgr_image = np.zeros((10, 10, 3), dtype=np.uint8)
        bgr_image[:] = (0, 255, 255)  # BGR黄色

        # 转换为RGB
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

        # 验证RGB值
        assert rgb_image[0, 0, 0] == 255, "R通道应为255"
        assert rgb_image[0, 0, 1] == 255, "G通道应为255"
        assert rgb_image[0, 0, 2] == 0, "B通道应为0"

    def test_image_mask(self):
        """测试图像掩码"""
        # 创建测试图像
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[:] = (0, 255, 255)  # 全黄

        # 转换为RGB
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 创建掩码
        lower = np.array([250, 250, 0])
        upper = np.array([255, 255, 5])
        mask = cv2.inRange(rgb, lower, upper)

        # 验证掩码
        assert mask.shape == (100, 100), "掩码尺寸应该为100x100"
        assert np.all(mask == 255), "所有像素应该匹配"

    def test_contour_detection(self):
        """测试轮廓检测"""
        # 创建带圆形的图像
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.circle(image, (50, 50), 10, (255, 255, 255), -1)

        # 转换为灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 检测轮廓
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 验证
        assert len(contours) == 1, "应该检测到1个轮廓"

    def test_contour_area(self):
        """测试轮廓面积计算"""
        # 创建带圆形的图像
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.circle(image, (50, 50), 10, (255, 255, 255), -1)

        # 转换为灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 检测轮廓
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 计算面积
        area = cv2.contourArea(contours[0])

        # 验证面积（大约πr² = 314）
        assert 280 < area < 350, f"圆形面积应约为314，实际为{area}"

    def test_contour_moments(self):
        """测试轮廓矩计算"""
        # 创建带圆形的图像
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.circle(image, (50, 50), 10, (255, 255, 255), -1)

        # 转换为灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 检测轮廓
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 计算矩
        M = cv2.moments(contours[0])

        # 计算质心
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # 验证质心位置（应该在圆心附近）
            assert abs(cx - 50) < 2, f"质心x坐标应为50左右，实际为{cx}"
            assert abs(cy - 50) < 2, f"质心y坐标应为50左右，实际为{cy}"


class TestTimeUtils:
    """时间工具测试类"""

    def test_cooldown_calculation(self):
        """测试冷却时间计算"""
        last_time = time.time() - 5.0  # 5秒前
        cooldown = 4.0

        # 检查是否已过冷却时间
        current_time = time.time()
        elapsed = current_time - last_time

        assert elapsed >= cooldown, f"已过{elapsed}秒，应该超过冷却时间{cooldown}秒"

    def test_time_interval(self):
        """测试时间间隔"""
        start = time.time()
        time.sleep(0.1)  # 睡眠100ms
        end = time.time()

        elapsed = end - start

        # 验证时间间隔（允许误差）
        assert 0.09 < elapsed < 0.2, f"时间间隔应约为0.1秒，实际为{elapsed}"


class TestStatistics:
    """统计信息测试类"""

    def test_stats_initialization(self):
        """测试统计信息初始化"""
        from mir2_auto_bot_v2 import Mir2AutoBotV2

        bot = Mir2AutoBotV2()

        # 验证统计信息初始化
        assert 'yellow_dots_detected' in bot.stats
        assert 'teleports_used' in bot.stats
        assert 'detection_runs' in bot.stats
        assert 'start_time' in bot.stats

        # 验证初始值
        assert bot.stats['yellow_dots_detected'] == 0
        assert bot.stats['teleports_used'] == 0
        assert bot.stats['detection_runs'] == 0
        assert bot.stats['start_time'] is None

    def test_stats_update(self):
        """测试统计信息更新"""
        from mir2_auto_bot_v2 import Mir2AutoBotV2

        bot = Mir2AutoBotV2()

        # 更新统计信息
        bot.stats['yellow_dots_detected'] = 10
        bot.stats['teleports_used'] = 5
        bot.stats['detection_runs'] = 20

        # 验证
        assert bot.stats['yellow_dots_detected'] == 10
        assert bot.stats['teleports_used'] == 5
        assert bot.stats['detection_runs'] == 20


class TestCoordinateCalculations:
    """坐标计算测试类"""

    def test_minimap_region_calculation(self):
        """测试小地图区域计算"""
        # 模拟客户区宽度
        client_width = 800

        # 配置参数
        offset_x = 10
        width = 150
        from_right = True

        # 计算x坐标
        if from_right:
            x = client_width - width - offset_x

        # 验证
        expected_x = 800 - 150 - 10  # 640
        assert x == expected_x, f"x坐标应为{expected_x}，实际为{x}"

    def test_client_offset_calculation(self):
        """测试客户区偏移计算"""
        # 模拟窗口和客户区位置
        window_left = 100
        window_top = 100
        client_screen_x = 108
        client_screen_y = 133

        # 计算偏移
        offset_x = client_screen_x - window_left
        offset_y = client_screen_y - window_top

        # 验证
        assert offset_x == 8, f"x偏移应为8，实际为{offset_x}"
        assert offset_y == 33, f"y偏移应为33，实际为{offset_y}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
