# -*- coding: utf-8 -*-
"""
传奇2自动挂机脚本 V2 - 多窗口GUI版本
功能: 同时监控多个游戏窗口，各自独立检测和传送
修复: 后台截图、独立统计、多线程响应
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
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
from PIL import Image, ImageTk
import ctypes

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, 'mir2_bot_v2.log')
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'bot_config_v2.ini')


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
        self.enabled = True  # 是否监控此窗口

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
        self.log_callback = None

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
            pass

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
            return None

    def detect_players(self) -> bool:
        """检测是否有其他玩家"""
        if not self.enabled:
            return False

        minimap = self.capture_minimap()
        if minimap is None:
            return False

        with self.lock:
            self.stats['detection_runs'] += 1

        yellow_dots = self.detector.detect(minimap)

        if yellow_dots:
            with self.lock:
                self.stats['yellow_dots_detected'] += len(yellow_dots)
            if self.log_callback:
                self.log_callback(f"[{self.title}] Detected {len(yellow_dots)} yellow dot(s)")
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
            if self.log_callback:
                self.log_callback(f"[{self.title}] Teleport used (key: {teleport_key}, hwnd: {self.hwnd})")
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"[{self.title}] Teleport failed: {e}", "ERROR")

    def _run_loop(self, detection_interval: float):
        """独立线程运行循环"""
        if self.log_callback:
            self.log_callback(f"[{self.title}] Started independent monitoring")
        
        while self.running:
            try:
                if not self.enabled:
                    time.sleep(0.1)
                    continue

                # 检查窗口是否还存在
                if not win32gui.IsWindow(self.hwnd):
                    if self.log_callback:
                        self.log_callback(f"[{self.title}] Window closed")
                    break

                # 检测玩家
                if self.detect_players():
                    self.teleport()

            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"[{self.title}] Error: {e}", "ERROR")

            time.sleep(detection_interval)

        if self.log_callback:
            self.log_callback(f"[{self.title}] Monitoring stopped")

    def start(self, detection_interval: float = 0.3, log_callback=None):
        """启动独立监控线程"""
        if self.running:
            return
        
        self.log_callback = log_callback
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, args=(detection_interval,), daemon=True)
        self.thread.start()

    def stop(self):
        """停止监控"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def is_valid(self) -> bool:
        """检查窗口是否仍然有效"""
        try:
            return win32gui.IsWindow(self.hwnd)
        except:
            return False


