# -*- coding: utf-8 -*-
"""
截屏问题诊断脚本
用于测试不同的截屏方法，找出黑色截屏的原因
"""

import win32gui
import win32ui
import win32con
import win32api
import ctypes
import numpy as np
import cv2
import os
from datetime import datetime

def find_game_window():
    """查找游戏窗口"""
    possible_titles = ['九五沉默', 'Legend of Mir2', '传奇']
    
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            for possible_title in possible_titles:
                if possible_title.lower() in title.lower():
                    windows.append((hwnd, title))
        return True
    
    windows = []
    win32gui.EnumWindows(callback, windows)
    
    if windows:
        return windows[0]
    return None, None

def capture_method_1(hwnd, width, height):
    """方法1: 使用PrintWindow (PW_CLIENTONLY = 2)"""
    try:
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        # PrintWindow with PW_CLIENTONLY = 2
        result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
        
        if result:
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        else:
            img = None
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        return img, f"PrintWindow (PW_CLIENTONLY=2) - result={result}"
    except Exception as e:
        return None, f"PrintWindow Error: {e}"

def capture_method_2(hwnd, width, height):
    """方法2: 使用PrintWindow (PW_RENDERFULLCONTENT = 2)"""
    try:
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        # PrintWindow with PW_RENDERFULLCONTENT = 2 (Windows 8.1+)
        result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
        
        if result:
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        else:
            img = None
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        return img, f"PrintWindow (PW_RENDERFULLCONTENT=2) - result={result}"
    except Exception as e:
        return None, f"PrintWindow Error: {e}"

def capture_method_3(hwnd, width, height):
    """方法3: 使用BitBlt (前台截图)"""
    try:
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        # 使用BitBlt
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
        
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype='uint8')
        img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        return img, "BitBlt (SRCCOPY)"
    except Exception as e:
        return None, f"BitBlt Error: {e}"

def capture_method_4(hwnd, width, height):
    """方法4: 使用GetDC + BitBlt"""
    try:
        # 获取客户区DC
        hwndDC = win32gui.GetDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        # 使用BitBlt
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
        
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype='uint8')
        img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        return img, "GetDC + BitBlt"
    except Exception as e:
        return None, f"GetDC Error: {e}"

def capture_method_5(hwnd):
    """方法5: 使用pyautogui (前台截图)"""
    try:
        import pyautogui
        
        # 获取窗口位置
        rect = win32gui.GetWindowRect(hwnd)
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        
        # 截图
        img = pyautogui.screenshot(region=(left, top, width, height))
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        return img, "pyautogui.screenshot"
    except Exception as e:
        return None, f"pyautogui Error: {e}"

def is_image_black(img):
    """检查图像是否全黑"""
    if img is None:
        return True
    return np.all(img == 0)

def main():
    print("=" * 60)
    print("截屏问题诊断工具")
    print("=" * 60)
    print()
    
    # 查找游戏窗口
    hwnd, title = find_game_window()
    if not hwnd:
        print("❌ 未找到游戏窗口")
        print("请确保游戏已启动，窗口标题包含: 九五沉默, Legend of Mir2, 或 传奇")
        return
    
    print(f"✅ 找到游戏窗口: {title}")
    print(f"   窗口句柄: {hwnd}")
    
    # 获取客户区大小
    client_rect = win32gui.GetClientRect(hwnd)
    client_width = client_rect[2] - client_rect[0]
    client_height = client_rect[3] - client_rect[1]
    
    print(f"   客户区大小: {client_width}x{client_height}")
    print()
    
    # 创建输出目录
    output_dir = "screenshot_test"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 测试不同的截屏方法
    methods = [
        ("方法1: PrintWindow (PW_CLIENTONLY=2)", capture_method_1, (hwnd, client_width, client_height)),
        ("方法2: PrintWindow (PW_RENDERFULLCONTENT)", capture_method_2, (hwnd, client_width, client_height)),
        ("方法3: BitBlt (GetWindowDC)", capture_method_3, (hwnd, client_width, client_height)),
        ("方法4: BitBlt (GetDC)", capture_method_4, (hwnd, client_width, client_height)),
        ("方法5: pyautogui", capture_method_5, (hwnd,)),
    ]
    
    print("开始测试不同的截屏方法...")
    print("-" * 60)
    
    for i, (name, method, args) in enumerate(methods, 1):
        print(f"\n测试 {name}...")
        
        try:
            img, info = method(*args)
            
            if img is not None:
                is_black = is_image_black(img)
                status = "❌ 全黑" if is_black else "✅ 正常"
                
                print(f"   结果: {status}")
                print(f"   信息: {info}")
                print(f"   图像大小: {img.shape}")
                
                # 保存图像
                filename = f"{output_dir}/method_{i}_{timestamp}.jpg"
                cv2.imwrite(filename, img)
                print(f"   已保存: {filename}")
                
                # 如果不是全黑，显示图像统计
                if not is_black:
                    print(f"   平均亮度: {np.mean(img):.2f}")
                    print(f"   最大像素值: {np.max(img)}")
            else:
                print(f"   ❌ 失败: {info}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    print()
    print("=" * 60)
    print("测试完成！")
    print(f"截图已保存到: {output_dir}/")
    print()
    print("建议:")
    print("1. 查看保存的截图，找出哪个方法能正常工作")
    print("2. 如果所有方法都是黑色，可能是游戏使用了DirectX渲染")
    print("3. 如果BitBlt方法正常，建议使用BitBlt替代PrintWindow")
    print("=" * 60)

if __name__ == '__main__':
    main()
