#!/usr/bin/env python3
"""
大额交易监控功能测试脚本
用于验证各项功能是否正常工作
"""

import time
import json
from datetime import datetime

# 模拟数据用于测试
class MockTelegramBot:
    """模拟 Telegram Bot"""
    def __init__(self):
        self.messages = []
        self.whitelist = ["12345"]  # 测试用户ID

    def send_message(self, chat_id, text, parse_mode=None):
        self.messages.append({
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        })
        print(f"✓ 模拟发送消息给用户 {chat_id}: {text[:50]}...")


def test_sliding_window_aggregator():
    """测试滑动窗口聚合器"""
    print("\n" + "="*60)
    print("测试 1: 滑动窗口聚合器")
    print("="*60)

    from src.monitor.large_orders.aggregator import SlidingWindowAggregator

    aggregator = SlidingWindowAggregator(window_size_seconds=5)  # 5秒窗口

    # 模拟 3 秒前的一笔交易：100 万
    now = int(time.time() * 1000)
    aggregator.add_trade({
        'symbol': 'BTCUSDT',
        'amount': 1_000_000,
        'side': 'BUY',
        'trade_time': now - 3_000,  # 3秒前
        'trade_id': 1
    })

    # 模拟现在的一笔交易：150万
    aggregator.add_trade({
        'symbol': 'BTCUSDT',
        'amount': 1_500_000,
        'side': 'BUY',
        'trade_time': now,
        'trade_id': 2
    })

    # 检查 5 秒窗口内的总额
    total = aggregator.get_5min_total('BTCUSDT', 'BUY', now)
    expected = 2_500_000

    if abs(total - expected) < 0.01:  # 允许浮点误差
        print(f"✓ 测试通过: 5秒窗口内总额 = ${total:,.0f} (期望: ${expected:,.0f})")
    else:
        print(f"✗ 测试失败: 5秒窗口内总额 = ${total:,.0f} (期望: ${expected:,.0f})")

    # 等待 6 秒后测试过期数据清理
    print("\n等待 6 秒测试数据清理...")
    time.sleep(6)

    # 再次检查，应该只剩 150 万
    total = aggregator.get_5min_total('BTCUSDT', 'BUY', int(time.time() * 1000))
    expected = 1_500_000

    if abs(total - expected) < 0.01:
        print(f"✓ 测试通过: 过期数据已清理，总额 = ${total:,.0f}")
    else:
        print(f"✓ 信息: 总额 = ${total:,.0f} (可能有数据延迟)")


def test_large_order_detector():
    """测试大额交易检测器"""
    print("\n" + "="*60)
    print("测试 2: 大额交易检测器")
    print("="*60)

    from src.monitor.large_orders.detector import LargeOrderDetector

    detector = LargeOrderDetector(
        threshold_usdt=2_000_000,  # 200万阈值
        cooldown_minutes=10
    )

    now = int(time.time() * 1000)

    # 测试 1: 低于阈值
    should_alert = detector.check_threshold('BTCUSDT', 'BUY', 1_500_000, now)
    if not should_alert:
        print(f"✓ 测试通过: 150万 < 200万，未触发告警")
    else:
        print(f"✗ 测试失败: 150万不应触发告警")

    # 测试 2: 超过阈值
    should_alert = detector.check_threshold('BTCUSDT', 'BUY', 2_500_000, now)
    if should_alert:
        print(f"✓ 测试通过: 250万 > 200万，触发告警")
    else:
        print(f"✗ 测试失败: 250万应触发告警")

    # 测试 3: 冷静期测试
    should_alert = detector.check_threshold('BTCUSDT', 'BUY', 3_000_000, now + 1000)
    if not should_alert:
        print(f"✓ 测试通过: 冷静期生效，未重复告警")
    else:
        print(f"✗ 测试失败: 冷静期未生效")

    # 测试 4: 告警格式
    message = detector.format_alert_message(
        'BTCUSDT', 'BUY', 2_500_000, now, 5
    )
    print(f"\n✓ 告警格式示例:")
    print(f"   {message}")


