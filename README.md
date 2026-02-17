# 传奇2自动挂机脚本 - 使用说明

## 功能介绍

本脚本用于传奇2游戏挂机，主要功能：
- **自动检测特定文字**：检测游戏画面中是否包含特定文字"人物斩杀"
- **自动传送**：检测到目标文字时自动使用随机传送石

## 目录结构

```
script/
├── mir2_auto_bot.py         # 命令行版本主程序
├── mir2_bot_gui.py          # 图形界面版本主程序
├── dependency_manager.py    # 依赖管理模块
├── bot_config.ini           # 配置文件
├── requirements.txt         # 依赖列表
├── install_deps.bat         # 依赖安装脚本
├── start_bot.bat            # 启动命令行版本
├── start_gui.bat            # 启动图形界面版本
├── README.md                # 本文档
├── GUI_README.md            # GUI使用说明
├── SETTINGS.md              # 设置说明
├── DEPENDENCIES.md          # 依赖管理说明
├── TROUBLESHOOTING.md       # 问题排查指南
├── CHANGELOG.md             # 更新日志
├── PROJECT_STRUCTURE.md     # 项目结构说明
├── mir2_bot.log            # 运行日志（自动生成）
└── test/                    # 测试脚本目录
    ├── README.md            # 测试脚本说明
    ├── test_all.py          # 完整功能测试
    ├── test_bot.py          # 依赖测试
    ├── test_config.py       # 配置测试
    ├── test_window_detection.py  # 窗口检测测试
    ├── test_window_rect.py       # 窗口矩形测试
    ├── test_keypress.py          # 按键测试
    ├── test_white_text.py        # 白色文字检测测试
    ├── test_ocr.py              # OCR识别测试
    ├── check_window_state.py     # 窗口状态检查
    ├── list_windows.py           # 窗口列表工具
    ├── quick_test.py            # 快速测试
    ├── check_python.bat         # Python环境检查
    ├── test_ocr.bat             # OCR测试批处理
    └── todo.md                  # 待办事项
```

详细的项目结构说明请查看 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)。

## 功能介绍

本脚本用于传奇2游戏挂机，主要功能：
- **自动检测特定文字**：检测游戏画面中是否包含特定文字"人物斩杀"
- **自动传送**：检测到目标文字**两次及以上**时自动使用随机传送石

## 安装依赖

### 方法1: 使用安装脚本（推荐）
```bash
cd script
install_deps.bat
```

### 方法2: 手动安装
```bash
cd script
pip install -r requirements.txt
```

### 依赖包列表

```
keyboard>=0.13.5
mouse>=0.7.1
pywin32>=306
opencv-python>=4.8.0
numpy>=1.24.0
pyautogui>=0.9.54
Pillow>=10.0.0
pyscreeze>=0.1.21
configparser>=5.3.0
pytesseract>=0.3.10
```

### Tesseract OCR 安装

本脚本使用OCR技术识别中文文字，需要安装Tesseract OCR引擎：

1. **下载Tesseract OCR**
   - 访问 https://github.com/UB-Mannheim/tesseract/wiki
   - 下载Windows版本的安装程序
   - 安装时勾选"中文简体"语言包

2. **配置环境变量**
   - 确保Tesseract安装路径已添加到系统PATH环境变量
   - 默认安装路径：`C:\Program Files\Tesseract-OCR`

3. **验证安装**
   - 打开命令行，输入 `tesseract --version` 查看版本
   - 输入 `tesseract --list-langs` 查看已安装语言包，应包含 `chi_sim`

## 配置说明

编辑 `bot_config.ini` 文件进行配置：

### 游戏设置
```ini
[Game]
window_title = 九五沉默
```
- `window_title`: 游戏窗口标题（支持部分匹配）
  - 游戏窗口标题格式：`九五沉默[区号] - [用户名]`
  - 例如：`九五沉默11号B组01区 - 千问`
  - 配置文件中只需填 `九五沉默` 即可匹配
  - 脚本会自动匹配以该标题开头的窗口

