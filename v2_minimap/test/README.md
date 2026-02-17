# V2版本测试脚本目录

本目录包含V2版本（小地图黄点检测）的所有测试脚本。

## 测试脚本列表

### 1. test_yellow_dot_detection.py
**功能**: 测试黄点检测功能
**用途**:
- 测试小地图黄点识别
- 验证HSV颜色范围
- 测试不同场景下的检测效果

**运行**:
```bash
cd d:\95CMV1.56\script\v2_minimap\test
python test_yellow_dot_detection.py
```

### 2. test_multi_instance.py
**功能**: 测试命令行版本多实例窗口选择
**用途**:
- 验证window_index参数
- 测试多实例窗口选择逻辑
- 验证每个实例选择不同窗口

**运行**:
```bash
cd d:\95CMV1.56\script\v2_minimap\test
python test_multi_instance.py
```

### 3. test_window_index_logic.py
**功能**: 模拟测试窗口索引选择逻辑
**用途**:
- 不需要游戏窗口运行
- 验证窗口索引选择逻辑
- 测试边界条件

**运行**:
```bash
cd d:\95CMV1.56\script\v2_minimap\test
python test_window_index_logic.py
```

### 4. test_gui_multi_instance.py
**功能**: 测试GUI多实例配置隔离
**用途**:
- 验证每个GUI实例使用独立配置文件
- 测试配置文件隔离
- 验证配置修改互不影响

**运行**:
```bash
cd d:\95CMV1.56\script\v2_minimap\test
python test_gui_multi_instance.py
```

### 5. test_fixed_screenshot.py
**功能**: 测试修复后的截屏功能
**用途**:
- 验证后台截图功能
- 测试BitBlt截图方法
- 检查截图质量

**运行**:
```bash
cd d:\95CMV1.56\script\v2_minimap\test
python test_fixed_screenshot.py
```

### 6. test_screenshot_issue.py
**功能**: 测试截图问题诊断
**用途**:
- 诊断截图相关问题
- 测试不同截图方法
- 生成诊断报告

**运行**:
```bash
cd d:\95CMV1.56\script\v2_minimap\test
python test_screenshot_issue.py
```

### 7. test_detection.bat
**功能**: 快速测试检测功能
**用途**:
- 批处理脚本快速启动测试
- 适合快速验证

**运行**:
```bash
cd d:\95CMV1.56\script\v2_minimap\test
test_detection.bat
```

## 测试运行说明

### 运行所有测试
```bash
cd d:\95CMV1.56\script\v2_minimap\test
python -m pytest
```

### 运行单个测试
```bash
cd d:\95CMV1.56\script\v2_minimap\test
python test_yellow_dot_detection.py
```

### 测试前准备
1. 确保游戏窗口已启动（部分测试需要）
2. 确保已安装所有依赖
3. 确保在正确的目录下运行

## 测试输出

### 调试图片
测试过程中生成的调试图片保存在：
- `../debug_v2/` - 黄点检测调试图片
- `../debug_test/` - 截图测试调试图片

### 配置文件
测试生成的配置文件保存在：
- `../bot_config_v2.ini` - 默认配置
- `../bot_config_v2_instanceN.ini` - 实例配置

## 测试覆盖范围

### 功能测试
- ✅ 黄点检测
- ✅ 窗口查找
- ✅ 后台截图
- ✅ 按键发送
- ✅ 配置管理

### 多实例测试
- ✅ 命令行版本多实例
- ✅ GUI版本多实例
- ✅ 配置文件隔离
- ✅ 窗口选择

### 边界测试
- ✅ 窗口索引超出范围
- ✅ 配置文件不存在
- ✅ 游戏窗口未启动

## 注意事项

1. **路径问题**: 测试脚本在test子目录，会自动添加父目录到路径
2. **游戏窗口**: 部分测试需要游戏窗口运行，请先启动游戏
3. **配置文件**: 测试会创建临时配置文件，可手动删除
4. **调试图片**: 测试会生成调试图片，定期清理

## 更新历史

- 2026-02-17: 整理测试文件到test目录
- 2026-02-17: 更新所有测试脚本的路径引用
- 2026-02-17: 添加README说明文档
