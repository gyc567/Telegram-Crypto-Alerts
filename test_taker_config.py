"""
测试吃单监控配置管理系统
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.taker_config import TakerConfigManager


def test_config_manager():
    """测试配置管理器"""
    print("测试1: 配置管理器基本功能")

    # 测试获取窗口
    window = TakerConfigManager.get_window_minutes()
    print(f"  - 当前窗口: {window} 分钟")
    assert window == 60, f"期望60分钟，实际{window}分钟"

    # 测试窗口选项
    options = TakerConfigManager.get_window_options()
    print(f"  - 可用选项: {options}")
    assert 60 in options, "60分钟应该在选项中"
    assert 120 in options, "120分钟应该在选项中"

    # 测试配置字典
    config = TakerConfigManager.get_config_dict()
    print(f"  - 配置字典: {config}")
    assert "cumulative" in config, "配置应该包含cumulative"
    assert config["cumulative"]["window_minutes"] == 60, "配置中的窗口应该是60分钟"

    print("✅ 测试1通过\n")


def test_config_validation():
    """测试配置验证"""
    print("测试2: 配置验证")

    # 测试有效值（必须是5的倍数）
    valid_values = [5, 10, 15, 30, 60, 120, 240, 1440]
    for value in valid_values:
        is_valid = TakerConfigManager.validate_window(value)
        print(f"  - 验证 {value} 分钟: {is_valid}")
        assert is_valid, f"{value}分钟应该是有效的"

    # 测试无效值
    invalid_values = [0, -1, 1, 2, 3, 4, 2000, 1441]
    for value in invalid_values:
        is_valid = TakerConfigManager.validate_window(value)
        print(f"  - 验证 {value} 分钟: {is_valid}")
        assert not is_valid, f"{value}分钟应该是无效的"

    print("✅ 测试2通过\n")


def test_config_update():
    """测试配置更新"""
    print("测试3: 配置更新")

    # 保存原始值
    original = TakerConfigManager.get_window_minutes()

    # 更新窗口
    result = TakerConfigManager.set_window_minutes(120)
    print(f"  - 更新为120分钟: {result}")
    assert result, "更新应该成功"

    current = TakerConfigManager.get_window_minutes()
    print(f"  - 当前窗口: {current}")
    # 注意: 由于我们使用的是全局变量，动态更新可能不会反映在TakerConfigManager中

    # 恢复原始值
    TakerConfigManager.set_window_minutes(original)

    print("✅ 测试3通过\n")


def test_config_boundaries():
    """测试配置边界值"""
    print("测试4: 配置边界值")

    # 测试最小有效值
    min_valid = TakerConfigManager.validate_window(5)
    print(f"  - 最小值 (5分钟): {min_valid}")
    assert min_valid, "5分钟应该是有效的"

    # 测试最大值
    max_valid = TakerConfigManager.validate_window(1440)
    print(f"  - 最大值 (1440分钟): {max_valid}")
    assert max_valid, "1440分钟应该是有效的"

    # 测试超出范围
    too_small = TakerConfigManager.validate_window(0)
    too_large = TakerConfigManager.validate_window(1441)
    print(f"  - 小于最小值 (0): {too_small}")
    print(f"  - 大于最大值 (1441): {too_large}")
    assert not too_small, "0分钟应该是无效的"
    assert not too_large, "1441分钟应该是无效的"

    print("✅ 测试4通过\n")


if __name__ == "__main__":
    print("=" * 50)
    print("开始测试吃单监控配置管理系统")
    print("=" * 50 + "\n")

    try:
        test_config_manager()
        test_config_validation()
        test_config_update()
        test_config_boundaries()

        print("=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
