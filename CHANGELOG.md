# 更新日志

## v3.0 - OCR版本 (2026-02-13)

### 重大更新：改用OCR技术检测特定文字

1. **检测方式变更**
   - 从OpenCV颜色检测改为OCR文字识别
   - 检测目标特定文字"人物斩杀"
   - 使用Tesseract OCR引擎
   - 支持中文识别（chi_sim语言包）

2. **依赖包更新**
   - 新增：pytesseract>=0.3.10
   - 移除OpenCV颜色检测依赖（但仍保留OpenCV用于图像处理）
   - 需要安装Tesseract OCR引擎和中文语言包

3. **检测逻辑优化**
   - 使用OCR识别屏幕中的所有文字
   - 检查识别结果中是否包含"人物斩杀"
   - OCR置信度阈值：30（只保留置信度>30的识别结果）
   - 检测到目标文字即触发传送（不再需要>=2个玩家）

4. **配置更新**
   ```ini
   [Detection]
   enabled = true
   detection_interval = 0.3
   confidence_threshold = 0.75  # OCR置信度阈值

   [Teleport]
   enabled = true
   teleport_key = 2
   cooldown = 4

   [Advanced]
   use_opencv = true  # 仍使用OpenCV进行图像处理
   min_detection_area = 100
   max_detection_area = 50000
   detection_top_percent = 20
   detection_bottom_percent = 60
   detection_left_percent = 5
   detection_right_percent = 95
   ```

5. **代码改进**
   - 添加 `target_text` 类变量，方便自定义检测文字
   - 优化OCR识别参数（--psm 6 --oem 3）
   - 改进调试图像输出

6. **文档更新**
   - 更新README.md，添加Tesseract OCR安装说明
   - 更新技术栈说明
   - 更新常见问题解答
   - 添加OCR检测算法说明

### Tesseract OCR 安装

1. 下载Tesseract OCR：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装时勾选"中文简体"语言包
3. 将Tesseract安装路径添加到系统PATH环境变量
4. 验证安装：`tesseract --list-langs` 应包含 `chi_sim`

