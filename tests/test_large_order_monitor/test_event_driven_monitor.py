"""
测试EventDrivenMonitor事件驱动监控器
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from src.monitor.large_orders.src.event_driven_monitor import (
    EventBus,
    EventDrivenMonitor,
    Event,
    EventType
)


class TestEvent:
    """测试Event数据模型"""
    
    def test_event_creation(self):
        """测试创建事件"""
        event = Event(
            type=EventType.TRADE_RECEIVED,
            timestamp=datetime.now(),
            data={"symbol": "BTCUSDT"},
            source="test",
            priority=5
        )
        
        assert event.type == EventType.TRADE_RECEIVED
        assert event.data == {"symbol": "BTCUSDT"}
        assert event.source == "test"
        assert event.priority == 5
        assert event.timestamp is not None


class TestEventBus:
    """测试EventBus事件总线"""
    
    @pytest.fixture
    def event_bus(self):
        """创建事件总线"""
        return EventBus()
    
    @pytest.mark.asyncio
    async def test_subscribe(self, event_bus):
        """测试订阅事件"""
        handler = Mock()
        
        handler_id = event_bus.subscribe(EventType.TRADE_RECEIVED, handler)
        
        assert handler_id is not None
        assert EventType.TRADE_RECEIVED in event_bus._subscribers
        assert len(event_bus._subscribers[EventType.TRADE_RECEIVED]) == 1
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus):
        """测试取消订阅"""
        handler = Mock()
        
        handler_id = event_bus.subscribe(EventType.TRADE_RECEIVED, handler)
        success = event_bus.unsubscribe(handler_id)
        
        assert success is True
        assert len(event_bus._subscribers[EventType.TRADE_RECEIVED]) == 0
    
    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, event_bus):
        """测试发布和订阅事件"""
        handler = Mock()
        
        event_bus.subscribe(EventType.TRADE_RECEIVED, handler)
        
        event = Event(
            type=EventType.TRADE_RECEIVED,
            data={"symbol": "BTCUSDT"}
        )
        
        await event_bus.publish(event)
        
        # 等待事件处理
        await asyncio.sleep(0.1)
        
        handler.assert_called_once()
        called_event = handler.call_args[0][0]
        assert called_event.type == EventType.TRADE_RECEIVED
        assert called_event.data == {"symbol": "BTCUSDT"}
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus):
        """测试多个订阅者"""
        handler1 = Mock()
        handler2 = Mock()
        
        event_bus.subscribe(EventType.TRADE_RECEIVED, handler1)
        event_bus.subscribe(EventType.TRADE_RECEIVED, handler2)
        
        event = Event(type=EventType.TRADE_RECEIVED)
        
        await event_bus.publish(event)
        await asyncio.sleep(0.1)
        
        handler1.assert_called_once()
        handler2.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_event_priority(self, event_bus):
        """测试事件优先级"""
        received_events = []
        
        def handler1(event):
            received_events.append(("low", event.priority))
        
        def handler2(event):
            received_events.append(("high", event.priority))
        
        event_bus.subscribe(EventType.TRADE_RECEIVED, handler1)
        event_bus.subscribe(EventType.TRADE_RECEIVED, handler2)
        
        # 发布低优先级事件
        low_event = Event(
            type=EventType.TRADE_RECEIVED,
            priority=1
        )
        await event_bus.publish(low_event)
        
        # 发布高优先级事件
        high_event = Event(
            type=EventType.TRADE_RECEIVED,
            priority=10
        )
        await event_bus.publish(high_event)
        
        await asyncio.sleep(0.1)
        
        # 高优先级事件应该先处理
        assert received_events[0][0] == "high"
        assert received_events[1][0] == "low"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, event_bus):
        """测试错误处理"""
        good_handler = Mock()
        bad_handler = Mock(side_effect=Exception("Test error"))
        
        event_bus.subscribe(EventType.TRADE_RECEIVED, good_handler)
        event_bus.subscribe(EventType.TRADE_RECEIVED, bad_handler)
        
        event = Event(type=EventType.TRADE_RECEIVED)
        
        await event_bus.publish(event)
        await asyncio.sleep(0.1)
        
        # 好的处理器应该被调用
        good_handler.assert_called_once()
        # 错误的处理器也应该被调用（虽然会出错）
        bad_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_stop(self, event_bus):
        """测试启动和停止"""
        assert event_bus._processing is False
        
        await event_bus.start()
        assert event_bus._processing is True
        
        await event_bus.stop()
        assert event_bus._processing is False
    
    def test_get_queue_size(self, event_bus):
        """测试获取队列大小"""
        size = event_bus.get_queue_size()
        assert size == 0


class TestEventDrivenMonitor:
    """测试EventDrivenMonitor"""
    
    @pytest.fixture
    def monitor(self):
        """创建事件驱动监控器"""
        return EventDrivenMonitor(cleanup_interval=300)
    
    @pytest.mark.asyncio
    async def test_initialization(self, monitor):
        """测试初始化"""
        assert monitor._running is False
        assert monitor.cleanup_interval == 300
        assert monitor.event_bus is not None
        assert len(monitor._tasks) == 0
        assert "events_processed" in monitor.stats
        assert "events_by_type" in monitor.stats
    
    @pytest.mark.asyncio
    async def test_start(self, monitor):
        """测试启动"""
        monitor.start()
        assert monitor._running is True
        assert len(monitor._tasks) == 3  # cleanup, stats, health_check tasks
        
        # 等待任务启动
        await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_stop(self, monitor):
        """测试停止"""
        monitor.start()
        assert monitor._running is True
        
        monitor.stop()
        assert monitor._running is False
        assert len(monitor._tasks) == 0
    
    @pytest.mark.asyncio
    async def test_publish_trade(self, monitor):
        """测试发布交易事件"""
        monitor.start()
        
        with patch.object(monitor, '_convert_to_usd', return_value=50000.0):
            with patch.object(monitor, '_update_aggregator', new_callable=AsyncMock):
                with patch.object(monitor, '_check_threshold', return_value=False):
                    await monitor.publish_trade({
                        "symbol": "BTCUSDT",
                        "price": 50000,
                        "quantity": 1
                    })
                    
                    await asyncio.sleep(0.1)
                    
                    # 检查统计
                    assert monitor.stats["events_by_type"][EventType.TRADE_RECEIVED] > 0
    
    @pytest.mark.asyncio
    async def test_publish_threshold_breach(self, monitor):
        """测试发布阈值突破事件"""
        monitor.start()
        
        with patch.object(monitor, '_send_alert', new_callable=AsyncMock):
            with patch.object(monitor, '_reset_aggregator', new_callable=AsyncMock):
                await monitor.publish_threshold_breach("BTCUSDT", 2500000.0)
                
                await asyncio.sleep(0.1)
                
                # 检查统计
                assert monitor.stats["events_by_type"][EventType.THRESHOLD_BREACHED] > 0
    
    @pytest.mark.asyncio
    async def test_publish_state_change(self, monitor):
        """测试发布状态变更事件"""
        monitor.start()
        
        await monitor.publish_state_change("connected")
        
        await asyncio.sleep(0.1)
        
        # 检查统计
        assert monitor.stats["events_by_type"][EventType.CONNECTION_STATE_CHANGED] > 0
    
    @pytest.mark.asyncio
    async def test_publish_error(self, monitor):
        """测试发布错误事件"""
        monitor.start()
        
        error = ConnectionError("WebSocket disconnected")
        await monitor.publish_error(error, "binance")
        
        await asyncio.sleep(0.1)
        
        # 检查统计
        assert monitor.stats["events_by_type"][EventType.ERROR_OCCURRED] > 0
    
    @pytest.mark.asyncio
    async def test_handle_trade_event(self, monitor):
        """测试处理交易事件"""
        event = Event(
            type=EventType.TRADE_RECEIVED,
            data={
                "symbol": "BTCUSDT",
                "price": 50000,
                "quantity": 10
            }
        )
        
        with patch.object(monitor, '_convert_to_usd', return_value=500000.0):
            with patch.object(monitor, '_update_aggregator', new_callable=AsyncMock):
                with patch.object(monitor, '_check_threshold', return_value=False):
                    await monitor._handle_trade_event(event)
                    
                    await asyncio.sleep(0.1)
                    
                    # 检查统计更新
                    assert monitor.stats["events_processed"] == 1
                    assert monitor.stats["events_by_type"][EventType.TRADE_RECEIVED] == 1
    
    @pytest.mark.asyncio
    async def test_handle_threshold_breach(self, monitor):
        """测试处理阈值突破事件"""
        event = Event(
            type=EventType.THRESHOLD_BREACHED,
            data={
                "symbol": "BTCUSDT",
                "volume": 2500000.0
            }
        )
        
        with patch.object(monitor, '_send_alert', new_callable=AsyncMock):
            with patch.object(monitor, '_reset_aggregator', new_callable=AsyncMock):
                await monitor._handle_threshold_breach(event)
                
                await asyncio.sleep(0.1)
                
                # 检查统计
                assert monitor.stats["events_by_type"][EventType.THRESHOLD_BREACHED] == 1
    
    @pytest.mark.asyncio
    async def test_handle_cleanup(self, monitor):
        """测试处理清理事件"""
        event = Event(type=EventType.CLEANUP_REQUIRED)
        
        await monitor._handle_cleanup(event)
        
        await asyncio.sleep(0.1)
        
        # 检查统计
        assert monitor.stats["events_by_type"][EventType.CLEANUP_REQUIRED] == 1
        assert monitor.stats["last_cleanup"] is not None
    
    @pytest.mark.asyncio
    async def test_handle_stats_update(self, monitor):
        """测试处理统计更新事件"""
        event = Event(type=EventType.STATS_UPDATE)
        
        await monitor._handle_stats_update(event)
        
        # 检查统计更新
        assert monitor.stats["uptime_seconds"] > 0
        assert monitor.stats["events_by_type"][EventType.STATS_UPDATE] == 1
    
    @pytest.mark.asyncio
    async def test_handle_health_check(self, monitor):
        """测试处理健康检查事件"""
        event = Event(type=EventType.HEALTH_CHECK)
        
        with patch('logging.warning') as mock_warning:
            await monitor._handle_health_check(event)
            
            await asyncio.sleep(0.1)
            
            # 检查统计
            assert monitor.stats["events_by_type"][EventType.HEALTH_CHECK] == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_task(self, monitor):
        """测试定期清理任务"""
        monitor.start()
        
        # 等待清理任务触发
        await asyncio.sleep(0.5)
        
        monitor.stop()
        
        # 检查统计
        assert monitor.stats["last_cleanup"] is not None
    
    @pytest.mark.asyncio
    async def test_stats_task(self, monitor):
        """测试定期统计更新任务"""
        monitor.start()
        
        # 等待统计任务触发
        await asyncio.sleep(0.5)
        
        monitor.stop()
        
        # 检查统计
        assert monitor.stats["uptime_seconds"] > 0
    
    @pytest.mark.asyncio
    async def test_health_check_task(self, monitor):
        """测试定期健康检查任务"""
        monitor.start()
        
        # 等待健康检查任务触发
        await asyncio.sleep(0.5)
        
        monitor.stop()
        
        # 检查统计
        assert monitor.stats["events_by_type"][EventType.HEALTH_CHECK] > 0
    
    def test_get_stats(self, monitor):
        """测试获取统计信息"""
        stats = monitor.get_stats()
        
        assert "events_processed" in stats
        assert "events_by_type" in stats
        assert "last_cleanup" in stats
        assert "uptime_seconds" in stats
    
    def test_get_queue_size(self, monitor):
        """测试获取队列大小"""
        size = monitor.get_queue_size()
        assert size == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
