# -*- coding: utf-8 -*-
"""
传奇2自动挂机脚本 - Pygame版本
功能: 检测到画面内有其他玩家角色时自动使用随机传送石
"""

import time
import keyboard
import win32gui
import win32con
import win32api
import win32process
import logging
import configparser
import os
import numpy as np
import cv2
import pyautogui
from datetime import datetime
from typing import Optional, Tuple, List
import pytesseract
from PIL import Image
from image_preprocessor import ImagePreprocessor

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, 'mir2_bot.log')
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'bot_config.ini')

# 禁用pyautogui的安全检查
pyautogui.FAILSAFE = False

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


class Mir2AutoBot:
    """传奇2自动挂机机器人 - OCR监测版"""

    def __init__(self, config_file: str = None):
        """
        初始化挂机机器人

        Args:
            config_file: 配置文件路径
        """
        self.running = False
        if config_file is None:
            config_file = CONFIG_FILE
        self.config = self._load_config(config_file)
        self.hwnd = None
        self.window_rect = None
        self.client_rect = None  # 客户区矩形
        self.client_offset = (0, 0)  # 客户区相对于窗口的偏移

        # 监测相关
        self.screen = None

        # 玩家检测相关
        self.last_teleport_time = 0
        self.teleport_cooldown = 10  # 传送冷却时间(秒)
        self.player_detected_count = 0
        self.target_text = self.config.get('Detection', 'target_text', fallback='游戏斩杀')  # 从配置文件读取目标文字

        # 图像预处理器
        self.preprocessor = ImagePreprocessor()

        # 统计信息
        self.stats = {
            'players_detected': 0,
            'teleports_used': 0,
            'detection_runs': 0,
            'start_time': None
        }

        logger.info("传奇2自动挂机机器人(OCR版本)初始化完成")

    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """加载配置文件"""
        config = configparser.ConfigParser()

        # 默认配置
        default_config = {
            'Game': {
                'window_title': '95W.Com【第二统战·三战区】·【09号 新区】',
                'auto_start': 'false',
            },
            'Detection': {
                'enabled': 'true',
                'detection_interval': '0.3',
                'confidence_threshold': '0.75',
                'player_name_color': 'white',
            },
            'Teleport': {
                'enabled': 'true',
                'teleport_key': '2',
                'cooldown': '1',
            },
            'Advanced': {
                'use_opencv': 'true',
                'min_detection_area': '100',
                'max_detection_area': '50000',
            }
        }

        # 读取配置文件
        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
            logger.info(f"已加载配置文件: {config_file}")

            # 检查是否缺少配置项，如果有则添加默认值
            for section, settings in default_config.items():
                if not config.has_section(section):
                    config.add_section(section)
                for key, value in settings.items():
                    if not config.has_option(section, key):
                        config.set(section, key, value)
        else:
            # 配置文件不存在，使用默认配置并创建
            for section, settings in default_config.items():
                config.add_section(section)
                for key, value in settings.items():
                    config.set(section, key, value)

            # 保存默认配置
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            logger.info(f"已创建默认配置文件: {config_file}")

        return config

    def find_game_window(self) -> bool:
        """查找游戏窗口"""
        window_title = self.config.get('Game', 'window_title', fallback='九五沉默')

        # 支持多个可能的窗口标题（按优先级排序）
        possible_titles = [
            window_title,  # 配置文件中的标题（九五沉默）
            'Legend of Mir2',  # 登录器窗口
            '传奇',  # 其他传奇游戏
        ]

        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                # 检查标题是否匹配任何一个可能的标题
                for possible_title in possible_titles:
                    if possible_title.lower() in title.lower():
                        windows.append((hwnd, title))
                        return True  # 找到匹配的窗口就停止
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)

        if windows:
            self.hwnd, title = windows[0]
            self.window_rect = win32gui.GetWindowRect(self.hwnd)

            # 获取客户区矩形（游戏画面的实际区域）
            self.client_rect = win32gui.GetClientRect(self.hwnd)

            # 计算客户区相对于窗口的偏移
            # GetClientRect返回的是相对于客户区左上角的坐标
            # 需要转换为屏幕坐标
            client_left, client_top = win32gui.ClientToScreen(self.hwnd, (0, 0))
            window_left, window_top = self.window_rect[0], self.window_rect[1]

            self.client_offset = (client_left - window_left, client_top - window_top)

            game_title = win32gui.GetWindowText(self.hwnd)
            logger.info(f"找到游戏窗口: {game_title}")
            logger.info(f"窗口位置: {self.window_rect}")
            logger.info(f"客户区大小: {self.client_rect}")
            logger.info(f"客户区偏移: {self.client_offset}")
            return True
        else:
            logger.error(f"未找到游戏窗口")
            logger.info(f"尝试的标题: {possible_titles}")
            logger.info("提示: 请确保游戏窗口已打开")
            return False

    def activate_game_window(self) -> bool:
        """激活游戏窗口（已禁用）"""
        # 不再激活窗口，直接返回True
        # 截图和传送都不需要窗口在前台
        return True

    def capture_game_screen(self) -> Optional[np.ndarray]:
        """
        捕获游戏窗口画面（使用pyautogui）

        Returns:
            游戏画面(numpy数组)
        """
        if not self.window_rect or not self.client_rect:
            return None

        try:
            # 使用客户区的屏幕坐标进行截图
            # 客户区的屏幕坐标 = 窗口左上角 + 客户区偏移
            window_left, window_top = self.window_rect[0], self.window_rect[1]
            offset_x, offset_y = self.client_offset

            # 客户区的屏幕坐标
            client_screen_left = window_left + offset_x
            client_screen_top = window_top + offset_y

            # 客户区的大小（GetClientRect返回的是(left, top, right, bottom)）
            client_width = self.client_rect[2] - self.client_rect[0]
            client_height = self.client_rect[3] - self.client_rect[1]

            # 使用pyautogui截取客户区区域
            screenshot = pyautogui.screenshot(region=(client_screen_left, client_screen_top, client_width, client_height))

            # 转换为OpenCV格式
            image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            return image

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    def detect_players_opencv(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        使用OCR检测画面中是否包含特定文字"人物斩杀"

        Args:
            image: 游戏画面

        Returns:
            检测到的目标文字矩形列表 [(x, y, w, h), ...]
        """
        if not self.config.getboolean('Detection', 'enabled', fallback=True):
            return []

        try:
            height, width = image.shape[:2]

            # 从配置文件读取检测范围百分比
            top_percent = self.config.getint('Advanced', 'detection_top_percent', fallback=20)
            bottom_percent = self.config.getint('Advanced', 'detection_bottom_percent', fallback=60)
            left_percent = self.config.getint('Advanced', 'detection_left_percent', fallback=5)
            right_percent = self.config.getint('Advanced', 'detection_right_percent', fallback=95)

            # 计算检测区域
            top_y = int(height * top_percent / 100)
            bottom_y = int(height * bottom_percent / 100)
            left_x = int(width * left_percent / 100)
            right_x = int(width * right_percent / 100)

            # 裁剪检测区域
            detection_region = image[top_y:bottom_y, left_x:right_x]

            # 可选：保存调试图像
            if self.config.get('Detection', 'debug', fallback='false') == 'true':
                debug_dir = os.path.join(SCRIPT_DIR, 'debug')
                os.makedirs(debug_dir, exist_ok=True)
                cv2.imwrite(os.path.join(debug_dir, '01_detection_region.jpg'), detection_region)

            # 图像预处理
            use_preprocessing = self.config.getboolean('Advanced', 'use_preprocessing', fallback=True)
            if use_preprocessing:
                # 使用自动预处理
                preprocessed = self.preprocessor.auto_preprocess(detection_region)

                # 保存预处理结果
                if self.config.get('Detection', 'debug', fallback='false') == 'true':
                    cv2.imwrite(os.path.join(debug_dir, '02_preprocessed.jpg'), preprocessed)

                # 将预处理后的图像转换为PIL图像
                if len(preprocessed.shape) == 2:
                    # 灰度图或二值图
                    pil_image = Image.fromarray(preprocessed)
                else:
                    # 彩色图
                    pil_image = Image.fromarray(cv2.cvtColor(preprocessed, cv2.COLOR_BGR2RGB))
            else:
                # 不使用预处理，直接转换
                pil_image = Image.fromarray(cv2.cvtColor(detection_region, cv2.COLOR_BGR2RGB))

            # 使用pytesseract进行OCR识别（支持中文）
            # --psm 6: 假设是一个统一的文本块
            # --oem 3: 使用默认的LSTM OCR引擎
            # -l chi_sim: 使用简体中文语言包
            text_data = pytesseract.image_to_data(
                pil_image,
                lang='chi_sim',
                config='--psm 6 --oem 3',
                output_type=pytesseract.Output.DICT
            )

            # 查找目标文字
            target_rects = []
            n_boxes = len(text_data['text'])

            for i in range(n_boxes):
                text = text_data['text'][i].strip()
                conf = int(text_data['conf'][i])

                # 只考虑置信度足够高的识别结果
                if conf > 30 and text:
                    # 检查是否完全匹配目标文字（避免误识别单个字）
                    # 使用精确匹配或目标文字占识别结果的大部分
                    is_match = False
                    if text == self.target_text:
                        # 完全匹配
                        is_match = True
                    elif self.target_text in text and len(text) <= len(self.target_text) + 2:
                        # 包含目标文字且长度接近（允许少量额外字符）
                        is_match = True

                    if is_match:
                        x, y, w, h = text_data['left'][i], text_data['top'][i], text_data['width'][i], text_data['height'][i]

                        # 调整坐标（因为我们只检测了裁剪区域）
                        x += left_x
                        y += top_y

                        target_rects.append((x, y, w, h))
                        logger.info(f"检测到目标文字 '{text}' 在位置 ({x}, {y}), 置信度: {conf}")

            # 可选：绘制检测框和检测范围
            if self.config.get('Detection', 'debug', fallback='false') == 'true':
                debug_img = image.copy()

                # 绘制检测范围（黄色半透明矩形）
                overlay = debug_img.copy()
                cv2.rectangle(overlay, (left_x, top_y), (right_x, bottom_y), (0, 255, 255), -1)
                cv2.addWeighted(overlay, 0.2, debug_img, 0.8, 0, debug_img)

                # 绘制检测范围边框（黄色实线）
                cv2.rectangle(debug_img, (left_x, top_y), (right_x, bottom_y), (0, 255, 255), 2)

                # 绘制检测到的目标文字（绿色框）
                for idx, (x, y, w, h) in enumerate(target_rects):
                    cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    # 在框左上角显示序号
                    cv2.putText(debug_img, f"{idx+1}", (x, y - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # 添加检测范围说明文字
                cv2.putText(debug_img, f"Detection: {left_x},{top_y} to {right_x},{bottom_y}",
                           (10, top_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                cv2.putText(debug_img, f"Target Found: {len(target_rects)}",
                           (10, bottom_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                cv2.imwrite(os.path.join(debug_dir, '03_detection_result.jpg'), debug_img)

            return target_rects

        except Exception as e:
            logger.error(f"检测目标文字失败: {e}")
            logger.error(f"请确保已安装Tesseract OCR和中文语言包")
            return []

    def detect_players(self, image: np.ndarray) -> bool:
        """
        检测画面中是否包含目标文字"人物斩杀"（主检测函数）

        Args:
            image: 游戏画面

        Returns:
            是否检测到目标文字（需要检测到两次及以上）
        """
        self.stats['detection_runs'] += 1

        use_opencv = self.config.getboolean('Advanced', 'use_opencv', fallback=True)

        if use_opencv:
            target_rects = self.detect_players_opencv(image)
        else:
            target_rects = []

        if target_rects:
            self.stats['players_detected'] += len(target_rects)
            logger.info(f"检测到目标文字 '{self.target_text}' {len(target_rects)} 次")

            # 检测到两次及以上才返回True（避免误报）
            if len(target_rects) >= 2:
                if self.config.get('Detection', 'debug', fallback='false') == 'true':
                    for x, y, w, h in target_rects:
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # 保存调试图像
                    debug_file = os.path.join(SCRIPT_DIR, 'debug_detection.jpg')
                    cv2.imwrite(debug_file, image)

                return True
            else:
                logger.info(f"检测到 {len(target_rects)} 次（需要两次及以上才传送）")
                return False
                cv2.imwrite(debug_file, image)

            return True

        return False

    def use_teleport(self):
        """使用随机传送石"""
        if not self.config.getboolean('Teleport', 'enabled', fallback=True):
            return

        current_time = time.time()
        self.teleport_cooldown = self.config.getfloat('Teleport', 'cooldown', fallback=10)

        # 检查冷却时间
        if current_time - self.last_teleport_time < self.teleport_cooldown:
            remaining = int(self.teleport_cooldown - (current_time - self.last_teleport_time))
            logger.debug(f"传送冷却中，剩余 {remaining} 秒")
            return

        # 获取传送快捷键
        teleport_key = self.config.get('Teleport', 'teleport_key', fallback='2')

        try:
            # 不激活窗口，直接发送按键
            # 这样不会影响用户的其他操作
            
            # 使用keyboard库发送按键（不需要窗口在前台）
            keyboard.press_and_release(teleport_key)

            self.last_teleport_time = current_time
            self.stats['teleports_used'] += 1
            logger.info(f"已使用随机传送石 (快捷键: {teleport_key})")

        except Exception as e:
            logger.error(f"使用传送石失败: {e}")

    def update_stats(self):
        """更新统计信息"""
        if not self.stats['start_time']:
            self.stats['start_time'] = datetime.now()

        # 每分钟打印一次统计信息
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            if elapsed > 0 and int(elapsed) % 60 == 0:
                logger.info(
                    f"运行时间: {int(elapsed // 60)}分钟 | "
                    f"检测次数: {self.stats['detection_runs']} | "
                    f"检测到玩家: {self.stats['players_detected']} | "
                    f"使用传送: {self.stats['teleports_used']}"
                )

    def run(self):
        """运行挂机脚本"""
        logger.info("开始运行挂机脚本...")
        logger.info("使用OCR进行画面监测")

        # 查找游戏窗口
        if not self.find_game_window():
            logger.error("无法找到游戏窗口，退出")
            return

        # 不强制激活窗口，允许用户继续其他操作
        logger.info("提示: 脚本将在后台运行，不影响您的其他操作")

        self.running = True
        logger.info("挂机脚本已启动，按 F10 停止")
        logger.info(f"功能: 检测到画面内有目标文字 '{self.target_text}' 时自动使用随机传送石")

        try:
            while self.running:
                # 捕获游戏画面（不需要窗口在前台）
                image = self.capture_game_screen()

                if image is not None:
                    # 检测是否有目标文字
                    if self.detect_players(image):
                        # 检测到目标文字，使用传送石
                        self.use_teleport()

                # 更新统计
                self.update_stats()

                # 等待下一次检测
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
        logger.info("挂机脚本已停止")

        # 打印最终统计
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            logger.info("=" * 50)
            logger.info("挂机统计:")
            logger.info(f"运行时间: {int(elapsed // 60)} 分钟 {int(elapsed % 60)} 秒")
            logger.info(f"检测次数: {self.stats['detection_runs']}")
            logger.info(f"检测到玩家: {self.stats['players_detected']}")
            logger.info(f"使用传送: {self.stats['teleports_used']}")
            logger.info("=" * 50)


def main():
    """主函数"""
    print("=" * 50)
    print("传奇2自动挂机脚本 - OCR版本")
    print("=" * 50)
    print()
    print("功能:")
    print("  - 使用OCR监测游戏画面")
    print(f"  - 检测画面内是否包含目标文字 '{Mir2AutoBot.target_text}'")
    print("  - 检测到目标文字时自动使用随机传送石")
    print()
    print("特性:")
    print("  - 支持中文OCR识别")
    print("  - 可配置检测间隔和冷却时间")
    print("  - 自动窗口检测和激活")
    print()
    print("控制:")
    print("  - F10: 停止挂机")
    print("  - Ctrl+C: 强制退出")
    print()
    print("=" * 50)
    print()

    # 创建机器人实例
    bot = Mir2AutoBot()

    # 设置快捷键
    keyboard.add_hotkey('F10', bot.stop)

    # 运行机器人
    bot.run()

    # 清理
    keyboard.unhook_all()


if __name__ == '__main__':
    main()
