# -*- coding: utf-8 -*-
"""
传奇2自动挂机脚本 V2 - 多窗口版本
功能: 同时监控多个游戏窗口，各自独立检测和传送
修复: 后台截图、独立统计、多线程响应
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
from typing import Optional, Tuple, List, Dict
from PIL import Image
import threading
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
        self.yellow_lower_rgb = np.array([250, 250, 0])
        self.yellow_upper_rgb = np.array([255, 255, 5])
        self.min_contour_area = 1

    def detect(self, image: np.ndarray) -> List[Tuple[int, int, int]]:
        """精确检测RGB(255,255,0)的黄点"""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        yellow_mask = cv2.inRange(rgb, self.yellow_lower_rgb, self.yellow_upper_rgb)
        contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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


class GameWindow:
    """单个游戏窗口 - 独立运行"""

    def __init__(self, hwnd: int, title: str, config: configparser.ConfigParser):
        self.hwnd = hwnd
        self.title = title
        self.config = config

        self.window_rect = None
        self.client_rect = None
        self.client_offset = (0, 0)
        self.minimap_region = None

        # 每个窗口独立的检测器实例
        self.detector = MinimapDetector()
        self.last_teleport_time = 0
        self.teleport_cooldown = config.getfloat('Teleport', 'cooldown', fallback=4.0)

        # 独立的统计数据（每个窗口自己的字典）
        self.stats = {
            'yellow_dots_detected': 0,
            'teleports_used': 0,
            'detection_runs': 0,
        }

        # 线程控制
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

        self._init_window()

    def _init_window(self):
        """初始化窗口信息"""
        try:
            self.window_rect = win32gui.GetWindowRect(self.hwnd)
            self.client_rect = win32gui.GetClientRect(self.hwnd)

            client_left, client_top = win32gui.ClientToScreen(self.hwnd, (0, 0))
            window_left, window_top = self.window_rect[0], self.window_rect[1]
            self.client_offset = (client_left - window_left, client_top - window_top)

            self._calculate_minimap_region()
        except Exception as e:
            logger.error(f"[{self.title}] 初始化窗口失败: {e}")

    def _calculate_minimap_region(self):
        """计算小地图区域"""
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

    def capture_minimap(self) -> Optional[np.ndarray]:
        """后台捕获小地图 - 使用Win32 API"""
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

            # 使用PrintWindow进行后台截图
            # PW_CLIENTONLY = 2 - 只截取客户区
            result = ctypes.windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 2)

            if result:
                # 转换为numpy数组
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                img = np.frombuffer(bmpstr, dtype='uint8')
                img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                # 裁剪小地图区域
                minimap_x, minimap_y, minimap_w, minimap_h = self.minimap_region
                minimap = img[minimap_y:minimap_y+minimap_h, minimap_x:minimap_x+minimap_w]
            else:
                # PrintWindow失败，尝试BitBlt
                saveDC.BitBlt((0, 0), (client_width, client_height), mfcDC, (0, 0), win32con.SRCCOPY)
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                img = np.frombuffer(bmpstr, dtype='uint8')
                img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                minimap_x, minimap_y, minimap_w, minimap_h = self.minimap_region
                minimap = img[minimap_y:minimap_y+minimap_h, minimap_x:minimap_x+minimap_w]

            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwndDC)

            return minimap

        except Exception as e:
            logger.error(f"[{self.title}] 后台截图失败: {e}")
            return None

    def detect_players(self) -> bool:
        """检测是否有其他玩家"""
        minimap = self.capture_minimap()
        if minimap is None:
            return False

        with self.lock:
            self.stats['detection_runs'] += 1

        yellow_dots = self.detector.detect(minimap)

        if yellow_dots:
            with self.lock:
                self.stats['yellow_dots_detected'] += len(yellow_dots)
            logger.info(f"[{self.title}] 检测到 {len(yellow_dots)} 个黄点")
            return True

        return False

    def teleport(self):
        """传送 - 使用PostMessage向特定窗口发送按键"""
        if not self.config.getboolean('Teleport', 'enabled', fallback=True):
            return

        current_time = time.time()
        if current_time - self.last_teleport_time < self.teleport_cooldown:
            return

        teleport_key = self.config.get('Teleport', 'teleport_key', fallback='2')

        try:
            # 将按键字符转换为虚拟键码
            vk_code = win32api.VkKeyScan(teleport_key)
            vk_code = vk_code & 0xFF  # 只取低字节

            # 使用PostMessage向特定窗口发送按键消息
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYDOWN, vk_code, 0)
            time.sleep(0.05)
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYUP, vk_code, 0)

            self.last_teleport_time = current_time
            with self.lock:
                self.stats['teleports_used'] += 1
            logger.info(f"[{self.title}] 已传送 (快捷键: {teleport_key}, hwnd: {self.hwnd})")
        except Exception as e:
            logger.error(f"[{self.title}] 传送失败: {e}")

    def _run_loop(self, detection_interval: float):
        """独立线程运行循环"""
        logger.info(f"[{self.title}] 开始独立监控")
        
        while self.running:
            try:
                # 检查窗口是否还存在
                if not win32gui.IsWindow(self.hwnd):
                    logger.info(f"[{self.title}] 窗口已关闭")
                    break

                # 检测玩家
                if self.detect_players():
                    self.teleport()

            except Exception as e:
                logger.error(f"[{self.title}] 检测错误: {e}")

            time.sleep(detection_interval)

        logger.info(f"[{self.title}] 监控已停止")

    def start(self, detection_interval: float = 0.3):
        """启动独立监控线程"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, args=(detection_interval,), daemon=True)
        self.thread.start()
        logger.info(f"[{self.title}] 启动独立监控线程")

    def stop(self):
        """停止监控"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        logger.info(f"[{self.title}] 已停止")

    def is_valid(self) -> bool:
        """检查窗口是否仍然有效"""
        try:
            return win32gui.IsWindow(self.hwnd)
        except:
            return False


class MultiWindowBot:
    """多窗口挂机机器人"""

    def __init__(self, config_file: str = None):
        self.running = False
        self.windows: Dict[int, GameWindow] = {}  # hwnd -> GameWindow

        if config_file is None:
            config_file = CONFIG_FILE
        self.config = self._load_config(config_file)

        self.stats = {
            'start_time': None,
            'total_teleports': 0,
        }

        logger.info("多窗口挂机机器人初始化完成")

    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """加载配置文件"""
        config = configparser.ConfigParser()

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

        return config

    def find_all_windows(self) -> List[Tuple[int, str]]:
        """查找所有游戏窗口"""
        window_title = self.config.get('Game', 'window_title', fallback='九五沉默')
        possible_titles = [window_title, 'Legend of Mir2', '传奇']

        found_windows = []

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
                                windows.append((hwnd, title))
                        except:
                            pass
            return True

        win32gui.EnumWindows(callback, found_windows)
        return found_windows

    def scan_windows(self) -> int:
        """扫描并添加所有游戏窗口"""
        found = self.find_all_windows()
        
        # 停止所有现有窗口
        for gw in self.windows.values():
            gw.stop()
        
        self.windows.clear()

        for hwnd, title in found:
            self.windows[hwnd] = GameWindow(hwnd, title, self.config)
            logger.info(f"添加窗口: {title} (hwnd: {hwnd})")

        logger.info(f"共找到 {len(self.windows)} 个游戏窗口")
        return len(self.windows)

    def add_window(self, hwnd: int, title: str):
        """添加单个窗口"""
        if hwnd not in self.windows:
            self.windows[hwnd] = GameWindow(hwnd, title, self.config)
            logger.info(f"添加窗口: {title}")

    def remove_window(self, hwnd: int):
        """移除窗口"""
        if hwnd in self.windows:
            self.windows[hwnd].stop()
            del self.windows[hwnd]
            logger.info(f"移除窗口: {hwnd}")

    def run(self):
        """运行多窗口监控 - 每个窗口独立线程"""
        if not self.windows:
            logger.error("没有游戏窗口，请先扫描窗口")
            return

        self.running = True
        self.stats['start_time'] = datetime.now()
        
        detection_interval = self.config.getfloat('Detection', 'detection_interval', fallback=0.3)
        
        logger.info(f"开始监控 {len(self.windows)} 个窗口（独立线程模式），按 F10 停止")

        # 启动所有窗口的独立线程
        for hwnd, game_window in self.windows.items():
            game_window.start(detection_interval)

        # 主线程等待
        try:
            while self.running:
                # 检查各窗口状态
                for hwnd, game_window in list(self.windows.items()):
                    if not game_window.is_valid():
                        logger.info(f"[{game_window.title}] 窗口已关闭")
                        game_window.stop()
                        del self.windows[hwnd]
                
                time.sleep(1.0)

        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            self.stop()

    def stop(self):
        """停止所有监控"""
        self.running = False
        
        # 停止所有窗口线程
        for gw in self.windows.values():
            gw.stop()

        logger.info("多窗口监控已停止")

        # 打印统计
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            total_teleports = sum(gw.stats['teleports_used'] for gw in self.windows.values())
            
            logger.info("=" * 50)
            logger.info("统计信息:")
            logger.info(f"运行时间: {int(elapsed // 60)} 分钟 {int(elapsed % 60)} 秒")
            logger.info(f"总传送次数: {total_teleports}")
            for hwnd, gw in self.windows.items():
                logger.info(f"  [{gw.title}] 检测: {gw.stats['detection_runs']}, 黄点: {gw.stats['yellow_dots_detected']}, 传送: {gw.stats['teleports_used']}")
            logger.info("=" * 50)


def main():
    """主函数"""
    print("=" * 50)
    print("传奇2自动挂机脚本 V2 - 多窗口版本")
    print("=" * 50)
    print()
    print("功能:")
    print("  - 同时监控多个游戏窗口")
    print("  - 各窗口独立检测和传送（独立线程）")
    print("  - 后台截图，不影响其他操作")
    print("  - 自动检测小地图黄点（其他玩家）")
    print()
    print("控制:")
    print("  - F10: 停止监控")
    print("  - Ctrl+C: 强制退出")
    print()
    print("=" * 50)
    print()

    bot = MultiWindowBot()

    # 扫描窗口
    count = bot.scan_windows()
    if count == 0:
        print("未找到游戏窗口，请确保游戏已启动")
        return

    # 设置快捷键
    keyboard.add_hotkey('F10', bot.stop)

    # 运行
    bot.run()

    # 清理
    keyboard.unhook_all()


if __name__ == '__main__':
    main()