### 检测设置
```ini
[Detection]
enabled = true
detection_interval = 0.3
confidence_threshold = 0.75
```
- `enabled`: 是否启用检测
- `detection_interval`: 检测间隔（秒），建议0.3-0.5
- `confidence_threshold`: OCR识别置信度阈值（暂未使用）

**注意**：本脚本使用OCR技术检测特定文字"人物斩杀"，不再依赖颜色检测。

### 传送设置
```ini
[Teleport]
enabled = true
teleport_key = 2
cooldown = 4
```
- `enabled`: 是否启用自动传送
- `teleport_key`: 传送石快捷键（如：'2', 'F4'等）
- `cooldown`: 传送冷却时间（秒）
- **重要**: 检测到目标文字"人物斩杀"**两次及以上**时才会传送（避免误报）

### 高级设置
```ini
[Advanced]
use_opencv = true
min_detection_area = 30
max_detection_area = 10000
detection_top_percent = 10
detection_bottom_percent = 80
detection_left_percent = 5
detection_right_percent = 95
```
- `use_opencv`: 是否使用OpenCV进行检测
- `min_detection_area`: 最小检测区域面积（过滤噪点）
- `max_detection_area`: 最大检测区域面积（过滤过大区域）
- `detection_top_percent`: 检测范围上边界（屏幕百分比，0-100）
- `detection_bottom_percent`: 检测范围下边界（屏幕百分比，0-100）
- `detection_left_percent`: 检测范围左边界（屏幕百分比，0-100）
- `detection_right_percent`: 检测范围右边界（屏幕百分比，0-100）
  - 例如：`10-80, 5-95` 表示检测屏幕中间区域，避开左右UI
  - 玩家名字通常在角色上方，建议设置为 `10-80, 5-95`
  - 如果检测不到，可以调整范围

## 使用方法

### 方法1: 使用启动脚本（推荐）
```bash
cd script
start_bot.bat
```

### 方法2: 直接运行Python脚本
```bash
cd script
python mir2_auto_bot.py
```

## 测试脚本

### 完整功能测试
```bash
cd script/test
python test_all.py
```

### 依赖测试
```bash
cd script/test
python test_bot.py
```

### 窗口检测测试
```bash
cd script/test
python test_window_detection.py
```

## 控制命令

- **F10**: 停止挂机
- **Ctrl+C**: 强制退出

## 工作原理

1. **窗口检测**: 自动查找并激活游戏窗口
2. **画面截图**: 使用pyautogui截取游戏窗口画面
3. **文字识别**: 使用OCR技术识别屏幕中的文字内容
4. **目标检测**: 检查识别结果中是否包含目标文字"人物斩杀"
5. **自动传送**: 检测到目标文字**两次及以上**时模拟按键使用传送石（避免误报）

## 调试模式

如需查看检测效果，在配置文件中添加：
```ini
[Detection]
debug = true
```
检测到的玩家会被标记并保存到 `debug_detection.jpg`

## 常见问题

### 1. 找不到游戏窗口
- 检查 `window_title` 配置是否正确
- 确保游戏窗口已打开
- 运行 `test/test_window_detection.py` 查看所有窗口

### 2. 检测不到目标文字
- 确保已安装Tesseract OCR和中文语言包
- 检查Tesseract是否在PATH环境变量中
- 运行 `tesseract --list-langs` 确认已安装 `chi_sim` 语言包
- 查看 `debug/` 目录下的调试图像：
  - `01_detection_region.jpg`: 检测区域截图
  - `03_detection_result.jpg`: 检测结果（黄色框=检测范围，绿色框=目标文字）
- 调整检测范围：修改 `detection_top_percent` 和 `detection_bottom_percent`
- 启用调试模式：在配置文件中设置 `debug = true`

