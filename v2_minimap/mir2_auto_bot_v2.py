# -*- coding: utf-8 -*-
"""
传奇2自动挂机脚本 V2 - 小地图黄点检测版
功能: 检测右上角小地图内的黄点（代表其他玩家），自动使用随机传送石
特性: 后台截图，窗口被遮挡也能正常工作
"""

import time
import keyboard
import win32gui
import win32con
import win32api
import win32ui
import logging
import configparser
import os
import numpy as np
import cv2
from datetime import datetime
from typing import Optional, Tuple, List
import ctypes

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, 'mir2_bot_v2.log')
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'bot_config_v2.ini')

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MinimapDetector:
    """小地图黄点检测器"""

    def __init__(self):
        # 精确黄色检测：RGB(255, 255, 0)
        self.yellow_lower_rgb = np.array([250, 250, 0])
        self.yellow_upper_rgb = np.array([255, 255, 5])
        self.min_contour_area = 1

    def detect(self, image: np.ndarray) -> List[Tuple[int, int, int]]:
        """
        精确检测RGB(255,255,0)的黄点

        Args:
            image: BGR格式的图像

        Returns:
            检测到的黄点列表 [(x, y, area), ...]
        """
        # 转换BGR到RGB
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 创建精确黄色掩码
        yellow_mask = cv2.inRange(rgb, self.yellow_lower_rgb, self.yellow_upper_rgb)

        # 查找轮廓
        contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 过滤小轮廓，获取黄点位置
        yellow_dots = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= self.min_contour_area:
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    yellow_dots.append((cx, cy, int(area)))

        return yellow_dots