### 依赖包更新

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
pytesseract>=0.3.10  # 新增
```

### 检测逻辑变更

**之前（v2.x）**：
- 检测白色文字（玩家名字）
- 需要>=2个玩家才传送
- 基于颜色检测

**现在（v3.0）**：
- OCR识别所有文字
- 检测到"人物斩杀"即传送
- 基于文字内容检测

### 扩展性

- 可通过修改 `target_text` 变量自定义检测文字
- 支持检测任意中文文字
- 可扩展为检测多个目标文字

### 注意事项

1. 需要安装Tesseract OCR引擎和中文语言包
2. 确保Tesseract在PATH环境变量中
3. OCR识别速度较慢，建议检测间隔>=0.3秒
4. 游戏画面清晰度影响OCR识别准确率

## v2.5 - 检测优化版本 (2026-02-11)

### 检测算法大幅改进

1. **添加左右边界限制**
   - `detection_left_percent`: 检测范围左边界（避开左侧UI）
   - `detection_right_percent`: 检测范围右边界（避开右侧地图）
   - 默认：5%-95%

2. **优化白色文字检测**
   - 更严格的白色检测：饱和度<=30，亮度>=220
   - 避免检测到浅色衣服
   - 使用膨胀-腐蚀操作连接文字区域
   - 水平连接（5x1核）+ 垂直连接（1x3核）

3. **增强过滤条件**
   - 最小面积：50 → 30
   - 额外高度限制：<30像素（避免检测大块白色区域）
   - 宽度>高度*2（确保是横向文字）

4. **调试图像优化**
   - 每个检测框显示序号
   - 显示检测范围坐标
   - 更清晰的检测结果展示

### 配置更新

```ini
[Advanced]
use_opencv = true
min_detection_area = 30
max_detection_area = 10000
detection_top_percent = 10
detection_bottom_percent = 80
detection_left_percent = 5      # 新增：左边界
detection_right_percent = 95     # 新增：右边界
```

### 检测范围说明

```
屏幕区域:
┌─────────────────────────────────┐
│ 0%-10% (UI区域)               │
├─────────────────────────────────┤
│ 5%   │                       │ 95% ← 右边界
│      │   检测范围            │
│      │   (黄色区域)          │
│      │                       │
├─────────────────────────────────┤
│ 80%-100% (角色下方)          │
└─────────────────────────────────┘
```

### 检测算法改进

**之前**：
- HSV范围：[0,0,200] 到 [180,50,255]
- 形态学：简单的开运算
- 过滤：面积50-10000，宽>高*2

**现在**：
- HSV范围：[0,0,220] 到 [180,30,255]（更严格）
- 形态学：先膨胀再腐蚀（连接文字）
- 过滤：面积30-10000，宽>高*2，高<30

### 调试图像说明

- **01_white_mask.jpg**: 白色掩码（清晰显示白色文字）
- **02_detection_region.jpg**: 检测区域截图
- **03_detection_result.jpg**: 检测结果
  - 黄色区域：检测范围
  - 绿色框：检测到的玩家名字（带序号）

### 性能提升

- ✅ 避开右上角地图白色文字
- ✅ 避开左侧UI
- ✅ 避免检测到浅色衣服
- ✅ 检测移动中的玩家更准确

## v2.4 - 检测可视化版本 (2026-02-11)

### 检测可视化改进

1. **添加检测范围可视化**
   - 黄色半透明区域显示检测范围
   - 黄色边框显示检测范围边界
   - 绿色框显示检测到的玩家名字
   - 显示检测范围像素值和玩家数量

2. **检测范围可配置**
   - `detection_top_percent`: 检测范围上边界（百分比）
   - `detection_bottom_percent`: 检测范围下边界（百分比）
   - 默认：20%-60%
   - 可根据实际情况调整

3. **调试图像优化**
   - `03_detection_result.jpg` 包含完整的检测信息
   - 清晰显示检测范围和检测结果
   - 便于调整参数

### 配置更新

```ini
[Advanced]
use_opencv = true
min_detection_area = 50
max_detection_area = 10000
detection_top_percent = 20      # 检测范围上边界
detection_bottom_percent = 60   # 检测范围下边界
```

### 检测范围说明

```
屏幕高度: 100%
├─ 0%-20%:   不检测（UI区域）
├─ 20%-60%:  检测范围（黄色区域）
└─ 60%-100%: 不检测（角色下方）
```

### 调试图像说明

- **黄色半透明区域**: 检测范围（只检测这个区域内的白色文字）
- **黄色边框**: 检测范围边界
- **绿色框**: 检测到的玩家名字
- **检测范围文字**: 显示检测范围像素值
- **玩家数量文字**: 显示检测到的玩家数量

### 建议调整

如果检测不稳定：
1. 扩大检测范围：`detection_top_percent=10`, `detection_bottom_percent=70`
2. 减小最小面积：`min_detection_area=30`
3. 查看调试图像，根据实际情况调整

## v2.3 - 功能优化版本 (2026-02-11)

### 功能改进

1. **优化传送逻辑**
   - 只有检测到>=2个玩家时才传送
   - 排除自己的名字（自己也会被检测到）
   - 避免在只有自己时误传送

2. **调整传送冷却**
   - `cooldown`: 10秒 → 4秒
   - 更快的响应速度

### 配置更新

```ini
[Teleport]
enabled = true
teleport_key = 2
cooldown = 4  # 传送冷却时间改为4秒
```

### 逻辑说明

```
检测玩家数量
├─ 0个: 不传送
├─ 1个: 不传送（可能是自己）
├─ >=2个: 传送（有其他玩家）
```

## v2.2 - 检测优化版本 (2026-02-11)

### 检测算法改进

1. **优化玩家检测逻辑**
   - 改为只检测屏幕中段（20%-60%）的白色文字
   - 玩家名字通常是白色且横向的
   - 过滤条件：宽度 > 高度 * 2（过滤非文字区域）

2. **调整检测参数**
   - `min_detection_area`: 100 → 50
   - `max_detection_area`: 50000 → 10000
   - 白色HSV范围优化：`[0, 0, 200]` 到 `[180, 50, 255]`

3. **添加调试功能**
   - 启用调试模式会保存4张图像到 `debug/` 目录
   - 包括：完整屏幕、检测区域、白色掩码、检测结果

4. **新增测试脚本**
   - `test/test_white_text.py`: 测试白色文字检测
   - `test/test_keypress.py`: 测试键盘按键功能

### 配置更新

```ini
[Detection]
player_name_color = white  # 只检测白色
debug = true              # 启用调试模式