**检测算法说明**：
- 使用OCR技术识别屏幕中的中文文字
- 检测识别结果中是否包含"人物斩杀"
- OCR置信度阈值：30（只保留置信度>30的识别结果）
- 检测范围：屏幕中间区域（可配置）

### 3. 传送快捷键没有反应
- 运行 `test/test_keypress.py` 测试按键功能
- 确认游戏内'2'键已绑定传送石
- 尝试以管理员权限运行脚本
- 检查游戏是否需要先选中传送石
- 如果是数字键，确保NumLock关闭（如果使用小键盘）

### 4. 传送太频繁
- 增加 `cooldown` 值
- 调整 `min_detection_area` 过滤小噪点

### 5. 检测误报
- 调整OCR置信度阈值（修改代码中的 `conf > 30`）
- 调整检测区域范围（修改top_percent和bottom_percent）
- 确保游戏画面清晰，避免模糊或干扰

### 6. Tesseract OCR 错误
错误信息：`TesseractNotFoundError` 或 `tesseract is not installed`

解决方案：
1. 下载并安装Tesseract OCR：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装时勾选"中文简体"语言包
3. 将Tesseract安装路径添加到系统PATH环境变量
4. 重启命令行或IDE，重新运行脚本

### 7. Pillow/Pyscreeze 错误
错误信息：`PyAutoGUI was unable to import pyscreeze`

解决方案：
```bash
pip install --upgrade Pillow
pip uninstall -y pyautogui
pip install pyautogui
```

详细说明见 [FIX_PILLOW_ERROR.md](FIX_PILLOW_ERROR.md)

### 8. Python 3.14 兼容性问题
Python 3.14 是较新版本，需要安装兼容的依赖包版本：
- Pillow >= 10.0.0
- pyscreeze >= 0.1.21

运行 `test/test_all.py` 验证所有功能是否正常。

## 日志文件

运行日志保存在 `mir2_bot.log`，包含：
- 启动信息
- 检测统计
- 错误信息

## 注意事项

1. 确保游戏窗口在前台运行
2. 建议使用窗口模式而非全屏模式
3. 检测间隔不宜过短，避免CPU占用过高
4. 传送冷却时间应合理设置，避免被封号

## 技术栈

- **Python 3.x**: 主要编程语言
- **Tesseract OCR**: OCR文字识别（支持中文）
- **PyAutoGUI**: 截图和输入模拟
- **Keyboard**: 快捷键监听
- **NumPy**: 数值计算
- **Pillow**: 图像处理库（pyautogui依赖）

## 依赖包说明

- **pytesseract**: Python Tesseract OCR封装库
- **numpy**: 数值计算
- **pyautogui**: 截图和键盘鼠标模拟
- **keyboard**: 全局快捷键监听
- **pywin32**: Windows窗口操作
- **mouse**: 鼠标操作
- **Pillow**: 图像处理（pyautogui依赖）
- **pyscreeze**: 截图功能（pyautogui依赖）
- **configparser**: 配置文件读取

## 扩展功能

脚本采用模块化设计，可以轻松添加新功能：
- 自动捡装备
- 自动打怪
- 自动吃药
- 自定义检测目标文字（修改代码中的 `target_text` 变量）
- 更多检测方式（模板匹配、AI识别等）

## 更新日志

详细更新记录见 [CHANGELOG.md](CHANGELOG.md)

## 版本历史

### v3.0 - OCR版本 (2026-02-13)
- 改用OCR技术检测特定文字"人物斩杀"
- 移除OpenCV颜色检测依赖
- 添加Tesseract OCR依赖
- 更新文档说明
- 优化检测逻辑

### v2.0 - OpenCV版本 (2026-02-11)
- 移除pygame依赖
- 改进窗口检测逻辑
- 支持多个窗口标题匹配
- 优化依赖包管理
- 添加完整测试套件

### v1.0 - 初始版本
- 基础玩家检测功能
- 自动传送功能
- 配置文件支持
