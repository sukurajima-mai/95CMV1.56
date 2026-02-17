# OCR检测问题排查指南

## 问题1: GUI按钮无响应

### 解决方法
1. 确保Python环境正常
2. 确保所有依赖包已安装
3. 尝试以管理员权限运行

### 测试步骤
1. 点击"测试窗口检测"按钮，查看是否能找到游戏窗口
2. 点击"测试截图"按钮，查看是否能正常截图
3. 如果以上测试都通过，但按钮仍无响应，可能是线程阻塞问题

## 问题2: OCR检测不到文字

### 可能原因
1. Tesseract OCR未正确安装
2. 中文语言包未安装
3. PATH环境变量未配置
4. 图像质量不佳
5. 检测范围设置不当

### 排查步骤

#### 1. 检查Tesseract安装
```bash
tesseract --version
tesseract --list-langs
```

应该看到包含 `chi_sim` 的语言列表。

#### 2. 测试OCR识别
运行测试脚本：
```bash
cd script
python test_ocr.py
```

或双击运行 `test_ocr.bat`

选择模式1，测试截图OCR识别。

#### 3. 查看调试信息
- 启用调试模式（已在配置文件中启用）
- 运行GUI程序
- 点击"启动"按钮
- 查看 `debug/` 目录下的图片：
  - `00_full_screen_*.jpg` - 完整屏幕截图
  - `01_detection_region_*.jpg` - 检测区域截图
  - `02_detection_result_*.jpg` - 检测结果（带标注）

#### 4. 查看日志输出
GUI会显示所有识别到的文字：
```
本次检测识别到的文字: 'xxx' (conf: 95), 'yyy' (conf: 80), ...
```

### 优化建议

#### 1. 调整检测范围
编辑 `bot_config.ini`：
```ini
[Advanced]
detection_top_percent = 10      # 检测范围上边界
detection_bottom_percent = 80   # 检测范围下边界
detection_left_percent = 5      # 检测范围左边界
detection_right_percent = 95    # 检测范围右边界
```

#### 2. 降低置信度阈值
如果识别率太低，可以降低阈值：
- 当前阈值：20
- 可以尝试：15 或 10

修改代码中的 `if conf > 20` 为 `if conf > 15`

#### 3. 尝试不同的PSM模式
代码已经尝试多种PSM模式（6, 7, 11, 12, 13），如果需要可以添加更多模式。

#### 4. 图像预处理
可以添加图像预处理步骤提高识别率：
- 提高对比度
- 去噪
- 二值化

## 问题3: Debug图片太多

### 解决方案
代码已经优化，每次检测都会生成带时间戳的图片：
- `00_full_screen_YYYYMMDD_HHMMSS.jpg`
- `01_detection_region_YYYYMMDD_HHMMSS.jpg`
- `02_detection_result_YYYYMMDD_HHMMSS.jpg`

这样可以避免图片被覆盖，方便对比不同时间的检测结果。

### 清理旧图片
定期清理 `debug/` 目录下的旧图片：
```bash
del script\debug\*.jpg
```

## 问题4: 窗口被遮挡时检测失败

### 已修复
新版本使用Win32 API的 `BitBlt` 函数直接从窗口设备上下文截图，即使窗口被遮挡也能正常捕获画面。

### 测试方法
1. 打开游戏窗口
2. 用其他窗口覆盖游戏窗口
3. 点击"测试截图"按钮
4. 查看截图是否正常

## 问题5: 窗口移动后检测失效

### 已修复
新版本每次检测前都会重新获取窗口位置：
```python
self.window_rect = win32gui.GetWindowRect(self.hwnd)
```

### 测试方法
1. 启动挂机脚本
2. 移动游戏窗口
3. 查看日志，检测应该继续正常工作

## 快速测试流程

### 1. 测试窗口检测
- 启动GUI
- 点击"测试窗口检测"
- 查看日志输出

### 2. 测试截图
- 点击"测试截图"
- 查看 `debug/` 目录下的截图

### 3. 测试OCR识别
- 运行 `test_ocr.bat`
- 选择模式1
- 查看识别结果

### 4. 测试完整流程
- 确保游戏窗口已打开
- 确保画面中有目标文字
- 点击"启动"
- 查看日志和debug图片

## 常见错误信息

### `TesseractNotFoundError`
- 原因：Tesseract OCR未安装或未添加到PATH
- 解决：安装Tesseract OCR并添加到PATH

### `Failed loading language 'chi_sim'`
- 原因：中文语言包未安装
- 解决：重新安装Tesseract OCR，勾选"中文简体"语言包

### `Image not found`
- 原因：截图失败
- 解决：检查游戏窗口是否可见，尝试以管理员权限运行

### `No text detected`
- 原因：OCR未识别到任何文字
- 解决：
  - 检查图像质量
  - 调整检测范围
  - 降低置信度阈值
  - 查看debug图片确认

## 联系支持

如果以上方法都无法解决问题，请提供以下信息：
1. Python版本
2. Tesseract版本
3. 已安装的语言包
4. Debug图片
5. 完整的错误日志