class Mir2AutoBotV2:
    """传奇2自动挂机机器人 V2 - 小地图黄点检测版（后台截图）"""

    def __init__(self, config_file: str = None, window_index: int = 0):
        self.running = False
        if config_file is None:
            config_file = CONFIG_FILE

        # 窗口索引（用于多实例）
        self.window_index = window_index

        # 小地图检测器
        self.minimap_detector = MinimapDetector()

        # 加载配置
        self.config = self._load_config(config_file)

        # 窗口信息
        self.hwnd = None
        self.window_rect = None
        self.client_rect = None
        self.client_offset = (0, 0)
        self.window_title = ""

        # 小地图区域（相对于客户区）
        self.minimap_region = None  # (x, y, width, height)

        # 传送相关
        self.last_teleport_time = 0
        self.teleport_cooldown = self.config.getfloat('Teleport', 'cooldown', fallback=4.0)

        # 统计信息
        self.stats = {
            'yellow_dots_detected': 0,
            'teleports_used': 0,
            'detection_runs': 0,
            'start_time': None
        }

        logger.info(f"传奇2自动挂机机器人V2（后台截图版）初始化完成 - 窗口索引: {window_index}")

    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """加载配置文件"""
        config = configparser.ConfigParser()

        # 默认配置
        default_config = {
            'Game': {
                'window_title': '九五沉默',
            },
            'Minimap': {
                'enabled': 'true',
                'offset_x': '10',
                'offset_y': '10',
                'width': '150',
                'height': '150',
                'from_right': 'true',
            },
            'Detection': {
                'enabled': 'true',
                'detection_interval': '0.3',
                'min_contour_area': '1',
                'debug': 'false',
            },
            'Teleport': {
                'enabled': 'true',
                'teleport_key': '2',
                'cooldown': '4.0',
            },
            'YellowColor': {
                'r_lower': '250',
                'r_upper': '255',
                'g_lower': '250',
                'g_upper': '255',
                'b_lower': '0',
                'b_upper': '5',
            }
        }

        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
            logger.info(f"已加载配置文件: {config_file}")
        else:
            for section, settings in default_config.items():
                config.add_section(section)
                for key, value in settings.items():
                    config.set(section, key, value)
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            logger.info(f"已创建默认配置文件: {config_file}")

        # 更新检测器参数
        self._update_detector_params(config)

        return config

    def _update_detector_params(self, config: configparser.ConfigParser):
        """更新检测器参数"""
        r_lower = config.getint('YellowColor', 'r_lower', fallback=250)
        r_upper = config.getint('YellowColor', 'r_upper', fallback=255)
        g_lower = config.getint('YellowColor', 'g_lower', fallback=250)
        g_upper = config.getint('YellowColor', 'g_upper', fallback=255)
        b_lower = config.getint('YellowColor', 'b_lower', fallback=0)
        b_upper = config.getint('YellowColor', 'b_upper', fallback=5)

        self.minimap_detector.yellow_lower_rgb = np.array([r_lower, g_lower, b_lower])
        self.minimap_detector.yellow_upper_rgb = np.array([r_upper, g_upper, b_upper])
        self.minimap_detector.min_contour_area = config.getint('Detection', 'min_contour_area', fallback=1)

    def find_game_window(self) -> bool:
        """查找游戏窗口"""
        window_title = self.config.get('Game', 'window_title', fallback='九五沉默')
        possible_titles = [window_title, 'Legend of Mir2', '传奇']

        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                for possible_title in possible_titles:
                    if possible_title.lower() in title.lower():
                        # 检查客户区是否有效
                        try:
                            client_rect = win32gui.GetClientRect(hwnd)
                            client_width = client_rect[2] - client_rect[0]
                            client_height = client_rect[3] - client_rect[1]
                            if client_width > 0 and client_height > 0:
                                windows.append((hwnd, title))
                        except:
                            pass
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)

        if windows:
            # 根据窗口索引选择窗口
            if self.window_index < len(windows):
                self.hwnd, self.window_title = windows[self.window_index]
                logger.info(f"找到 {len(windows)} 个游戏窗口，选择第 {self.window_index + 1} 个窗口")
            else:
                logger.warning(f"窗口索引 {self.window_index} 超出范围（共 {len(windows)} 个窗口），使用第一个窗口")
                self.hwnd, self.window_title = windows[0]
            
            self._init_window_info()
            return True
        else:
            logger.error("未找到游戏窗口")
            return False

    def _init_window_info(self):
        """初始化窗口信息"""
        self.window_rect = win32gui.GetWindowRect(self.hwnd)
        self.client_rect = win32gui.GetClientRect(self.hwnd)

        client_left, client_top = win32gui.ClientToScreen(self.hwnd, (0, 0))
        window_left, window_top = self.window_rect[0], self.window_rect[1]
        self.client_offset = (client_left - window_left, client_top - window_top)

        logger.info(f"找到游戏窗口: {self.window_title}")
        logger.info(f"窗口位置: {self.window_rect}")
        logger.info(f"客户区大小: {self.client_rect}")
        logger.info(f"客户区偏移: {self.client_offset}")

        self._calculate_minimap_region()

    def _calculate_minimap_region(self):
        """计算小地图区域（相对于客户区）"""
        if not self.client_rect:
            return

        client_width = self.client_rect[2] - self.client_rect[0]

        offset_x = self.config.getint('Minimap', 'offset_x', fallback=10)
        offset_y = self.config.getint('Minimap', 'offset_y', fallback=10)
        width = self.config.getint('Minimap', 'width', fallback=150)
        height = self.config.getint('Minimap', 'height', fallback=150)
        from_right = self.config.getboolean('Minimap', 'from_right', fallback=True)

        if from_right:
            x = client_width - width - offset_x
        else:
            x = offset_x
        y = offset_y

        self.minimap_region = (x, y, width, height)
        logger.info(f"小地图区域（相对客户区）: {self.minimap_region}")

    def capture_minimap(self) -> Optional[np.ndarray]:
        """
        后台捕获小地图 - 使用Win32 API
        即使窗口被遮挡也能正确截图
        """
        if not self.client_rect or not self.minimap_region:
            return None

        try:
            client_width = self.client_rect[2] - self.client_rect[0]
            client_height = self.client_rect[3] - self.client_rect[1]

            # 获取窗口DC
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # 创建位图
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, client_width, client_height)
            saveDC.SelectObject(saveBitMap)

            # 使用BitBlt进行截图（比PrintWindow更可靠）
            # 注意：BitBlt需要窗口可见，但不需要窗口在最前面
            saveDC.BitBlt((0, 0), (client_width, client_height), mfcDC, (0, 0), win32con.SRCCOPY)

            # 转换为numpy数组
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # 裁剪小地图区域
            minimap_x, minimap_y, minimap_w, minimap_h = self.minimap_region
            minimap = img[minimap_y:minimap_y+minimap_h, minimap_x:minimap_x+minimap_w]

            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwndDC)

            return minimap

        except Exception as e:
            logger.error(f"后台截图失败: {e}")
            return None


    def detect_yellow_dots(self, minimap_image: np.ndarray) -> Tuple[bool, List[Tuple[int, int, int]]]:
        """检测小地图中的黄点"""
        if not self.config.getboolean('Detection', 'enabled', fallback=True):
            return False, []

        yellow_dots = self.minimap_detector.detect(minimap_image)

        # 调试模式：保存检测结果
        if self.config.getboolean('Detection', 'debug', fallback=False):
            self._save_debug_image(minimap_image, yellow_dots)

        if yellow_dots:
            self.stats['yellow_dots_detected'] += len(yellow_dots)
            logger.info(f"检测到 {len(yellow_dots)} 个黄点 - 其他玩家!")
            return True, yellow_dots

        return False, []

    def _save_debug_image(self, minimap_image: np.ndarray, yellow_dots: List[Tuple[int, int, int]]):
        """保存调试图像"""
        debug_dir = os.path.join(SCRIPT_DIR, 'debug')
        os.makedirs(debug_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存原始小地图
        cv2.imwrite(os.path.join(debug_dir, f'minimap_{timestamp}.jpg'), minimap_image)

        # 绘制检测结果
        debug_img = minimap_image.copy()
        for x, y, area in yellow_dots:
            cv2.circle(debug_img, (x, y), 5, (0, 0, 255), -1)
            cv2.putText(debug_img, f"{area}", (x + 5, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        cv2.imwrite(os.path.join(debug_dir, f'detection_{timestamp}.jpg'), debug_img)

    def use_teleport(self):
        """使用随机传送石 - 使用PostMessage发送按键"""
        if not self.config.getboolean('Teleport', 'enabled', fallback=True):
            return

        current_time = time.time()
        self.teleport_cooldown = self.config.getfloat('Teleport', 'cooldown', fallback=4.0)

        if current_time - self.last_teleport_time < self.teleport_cooldown:
            return

        teleport_key = self.config.get('Teleport', 'teleport_key', fallback='2')

        try:
            # 将按键字符转换为虚拟键码
            vk_code = win32api.VkKeyScan(teleport_key)
            vk_code = vk_code & 0xFF

            # 使用PostMessage向窗口发送按键消息
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYDOWN, vk_code, 0)
            time.sleep(0.05)
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYUP, vk_code, 0)

            self.last_teleport_time = current_time
            self.stats['teleports_used'] += 1
            logger.info(f"已使用随机传送石 (快捷键: {teleport_key})")

        except Exception as e:
            logger.error(f"使用传送石失败: {e}")

    def update_stats(self):
        """更新统计信息"""
        if not self.stats['start_time']:
            self.stats['start_time'] = datetime.now()

        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            if elapsed > 0 and int(elapsed) % 60 == 0:
                logger.info(
                    f"运行时间: {int(elapsed // 60)}分钟 | "
                    f"检测次数: {self.stats['detection_runs']} | "
                    f"黄点检测: {self.stats['yellow_dots_detected']} | "
                    f"使用传送: {self.stats['teleports_used']}"
                )

    def run(self):
        """运行挂机脚本"""
        logger.info("开始运行挂机脚本V2...")
        logger.info("使用小地图黄点检测（后台截图模式）")

        if not self.find_game_window():
            logger.error("无法找到游戏窗口，退出")
            return

        logger.info("提示: 脚本支持后台运行，窗口被遮挡也能正常工作")

        self.running = True
        logger.info("挂机脚本V2已启动，按 F10 停止")
        logger.info(f"功能: 检测小地图黄点（其他玩家），自动使用随机传送石")
        logger.info(f"小地图区域: {self.minimap_region}")

        try:
            while self.running:
                # 检查窗口是否还存在
                if not win32gui.IsWindow(self.hwnd):
                    logger.warning("游戏窗口已关闭")
                    break

                # 后台捕获小地图
                minimap = self.capture_minimap()

                if minimap is not None:
                    self.stats['detection_runs'] += 1

                    # 检测黄点
                    has_players, yellow_dots = self.detect_yellow_dots(minimap)

                    if has_players:
                        self.use_teleport()

                self.update_stats()

                detection_interval = self.config.getfloat('Detection', 'detection_interval', fallback=0.3)
                time.sleep(detection_interval)

        except KeyboardInterrupt:
            logger.info("收到中断信号")
        except Exception as e:
            logger.error(f"运行出错: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """停止挂机脚本"""
        self.running = False
        logger.info("挂机脚本V2已停止")

        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            logger.info("=" * 50)
            logger.info("挂机统计:")
            logger.info(f"运行时间: {int(elapsed // 60)} 分钟 {int(elapsed % 60)} 秒")
            logger.info(f"检测次数: {self.stats['detection_runs']}")
            logger.info(f"黄点检测: {self.stats['yellow_dots_detected']}")
            logger.info(f"使用传送: {self.stats['teleports_used']}")
            logger.info("=" * 50)

def main():
    """主函数"""
    import sys
    
    print("=" * 50)
    print("传奇2自动挂机脚本 V2 - 小地图黄点检测版")
    print("=" * 50)
    print()
    print("功能:")
    print("  - 检测右上角小地图内的黄点")
    print("  - 黄点代表其他玩家")
    print("  - 检测到其他玩家时自动使用随机传送石")
    print()
    print("特性:")
    print("  - 后台截图，窗口被遮挡也能正常工作")
    print("  - 使用PrintWindow API实现后台截图")
    print("  - 可配置小地图位置和大小")
    print("  - 支持多实例运行，每个实例监控不同窗口")
    print()
    print("控制:")
    print("  - F10: 停止挂机")
    print("  - Ctrl+C: 强制退出")
    print()
    print("使用方法:")
    print("  python mir2_auto_bot_v2.py [窗口索引]")
    print("  窗口索引: 0=第1个窗口, 1=第2个窗口, 2=第3个窗口...")
    print("  示例: python mir2_auto_bot_v2.py 0  # 监控第1个窗口")
    print("        python mir2_auto_bot_v2.py 1  # 监控第2个窗口")
    print()
    print("=" * 50)
    print()

    # 解析窗口索引参数
    window_index = 0
    if len(sys.argv) > 1:
        try:
            window_index = int(sys.argv[1])
            print(f"窗口索引: {window_index} (监控第 {window_index + 1} 个窗口)")
        except ValueError:
            print(f"警告: 无效的窗口索引参数 '{sys.argv[1]}'，使用默认值 0")
    
    bot = Mir2AutoBotV2(window_index=window_index)
    keyboard.add_hotkey('F10', bot.stop)
    bot.run()
    keyboard.unhook_all()

if __name__ == '__main__':
    main()