[Teleport]
teleport_key = 2          # 传送快捷键改为'2'

[Advanced]
min_detection_area = 50   # 最小检测区域
max_detection_area = 10000  # 最大检测区域
```

### 使用建议

1. **首次使用**
   ```bash
   # 测试检测效果
   cd test
   python test_white_text.py

   # 查看debug/目录下的图像
   # 根据检测结果调整参数
   ```

2. **测试按键**
   ```bash
   # 测试按键是否正常
   python test_keypress.py
   ```

3. **调整参数**
   - 如果检测太少：减小 `min_detection_area`
   - 如果检测太多：增大 `min_detection_area`
   - 如果检测位置不对：修改代码中的 `top_y` 和 `bottom_y`

## v2.1 - 文档整理版本 (2026-02-11)

### 文档改进
- 整理文档结构，合并重复内容
- 移动测试脚本到 `test/` 目录
- 更新README，添加完整的使用说明
- 添加常见问题解答（FAQ）
- 添加依赖包详细说明

### 文件结构调整
```
script/
├── mir2_auto_bot.py      # 主程序
├── bot_config.ini         # 配置文件
├── requirements.txt       # 依赖列表
├── README.md              # 主文档
├── CHANGELOG.md           # 本文档
└── test/                  # 测试脚本目录
    ├── test_all.py        # 完整功能测试
    ├── test_bot.py        # 依赖测试
    ├── test_config.py     # 配置测试
    ├── test_window_detection.py  # 窗口检测测试
    └── list_windows.py    # 窗口列表
```

## v2.0 - OpenCV版本 (2026-02-11)

### 主要改进

1. **移除pygame依赖**
   - pygame在Python 3.14上安装困难
   - 主要使用OpenCV进行图像处理，pygame不是必需的

2. **改进窗口检测**
   - 支持多个窗口标题匹配
   - 自动识别游戏窗口（九五沉默开头）
   - 忽略登录器窗口（Legend of Mir2）

3. **优化依赖包**
   - opencv-python: 图像处理和颜色检测
   - numpy: 数值计算
   - pyautogui: 截图和键盘鼠标模拟
   - keyboard: 快捷键监听
   - pywin32: Windows窗口操作
   - Pillow >= 10.0.0: 图像处理（支持Python 3.14）
   - pyscreeze >= 0.1.21: 截图功能

4. **修复Pillow/Pyscreeze错误**
   - 升级Pillow到12.1.1
   - 重新安装pyautogui
   - 添加兼容性检查

### 配置更新

```ini
[Game]
window_title = 九五沉默  # 游戏窗口标题（部分匹配）

[Detection]
enabled = true
detection_interval = 0.3
player_name_color = green,white  # 玩家名字颜色

[Teleport]
enabled = true
teleport_key = F4
cooldown = 10
```

### 游戏窗口说明

- **登录器窗口**: `Legend of Mir2`（可最小化）
- **游戏窗口**: `九五沉默[区号] - [用户名]`
  - 例如：`九五沉默11号B组01区 - 千问`
  - 配置文件中只需填 `九五沉默` 即可

### 测试结果

```
✓ OpenCV 正常工作
✓ NumPy 正常工作
✓ PyAutoGUI 正常工作
✓ Keyboard 正常工作
✓ Win32GUI 正常工作
✓ 找到游戏窗口: 九五沉默11号B组01区 - 等待
  窗口大小: 1936 x 1119
```

### 使用方法

```bash
# 运行测试
cd test
python test_all.py

# 运行主程序
python mir2_auto_bot.py
```

### 注意事项

1. 确保游戏窗口已打开且可见
2. 登录器窗口可以最小化
3. 游戏窗口标题格式：`九五沉默[区号] - [用户名]`
4. 配置文件中的 `window_title` 只需填 `九五沉默` 即可

## v1.0 - 初始版本

### 基础功能
- 自动检测玩家（基于颜色检测）
- 自动使用随机传送石
- 配置文件支持
- 游戏窗口检测和激活

### 技术栈
- Python 3.x
- Pygame（已移除）
- OpenCV
- PyAutoGUI
- Keyboard
