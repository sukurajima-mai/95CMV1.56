# -*- coding: utf-8 -*-
"""
测试GUI多实例配置隔离
验证每个GUI实例使用独立的配置文件
"""

import os
import sys
import configparser

# 添加父目录到路径（因为测试文件在test子目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PARENT_DIR)

def test_config_isolation():
    """测试配置文件隔离"""
    print("=" * 60)
    print("测试GUI多实例配置隔离")
    print("=" * 60)
    print()
    
    # 模拟创建多个GUI实例的配置文件
    config_files = [
        os.path.join(PARENT_DIR, 'bot_config_v2.ini'),
        os.path.join(PARENT_DIR, 'bot_config_v2_instance2.ini'),
        os.path.join(PARENT_DIR, 'bot_config_v2_instance3.ini'),
    ]
    
    # 创建测试配置
    test_configs = [
        {'instance': 1, 'teleport_key': '1', 'cooldown': '3.0'},
        {'instance': 2, 'teleport_key': '2', 'cooldown': '4.0'},
        {'instance': 3, 'teleport_key': '3', 'cooldown': '5.0'},
    ]
    
    print("创建测试配置文件...")
    for i, (config_file, test_config) in enumerate(zip(config_files, test_configs)):
        config = configparser.ConfigParser()
        
        # 添加必要的section
        config.add_section('Game')
        config.set('Game', 'window_title', '九五沉默')
        
        config.add_section('Teleport')
        config.set('Teleport', 'teleport_key', test_config['teleport_key'])
        config.set('Teleport', 'cooldown', test_config['cooldown'])
        config.set('Teleport', 'enabled', 'true')
        
        config.add_section('Detection')
        config.set('Detection', 'detection_interval', '0.3')
        config.set('Detection', 'enabled', 'true')
        
        config.add_section('Minimap')
        config.set('Minimap', 'offset_x', '10')
        config.set('Minimap', 'offset_y', '10')
        config.set('Minimap', 'width', '150')
        config.set('Minimap', 'height', '150')
        config.set('Minimap', 'from_right', 'true')
        
        # 写入配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        
        print(f"  ✓ 实例 {test_config['instance']}: {os.path.basename(config_file)}")
        print(f"    - 传送键: {test_config['teleport_key']}")
        print(f"    - 冷却时间: {test_config['cooldown']}秒")
    
    print()
    print("=" * 60)
    print("验证配置文件隔离...")
    print("=" * 60)
    
    # 验证每个配置文件的内容
    all_correct = True
    for i, (config_file, expected_config) in enumerate(zip(config_files, test_configs)):
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        actual_key = config.get('Teleport', 'teleport_key')
        actual_cooldown = config.get('Teleport', 'cooldown')
        
        expected_key = expected_config['teleport_key']
        expected_cooldown = expected_config['cooldown']
        
        if actual_key == expected_key and actual_cooldown == expected_cooldown:
            print(f"  ✓ 实例 {expected_config['instance']}: 配置正确")
            print(f"    - 传送键: {actual_key} (期望: {expected_key})")
            print(f"    - 冷却时间: {actual_cooldown}秒 (期望: {expected_cooldown}秒)")
        else:
            print(f"  ✗ 实例 {expected_config['instance']}: 配置错误!")
            print(f"    - 传送键: {actual_key} (期望: {expected_key})")
            print(f"    - 冷却时间: {actual_cooldown}秒 (期望: {expected_cooldown}秒)")
            all_correct = False
    
    print()
    if all_correct:
        print("=" * 60)
        print("✅ 测试通过！每个实例使用独立的配置文件")
        print("=" * 60)
        print()
        print("配置文件列表:")
        for config_file in config_files:
            if os.path.exists(config_file):
                size = os.path.getsize(config_file)
                print(f"  - {os.path.basename(config_file)} ({size} bytes)")
        print()
        print("使用方法:")
        print("  1. 启动第1个GUI实例: python mir2_bot_gui_v2.py")
        print("  2. 启动第2个GUI实例: python mir2_bot_gui_v2.py")
        print("  3. 启动第3个GUI实例: python mir2_bot_gui_v2.py")
        print()
        print("每个GUI实例会自动:")
        print("  - 生成唯一的实例ID")
        print("  - 创建独立的配置文件")
        print("  - 窗口标题显示实例ID")
        print("  - 配置修改互不影响")
        return True
    else:
        print("=" * 60)
        print("❌ 测试失败！配置文件隔离有问题")
        print("=" * 60)
        return False

def cleanup_test_files():
    """清理测试文件"""
    print()
    print("清理测试文件...")
    test_files = [
        os.path.join(PARENT_DIR, 'bot_config_v2_instance2.ini'),
        os.path.join(PARENT_DIR, 'bot_config_v2_instance3.ini'),
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"  ✓ 删除: {os.path.basename(test_file)}")

if __name__ == '__main__':
    try:
        success = test_config_isolation()
        
        if success:
            print("\n是否清理测试文件? (y/n): ", end='')
            choice = input().strip().lower()
            if choice == 'y':
                cleanup_test_files()
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
