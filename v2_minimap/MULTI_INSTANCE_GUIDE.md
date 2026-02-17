# V2版本多实例使用说明

## 问题描述

之前V2命令行版本存在一个问题：打开多个bot实例时，所有实例都只能检测同一个窗口（第一个找到的窗口）。

## 问题原因

`mir2_auto_bot_v2.py` 中的 `find_game_window()` 方法总是选择找到的第一个窗口：

```python
if windows:
    self.hwnd, self.window_title = windows[0]  # ❌ 总是选择第一个窗口
```

## 解决方案

### 1. 添加窗口索引参数

修改了 `Mir2AutoBotV2` 类，添加 `window_index` 参数：

```python
def __init__(self, config_file: str = None, window_index: int = 0):
    # ...
    self.window_index = window_index
```

### 2. 修改窗口选择逻辑

修改 `find_game_window()` 方法，根据索引选择窗口：

```python
if windows:
    # 根据窗口索引选择窗口
    if self.window_index < len(windows):
        self.hwnd, self.window_title = windows[self.window_index]
        logger.info(f"找到 {len(windows)} 个游戏窗口，选择第 {self.window_index + 1} 个窗口")
    else:
        logger.warning(f"窗口索引 {self.window_index} 超出范围，使用第一个窗口")
        self.hwnd, self.window_title = windows[0]
```

### 3. 添加命令行参数支持

修改 `main()` 函数，支持命令行参数：

```python
# 解析窗口索引参数
window_index = 0
if len(sys.argv) > 1:
    try:
        window_index = int(sys.argv[1])
    except ValueError:
        print(f"警告: 无效的窗口索引参数，使用默认值 0")

bot = Mir2AutoBotV2(window_index=window_index)
```

## 使用方法

### 方法1: 命令行参数

```bash
# 监控第1个窗口
python mir2_auto_bot_v2.py 0

# 监控第2个窗口
python mir2_auto_bot_v2.py 1

# 监控第3个窗口
python mir2_auto_bot_v2.py 2
```

### 方法2: 使用批处理文件

运行 `start_bot_instance.bat`，输入窗口索引：

```
请输入窗口索引 (0=第1个窗口, 1=第2个窗口...): 0
```

### 方法3: Python代码

```python
from mir2_auto_bot_v2 import Mir2AutoBotV2

# 创建监控第1个窗口的实例
bot1 = Mir2AutoBotV2(window_index=0)
bot1.run()

# 创建监控第2个窗口的实例
bot2 = Mir2AutoBotV2(window_index=1)
bot2.run()
```

## 多实例运行示例

### 场景：同时监控3个游戏窗口

**步骤1**: 启动3个游戏窗口

**步骤2**: 打开3个命令行窗口，分别运行：

```bash
# 命令行窗口1
cd d:\95CMV1.56\script\v2_minimap
python mir2_auto_bot_v2.py 0

# 命令行窗口2
cd d:\95CMV1.56\script\v2_minimap
python mir2_auto_bot_v2.py 1

# 命令行窗口3
cd d:\95CMV1.56\script\v2_minimap
python mir2_auto_bot_v2.py 2
```

**结果**: 每个bot实例监控不同的游戏窗口，互不干扰。

## 测试验证

运行测试脚本验证修复效果：

```bash
# 测试窗口索引逻辑（不需要游戏运行）
python test_window_index_logic.py

# 测试实际窗口选择（需要游戏运行）
python test_multi_instance.py
```

## 注意事项

1. **窗口索引从0开始**: 0表示第1个窗口，1表示第2个窗口，以此类推
2. **索引超出范围**: 如果指定的索引超出范围，会自动使用第一个窗口
3. **窗口顺序**: 窗口顺序由Windows系统决定，通常是按窗口创建顺序或Z序排列
4. **GUI版本**: GUI版本已经通过窗口选择下拉框解决了这个问题，无需使用命令行参数

## 与多窗口模式的区别

### V2单窗口多实例模式（本次修复）
- 每个bot实例是独立的进程
- 每个实例监控一个窗口
- 需要手动启动多个实例
- 适合需要独立控制每个窗口的场景

### 多窗口模式（mir2_multi_window_bot.py）
- 单个bot进程监控多个窗口
- 自动检测所有游戏窗口
- 统一管理所有窗口
- 适合需要集中管理的场景

## 更新历史

- 2026-02-17: 修复V2命令行版本多实例窗口检测问题
- 2026-02-17: 添加window_index参数支持
- 2026-02-17: 添加命令行参数支持
- 2026-02-17: 创建启动脚本和测试脚本
