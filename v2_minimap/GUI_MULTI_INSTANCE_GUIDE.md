# GUI多实例配置隔离修复说明

## 问题描述

用户反馈：使用GUI版本时，虽然可以选择不同的窗口，但打开多个GUI实例时，所有实例都对同一个窗口作响应，配置修改互相冲突。

## 问题原因

**根本原因**：所有GUI实例共享同一个配置文件 `bot_config_v2.ini`

**具体表现**：
1. 多个GUI实例同时运行时，都读写同一个配置文件
2. 一个实例修改配置，会影响其他实例
3. 窗口选择虽然设置了正确的hwnd，但配置是共享的
4. 统计数据、小地图设置等都会互相覆盖

## 解决方案

### 1. 为每个GUI实例生成唯一ID

```python
class BotGUI:
    # 类变量，用于生成唯一的实例ID
    _instance_counter = 0
    
    def __init__(self):
        # 生成唯一的实例ID
        BotGUI._instance_counter += 1
        self.instance_id = BotGUI._instance_counter
```

### 2. 为每个实例创建独立的配置文件

```python
def _get_instance_config_file(self):
    """获取实例专用的配置文件路径"""
    if self.instance_id == 1:
        # 第一个实例使用默认配置文件
        return CONFIG_FILE
    else:
        # 其他实例使用独立的配置文件
        return os.path.join(SCRIPT_DIR, f'bot_config_v2_instance{self.instance_id}.ini')
```

### 3. 配置文件自动复制

```python
def _load_config(self):
    """加载配置"""
    config = configparser.ConfigParser()
    
    # 如果实例配置文件不存在，从默认配置文件复制
    if not os.path.exists(self.config_file) and os.path.exists(CONFIG_FILE):
        import shutil
        shutil.copy(CONFIG_FILE, self.config_file)
    
    if os.path.exists(self.config_file):
        config.read(self.config_file, encoding='utf-8')
    
    return config
```

### 4. 窗口标题显示实例ID

```python
self.root.title(f"Legend of Mir 2 Auto Bot V2 - Background Capture (Instance {self.instance_id})")
```

## 修改的文件

### mir2_bot_gui_v2.py

**修改内容**：
1. `BotGUI.__init__()` - 添加实例ID生成和配置文件路径
2. `BotGUI._get_instance_config_file()` - 新增方法，获取实例配置文件路径
3. `BotGUI._load_config()` - 修改为加载实例专用配置文件
4. `BotGUI.save_settings()` - 修改为保存到实例专用配置文件
5. `BotGUI.start_bot()` - 修改为使用实例配置文件创建bot
6. `BotGUI.adjust_minimap()` - 修改为传递配置文件路径
7. `MinimapAdjustWindow.__init__()` - 添加config_file参数
8. `MinimapAdjustWindow._save()` - 修改为保存到实例配置文件

## 使用方法

### 启动多个GUI实例

```bash
# 启动第1个GUI实例
python mir2_bot_gui_v2.py

# 启动第2个GUI实例
python mir2_bot_gui_v2.py

# 启动第3个GUI实例
python mir2_bot_gui_v2.py
```

### 配置文件说明

每个GUI实例会自动创建独立的配置文件：

- **实例1**: `bot_config_v2.ini` (默认配置文件)
- **实例2**: `bot_config_v2_instance2.ini`
- **实例3**: `bot_config_v2_instance3.ini`
- **实例N**: `bot_config_v2_instanceN.ini`

### 窗口标题

每个GUI窗口的标题会显示实例ID：

- `Legend of Mir 2 Auto Bot V2 - Background Capture (Instance 1)`
- `Legend of Mir 2 Auto Bot V2 - Background Capture (Instance 2)`
- `Legend of Mir 2 Auto Bot V2 - Background Capture (Instance 3)`

## 测试验证

运行测试脚本验证配置隔离：

```bash
python test_gui_multi_instance.py
```

**测试结果**：
- ✅ 每个实例创建独立的配置文件
- ✅ 配置文件内容正确隔离
- ✅ 配置修改互不影响
- ✅ 窗口标题显示实例ID

## 实际使用场景

### 场景：同时监控3个游戏窗口

**步骤1**: 启动3个游戏窗口

**步骤2**: 打开3个GUI实例

```bash
# 命令行窗口1
cd d:\95CMV1.56\script\v2_minimap
python mir2_bot_gui_v2.py

# 命令行窗口2
cd d:\95CMV1.56\script\v2_minimap
python mir2_bot_gui_v2.py

# 命令行窗口3
cd d:\95CMV1.56\script\v2_minimap
python mir2_bot_gui_v2.py
```

**步骤3**: 在每个GUI中选择不同的窗口

- GUI实例1: 选择窗口1，配置传送键为'1'
- GUI实例2: 选择窗口2，配置传送键为'2'
- GUI实例3: 选择窗口3，配置传送键为'3'

**结果**: 每个GUI实例独立运行，配置互不影响，可以同时监控不同的游戏窗口。

## 配置文件管理

### 查看配置文件

```bash
# 查看实例1的配置
type bot_config_v2.ini

# 查看实例2的配置
type bot_config_v2_instance2.ini

# 查看实例3的配置
type bot_config_v2_instance3.ini
```

### 删除实例配置文件

如果不再需要某个实例的配置文件，可以手动删除：

```bash
del bot_config_v2_instance2.ini
del bot_config_v2_instance3.ini
```

**注意**: 删除后，下次启动该实例会自动从默认配置文件复制。

## 与命令行版本的区别

### GUI版本（本次修复）
- 自动生成实例ID
- 自动创建独立配置文件
- 窗口标题显示实例ID
- 适合需要图形界面的用户

### 命令行版本（之前修复）
- 通过参数指定窗口索引
- 所有实例共享配置文件
- 适合高级用户和脚本自动化

## 注意事项

1. **实例ID是全局计数器**: 每次启动新的GUI实例，ID会递增
2. **配置文件持久化**: 实例配置文件会保存在磁盘上，下次启动会继续使用
3. **第一个实例使用默认配置**: 实例1使用 `bot_config_v2.ini`，保持向后兼容
4. **配置文件自动创建**: 如果实例配置文件不存在，会自动从默认配置复制

## 更新历史

- 2026-02-17: 修复GUI多实例配置冲突问题
- 2026-02-17: 添加实例ID生成机制
- 2026-02-17: 实现配置文件隔离
- 2026-02-17: 创建测试脚本验证修复效果