class MultiWindowBotGUI:
    """多窗口GUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Legend of Mir 2 Auto Bot V2 - Multi-Window")
        self.root.geometry("800x750")
        self.root.resizable(True, True)

        self.windows: Dict[int, GameWindow] = {}
        self.config = self._load_config()
        self.running = False

        self._create_widgets()
        keyboard.add_hotkey('F10', self.stop_bot)

    def _load_config(self):
        """加载配置"""
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE, encoding='utf-8')
        return config

    def _create_widgets(self):
        """创建界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="Bot V2 - Multi-Window Mode (Background Capture)",
                                font=('Arial', 14, 'bold'))
        title_label.pack(pady=5)

        desc_label = ttk.Label(main_frame,
                               text="Each window runs in independent thread with background screenshot",
                               font=('Arial', 10))
        desc_label.pack(pady=2)

        # 窗口管理框架
        window_frame = ttk.LabelFrame(main_frame, text="Game Windows", padding="5")
        window_frame.pack(fill=tk.X, pady=5)

        # 窗口列表
        columns = ('hwnd', 'title', 'status', 'detections', 'yellow_dots', 'teleports')
        self.window_tree = ttk.Treeview(window_frame, columns=columns, show='headings', height=6)
        self.window_tree.heading('hwnd', text='HWND')
        self.window_tree.heading('title', text='Window Title')
        self.window_tree.heading('status', text='Status')
        self.window_tree.heading('detections', text='Detections')
        self.window_tree.heading('yellow_dots', text='Yellow Dots')
        self.window_tree.heading('teleports', text='Teleports')

        self.window_tree.column('hwnd', width=70)
        self.window_tree.column('title', width=220)
        self.window_tree.column('status', width=70)
        self.window_tree.column('detections', width=80)
        self.window_tree.column('yellow_dots', width=90)
        self.window_tree.column('teleports', width=70)

        self.window_tree.pack(fill=tk.X, pady=5)

        # 窗口操作按钮
        window_btn_frame = ttk.Frame(window_frame)
        window_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(window_btn_frame, text="Scan Windows", command=self.scan_windows, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(window_btn_frame, text="Enable Selected", command=self.enable_selected, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(window_btn_frame, text="Disable Selected", command=self.disable_selected, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(window_btn_frame, text="Remove Selected", command=self.remove_selected, width=12).pack(side=tk.LEFT, padx=5)

        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        self.start_btn = ttk.Button(control_frame, text="Start All", command=self.start_bot, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop All", command=self.stop_bot, width=12, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.test_btn = ttk.Button(control_frame, text="Test Selected", command=self.test_selected, width=12)
        self.test_btn.pack(side=tk.LEFT, padx=5)

        self.adjust_btn = ttk.Button(control_frame, text="Adjust Minimap", command=self.adjust_minimap, width=12)
        self.adjust_btn.pack(side=tk.LEFT, padx=5)

        # 状态
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(status_frame, text="Status: Stopped", font=('Arial', 10))
        self.status_label.pack(anchor=tk.W)

        self.stats_label = ttk.Label(status_frame, text="Windows: 0 | Total Teleports: 0", font=('Arial', 10))
        self.stats_label.pack(anchor=tk.W)

        # 日志
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 设置
        settings_frame = ttk.LabelFrame(main_frame, text="Quick Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)

        row1_frame = ttk.Frame(settings_frame)
        row1_frame.pack(fill=tk.X, pady=2)

        ttk.Label(row1_frame, text="Teleport Key:").pack(side=tk.LEFT, padx=5)
        self.teleport_key_var = tk.StringVar(value=self.config.get('Teleport', 'teleport_key', fallback='2'))
        ttk.Entry(row1_frame, textvariable=self.teleport_key_var, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1_frame, text="Cooldown (s):").pack(side=tk.LEFT, padx=5)
        self.cooldown_var = tk.StringVar(value=self.config.get('Teleport', 'cooldown', fallback='4.0'))
        ttk.Entry(row1_frame, textvariable=self.cooldown_var, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1_frame, text="Interval (s):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value=self.config.get('Detection', 'detection_interval', fallback='0.3'))
        ttk.Entry(row1_frame, textvariable=self.interval_var, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Button(row1_frame, text="Save Settings", command=self.save_settings, width=12).pack(side=tk.LEFT, padx=20)

        # 初始扫描
        self.root.after(500, self.scan_windows)

    def log(self, message: str, level: str = "INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

    def scan_windows(self):
        """扫描游戏窗口"""
        self.log("Scanning for game windows...")
        self.window_tree.delete(*self.window_tree.get_children())

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

        # 停止所有现有窗口
        for gw in self.windows.values():
            gw.stop()

        # 更新窗口列表
        new_windows = {}
        for hwnd, title in found_windows:
            new_windows[hwnd] = GameWindow(hwnd, title, self.config)

            # 添加到树形列表
            gw = new_windows[hwnd]
            status = "Enabled" if gw.enabled else "Disabled"
            self.window_tree.insert('', 'end', iid=str(hwnd),
                                    values=(hwnd, gw.title[:30], status,
                                            gw.stats['detection_runs'],
                                            gw.stats['yellow_dots_detected'],
                                            gw.stats['teleports_used']))

        self.windows = new_windows
        self.log(f"Found {len(self.windows)} game window(s)")
        self.update_stats()

    def enable_selected(self):
        """启用选中的窗口"""
        selected = self.window_tree.selection()
        for item in selected:
            hwnd = int(item)
            if hwnd in self.windows:
                self.windows[hwnd].enabled = True
        self.refresh_window_list()

    def disable_selected(self):
        """禁用选中的窗口"""
        selected = self.window_tree.selection()
        for item in selected:
            hwnd = int(item)
            if hwnd in self.windows:
                self.windows[hwnd].enabled = False
        self.refresh_window_list()

    def remove_selected(self):
        """移除选中的窗口"""
        selected = self.window_tree.selection()
        for item in selected:
            hwnd = int(item)
            if hwnd in self.windows:
                self.windows[hwnd].stop()
                del self.windows[hwnd]
        self.refresh_window_list()

    def refresh_window_list(self):
        """刷新窗口列表显示"""
        for item in self.window_tree.get_children():
            hwnd = int(item)
            if hwnd in self.windows:
                gw = self.windows[hwnd]
                status = "Enabled" if gw.enabled else "Disabled"
                self.window_tree.item(item, values=(
                    hwnd, gw.title[:30], status,
                    gw.stats['detection_runs'],
                    gw.stats['yellow_dots_detected'],
                    gw.stats['teleports_used']
                ))

    def start_bot(self):
        """开始监控"""
        if not self.windows:
            messagebox.showwarning("Warning", "No game windows found. Please scan first.")
            return

        enabled_count = sum(1 for gw in self.windows.values() if gw.enabled)
        if enabled_count == 0:
            messagebox.showwarning("Warning", "No enabled windows. Please enable at least one window.")
            return

        self.log(f"Starting monitoring {enabled_count} window(s) (independent threads)...")
        self.running = True
        self.start_time = datetime.now()  # 记录启动时间

        # 更新配置
        self.config.set('Teleport', 'teleport_key', self.teleport_key_var.get())
        self.config.set('Teleport', 'cooldown', self.cooldown_var.get())
        self.config.set('Detection', 'detection_interval', self.interval_var.get())

        detection_interval = float(self.interval_var.get())

        # 启动所有窗口的独立线程
        for gw in self.windows.values():
            gw.config = self.config
            gw.teleport_cooldown = float(self.cooldown_var.get())
            gw.start(detection_interval, self.log)

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Running (Independent Threads)")

        self._update_stats_loop()

    def stop_bot(self):
        """停止监控"""
        self.running = False
        
        # 停止所有窗口线程
        for gw in self.windows.values():
            gw.stop()

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Stopped")
        self.log("Monitoring stopped")

    def _update_stats_loop(self):
        """更新统计"""
        if self.running:
            self.update_stats()
            self.refresh_window_list()
            
            # 每15分钟清理一次debug目录
            if hasattr(self, 'start_time') and self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                if int(elapsed) > 0 and int(elapsed) % 900 == 0:  # 900秒 = 15分钟
                    self._cleanup_debug_dir()
            
            self.root.after(1000, self._update_stats_loop)
    
    def _cleanup_debug_dir(self):
        """清理debug目录"""
        debug_dir = os.path.join(SCRIPT_DIR, 'debug')
        if not os.path.exists(debug_dir):
            return
        
        try:
            # 获取目录下所有文件
            files = [f for f in os.listdir(debug_dir) if f.endswith(('.jpg', '.png', '.bmp'))]
            if files:
                for file in files:
                    file_path = os.path.join(debug_dir, file)
                    try:
                        os.remove(file_path)
                    except:
                        pass
                self.log(f"Cleaned debug directory: {len(files)} files removed")
        except Exception as e:
            self.log(f"Failed to clean debug directory: {e}", "WARNING")

    def update_stats(self):
        """更新统计显示"""
        enabled = sum(1 for gw in self.windows.values() if gw.enabled)
        total_teleports = sum(gw.stats['teleports_used'] for gw in self.windows.values())
        total_detections = sum(gw.stats['yellow_dots_detected'] for gw in self.windows.values())
        self.stats_label.config(text=f"Windows: {len(self.windows)} ({enabled} enabled) | Yellow Dots: {total_detections} | Teleports: {total_teleports}")

    def test_selected(self):
        """测试选中的窗口"""
        selected = self.window_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a window to test")
            return

        for item in selected:
            hwnd = int(item)
            if hwnd in self.windows:
                gw = self.windows[hwnd]
                self.log(f"Testing window: {gw.title}")

                minimap = gw.capture_minimap()
                if minimap is not None:
                    yellow_dots = gw.detector.detect(minimap)
                    self.log(f"  Result: {len(yellow_dots)} yellow dot(s) detected")

                    # 保存测试图像
                    debug_dir = os.path.join(SCRIPT_DIR, 'debug')
                    os.makedirs(debug_dir, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    cv2.imwrite(os.path.join(debug_dir, f'test_{hwnd}_{timestamp}.jpg'), minimap)
                    self.log(f"  Image saved to debug/test_{hwnd}_{timestamp}.jpg")
                else:
                    self.log(f"  Failed to capture minimap", "ERROR")

    def adjust_minimap(self):
        """调整小地图范围"""
        from mir2_bot_gui_v2 import MinimapAdjustWindow
        MinimapAdjustWindow(self.root, self.config, self._on_minimap_adjusted)

    def _on_minimap_adjusted(self):
        """小地图调整完成"""
        self.config = self._load_config()
        # 重新初始化所有窗口
        for hwnd, gw in self.windows.items():
            gw.config = self.config
            gw._init_window()
        self.log("Minimap settings updated for all windows")

    def save_settings(self):
        """保存设置"""
        self.config.set('Teleport', 'teleport_key', self.teleport_key_var.get())
        self.config.set('Teleport', 'cooldown', self.cooldown_var.get())
        self.config.set('Detection', 'detection_interval', self.interval_var.get())

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            self.config.write(f)
        self.log("Settings saved")

    def run(self):
        """运行"""
        self.log("Multi-window GUI initialized (Background Capture Mode)")
        self.log("Each window runs in independent thread")
        self.root.mainloop()

    def on_closing(self):
        """关闭"""
        self.stop_bot()
        keyboard.unhook_all()
        self.root.destroy()


def main():
    gui = MultiWindowBotGUI()
    gui.root.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.run()


if __name__ == '__main__':
    main()
