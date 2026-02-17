# -*- coding: utf-8 -*-
"""
依赖管理模块
用于检测、安装和更新Python依赖包
"""

import subprocess
import sys
import importlib
from typing import Dict, List, Tuple

# 需要的依赖包列表
REQUIRED_PACKAGES = {
    'keyboard': {'min_version': '0.13.5', 'description': '键盘监听'},
    'mouse': {'min_version': '0.7.1', 'description': '鼠标操作'},
    'pywin32': {'min_version': '306', 'description': 'Windows API'},
    'opencv-python': {'min_version': '4.8.0', 'description': '图像处理'},
    'numpy': {'min_version': '1.24.0', 'description': '数值计算'},
    'pyautogui': {'min_version': '0.9.54', 'description': '屏幕操作'},
    'Pillow': {'min_version': '10.0.0', 'description': '图像处理'},
    'pyscreeze': {'min_version': '0.1.21', 'description': '截图功能'},
    'configparser': {'min_version': '5.3.0', 'description': '配置文件'},
    'pytesseract': {'min_version': '0.3.10', 'description': 'OCR文字识别'},
}

# 可选依赖
OPTIONAL_PACKAGES = {
    'win32ui': {'description': 'Windows UI (pywin32的一部分)', 'optional': True},
}


class DependencyManager:
    """依赖管理器"""

    def __init__(self, log_callback=None):
        """
        初始化依赖管理器

        Args:
            log_callback: 日志回调函数
        """
        self.log_callback = log_callback

    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")

    def check_package(self, package_name: str) -> Tuple[bool, str]:
        """
        检查单个包是否已安装

        Args:
            package_name: 包名

        Returns:
            (是否已安装, 版本信息)
        """
        try:
            # 尝试导入包
            if package_name == 'opencv-python':
                import cv2
                version = cv2.__version__
            elif package_name == 'Pillow':
                import PIL
                version = PIL.__version__
            elif package_name == 'pywin32':
                import win32api
                version = win32api.__version__
            elif package_name == 'pytesseract':
                import pytesseract
                version = pytesseract.__version__
            else:
                module = importlib.import_module(package_name)
                version = getattr(module, '__version__', 'unknown')

            return True, version

        except ImportError:
            return False, "Not installed"
        except Exception as e:
            return False, f"Error: {e}"

    def check_all_packages(self) -> Dict[str, Dict]:
        """
        检查所有依赖包

        Returns:
            包状态字典
        """
        self._log("正在检查依赖包...")

        results = {}

        # 检查必需包
        for package_name, package_info in REQUIRED_PACKAGES.items():
            installed, version = self.check_package(package_name)
            results[package_name] = {
                'installed': installed,
                'version': version,
                'min_version': package_info['min_version'],
                'description': package_info['description'],
                'required': True
            }

        # 检查可选包
        for package_name, package_info in OPTIONAL_PACKAGES.items():
            installed, version = self.check_package(package_name)
            results[package_name] = {
                'installed': installed,
                'version': version,
                'min_version': None,
                'description': package_info['description'],
                'required': False
            }

        self._log("依赖包检查完成")

        return results

    def install_package(self, package_name: str) -> bool:
        """
        安装单个包

        Args:
            package_name: 包名

        Returns:
            是否安装成功
        """
        self._log(f"正在安装 {package_name}...")

        try:
            # 使用pip安装
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                self._log(f"✓ {package_name} 安装成功")
                return True
            else:
                self._log(f"✗ {package_name} 安装失败: {result.stderr}", "ERROR")
                return False

        except subprocess.TimeoutExpired:
            self._log(f"✗ {package_name} 安装超时", "ERROR")
            return False
        except Exception as e:
            self._log(f"✗ {package_name} 安装出错: {e}", "ERROR")
            return False

    def update_package(self, package_name: str) -> bool:
        """
        更新单个包

        Args:
            package_name: 包名

        Returns:
            是否更新成功
        """
        self._log(f"正在更新 {package_name}...")

        try:
            # 使用pip更新
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', package_name],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                self._log(f"✓ {package_name} 更新成功")
                return True
            else:
                self._log(f"✗ {package_name} 更新失败: {result.stderr}", "ERROR")
                return False

        except subprocess.TimeoutExpired:
            self._log(f"✗ {package_name} 更新超时", "ERROR")
            return False
        except Exception as e:
            self._log(f"✗ {package_name} 更新出错: {e}", "ERROR")
            return False

    def install_all_missing(self, packages: Dict[str, Dict]) -> int:
        """
        安装所有缺失的包

        Args:
            packages: 包状态字典

        Returns:
            安装成功的包数量
        """
        missing_packages = [
            name for name, info in packages.items()
            if not info['installed'] and info.get('required', False)
        ]

        if not missing_packages:
            self._log("所有必需的依赖包都已安装")
            return 0

        self._log(f"发现 {len(missing_packages)} 个缺失的包，开始安装...")
        success_count = 0

        for package_name in missing_packages:
            if self.install_package(package_name):
                success_count += 1

        self._log(f"安装完成: {success_count}/{len(missing_packages)} 成功")

        return success_count

    def update_all_packages(self, packages: Dict[str, Dict]) -> int:
        """
        更新所有已安装的包

        Args:
            packages: 包状态字典

        Returns:
            更新成功的包数量
        """
        installed_packages = [
            name for name, info in packages.items()
            if info['installed'] and info.get('required', False)
        ]

        if not installed_packages:
            self._log("没有已安装的包需要更新")
            return 0

        self._log(f"正在更新 {len(installed_packages)} 个包...")
        success_count = 0

        for package_name in installed_packages:
            if self.update_package(package_name):
                success_count += 1

        self._log(f"更新完成: {success_count}/{len(installed_packages)} 成功")

        return success_count

    def check_tesseract(self) -> Tuple[bool, str]:
        """
        检查Tesseract OCR是否已安装

        Returns:
            (是否已安装, 版本信息)
        """
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # 提取版本号
                version_line = result.stdout.split('\n')[0]
                return True, version_line
            else:
                return False, "Not installed"

        except FileNotFoundError:
            return False, "Not found in PATH"
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, f"Error: {e}"

    def check_tesseract_languages(self) -> Tuple[bool, List[str]]:
        """
        检查Tesseract已安装的语言包

        Returns:
            (是否成功, 语言列表)
        """
        try:
            result = subprocess.run(
                ['tesseract', '--list-langs'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # 解析语言列表
                lines = result.stdout.split('\n')
                languages = [line.strip() for line in lines[1:] if line.strip()]
                has_chinese = 'chi_sim' in languages
                return has_chinese, languages
            else:
                return False, []

        except Exception as e:
            return False, []

    def get_pip_version(self) -> str:
        """
        获取pip版本

        Returns:
            pip版本字符串
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "Unknown"

        except Exception as e:
            return f"Error: {e}"


def main():
    """测试依赖管理器"""
    print("依赖管理器测试")
    print("=" * 50)

    manager = DependencyManager()

    # 检查所有包
    packages = manager.check_all_packages()

    print("\n依赖包状态:")
    print("-" * 50)
    for name, info in packages.items():
        status = "✓" if info['installed'] else "✗"
        version = info['version'] if info['installed'] else "Not installed"
        required = "必需" if info.get('required', False) else "可选"
        print(f"{status} {name:20s} {version:15s} ({required}) - {info['description']}")

    # 检查Tesseract
    print("\n" + "-" * 50)
    tesseract_installed, tesseract_version = manager.check_tesseract()
    if tesseract_installed:
        print(f"✓ Tesseract OCR: {tesseract_version}")

        has_chinese, languages = manager.check_tesseract_languages()
        if has_chinese:
            print(f"✓ 中文语言包已安装")
        else:
            print(f"✗ 中文语言包未安装")
    else:
        print(f"✗ Tesseract OCR: {tesseract_version}")

    # 检查pip版本
    print(f"\n{manager.get_pip_version()}")


if __name__ == '__main__':
    main()
