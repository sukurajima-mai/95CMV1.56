# 依赖管理说明

## 功能介绍

GUI版本集成了完整的依赖管理功能，可以方便地检测、安装和更新所有依赖包。

## 依赖包列表

### 必需依赖包

| 包名 | 最低版本 | 说明 |
|------|---------|------|
| keyboard | 0.13.5 | 键盘监听 |
| mouse | 0.7.1 | 鼠标操作 |
| pywin32 | 306 | Windows API |
| opencv-python | 4.8.0 | 图像处理 |
| numpy | 1.24.0 | 数值计算 |
| pyautogui | 0.9.54 | 屏幕操作 |
| Pillow | 10.0.0 | 图像处理 |
| pyscreeze | 0.1.21 | 截图功能 |
| configparser | 5.3.0 | 配置文件 |
| pytesseract | 0.3.10 | OCR文字识别 |

### 可选依赖包

| 包名 | 说明 |
|------|------|
| win32ui | Windows UI (pywin32的一部分) |

## 使用方法

### 1. 启动GUI

双击运行 `start_gui.bat` 启动图形界面。

### 2. 自动检查依赖

GUI启动后会自动检查所有依赖包的状态，并在日志中显示结果。

### 3. 手动检查依赖

点击"检查依赖"按钮，可以手动检查所有依赖包的状态。

检查结果会显示：
- ✓ 已安装的包（显示版本号）
- ✗ 未安装的包
- (必需) 或 (可选) 标记

### 4. 安装缺失依赖

如果有缺失的必需依赖包，"安装缺失依赖"按钮会变为可用状态。

点击该按钮，会：
1. 弹出确认对话框
2. 自动安装所有缺失的必需依赖包
3. 显示安装进度
4. 安装完成后重新检查依赖

### 5. 更新所有依赖

点击"更新所有依赖"按钮，可以更新所有已安装的依赖包到最新版本。

### 6. 检查Tesseract OCR

点击"检查Tesseract"按钮，可以检查：
- Tesseract OCR是否已安装
- Tesseract OCR的版本
- 中文简体语言包是否已安装
- 已安装的所有语言包

## 命令行使用

### 检查依赖

```bash
cd script
python dependency_manager.py
```

### 手动安装依赖

```bash
cd script
pip install -r requirements.txt
```

### 更新依赖

```bash
cd script
pip install --upgrade -r requirements.txt
```

## 常见问题

### 1. 依赖安装失败

如果安装失败，可能的原因：
- 网络连接问题
- pip版本过旧
- Python版本不兼容

解决方法：
1. 检查网络连接
2. 更新pip：`python -m pip install --upgrade pip`
3. 尝试使用国内镜像源：
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### 2. Tesseract OCR未安装

Tesseract OCR不是Python包，需要单独安装。

安装步骤：
1. 访问 https://github.com/UB-Mannheim/tesseract/wiki
2. 下载Windows版本的安装程序
3. 安装时勾选"中文简体"语言包
4. 将安装路径添加到系统PATH环境变量

验证安装：
```bash
tesseract --version
tesseract --list-langs
```

### 3. 中文语言包未安装

如果Tesseract已安装但缺少中文语言包：

1. 重新安装Tesseract OCR
2. 安装时确保勾选"中文简体"语言包
3. 或者手动下载语言包并放到tessdata目录

### 4. 权限问题

如果安装时提示权限不足：

1. 以管理员身份运行GUI
2. 或者在命令行中以管理员身份运行：
   ```bash
   右键点击命令提示符 -> 以管理员身份运行
   cd script
   python mir2_bot_gui.py
   ```

## 依赖管理模块

`dependency_manager.py` 提供了完整的依赖管理功能：

### 主要类和方法

```python
from dependency_manager import DependencyManager

# 创建依赖管理器
manager = DependencyManager(log_callback=print)

# 检查所有包
packages = manager.check_all_packages()

# 安装缺失的包
manager.install_all_missing(packages)

# 更新所有包
manager.update_all_packages(packages)

# 检查Tesseract
installed, version = manager.check_tesseract()
has_chinese, languages = manager.check_tesseract_languages()
```

## 日志颜色说明

- **黑色** - 普通信息
- **绿色** - 成功信息
- **橙色** - 警告信息
- **红色** - 错误信息

## 自动检查

GUI启动后会自动检查依赖，并在日志中显示结果。如果发现缺失的依赖，会自动启用"安装缺失依赖"按钮。

## 更新日志

### v3.2 - 依赖管理功能 (2026-02-13)

**新增功能**：
- ✅ 依赖检测功能
- ✅ 依赖安装功能
- ✅ 依赖更新功能
- ✅ Tesseract OCR检查功能
- ✅ 自动依赖检查
- ✅ 依赖管理模块

**界面改进**：
- 添加"依赖管理"按钮组
- 界面尺寸调整（900x700）
- 添加绿色日志颜色
- 改进按钮布局

**文件新增**：
- `dependency_manager.py` - 依赖管理模块
- `DEPENDENCIES.md` - 本文档
