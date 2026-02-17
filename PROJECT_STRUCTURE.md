# 项目结构说明

## 目录结构

```
script/
├── mir2_auto_bot.py         # 命令行版本主程序
├── mir2_bot_gui.py          # 图形界面版本主程序
├── dependency_manager.py    # 依赖管理模块
├── bot_config.ini           # 配置文件
├── requirements.txt         # Python依赖列表
├── install_deps.bat         # 依赖安装脚本
├── start_bot.bat            # 启动命令行版本
├── start_gui.bat            # 启动图形界面版本
│
├── README.md                # 主文档
├── GUI_README.md            # GUI使用说明
├── SETTINGS.md              # 设置说明
├── DEPENDENCIES.md          # 依赖管理说明
├── TROUBLESHOOTING.md       # 问题排查指南
├── CHANGELOG.md             # 更新日志
├── PROJECT_STRUCTURE.md     # 本文档
│
├── test/                    # 测试脚本目录
│   ├── README.md            # 测试脚本说明
│   ├── test_all.py          # 完整功能测试
│   ├── test_bot.py          # 依赖测试
│   ├── test_config.py       # 配置测试
│   ├── test_window_detection.py  # 窗口检测测试
│   ├── test_window_rect.py       # 窗口矩形测试
│   ├── test_keypress.py          # 按键测试
│   ├── test_white_text.py        # 白色文字检测测试
│   ├── test_ocr.py              # OCR识别测试
│   ├── check_window_state.py     # 窗口状态检查
│   ├── list_windows.py           # 窗口列表工具
│   ├── quick_test.py            # 快速测试
│   ├── check_python.bat         # Python环境检查
│   ├── test_ocr.bat             # OCR测试批处理
│   ├── todo.md                  # 待办事项
│   └── tool.png                 # 测试工具图片
│
├── debug/                   # 调试图片目录（自动生成）
│   ├── 00_full_screen_*.jpg     # 完整屏幕截图
│   ├── 01_detection_region_*.jpg # 检测区域截图
│   └── 02_detection_result_*.jpg # 检测结果（带标注）
│
└── mir2_bot.log            # 运行日志（自动生成）
```

## 文件说明

### 主程序文件

#### mir2_auto_bot.py
- **类型**: Python脚本
- **功能**: 命令行版本的挂机脚本
- **启动方式**: `start_bot.bat` 或 `python mir2_auto_bot.py`
- **特点**: 纯命令行界面，适合高级用户

#### mir2_bot_gui.py
- **类型**: Python脚本 + Tkinter GUI
- **功能**: 图形界面版本的挂机脚本
- **启动方式**: `start_gui.bat` 或 `python mir2_bot_gui.py`
- **特点**: 友好的图形界面，包含设置和依赖管理功能

#### dependency_manager.py
- **类型**: Python模块
- **功能**: 依赖包检测、安装和更新
- **使用方式**: 被mir2_bot_gui.py调用
- **特点**: 自动检测缺失依赖，一键安装

### 配置文件

#### bot_config.ini
- **类型**: INI配置文件
- **功能**: 存储所有设置参数
- **包含内容**:
  - 游戏窗口标题
  - 检测设置（间隔、调试模式等）
  - 传送设置（按键、冷却时间）
  - 高级设置（检测范围）

#### requirements.txt
- **类型**: 文本文件
- **功能**: Python依赖包列表
- **包含内容**: 所有必需的Python包及其版本要求

### 启动脚本

#### install_deps.bat
- **类型**: Windows批处理文件
- **功能**: 安装所有Python依赖包
- **使用方式**: 双击运行

#### start_bot.bat
- **类型**: Windows批处理文件
- **功能**: 启动命令行版本
- **使用方式**: 双击运行

#### start_gui.bat
- **类型**: Windows批处理文件
- **功能**: 启动图形界面版本
- **使用方式**: 双击运行

### 文档文件

#### README.md
- **内容**: 主文档，包含功能介绍、安装指南、使用方法
- **目标用户**: 所有用户

#### GUI_README.md
- **内容**: GUI版本使用说明
- **目标用户**: 使用GUI版本的用户

#### SETTINGS.md
- **内容**: 设置说明，包含所有设置选项的详细说明
- **目标用户**: 需要调整设置的用户

#### DEPENDENCIES.md
- **内容**: 依赖管理说明，包含依赖包列表和使用方法
- **目标用户**: 需要管理依赖的用户

#### TROUBLESHOOTING.md
- **内容**: 问题排查指南，包含常见问题和解决方法
- **目标用户**: 遇到问题的用户

