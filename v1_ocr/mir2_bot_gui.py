# -*- coding: utf-8 -*-
"""
传奇2自动挂机脚本 - 图形界面版本
功能: 检测到画面内有目标文字"人物斩杀"时自动使用随机传送石
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import keyboard
import win32gui
import win32con
import win32ui
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
from dependency_manager import DependencyManager

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, 'mir2_bot.log')
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'bot_config.ini')

# 禁用pyautogui的安全检查
pyautogui.FAILSAFE = False


class Mir2AutoBot:
    """传奇2自动挂机机器人 - OCR监测版"""

    def __init__(self, config_file: str = None, log_callback=None, screenshot_mode: str = 'win32'):
        """
        初始化挂机机器人

        Args:
            config_file: 配置文件路径
            log_callback: 日志回调函数
            screenshot_mode: 截图模式 ('win32' 或 'pyautogui')
        """
        self.running = False
        self.paused = False
        self.log_callback = log_callback  # 先设置log_callback
        self.hwnd = None
        self.window_rect = None
        self.screenshot_mode = screenshot_mode  # 截图模式

        if config_file is None:
            config_file = CONFIG_FILE
        self.config = self._load_config(config_file)  # 然后加载配置

        # 监测相关
        self.screen = None

        # 玩家检测相关
        self.last_teleport_time = 0
        self.teleport_cooldown = 10  # 传送冷却时间(秒)
        self.player_detected_count = 0
        self.target_text = self.config.get('Detection', 'target_text', fallback='游戏斩杀')  # 从配置文件读取目标文字

        # 统计信息
        self.stats = {
            'players_detected': 0,
            'teleports_used': 0,
            'detection_runs': 0,
            'start_time': None
        }

        self._log("传奇2自动挂机机器人(OCR版本)初始化完成")

    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")

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
                'detection_top_percent': '20',
                'detection_bottom_percent': '60',
                'detection_left_percent': '5',
                'detection_right_percent': '95',
            }
        }

        # 读取配置文件
        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
            self._log(f"已加载配置文件: {config_file}")

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
            self._log(f"已创建默认配置文件: {config_file}")

        return config

    def find_game_window(self) -> bool:
        """查找游戏窗口"""
        window_title = self.config.get('Game', 'window_title', fallback='九五沉默')

        # 支持多个可能的窗口标题（按优先级排序）
        possible_titles = [
            window_title,  # 配置文件中的标题（九五沉默）
            '九五',  # 九五服务器
            'Legend of Mir2',  # 登录器窗口
            '传奇',  # 其他传奇游戏
        ]

        # 需要排除的窗口标题（避免误匹配GUI窗口）
        exclude_titles = [
            '传奇2自动挂机脚本',
            'Auto Bot',
            'GUI',
            '图形界面',
        ]

        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                
                # 先检查是否需要排除
                is_excluded = False
                for exclude_title in exclude_titles:
                    if exclude_title in title:
                        is_excluded = True
                        break
                
                if is_excluded:
                    return True  # 跳过这个窗口，继续查找
                
                # 检查标题是否匹配任何一个可能的标题
                for possible_title in possible_titles:
                    if possible_title.lower() in title.lower():
                        # 检查窗口是否有效（客户区大小不为0）
                        client_rect = win32gui.GetClientRect(hwnd)
                        client_width = client_rect[2] - client_rect[0]
                        client_height = client_rect[3] - client_rect[1]
                        
                        # 排除客户区为0的窗口（隐藏或最小化的窗口）
                        if client_width > 0 and client_height > 0:
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
            self._log(f"找到游戏窗口: {game_title}")
            self._log(f"窗口位置: {self.window_rect}")
            self._log(f"客户区大小: {self.client_rect}")
            self._log(f"客户区偏移: {self.client_offset}")
            return True
        else:
            self._log(f"未找到游戏窗口", "ERROR")
            self._log(f"尝试的标题: {possible_titles}", "INFO")
            self._log("提示: 请确保游戏窗口已打开且未最小化", "INFO")
            return False

    def activate_game_window(self) -> bool:
        """激活游戏窗口（已禁用）"""
        # 不再激活窗口，直接返回True
        # 截图和传送都不需要窗口在前台
        return True

    def capture_game_screen(self) -> Optional[np.ndarray]:
        """
        捕获游戏窗口画面

        Returns:
            游戏画面(numpy数组)
        """
        if self.screenshot_mode == 'pyautogui':
            return self._capture_with_pyautogui()
        else:
            return self._capture_with_win32()

    def _capture_with_pyautogui(self) -> Optional[np.ndarray]:
        """
        使用PyAutoGUI截取游戏窗口（需要窗口在最前端）

        Returns:
            游戏画面(numpy数组)
        """
        if not self.hwnd:
            return None

        try:
            # 获取客户区屏幕坐标
            client_left, client_top = win32gui.ClientToScreen(self.hwnd, (0, 0))
            client_rect = win32gui.GetClientRect(self.hwnd)
            client_width = client_rect[2] - client_rect[0]
            client_height = client_rect[3] - client_rect[1]

            # 使用pyautogui截图
            screenshot = pyautogui.screenshot(region=(client_left, client_top, client_width, client_height))

            # 转换为OpenCV格式
            image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            return image

        except Exception as e:
            self._log(f"PyAutoGUI截图失败: {e}", "ERROR")
            return None

    def _capture_with_win32(self) -> Optional[np.ndarray]:
        """
        使用Win32 API截取游戏窗口（即使窗口被遮挡也能截取，但可能有黑边）

        Returns:
            游戏画面(numpy数组)
        """
        if not self.hwnd:
            return None

        try:
            # 每次都重新获取窗口位置，确保跟随窗口移动
            self.window_rect = win32gui.GetWindowRect(self.hwnd)

            # 获取客户区矩形
            self.client_rect = win32gui.GetClientRect(self.hwnd)

            # 客户区大小
            client_width = self.client_rect[2] - self.client_rect[0]
            client_height = self.client_rect[3] - self.client_rect[1]

            # 使用Win32 API截取窗口（即使被遮挡也能截取）
            # 获取窗口设备上下文
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # 创建位图对象（使用客户区大小）
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, client_width, client_height)
            saveDC.SelectObject(saveBitMap)

            # 计算客户区相对于窗口的偏移
            client_left, client_top = win32gui.ClientToScreen(self.hwnd, (0, 0))
            window_left, window_top = self.window_rect[0], self.window_rect[1]
            offset_x = client_left - window_left
            offset_y = client_top - window_top

            # 截取客户区（从偏移位置开始）
            result = saveDC.BitBlt((0, 0), (client_width, client_height), mfcDC, (offset_x, offset_y), win32con.SRCCOPY)

            # 转换为OpenCV格式
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwndDC)

            # 转换为numpy数组
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (client_height, client_width, 4)

            # 转换为BGR格式
            image = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            return image

        except Exception as e:
            self._log(f"Win32截图失败: {e}", "ERROR")
            return None

    def _load_template(self) -> Optional[np.ndarray]:
        """加载目标模板图片"""
        template_path = os.path.join(SCRIPT_DIR, 'target', '1.png')
        if os.path.exists(template_path):
            template = cv2.imread(template_path)
            if template is not None:
                self._log(f"已加载模板图片: {template_path}")
                return template
        return None

    def detect_players_opencv(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        使用模板匹配检测画面中是否包含目标文字"游戏斩杀"

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

            # 创建调试目录
            debug_enabled = self.config.get('Detection', 'debug', fallback='false') == 'true'
            if debug_enabled:
                debug_dir = os.path.join(SCRIPT_DIR, 'debug')
                os.makedirs(debug_dir, exist_ok=True)

                # 保存完整截图
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(os.path.join(debug_dir, f'00_full_screen_{timestamp}.jpg'), image)

                # 保存检测区域
                cv2.imwrite(os.path.join(debug_dir, f'01_detection_region_{timestamp}.jpg'), detection_region)

            # ===== 模板匹配检测 =====
            target_rects = []

            # 加载模板
            template = self._load_template()
            if template is not None:
                template_h, template_w = template.shape[:2]

                # 转换为灰度图进行模板匹配
                gray_region = cv2.cvtColor(detection_region, cv2.COLOR_BGR2GRAY)
                gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

                # 模板匹配
                result = cv2.matchTemplate(gray_region, gray_template, cv2.TM_CCOEFF_NORMED)

                # 获取匹配阈值
                threshold = self.config.getfloat('Detection', 'confidence_threshold', fallback=0.75)

                # 找到所有匹配位置
                locations = np.where(result >= threshold)

                # 合并重叠的匹配结果
                matches = []
                for pt in zip(*locations[::-1]):  # (x, y) 格式
                    confidence = result[pt[1], pt[0]]
                    matches.append((pt[0], pt[1], template_w, template_h, confidence))

                # 非极大值抑制，合并重叠的检测框
                if matches:
                    # 按置信度排序
                    matches.sort(key=lambda x: x[4], reverse=True)

                    # 合并重叠的框
                    keep = []
                    for m in matches:
                        x1, y1, w, h, conf = m
                        overlap = False
                        for k in keep:
                            kx1, ky1, kw, kh, kconf = k
                            # 计算重叠
                            x_overlap = max(0, min(x1 + w, kx1 + kw) - max(x1, kx1))
                            y_overlap = max(0, min(y1 + h, ky1 + kh) - max(y1, ky1))
                            overlap_area = x_overlap * y_overlap
                            area1 = w * h
                            area2 = kw * kh

                            if overlap_area > 0.5 * min(area1, area2):
                                overlap = True
                                break

                        if not overlap:
                            keep.append(m)

                    # 转换为原图坐标
                    for x, y, w, h, conf in keep:
                        orig_x = x + left_x
                        orig_y = y + top_y
                        target_rects.append((orig_x, orig_y, w, h))
                        self._log(f"模板匹配检测到目标在位置 ({orig_x}, {orig_y}), 置信度: {conf:.2f}")

            # 如果模板匹配没有找到，尝试OCR检测作为备选
            if not target_rects:
                # 图像预处理 - 简化流程，避免过度处理
                # 1. 转换为灰度图
                gray = cv2.cvtColor(detection_region, cv2.COLOR_BGR2GRAY)

                # 2. 轻微增强对比度
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)

                # 3. 放大图像 - 提高OCR识别率
                scale_factor = 2
                enhanced_scaled = cv2.resize(enhanced, None, fx=scale_factor, fy=scale_factor,
                                             interpolation=cv2.INTER_CUBIC)

                # 保存预处理结果
                if debug_enabled:
                    cv2.imwrite(os.path.join(debug_dir, f'02_preprocessed_{timestamp}.jpg'), enhanced_scaled)

                # 将预处理后的图像转换为PIL图像
                pil_image = Image.fromarray(enhanced_scaled)

                # 使用pytesseract进行OCR识别（支持中文）
                # 尝试多种PSM模式以提高识别率
                text_data_list = []
                psm_modes = [6, 7, 11, 12, 13]  # 尝试多种模式

                for psm in psm_modes:
                    try:
                        text_data = pytesseract.image_to_data(
                            pil_image,
                            lang='chi_sim',
                            config=f'--psm {psm} --oem 3 --dpi 300',
                            output_type=pytesseract.Output.DICT
                        )
                        text_data_list.append(text_data)
                    except Exception as e:
                        self._log(f"PSM {psm} 模式识别失败: {e}", "WARNING")
                        continue

                # 查找目标文字（合并所有模式的结果）
                all_detected_texts = []
                all_text_rects = []  # 存储所有识别到的文字矩形

                for text_data in text_data_list:
                    n_boxes = len(text_data['text'])

                    for i in range(n_boxes):
                        text = text_data['text'][i].strip()
                        conf = int(text_data['conf'][i])

                        # 只考虑置信度足够高的识别结果（降低阈值到10）
                        if conf > 10 and text:
                            x, y, w, h = text_data['left'][i], text_data['top'][i], text_data['width'][i], text_data['height'][i]

                            # 调整坐标（因为图像被放大了2倍，需要缩小回来）
                            x = int(x / scale_factor)
                            y = int(y / scale_factor)
                            w = int(w / scale_factor)
                            h = int(h / scale_factor)

                            # 调整坐标（因为我们只检测了裁剪区域）
                            x += left_x
                            y += top_y

                            # 保存所有识别到的文字
                            all_text_rects.append((x, y, w, h, text, conf))
                            all_detected_texts.append(f"'{text}' (conf: {conf})")

                            # 检查是否包含目标文字（模糊匹配）
                            # 支持部分匹配和相似字符
                            is_match = False

                            # 完全匹配
                            if text == self.target_text:
                                is_match = True
                            # 包含目标文字
                            elif self.target_text in text:
                                is_match = True
                            # 目标文字包含识别结果（可能是部分识别）
                            elif text in self.target_text and len(text) >= 2:
                                is_match = True
                            # 相似字符匹配（处理OCR常见错误）
                            else:
                                # 替换常见OCR错误字符
                                text_normalized = text.replace('斩', '斩').replace('杀', '杀').replace('游', '游').replace('戏', '戏')
                                target_normalized = self.target_text.replace('斩', '斩').replace('杀', '杀').replace('游', '游').replace('戏', '戏')

                                if text_normalized == target_normalized or target_normalized in text_normalized:
                                    is_match = True

                            if is_match:
                                target_rects.append((x, y, w, h))
                                self._log(f"OCR检测到目标文字 '{text}' 在位置 ({x}, {y}), 置信度: {conf}")

                # 调试信息：显示所有识别到的文字
                if all_detected_texts:
                    self._log(f"本次OCR识别到的文字: {', '.join(all_detected_texts[:10])}")  # 只显示前10个

            # 绘制检测框和检测范围
            if debug_enabled:
                debug_img = image.copy()

                # 绘制检测范围（黄色半透明矩形）
                overlay = debug_img.copy()
                cv2.rectangle(overlay, (left_x, top_y), (right_x, bottom_y), (0, 255, 255), -1)
                cv2.addWeighted(overlay, 0.2, debug_img, 0.8, 0, debug_img)

                # 绘制检测范围边框（黄色实线）
                cv2.rectangle(debug_img, (left_x, top_y), (right_x, bottom_y), (0, 255, 255), 2)

                # 绘制所有识别到的文字（蓝色框）- 仅在debug模式下有OCR结果时
                if debug_enabled and 'all_text_rects' in dir():
                    for x, y, w, h, text, conf in all_text_rects:
                        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (255, 0, 0), 1)
                        # 在框上方显示文字和置信度
                    label = f"{text} ({conf})"
                    cv2.putText(debug_img, label, (x, y - 2),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)

                # 绘制检测到的目标文字（绿色框，更粗）
                for idx, (x, y, w, h) in enumerate(target_rects):
                    cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    # 在框左上角显示序号
                    cv2.putText(debug_img, f"TARGET {idx+1}", (x, y - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # 添加检测范围说明文字
                cv2.putText(debug_img, f"Detection: {left_x},{top_y} to {right_x},{bottom_y}",
                           (10, top_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                cv2.putText(debug_img, f"Target: {len(target_rects)}",
                           (10, bottom_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # 保存检测结果
                cv2.imwrite(os.path.join(debug_dir, f'03_detection_result_{timestamp}.jpg'), debug_img)

            return target_rects

        except Exception as e:
            self._log(f"检测目标文字失败: {e}", "ERROR")
            self._log(f"请确保已安装Tesseract OCR和中文语言包", "INFO")
            import traceback
            self._log(f"详细错误: {traceback.format_exc()}", "ERROR")
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
            self._log(f"检测到目标文字 '{self.target_text}' {len(target_rects)} 次")

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
                self._log(f"检测到 {len(target_rects)} 次（需要两次及以上才传送）", "INFO")
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
            self._log(f"传送冷却中，剩余 {remaining} 秒")
            return

        # 获取传送快捷键
        teleport_key = self.config.get('Teleport', 'teleport_key', fallback='2')

        try:
            # 激活游戏窗口
            self.activate_game_window()

            # 按下传送快捷键
            keyboard.press(teleport_key)
            time.sleep(0.1)
            keyboard.release(teleport_key)

            self.last_teleport_time = current_time
            self.stats['teleports_used'] += 1
            self._log(f"已使用随机传送石 (快捷键: {teleport_key})")

        except Exception as e:
            self._log(f"使用传送石失败: {e}", "ERROR")

    def update_stats(self):
        """更新统计信息"""
        if not self.stats['start_time']:
            self.stats['start_time'] = datetime.now()

        # 每分钟打印一次统计信息
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            if elapsed > 0 and int(elapsed) % 60 == 0:
                self._log(
                    f"运行时间: {int(elapsed // 60)}分钟 | "
                    f"检测次数: {self.stats['detection_runs']} | "
                    f"检测到目标: {self.stats['players_detected']} | "
                    f"使用传送: {self.stats['teleports_used']}"
                )

    def run(self):
        """运行挂机脚本"""
        self._log("开始运行挂机脚本...")
        self._log("使用OCR进行画面监测")

        # 查找游戏窗口
        if not self.find_game_window():
            self._log("无法找到游戏窗口，退出", "ERROR")
            return

        # 激活游戏窗口
        self.activate_game_window()

        self.running = True
        self._log("挂机脚本已启动")
        self._log(f"功能: 检测到画面内有目标文字 '{self.target_text}' 时自动使用随机传送石")

        try:
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue

                # 捕获游戏画面
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

        except Exception as e:
            self._log(f"运行出错: {e}", "ERROR")
        finally:
            self.stop()

    def stop(self):
        """停止挂机脚本"""
        self.running = False
        self._log("挂机脚本已停止")

        # 打印最终统计
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            self._log("=" * 50)
            self._log("挂机统计:")
            self._log(f"运行时间: {int(elapsed // 60)} 分钟 {int(elapsed % 60)} 秒")
            self._log(f"检测次数: {self.stats['detection_runs']}")
            self._log(f"检测到目标: {self.stats['players_detected']}")
            self._log(f"使用传送: {self.stats['teleports_used']}")
            self._log("=" * 50)

    def pause(self):
        """暂停挂机脚本"""
        self.paused = True
        self._log("挂机脚本已暂停")

    def resume(self):
        """恢复挂机脚本"""
        self.paused = False
        self._log("挂机脚本已恢复")


class BotGUI:
    """挂机脚本图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("传奇2自动挂机脚本 - 图形界面")
        self.root.geometry("1100x800")

        self.bot = None
        self.bot_thread = None
        self.dep_manager = DependencyManager(log_callback=self._log)
        self.packages_status = None

        # 设置变量
        self.target_text_var = tk.StringVar(value='游戏斩杀')  # 默认值，会在加载配置后更新
        self.teleport_key_var = tk.StringVar(value='2')
        self.detection_interval_var = tk.DoubleVar(value=0.3)
        self.cooldown_var = tk.DoubleVar(value=4.0)
        self.top_percent_var = tk.IntVar(value=20)
        self.bottom_percent_var = tk.IntVar(value=60)
        self.left_percent_var = tk.IntVar(value=5)
        self.right_percent_var = tk.IntVar(value=95)
        self.debug_enabled_var = tk.BooleanVar(value=True)
        self.screenshot_mode_var = tk.StringVar(value='win32')  # 'win32' 或 'pyautogui'

        # 当前截图（用于可视化检测范围）
        self.current_screenshot = None
        self.detection_preview_label = None

        self._create_widgets()

    def _create_widgets(self):
        """创建界面组件"""
        # 主框架 - 使用PanedWindow分割左右
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧面板 - 控制和日志
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=1)

        # 右侧面板 - 设置和预览
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)

        # ===== 左侧面板 =====
        # 标题
        title_label = ttk.Label(
            left_frame,
            text="传奇2自动挂机脚本 - OCR版本",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 主要功能按钮
        main_button_frame = ttk.LabelFrame(left_frame, text="主要功能", padding="5")
        main_button_frame.pack(fill=tk.X, pady=(0, 10))

        button_frame = ttk.Frame(main_button_frame)
        button_frame.pack(fill=tk.X)

        self.start_button = ttk.Button(button_frame, text="启动", command=self.start_bot, width=12)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.pause_button = ttk.Button(button_frame, text="暂停", command=self.pause_bot, width=12, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_bot, width=12, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Separator(button_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.test_button = ttk.Button(button_frame, text="测试窗口检测", command=self.test_window, width=12)
        self.test_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.screenshot_button = ttk.Button(button_frame, text="测试截图", command=self.test_screenshot, width=12)
        self.screenshot_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 依赖管理按钮
        dep_button_frame = ttk.LabelFrame(left_frame, text="依赖管理", padding="5")
        dep_button_frame.pack(fill=tk.X, pady=(0, 10))

        dep_frame = ttk.Frame(dep_button_frame)
        dep_frame.pack(fill=tk.X)

        self.check_deps_button = ttk.Button(dep_frame, text="检查依赖", command=self.check_dependencies, width=12)
        self.check_deps_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.install_deps_button = ttk.Button(dep_frame, text="安装缺失依赖", command=self.install_dependencies, width=15, state=tk.DISABLED)
        self.install_deps_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.update_deps_button = ttk.Button(dep_frame, text="更新所有依赖", command=self.update_dependencies, width=12)
        self.update_deps_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.check_tesseract_button = ttk.Button(dep_frame, text="检查Tesseract", command=self.check_tesseract, width=12)
        self.check_tesseract_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 日志输出
        log_label = ttk.Label(left_frame, text="运行日志:")
        log_label.pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(left_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(left_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X)

        # ===== 右侧面板 =====
        # 标题
        settings_title = ttk.Label(
            right_frame,
            text="设置",
            font=("Arial", 14, "bold")
        )
        settings_title.pack(pady=(0, 10))

        # 设置框架
        settings_frame = ttk.LabelFrame(right_frame, text="检测设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # 检测关键词
        ttk.Label(settings_frame, text="检测关键词:").grid(row=0, column=0, sticky=tk.W, pady=5)
        target_text_entry = ttk.Entry(settings_frame, textvariable=self.target_text_var, width=20)
        target_text_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 传送按键
        ttk.Label(settings_frame, text="传送按键:").grid(row=1, column=0, sticky=tk.W, pady=5)
        teleport_key_entry = ttk.Entry(settings_frame, textvariable=self.teleport_key_var, width=20)
        teleport_key_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 检测间隔
        ttk.Label(settings_frame, text="检测间隔(秒):").grid(row=2, column=0, sticky=tk.W, pady=5)
        detection_interval_spin = ttk.Spinbox(settings_frame, from_=0.1, to=5.0, increment=0.1, textvariable=self.detection_interval_var, width=18)
        detection_interval_spin.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 传送冷却
        ttk.Label(settings_frame, text="传送冷却(秒):").grid(row=3, column=0, sticky=tk.W, pady=5)
        cooldown_spin = ttk.Spinbox(settings_frame, from_=1.0, to=60.0, increment=1.0, textvariable=self.cooldown_var, width=18)
        cooldown_spin.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 检测范围
        range_frame = ttk.LabelFrame(right_frame, text="检测范围 (%)", padding="10")
        range_frame.pack(fill=tk.X, pady=(0, 10))

        # 上边界
        ttk.Label(range_frame, text="上边界:").grid(row=0, column=0, sticky=tk.W, pady=5)
        top_spin = ttk.Spinbox(range_frame, from_=0, to=100, increment=5, textvariable=self.top_percent_var, width=18, command=self.update_detection_preview)
        top_spin.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 下边界
        ttk.Label(range_frame, text="下边界:").grid(row=1, column=0, sticky=tk.W, pady=5)
        bottom_spin = ttk.Spinbox(range_frame, from_=0, to=100, increment=5, textvariable=self.bottom_percent_var, width=18, command=self.update_detection_preview)
        bottom_spin.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 左边界
        ttk.Label(range_frame, text="左边界:").grid(row=2, column=0, sticky=tk.W, pady=5)
        left_spin = ttk.Spinbox(range_frame, from_=0, to=100, increment=5, textvariable=self.left_percent_var, width=18, command=self.update_detection_preview)
        left_spin.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 右边界
        ttk.Label(range_frame, text="右边界:").grid(row=3, column=0, sticky=tk.W, pady=5)
        right_spin = ttk.Spinbox(range_frame, from_=0, to=100, increment=5, textvariable=self.right_percent_var, width=18, command=self.update_detection_preview)
        right_spin.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))

        # 调试模式
        debug_check = ttk.Checkbutton(range_frame, text="启用调试模式", variable=self.debug_enabled_var)
        debug_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10)

        # 截图模式选择
        screenshot_mode_frame = ttk.LabelFrame(right_frame, text="截图模式", padding="10")
        screenshot_mode_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Radiobutton(
            screenshot_mode_frame,
            text="Win32 API (后台截图，可能有黑边)",
            variable=self.screenshot_mode_var,
            value="win32"
        ).pack(anchor=tk.W, pady=2)

        ttk.Radiobutton(
            screenshot_mode_frame,
            text="PyAutoGUI (前台截图，窗口需在最前)",
            variable=self.screenshot_mode_var,
            value="pyautogui"
        ).pack(anchor=tk.W, pady=2)

        # 应用设置按钮
        apply_button = ttk.Button(range_frame, text="应用设置", command=self.apply_settings, width=20)
        apply_button.grid(row=5, column=0, columnspan=2, pady=10)

        # 检测范围预览
        preview_frame = ttk.LabelFrame(right_frame, text="检测范围预览", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        preview_label = ttk.Label(preview_frame, text="点击'测试截图'查看检测范围")
        preview_label.pack(expand=True)

        self.detection_preview_label = preview_label

        # 配置日志文本颜色
        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")
        self.log_text.tag_config("SUCCESS", foreground="green")

        # 添加初始日志
        self._log("传奇2自动挂机脚本 - 图形界面版本")
        self._log("=" * 50)
        self._log("功能:")
        self._log("  - 使用OCR监测游戏画面")
        self._log(f"  - 检测画面内是否包含目标文字 '游戏斩杀'")
        self._log("  - 检测到目标文字时自动使用随机传送石")
        self._log("")
        self._log("特性:")
        self._log("  - 支持中文OCR识别")
        self._log("  - 自动跟随窗口移动")
        self._log("  - 窗口被遮挡时仍能检测")
        self._log("  - 可配置检测间隔和冷却时间")
        self._log("  - 自动窗口检测和激活")
        self._log("  - 依赖检测、安装和更新")
        self._log("=" * 50)
        self._log("")

        # 自动检查依赖
        self.root.after(1000, self.auto_check_dependencies)
        
        # 加载配置文件中的设置
        self.root.after(1500, self.load_settings_from_config)

    def _log(self, message: str, level: str = "INFO"):
        """添加日志到文本框"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] [{level}] {message}\n"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, full_message, level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_bot(self):
        """启动挂机脚本"""
        if self.bot is not None and self.bot.running:
            messagebox.showwarning("警告", "挂机脚本已在运行中")
            return

        self._log("正在启动挂机脚本...")
        self.status_var.set("正在启动...")

        # 获取截图模式
        screenshot_mode = self.screenshot_mode_var.get()
        self._log(f"截图模式: {screenshot_mode}")

        # 创建机器人实例
        self.bot = Mir2AutoBot(log_callback=self._log, screenshot_mode=screenshot_mode)

        # 在新线程中运行
        self.bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        self.bot_thread.start()

        # 更新按钮状态
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)

        self.status_var.set("运行中")

    def pause_bot(self):
        """暂停挂机脚本"""
        if self.bot is None or not self.bot.running:
            return

        if self.bot.paused:
            self.bot.resume()
            self.pause_button.config(text="暂停")
            self.status_var.set("运行中")
        else:
            self.bot.pause()
            self.pause_button.config(text="恢复")
            self.status_var.set("已暂停")

    def stop_bot(self):
        """停止挂机脚本"""
        if self.bot is None:
            return

        self._log("正在停止挂机脚本...")
        self.status_var.set("正在停止...")

        self.bot.stop()

        # 等待线程结束
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=2)

        self.bot = None
        self.bot_thread = None

        # 更新按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="暂停")
        self.stop_button.config(state=tk.DISABLED)

        self.status_var.set("已停止")

    def test_window(self):
        """测试窗口检测"""
        self._log("正在测试窗口检测...")

        # 创建临时机器人实例
        test_bot = Mir2AutoBot(log_callback=self._log)

        if test_bot.find_game_window():
            self._log(f"窗口检测成功！")
            self._log(f"窗口句柄: {test_bot.hwnd}")
            self._log(f"窗口位置: {test_bot.window_rect}")
        else:
            self._log("窗口检测失败，请确保游戏窗口已打开", "ERROR")

    def test_screenshot(self):
        """测试截图功能"""
        self._log("正在测试截图功能...")

        # 获取截图模式
        screenshot_mode = self.screenshot_mode_var.get()
        self._log(f"使用截图模式: {screenshot_mode}")

        # 创建临时机器人实例
        test_bot = Mir2AutoBot(log_callback=self._log, screenshot_mode=screenshot_mode)

        # 查找窗口
        if not test_bot.find_game_window():
            self._log("无法找到游戏窗口", "ERROR")
            return

        # 截图
        image = test_bot.capture_game_screen()

        if image is not None:
            self._log(f"截图成功！图像大小: {image.shape}")

            # 保存当前截图用于预览
            self.current_screenshot = image

            # 保存截图
            debug_dir = os.path.join(SCRIPT_DIR, 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(debug_dir, f'test_screenshot_{timestamp}.jpg')
            cv2.imwrite(screenshot_path, image)

            self._log(f"截图已保存到: {screenshot_path}")

            # 更新检测范围预览
            self.update_detection_preview()
        else:
            self._log("截图失败", "ERROR")

    def apply_settings(self):
        """应用设置"""
        self._log("正在应用设置...")

        try:
            # 更新目标文字
            new_target_text = self.target_text_var.get()
            self._log(f"检测关键词已更新为: {new_target_text}")

            # 更新配置文件
            config = configparser.ConfigParser()
            
            # 先读取现有配置
            try:
                if os.path.exists(CONFIG_FILE):
                    config.read(CONFIG_FILE, encoding='utf-8')
                    self._log(f"读取现有配置: {CONFIG_FILE}")
            except Exception as e:
                self._log(f"读取配置失败: {e}，将创建新配置")
                config = configparser.ConfigParser()

            # 更新检测设置
            if not config.has_section('Detection'):
                config.add_section('Detection')

            config.set('Detection', 'enabled', 'true')
            config.set('Detection', 'detection_interval', str(self.detection_interval_var.get()))
            config.set('Detection', 'debug', 'true' if self.debug_enabled_var.get() else 'false')
            config.set('Detection', 'target_text', new_target_text)

            # 更新传送设置
            if not config.has_section('Teleport'):
                config.add_section('Teleport')

            config.set('Teleport', 'enabled', 'true')
            config.set('Teleport', 'teleport_key', self.teleport_key_var.get())
            config.set('Teleport', 'cooldown', str(self.cooldown_var.get()))

            # 更新高级设置
            if not config.has_section('Advanced'):
                config.add_section('Advanced')

            config.set('Advanced', 'use_opencv', 'true')
            config.set('Advanced', 'use_preprocessing', 'true')
            config.set('Advanced', 'detection_top_percent', str(self.top_percent_var.get()))
            config.set('Advanced', 'detection_bottom_percent', str(self.bottom_percent_var.get()))
            config.set('Advanced', 'detection_left_percent', str(self.left_percent_var.get()))
            config.set('Advanced', 'detection_right_percent', str(self.right_percent_var.get()))

            # 直接保存配置（不使用临时文件）
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    config.write(f)
                self._log(f"✓ 配置已保存到: {CONFIG_FILE}", "SUCCESS")
            except PermissionError:
                self._log(f"❌ 权限不足，无法写入配置文件", "ERROR")
                messagebox.showerror("错误", "权限不足，无法保存配置文件。\n请以管理员身份运行或检查文件权限。")
                return
            except Exception as e:
                self._log(f"❌ 保存配置失败: {e}", "ERROR")
                messagebox.showerror("错误", f"保存配置失败: {e}")
                return

            # 验证配置是否保存成功
            if os.path.exists(CONFIG_FILE):
                self._log("✓ 配置文件验证成功", "SUCCESS")
            else:
                self._log("⚠ 配置文件未找到，可能保存失败", "WARNING")

            # 如果机器人正在运行，立即应用新配置
            if self.bot is not None and self.bot.running:
                self._log("正在重新加载配置...")
                # 重新加载配置
                self.bot.config = self.bot._load_config(CONFIG_FILE)
                # 更新目标文字
                self.bot.target_text = new_target_text
                self._log("✓ 配置已实时应用", "SUCCESS")
                messagebox.showinfo("成功", "设置已保存并实时应用！")
            else:
                messagebox.showinfo("成功", "设置已保存！")

        except Exception as e:
            self._log(f"❌ 应用设置失败: {e}", "ERROR")
            messagebox.showerror("错误", f"应用设置失败: {e}")

    def update_detection_preview(self):
        """更新检测范围预览"""
        if self.current_screenshot is None:
            return

        try:
            # 复制图像
            preview_img = self.current_screenshot.copy()
            height, width = preview_img.shape[:2]

            # 获取检测范围
            top_percent = self.top_percent_var.get()
            bottom_percent = self.bottom_percent_var.get()
            left_percent = self.left_percent_var.get()
            right_percent = self.right_percent_var.get()

            # 计算检测区域
            top_y = int(height * top_percent / 100)
            bottom_y = int(height * bottom_percent / 100)
            left_x = int(width * left_percent / 100)
            right_x = int(width * right_percent / 100)

            # 绘制检测范围（黄色半透明矩形）
            overlay = preview_img.copy()
            cv2.rectangle(overlay, (left_x, top_y), (right_x, bottom_y), (0, 255, 255), -1)
            cv2.addWeighted(overlay, 0.3, preview_img, 0.7, 0, preview_img)

            # 绘制检测范围边框（黄色实线）
            cv2.rectangle(preview_img, (left_x, top_y), (right_x, bottom_y), (0, 255, 255), 2)

            # 添加文字说明
            cv2.putText(preview_img, f"Detection: {left_x},{top_y} to {right_x},{bottom_y}",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

            # 缩小图像以适应预览区域（保持宽高比）
            max_width = 400
            max_height = 300
            
            # 计算缩放比例
            scale_w = max_width / width
            scale_h = max_height / height
            scale = min(scale_w, scale_h)  # 选择较小的缩放比例
            
            if scale < 1:
                new_width = int(width * scale)
                new_height = int(height * scale)
                preview_img = cv2.resize(preview_img, (new_width, new_height))

            # 转换为PIL图像
            pil_image = Image.fromarray(cv2.cvtColor(preview_img, cv2.COLOR_BGR2RGB))

            # 转换为PhotoImage
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(pil_image)

            # 更新预览标签
            self.detection_preview_label.configure(text="")
            self.detection_preview_label.configure(image=photo)
            self.detection_preview_label.image = photo  # 保持引用

        except Exception as e:
            self._log(f"更新预览失败: {e}")

        except Exception as e:
            self._log(f"更新预览失败: {e}", "ERROR")

    def clear_debug_folder(self):
        """清空debug文件夹"""
        debug_dir = os.path.join(SCRIPT_DIR, 'debug')

        if not os.path.exists(debug_dir):
            return

        try:
            # 删除所有jpg文件
            for filename in os.listdir(debug_dir):
                if filename.endswith('.jpg'):
                    file_path = os.path.join(debug_dir, filename)
                    os.remove(file_path)

            self._log(f"已清空debug文件夹", "INFO")
        except Exception as e:
            self._log(f"清空debug文件夹失败: {e}", "ERROR")

    def auto_check_dependencies(self):
        """自动检查依赖"""
        self._log("正在自动检查依赖...")
        self.check_dependencies()

    def load_settings_from_config(self):
        """从配置文件加载设置到GUI"""
        try:
            if os.path.exists(CONFIG_FILE):
                config = configparser.ConfigParser()
                config.read(CONFIG_FILE, encoding='utf-8')
                
                # 加载目标文字
                if config.has_option('Detection', 'target_text'):
                    self.target_text_var.set(config.get('Detection', 'target_text'))
                
                # 加载检测间隔
                if config.has_option('Detection', 'detection_interval'):
                    self.detection_interval_var.set(config.getfloat('Detection', 'detection_interval'))
                
                # 加载调试模式
                if config.has_option('Detection', 'debug'):
                    self.debug_enabled_var.set(config.getboolean('Detection', 'debug'))
                
                # 加载传送按键
                if config.has_option('Teleport', 'teleport_key'):
                    self.teleport_key_var.set(config.get('Teleport', 'teleport_key'))
                
                # 加载传送冷却
                if config.has_option('Teleport', 'cooldown'):
                    self.cooldown_var.set(config.getfloat('Teleport', 'cooldown'))
                
                # 加载检测范围
                if config.has_option('Advanced', 'detection_top_percent'):
                    self.top_percent_var.set(config.getint('Advanced', 'detection_top_percent'))
                
                if config.has_option('Advanced', 'detection_bottom_percent'):
                    self.bottom_percent_var.set(config.getint('Advanced', 'detection_bottom_percent'))
                
                if config.has_option('Advanced', 'detection_left_percent'):
                    self.left_percent_var.set(config.getint('Advanced', 'detection_left_percent'))
                
                if config.has_option('Advanced', 'detection_right_percent'):
                    self.right_percent_var.set(config.getint('Advanced', 'detection_right_percent'))
                
                self._log("✓ 已从配置文件加载设置", "SUCCESS")
        except Exception as e:
            self._log(f"加载配置文件设置失败: {e}", "WARNING")

    def check_dependencies(self):
        """检查依赖包"""
        self._log("=" * 50)
        self._log("检查依赖包...")
        self._log("=" * 50)

        self.packages_status = self.dep_manager.check_all_packages()

        self._log("\n依赖包状态:")
        self._log("-" * 50)

        missing_count = 0
        for name, info in self.packages_status.items():
            status = "✓" if info['installed'] else "✗"
            version = info['version'] if info['installed'] else "未安装"
            required = "必需" if info.get('required', False) else "可选"
            self._log(f"{status} {name:20s} {version:15s} ({required}) - {info['description']}")

            if not info['installed'] and info.get('required', False):
                missing_count += 1

        self._log("-" * 50)

        if missing_count > 0:
            self._log(f"发现 {missing_count} 个缺失的必需依赖包", "WARNING")
            self.install_deps_button.config(state=tk.NORMAL)
        else:
            self._log("所有必需的依赖包都已安装", "SUCCESS")
            self.install_deps_button.config(state=tk.DISABLED)

        # 检查pip版本
        pip_version = self.dep_manager.get_pip_version()
        self._log(f"\n{pip_version}")

        self._log("=" * 50)

    def install_dependencies(self):
        """安装缺失的依赖包"""
        if self.packages_status is None:
            self.check_dependencies()
            return

        if not messagebox.askyesno("确认", "确定要安装缺失的依赖包吗？\n这可能需要几分钟时间。"):
            return

        self._log("=" * 50)
        self._log("开始安装缺失的依赖包...")
        self._log("=" * 50)

        success_count = self.dep_manager.install_all_missing(self.packages_status)

        self._log("=" * 50)
        if success_count > 0:
            self._log(f"安装完成！成功安装 {success_count} 个包", "SUCCESS")
            messagebox.showinfo("安装完成", f"成功安装 {success_count} 个依赖包！")
        else:
            self._log("没有需要安装的包", "WARNING")
        self._log("=" * 50)

        # 重新检查依赖
        self.check_dependencies()

    def update_dependencies(self):
        """更新所有依赖包"""
        if not messagebox.askyesno("确认", "确定要更新所有依赖包吗？\n这可能需要几分钟时间。"):
            return

        self._log("=" * 50)
        self._log("开始更新所有依赖包...")
        self._log("=" * 50)

        if self.packages_status is None:
            self.packages_status = self.dep_manager.check_all_packages()

        success_count = self.dep_manager.update_all_packages(self.packages_status)

        self._log("=" * 50)
        if success_count > 0:
            self._log(f"更新完成！成功更新 {success_count} 个包", "SUCCESS")
            messagebox.showinfo("更新完成", f"成功更新 {success_count} 个依赖包！")
        else:
            self._log("没有需要更新的包", "WARNING")
        self._log("=" * 50)

        # 重新检查依赖
        self.check_dependencies()

    def check_tesseract(self):
        """检查Tesseract OCR"""
        self._log("=" * 50)
        self._log("检查Tesseract OCR...")
        self._log("=" * 50)

        # 检查Tesseract是否安装
        installed, version = self.dep_manager.check_tesseract()

        if installed:
            self._log(f"✓ Tesseract OCR已安装: {version}", "SUCCESS")

            # 检查语言包
            has_chinese, languages = self.dep_manager.check_tesseract_languages()

            if has_chinese:
                self._log(f"✓ 中文简体语言包已安装", "SUCCESS")
            else:
                self._log(f"✗ 中文简体语言包未安装", "WARNING")
                self._log(f"已安装的语言包: {', '.join(languages)}")
                self._log("请重新安装Tesseract OCR并勾选'中文简体'语言包", "WARNING")
        else:
            self._log(f"✗ Tesseract OCR未安装: {version}", "ERROR")
            self._log("请从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装", "WARNING")

        self._log("=" * 50)

    def on_closing(self):
        """窗口关闭事件"""
        if self.bot is not None and self.bot.running:
            if messagebox.askokcancel("退出", "挂机脚本正在运行，确定要退出吗？"):
                self.stop_bot()
                self._cleanup_and_exit()
        else:
            self._cleanup_and_exit()

    def _cleanup_and_exit(self):
        """清理并退出"""
        # 清空debug文件夹
        self.clear_debug_folder()

        # 销毁窗口
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = BotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()
