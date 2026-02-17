# -*- coding: utf-8 -*-
"""
配置加载功能单元测试
测试配置文件的加载和解析
"""

import pytest
import configparser
import os
import tempfile
import sys

# 添加父目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PARENT_DIR)


class TestConfigLoading:
    """配置加载测试类"""

    def test_default_config_creation(self):
        """测试默认配置文件的创建"""
        from mir2_auto_bot_v2 import Mir2AutoBotV2

        # 创建一个不存在的临时文件路径
        temp_dir = tempfile.mkdtemp()
        temp_config = os.path.join(temp_dir, 'test_config.ini')

        try:
            # 确保文件不存在
            assert not os.path.exists(temp_config), "测试前文件不应存在"

            # 创建bot实例（会创建默认配置）
            bot = Mir2AutoBotV2(config_file=temp_config)

            # 验证配置文件已创建
            assert os.path.exists(temp_config), "配置文件应该被创建"

            # 重新读取配置文件验证内容
            config = configparser.ConfigParser()
            config.read(temp_config, encoding='utf-8')

            # 检查必要的section
            assert 'Game' in config, "应该包含Game section"
            assert 'Minimap' in config, "应该包含Minimap section"
            assert 'Detection' in config, "应该包含Detection section"
            assert 'Teleport' in config, "应该包含Teleport section"
            assert 'YellowColor' in config, "应该包含YellowColor section"

        finally:
            # 清理临时文件和目录
            if os.path.exists(temp_config):
                os.unlink(temp_config)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

    def test_config_values(self):
        """测试配置值的正确性"""
        from mir2_auto_bot_v2 import Mir2AutoBotV2

        # 创建测试配置文件
        config_content = """
[Game]
window_title = 测试窗口

[Minimap]
enabled = true
offset_x = 20
offset_y = 30
width = 160
height = 160
from_right = false

[Detection]
enabled = true
detection_interval = 0.5
min_contour_area = 2
debug = true

[Teleport]
enabled = true
teleport_key = 3
cooldown = 5.0

[YellowColor]
r_lower = 245
r_upper = 255
g_lower = 245
g_upper = 255
b_lower = 0
b_upper = 10
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8') as f:
            f.write(config_content)
            temp_config = f.name

        try:
            bot = Mir2AutoBotV2(config_file=temp_config)

            # 验证配置值
            assert bot.config.get('Game', 'window_title') == '测试窗口'
            assert bot.config.getint('Minimap', 'offset_x') == 20
            assert bot.config.getint('Minimap', 'offset_y') == 30
            assert bot.config.getint('Minimap', 'width') == 160
            assert bot.config.getint('Minimap', 'height') == 160
            assert bot.config.getboolean('Minimap', 'from_right') == False

            assert bot.config.getfloat('Detection', 'detection_interval') == 0.5
            assert bot.config.getint('Detection', 'min_contour_area') == 2

            assert bot.config.get('Teleport', 'teleport_key') == '3'
            assert bot.config.getfloat('Teleport', 'cooldown') == 5.0

        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)

    def test_missing_config_file(self):
        """测试配置文件不存在的情况"""
        from mir2_auto_bot_v2 import Mir2AutoBotV2

        # 使用临时目录创建不存在的配置文件路径
        import tempfile
        temp_dir = tempfile.mkdtemp()
        non_existent = os.path.join(temp_dir, 'non_existent_config_12345.ini')

        try:
            # 创建bot实例（应该创建默认配置）
            bot = Mir2AutoBotV2(config_file=non_existent)

            # 验证使用了默认配置
            assert bot.config is not None, "应该有默认配置"
            assert bot.config.get('Game', 'window_title', fallback='九五沉默') == '九五沉默'

        finally:
            # 清理可能创建的文件和目录
            if os.path.exists(non_existent):
                os.unlink(non_existent)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

    def test_detector_params_update(self):
        """测试检测器参数更新"""
        from mir2_auto_bot_v2 import Mir2AutoBotV2
        import numpy as np

        # 创建自定义配置
        config_content = """
[YellowColor]
r_lower = 240
r_upper = 255
g_lower = 240
g_upper = 255
b_lower = 0
b_upper = 10

[Detection]
min_contour_area = 5
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8') as f:
            f.write(config_content)
            temp_config = f.name

        try:
            bot = Mir2AutoBotV2(config_file=temp_config)

            # 验证检测器参数已更新
            expected_lower = np.array([240, 240, 0])
            expected_upper = np.array([255, 255, 10])

            assert np.array_equal(bot.minimap_detector.yellow_lower_rgb, expected_lower), \
                "检测器下限参数应该更新"
            assert np.array_equal(bot.minimap_detector.yellow_upper_rgb, expected_upper), \
                "检测器上限参数应该更新"
            assert bot.minimap_detector.min_contour_area == 5, \
                "最小轮廓面积应该更新"

        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)

    def test_teleport_cooldown(self):
        """测试传送冷却时间配置"""
        from mir2_auto_bot_v2 import Mir2AutoBotV2

        config_content = """
[Teleport]
cooldown = 6.5
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8') as f:
            f.write(config_content)
            temp_config = f.name

        try:
            bot = Mir2AutoBotV2(config_file=temp_config)

            # 验证冷却时间
            assert bot.teleport_cooldown == 6.5, f"传送冷却时间应为6.5，实际为{bot.teleport_cooldown}"

        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)

    def test_config_with_missing_sections(self):
        """测试配置文件缺少某些section的情况"""
        from mir2_auto_bot_v2 import Mir2AutoBotV2

        # 只包含部分section的配置
        config_content = """
[Game]
window_title = 测试
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8') as f:
            f.write(config_content)
            temp_config = f.name

        try:
            # 应该使用默认值填充缺失的section
            bot = Mir2AutoBotV2(config_file=temp_config)

            # 验证使用了默认值
            assert bot.config.get('Minimap', 'width', fallback='150') == '150'
            assert bot.config.get('Detection', 'detection_interval', fallback='0.3') == '0.3'

        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