#### CHANGELOG.md
- **内容**: 版本更新记录
- **目标用户**: 想了解更新内容的用户

#### PROJECT_STRUCTURE.md
- **内容**: 本文档，项目结构说明
- **目标用户**: 开发者和高级用户

### 测试目录 (test/)

#### 测试脚本
- **test_all.py**: 完整功能测试
- **test_bot.py**: 依赖测试
- **test_config.py**: 配置测试
- **test_window_detection.py**: 窗口检测测试
- **test_window_rect.py**: 窗口矩形测试
- **test_keypress.py**: 按键测试
- **test_white_text.py**: 白色文字检测测试
- **test_ocr.py**: OCR识别测试

#### 工具脚本
- **check_window_state.py**: 窗口状态检查
- **list_windows.py**: 窗口列表工具
- **quick_test.py**: 快速测试
- **check_python.bat**: Python环境检查
- **test_ocr.bat**: OCR测试批处理

#### 其他文件
- **todo.md**: 待办事项列表
- **tool.png**: 测试工具图片

### 调试目录 (debug/)

- **类型**: 自动生成的目录
- **内容**: 调试图片
- **包含文件**:
  - `00_full_screen_*.jpg`: 完整屏幕截图
  - `01_detection_region_*.jpg`: 检测区域截图
  - `02_detection_result_*.jpg`: 检测结果（带标注）
- **清理**: 退出GUI时自动清空

### 日志文件

#### mir2_bot.log
- **类型**: 文本文件
- **功能**: 运行日志
- **内容**: 启动信息、检测统计、错误信息
- **生成**: 自动生成

## 使用流程

### 首次使用
```
1. 运行 install_deps.bat 安装依赖
2. 运行 test/test_ocr.py 测试OCR功能
3. 运行 start_gui.bat 启动GUI
4. 在GUI中调整设置
5. 点击"启动"开始挂机
```

### 日常使用
```
1. 运行 start_gui.bat 启动GUI
2. 点击"启动"开始挂机
3. 需要时点击"暂停"或"停止"
```

### 遇到问题
```
1. 查看 TROUBLESHOOTING.md
2. 运行 test/ 目录下的测试脚本
3. 查看 debug/ 目录下的调试图片
4. 查看 mir2_bot.log 日志文件
```

## 文件关系图

```
mir2_bot_gui.py
    ├── dependency_manager.py (依赖管理)
    ├── mir2_auto_bot.py (核心逻辑)
    ├── bot_config.ini (配置文件)
    └── test/ (测试脚本)

mir2_auto_bot.py
    ├── bot_config.ini (配置文件)
    └── requirements.txt (依赖列表)
```

## 命名规范

### Python文件
- 主程序: `mir2_*.py`
- 测试脚本: `test_*.py` 或 `check_*.py`
- 模块: `*.py`

### 批处理文件
- 安装脚本: `install_*.bat`
- 启动脚本: `start_*.bat`
- 测试脚本: `test_*.bat` 或 `check_*.bat`

### 文档文件
- 主文档: `README.md`
- 专题文档: `*.md` (大写)
- 测试文档: `test/README.md`

## 维护建议

### 添加新功能
1. 在 `mir2_auto_bot.py` 中添加核心逻辑
2. 在 `mir2_bot_gui.py` 中添加GUI界面
3. 在 `test/` 目录添加测试脚本
4. 更新相关文档

### 更新依赖
1. 修改 `requirements.txt`
2. 更新 `dependency_manager.py`
3. 更新 `DEPENDENCIES.md`
4. 运行测试验证

### 修改设置
1. 修改 `bot_config.ini` 默认值
2. 更新 `SETTINGS.md`
3. 更新GUI界面（如果需要）

### 添加测试
1. 在 `test/` 目录创建测试脚本
2. 更新 `test/README.md`
3. 运行测试验证

## 清理建议

### 可以安全删除的文件
- `mir2_bot.log` (运行日志)
- `debug/` 目录下的所有文件 (调试图片)
- `__pycache__/` 目录 (Python缓存)

### 不应删除的文件
- 所有 `*.py` 文件
- `*.bat` 文件
- `*.ini` 配置文件
- `*.md` 文档文件
- `requirements.txt`

## 版本历史

### v3.3 - 完整版本 (2026-02-13)
- 添加图形界面
- 添加依赖管理
- 添加设置面板
- 添加检测范围可视化
- 添加退出时清理功能
- 整理测试文件到test目录
