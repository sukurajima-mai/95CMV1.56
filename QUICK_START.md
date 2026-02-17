# 快速开始指南

## 1. 安装依赖

### 方法1: 使用安装脚本（推荐）
```bash
cd script
install_deps.bat
```

### 方法2: 使用GUI
1. 双击运行 `start_gui.bat`
2. 点击"检查依赖"
3. 如果有缺失的依赖，点击"安装缺失依赖"

### 方法3: 手动安装
```bash
cd script
pip install -r requirements.txt
```

## 2. 安装Tesseract OCR

### 下载和安装
1. 访问 https://github.com/UB-Mannheim/tesseract/wiki
2. 下载Windows版本的安装程序
3. 安装时勾选"中文简体"语言包
4. 将安装路径添加到系统PATH环境变量

### 验证安装
```bash
tesseract --version
tesseract --list-langs
```

应该看到包含 `chi_sim` 的语言列表。

### 使用GUI检查
1. 双击运行 `start_gui.bat`
2. 点击"检查Tesseract"按钮
3. 查看安装状态

## 3. 测试功能

### 测试OCR识别
```bash
cd script/test
test_ocr.bat
```

或使用GUI：
1. 双击运行 `start_gui.bat`
2. 点击"测试窗口检测"
3. 点击"测试截图"
4. 查看日志和debug图片

### 运行完整测试
```bash
cd script/test
python test_all.py
```

## 4. 配置设置

### 使用GUI配置（推荐）
1. 双击运行 `start_gui.bat`
2. 在右侧"设置"面板中：
   - 修改"检测关键词"（默认：人物斩杀）
   - 修改"传送按键"（默认：2）
   - 调整"检测间隔"（默认：0.3秒）
   - 调整"传送冷却"（默认：4秒）
   - 调整"检测范围"（上下左右百分比）
3. 点击"测试截图"查看检测范围预览
4. 点击"应用设置"保存配置

### 手动配置
编辑 `bot_config.ini` 文件：
```ini
[Detection]
enabled = true
detection_interval = 0.3
debug = true

[Teleport]
enabled = true
teleport_key = 2
cooldown = 4

[Advanced]
detection_top_percent = 20
detection_bottom_percent = 60
detection_left_percent = 5
detection_right_percent = 95
```

## 5. 启动挂机

### 使用GUI（推荐）
1. 双击运行 `start_gui.bat`
2. 确保游戏窗口已打开
3. 点击"启动"按钮
4. 查看日志输出
5. 需要时点击"暂停"或"停止"

### 使用命令行
```bash
cd script
start_bot.bat
```

按 `F10` 停止挂机。

## 6. 常见问题

### 找不到游戏窗口
- 确保游戏窗口已打开
- 检查窗口标题是否匹配（默认：九五沉默）
- 使用"测试窗口检测"按钮测试

### 检测不到目标文字
- 检查Tesseract OCR是否已安装
- 检查中文语言包是否已安装
- 调整检测范围
- 查看debug文件夹中的截图

### 传送按键没有反应
- 确认游戏内已绑定传送石到该按键
- 确认按键名称正确（如：'2', 'F4'）
- 测试按键功能

### OCR识别失败
- 运行 `test_ocr.bat` 测试
- 检查Tesseract是否在PATH中
- 检查中文语言包是否已安装

## 7. 文档导航

- [README.md](README.md) - 主文档
- [GUI_README.md](GUI_README.md) - GUI使用说明
- [SETTINGS.md](SETTINGS.md) - 设置说明
- [DEPENDENCIES.md](DEPENDENCIES.md) - 依赖管理说明
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 问题排查指南
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 项目结构说明
- [CHANGELOG.md](CHANGELOG.md) - 更新日志

## 8. 获取帮助

### 查看日志
- GUI日志：在GUI界面中查看
- 命令行日志：查看 `mir2_bot.log` 文件
- Debug图片：查看 `debug/` 目录

### 运行测试
```bash
cd script/test
python test_all.py
```

### 查看问题排查指南
[点击查看 TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 9. 快速命令

### 安装依赖
```bash
cd script
install_deps.bat
```

### 启动GUI
```bash
cd script
start_gui.bat
```

### 启动命令行版本
```bash
cd script
start_bot.bat
```

### 测试OCR
```bash
cd script/test
test_ocr.bat
```

### 完整测试
```bash
cd script/test
python test_all.py
```

## 10. 版本信息

当前版本: v3.3

更新日期: 2026-02-13

主要功能:
- 图形界面
- OCR文字识别
- 依赖管理
- 设置面板
- 检测范围可视化
- 自动清理debug文件夹

## 下一步

- 查看 [GUI_README.md](GUI_README.md) 了解GUI详细功能
- 查看 [SETTINGS.md](SETTINGS.md) 了解设置选项
- 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 解决常见问题