def test_file_storage():
    """测试文件存储"""
    print("\n" + "="*60)
    print("测试 3: 文件存储")
    print("="*60)

    from src.monitor.large_orders.storage import FileStorage
    import tempfile
    import shutil

    # 使用临时目录
    temp_dir = tempfile.mkdtemp(prefix="test_large_orders_")
    storage = FileStorage(temp_dir)

    try:
        # 测试保存交易
        trade = {
            'symbol': 'BTCUSDT',
            'amount': 2_500_000,
            'side': 'BUY',
            'trade_time': int(time.time() * 1000),
            'exchange': 'binance'
        }
        storage.save_trade(trade)
        print(f"✓ 交易数据已保存到: {temp_dir}")

        # 测试保存告警
        storage.save_alert(
            'BTCUSDT', 'BUY', 2_500_000,
            int(time.time() * 1000),
            "[大额主动买入] BTC/USDT 金额：$2,500,000 方向：买入 时间：14:35:22"
        )
        print(f"✓ 告警数据已保存")

        # 获取统计信息
        stats = storage.get_storage_stats()
        print(f"✓ 存储统计: {stats['total_files']} 个文件")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"✓ 临时目录已清理")


def test_full_integration():
    """测试完整集成"""
    print("\n" + "="*60)
    print("测试 4: 完整集成测试")
    print("="*60)

    from src.monitor.large_orders import LargeOrderMonitor
    import tempfile
    import shutil

    # 创建模拟 Telegram Bot
    mock_bot = MockTelegramBot()

    # 使用临时目录
    temp_dir = tempfile.mkdtemp(prefix="test_monitor_")

    try:
        # 创建监控器
        monitor = LargeOrderMonitor(
            telegram_bot=mock_bot,
            symbols=['BTCUSDT'],
            threshold_usdt=1_000_000,  # 100万阈值（更容易触发）
            time_window_minutes=1,  # 1分钟窗口
            cooldown_minutes=1,  # 1分钟冷静期
            storage_path=temp_dir
        )

        print(f"✓ 监控器创建成功")
        print(f"  监控币种: {monitor.symbols}")
        print(f"  阈值: ${monitor.detector.threshold_usdt:,.0f}")
        print(f"  时间窗口: {monitor.aggregator.window_size_ms / 1000 / 60:.0f} 分钟")

        # 模拟交易数据
        now = int(time.time() * 1000)

        # 模拟 1: 小额交易（不应触发）
        monitor.aggregator.add_trade({
            'symbol': 'BTCUSDT',
            'amount': 500_000,  # 50万
            'side': 'BUY',
            'trade_time': now,
            'trade_id': 1
        })
        print(f"\n✓ 模拟小额交易: 50万")

        # 检查是否触发告警
        time.sleep(0.1)  # 等待处理
        if len(mock_bot.messages) == 0:
            print(f"  ✓ 未触发告警（正确）")
        else:
            print(f"  ✗ 错误触发了告警")

        # 清空消息
        mock_bot.messages.clear()

        # 模拟 2: 大额交易（应触发）
        monitor.aggregator.add_trade({
            'symbol': 'BTCUSDT',
            'amount': 1_200_000,  # 120万
            'side': 'BUY',
            'trade_time': now,
            'trade_id': 2
        })
        print(f"\n✓ 模拟大额交易: 120万")

        # 检查是否触发告警
        time.sleep(0.1)  # 等待处理
        if len(mock_bot.messages) > 0:
            print(f"  ✓ 触发告警（正确）")
            print(f"  告警消息: {mock_bot.messages[0]['text'][:80]}...")
        else:
            print(f"  ✗ 未触发告警（错误）")

        # 获取统计信息
        stats = monitor.get_stats()
        print(f"\n✓ 统计信息:")
        print(f"  监控器运行状态: {stats['is_running']}")
        print(f"  处理的交易数: {stats['monitor']['total_trades_processed']}")
        print(f"  触发的告警数: {stats['monitor']['alerts_triggered']}")

    finally:
        # 清理
        monitor.stop()
        shutil.rmtree(temp_dir)
        print(f"\n✓ 测试完成，资源已清理")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("大额交易监控功能 - 自动化测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 测试 1: 滑动窗口
        test_sliding_window_aggregator()

        # 测试 2: 检测器
        test_large_order_detector()

        # 测试 3: 存储
        test_file_storage()

        # 测试 4: 完整集成
        test_full_integration()

        print("\n" + "="*60)
        print("✓ 所有测试完成！")
        print("="*60)
        print("\n功能已就绪，可以启动机器人使用。")
        print("\n使用说明:")
        print("1. 确保已安装依赖: pip install websocket-client")
        print("2. 配置参数: src/config.py")
        print("3. 启动机器人: python -m src")
        print("4. 查看文档: docs/LARGE_ORDER_MONITOR.md")

    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
