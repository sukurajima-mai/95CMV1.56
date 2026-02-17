# 窗口检测问题修复说明

## 问题描述

在其他设备上测试时遇到以下问题：

1. **检测范围异常**：截图范围比正常的游戏窗口多出了右下角的黑边
2. **检测成功率极低**：OCR识别成功率很低，无法正确检测目标文字

## 问题根源分析

### 问题一：检测范围异常

**原因**：
- 原代码使用 `win32gui.GetWindowRect()` 获取窗口矩形
- 这个方法返回的是**整个窗口**的矩形，包括：
  - 标题栏
  - 窗口边框
  - 菜单栏
  - 状态栏
  - 客户区（实际游戏画面）

- 不同设备的DPI缩放比例、窗口样式、主题设置不同，导致：
  - 边框宽度不一致
  - 标题栏高度不一致
  - 客户区位置偏移不同

**结果**：
- 截图时包含了非游戏画面的区域（黑边）
- 检测范围计算错误
- OCR识别区域不正确

### 问题二：检测成功率极低

**原因**：
1. **目标文字不一致**：
   - 代码中第79行定义：`self.target_text = "人物斩杀"`
   - 代码中第139行又定义：`self.target_text = "游戏斩杀"`（覆盖了前一个）
   - 导致实际检测的文字与游戏中的文字不匹配

2. **检测范围配置不当**：
   - 当前配置：`detection_right_percent = 80`
   - 可能检测范围过小，错过了目标文字的位置

3. **截图区域错误**：
   - 由于使用了错误的窗口矩形，截图包含了黑边
   - OCR在黑边区域无法识别文字

## 修复方案

### 修复一：使用客户区坐标进行截图

**修改内容**：

1. **添加客户区信息获取**：
```python
def find_game_window(self) -> bool:
    # ... 原有代码 ...

    # 获取客户区矩形（游戏画面的实际区域）
    self.client_rect = win32gui.GetClientRect(self.hwnd)

    # 计算客户区相对于窗口的偏移
    client_left, client_top = win32gui.ClientToScreen(self.hwnd, (0, 0))
    window_left, window_top = self.window_rect[0], self.window_rect[1]

    self.client_offset = (client_left - window_left, client_top - window_top)

    logger.info(f"客户区大小: {self.client_rect}")
    logger.info(f"客户区偏移: {self.client_offset}")
```

2. **修改截图函数**：
```python
def capture_game_screen(self) -> Optional[np.ndarray]:
    # 使用客户区的屏幕坐标进行截图
    window_left, window_top = self.window_rect[0], self.window_rect[1]
    offset_x, offset_y = self.client_offset

    # 客户区的屏幕坐标
    client_screen_left = window_left + offset_x
    client_screen_top = window_top + offset_y

    # 客户区的大小
    client_width, client_height = self.client_rect

    # 截取客户区区域
    screenshot = pyautogui.screenshot(
        region=(client_screen_left, client_screen_top, client_width, client_height)
    )

    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
```

**效果**：
- 只截取游戏画面的实际区域
- 避免包含标题栏、边框等非游戏区域
- 适应不同设备的窗口样式和DPI设置

### 修复二：统一目标文字

**修改内容**：
```python
def __init__(self, config_file: str = None):
    # ... 其他初始化代码 ...

    # 统一使用正确的目标文字
    self.target_text = "人物斩杀"  # 要检测的目标文字
```

**效果**：
- 确保检测的目标文字与游戏中的文字一致
- 避免因文字不匹配导致的检测失败

### 修复三：添加诊断工具

**新增文件**：`test/window_diagnostic.py`

**功能**：
- 查找游戏窗口
- 获取窗口详细信息
- 对比整个窗口和客户区的区别
- 生成诊断截图

**使用方法**：
```bash
cd script
python test\window_diagnostic.py
```

**输出内容**：
- 窗口标题和句柄
- 窗口矩形（整个窗口）
- 客户区矩形（游戏画面）
- 客户区偏移量
- 窗口样式信息
- 对比截图

## 使用修复工具

### 方法一：使用快速修复脚本

```bash
cd script
fix_window_issues.bat
```

这个脚本会：
1. 创建调试目录
2. 运行窗口诊断工具
3. 生成诊断截图
4. 显示修复结果

### 方法二：手动运行诊断

```bash
cd script
python test\window_diagnostic.py
```

## 验证修复

### 1. 查看诊断截图

修复完成后，查看 `debug/` 目录下的截图：

