# 单元测试文档

## 概述

本项目包含完整的单元测试套件，用于测试核心功能的正确性。

## 测试结构

```
script/v2_minimap/tests/
├── __init__.py              # 测试包初始化
├── test_minimap_detector.py # 小地图检测器测试
├── test_config.py           # 配置加载测试
└── test_utils.py            # 工具函数测试
```

## 安装测试依赖

```bash
pip install pytest pytest-cov pytest-html
```

## 运行测试

### 方法1: 使用批处理脚本（Windows）

```bash
# 运行所有测试
run_tests.bat

# 详细输出
run_tests.bat -v

# 生成覆盖率报告
run_tests.bat --cov

# 生成HTML报告
run_tests.bat --html
```

### 方法2: 使用pytest命令

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试文件
python -m pytest tests/test_minimap_detector.py

# 运行特定测试类
python -m pytest tests/test_minimap_detector.py::TestMinimapDetector

# 运行特定测试方法
python -m pytest tests/test_minimap_detector.py::TestMinimapDetector::test_detect_single_yellow_dot

# 详细输出
python -m pytest tests/ -v

# 显示打印输出
python -m pytest tests/ -s

# 生成覆盖率报告
python -m pytest tests/ --cov=. --cov-report=html

# 生成JUnit XML报告
python -m pytest tests/ --junitxml=test-results.xml
```

## 测试覆盖范围

### 1. MinimapDetector 测试 (test_minimap_detector.py)

- ✅ 单个黄点检测
- ✅ 多个黄点检测
- ✅ 无黄点情况
- ✅ 忽略其他颜色
- ✅ 黄色颜色范围检测
- ✅ 小轮廓过滤
- ✅ 模拟真实小地图检测
- ✅ 边界情况处理
- ✅ 自定义颜色范围

### 2. 配置加载测试 (test_config.py)

- ✅ 默认配置创建
- ✅ 配置值读取
- ✅ 缺失配置文件处理
- ✅ 检测器参数更新
- ✅ 传送冷却时间配置
- ✅ 缺失section处理

### 3. 工具函数测试 (test_utils.py)

- ✅ 图像创建
- ✅ 颜色转换
- ✅ 图像掩码
- ✅ 轮廓检测
- ✅ 轮廓面积计算
- ✅ 轮廓矩计算
- ✅ 冷却时间计算
- ✅ 时间间隔测量
- ✅ 统计信息管理
- ✅ 坐标计算

## 测试标记

可以使用pytest标记来运行特定类型的测试：

```bash
# 运行单元测试
python -m pytest tests/ -m unit

# 运行慢速测试
python -m pytest tests/ -m slow

# 跳过慢速测试
python -m pytest tests/ -m "not slow"
```

## 持续集成

可以将测试集成到CI/CD流程中：

```yaml
# GitHub Actions 示例
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          cd script/v2_minimap
          python -m pytest tests/ --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 测试最佳实践

1. **测试命名**: 测试方法名应清晰描述测试内容
   - ✅ `test_detect_single_yellow_dot`
   - ❌ `test_1`

2. **测试独立性**: 每个测试应该独立运行，不依赖其他测试

3. **测试覆盖**: 确保测试覆盖正常情况、边界情况和异常情况

4. **断言清晰**: 使用清晰的断言消息
   ```python
   assert len(yellow_dots) == 1, f"应该检测到1个黄点，但检测到{len(yellow_dots)}个"
   ```

5. **测试数据**: 使用工厂方法创建测试数据
   ```python
   def create_test_image_with_yellow_dots(num_dots=3):
       # 创建测试图像
       pass
   ```

## 故障排查

### 测试失败常见原因

1. **导入错误**: 确保PYTHONPATH包含项目根目录
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **依赖缺失**: 安装所有必需依赖
   ```bash
   pip install -r requirements.txt
   ```

3. **路径问题**: 使用绝对路径或相对于测试文件的路径

4. **环境差异**: 某些测试可能依赖特定环境（如游戏窗口）

## 测试报告

### HTML报告

```bash
python -m pytest tests/ --html=test-report.html --self-contained-html
```

### 覆盖率报告

```bash
python -m pytest tests/ --cov=. --cov-report=html
# 然后打开 htmlcov/index.html
```

## 贡献测试

添加新测试时：

1. 在`tests/`目录下创建`test_*.py`文件
2. 导入必要的模块和pytest
3. 创建测试类继承`object`
4. 编写测试方法，以`test_`开头
5. 使用断言验证结果
6. 运行测试确保通过

## 联系方式

如有问题，请提交Issue或联系开发团队。