- `debug/01_full_window.jpg` - 整个窗口截图（包含标题栏和边框）
- `debug/02_client_area.jpg` - 客户区截图（只有游戏画面）
- `debug/03_comparison.jpg` - 对比图

**验证标准**：
- 客户区截图应该只包含游戏画面
- 不应该有黑边
- 不应该有标题栏或窗口边框

### 2. 查看日志信息

运行脚本时，查看输出的日志：

```
找到游戏窗口: 九五沉默11号B组01区 - 等待
窗口位置: (100, 100, 900, 700)
客户区大小: (800, 600)
客户区偏移: (8, 31)
```

**验证标准**：
- 客户区偏移应该反映窗口边框和标题栏的大小
- 客户区大小应该与游戏画面大小一致

### 3. 测试检测功能

启动脚本并测试：

```bash
cd script
start_gui.bat
```

**验证标准**：
- 截图应该只包含游戏画面
- 检测范围应该在游戏画面内
- OCR识别成功率应该提高

## 常见问题排查

### 问题1：客户区截图仍有黑边

**可能原因**：
- 窗口使用了非标准样式
- 窗口有额外的装饰元素

**解决方法**：
1. 运行诊断工具查看窗口样式
2. 检查是否有额外的窗口装饰
3. 尝试调整客户区偏移值

### 问题2：检测成功率仍然很低

**可能原因**：
1. 目标文字不对
2. 检测范围配置不当
3. 游戏画面模糊或分辨率低

**解决方法**：

1. **确认目标文字**：
   - 在游戏中查看实际显示的文字
   - 修改代码中的 `target_text` 变量

2. **调整检测范围**：
   编辑 `bot_config.ini`：
   ```ini
   [Advanced]
   detection_top_percent = 10      # 上边界（屏幕百分比）
   detection_bottom_percent = 80   # 下边界（屏幕百分比）
   detection_left_percent = 5      # 左边界（屏幕百分比）
   detection_right_percent = 95    # 右边界（屏幕百分比）
   ```

3. **启用调试模式**：
   ```ini
   [Detection]
   debug = true
   ```
   查看检测区域的截图

### 问题3：找不到游戏窗口

**可能原因**：
- 窗口标题匹配失败
- 游戏窗口未打开
- 窗口被最小化

**解决方法**：
1. 运行诊断工具查看所有窗口
2. 确认游戏窗口已打开
3. 检查窗口标题是否匹配

### 问题4：截图失败

**可能原因**：
- 窗口不在前台
- 窗口被其他窗口遮挡
- 权限不足

**解决方法**：
1. 激活游戏窗口
2. 以管理员权限运行脚本
3. 关闭其他可能遮挡的窗口

## 技术细节

### 窗口坐标系

Windows窗口有两个坐标系：

1. **窗口坐标系**：
   - 原点在窗口左上角
   - 包含整个窗口（标题栏、边框、客户区）
   - 使用 `GetWindowRect()` 获取

2. **客户区坐标系**：
   - 原点在客户区左上角
   - 只包含客户区（游戏画面）
   - 使用 `GetClientRect()` 获取

### 坐标转换

```python
# 获取客户区的屏幕坐标
client_screen_x, client_screen_y = win32gui.ClientToScreen(hwnd, (0, 0))

# 计算客户区相对于窗口的偏移
offset_x = client_screen_x - window_rect[0]
offset_y = client_screen_y - window_rect[1]
```

### DPI缩放影响

不同设备的DPI缩放比例不同：

- 100% DPI：标准大小
- 125% DPI：窗口和文字放大25%
- 150% DPI：窗口和文字放大50%

**影响**：
- 窗口边框宽度变化
- 标题栏高度变化
- 客户区偏移变化

**解决方法**：
- 使用客户区坐标（不受DPI影响）
- 动态计算偏移量

## 总结

通过以下修复，可以解决窗口检测问题：

1. ✓ 使用客户区坐标进行截图（避免黑边）
2. ✓ 动态计算窗口偏移（适应不同设备）
3. ✓ 统一目标文字（提高检测准确率）
4. ✓ 添加诊断工具（方便调试）

修复后，脚本应该能够在不同设备上正常工作，检测成功率显著提高。

## 联系支持

如果问题仍然存在，请提供以下信息：

1. 诊断截图（debug/目录下的图片）
2. 日志文件（mir2_bot.log）
3. 系统信息（操作系统版本、DPI设置）
4. 游戏窗口截图（游戏画面中目标文字的位置）
