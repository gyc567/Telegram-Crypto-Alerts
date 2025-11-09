"""
测试BaseExchangeCollector抽象基类的实现
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from src.monitor.large_orders.src.base import (
    BaseExchangeCollector, 
    ConnectionState, 
    TradeEvent,
    ExchangeCollectorFactory
)


class TestExchangeCollector(BaseExchangeCollector):
    """测试用的采集器实现"""
    
    def __init__(self, symbols: List[str]):
        super().__init__("test", symbols)
        self._connected = False
    
    async def start(self) -> None:
        self._update_state(ConnectionState.CONNECTED)
    
    async def stop(self) -> None:
        self._update_state(ConnectionState.CLOSED)
    
    async def reconnect(self) -> None:
        await asyncio.sleep(0.1)  # 模拟重连延迟
        self._update_state(ConnectionState.CONNECTED)
    
    def get_supported_symbols(self) -> List[str]:
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    
    def validate_symbol(self, symbol: str) -> bool:
        return symbol in self.get_supported_symbols()


class TestBaseExchangeCollector:
    """测试BaseExchangeCollector"""
    
    @pytest.fixture
    def collector(self):
        """创建测试采集器"""
        return TestExchangeCollector(["BTCUSDT", "ETHUSDT"])
    
    @pytest.fixture
    def mock_trade_event(self):
        """模拟交易事件"""
        return TradeEvent(
            exchange="binance",
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            price=50000.0,
            quantity=50.0,
            amount=2500000.0,
            trade_time=1234567890000,
            is_taker=True,
            trade_id="12345",
            raw_data={}
        )
    
    def test_collector_initialization(self, collector):
        """测试采集器初始化"""
        assert collector.exchange_name == "test"
        assert collector.symbols == ["BTCUSDT", "ETHUSDT"]
        assert collector.state == ConnectionState.DISCONNECTED
        assert collector.trade_callback is None
        assert collector.state_callback is None
        assert collector.error_callback is None
        assert not collector.is_connected()
    
    def test_state_update(self, collector):
        """测试状态更新"""
        mock_callback = Mock()
        collector.set_state_callback(mock_callback)
        
        collector._update_state(ConnectionState.CONNECTED)
        
        assert collector.state == ConnectionState.CONNECTED
        mock_callback.assert_called_once_with(ConnectionState.CONNECTED)
    
    def test_emit_trade(self, collector, mock_trade_event):
        """测试交易事件发射"""
        mock_callback = Mock()
        collector.set_trade_callback(mock_callback)
        
        collector._emit_trade(mock_trade_event)
        
        assert collector.stats["trades_received"] == 1
        assert collector.stats["last_trade_time"] == 1234567890000
        mock_callback.assert_called_once_with(mock_trade_event)
    
    def test_emit_error(self, collector):
        """测试错误事件发射"""
        mock_callback = Mock()
        collector.set_error_callback(mock_callback)
        
        error = ValueError("Test error")
        collector._emit_error(error)
        
        mock_callback.assert_called_once_with(error)
    
    @pytest.mark.asyncio
    async def test_start(self, collector):
        """测试启动"""
        await collector.start()
        assert collector.state == ConnectionState.CONNECTED
        assert collector.is_connected()
    
    @pytest.mark.asyncio
    async def test_stop(self, collector):
        """测试停止"""
        await collector.start()
        assert collector.is_connected()
        
        await collector.stop()
        assert collector.state == ConnectionState.CLOSED
        assert not collector.is_connected()
    
    @pytest.mark.asyncio
    async def test_reconnect(self, collector):
        """测试重连"""
        await collector.start()
        assert collector.is_connected()
        
        await collector.reconnect()
        assert collector.is_connected()
    
    def test_get_supported_symbols(self, collector):
        """测试获取支持的交易对"""
        symbols = collector.get_supported_symbols()
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" in symbols
        assert "BNBUSDT" in symbols
    
    def test_validate_symbol_valid(self, collector):
        """测试验证有效交易对"""
        assert collector.validate_symbol("BTCUSDT")
        assert collector.validate_symbol("ETHUSDT")
    
    def test_validate_symbol_invalid(self, collector):
        """测试验证无效交易对"""
        assert not collector.validate_symbol("INVALID")
        assert not collector.validate_symbol("XRPUSDT")
    
    def test_get_stats(self, collector):
        """测试获取统计信息"""
        stats = collector.get_stats()
        
        assert "trades_received" in stats
        assert "connection_attempts" in stats
        assert "reconnect_count" in stats
        assert "last_trade_time" in stats
        assert "uptime_seconds" in stats
        
        assert stats["trades_received"] == 0
        assert stats["connection_attempts"] == 0
    
    def test_repr(self, collector):
        """测试字符串表示"""
        repr_str = repr(collector)
        assert "TestExchangeCollector" in repr_str
        assert "test" in repr_str
        assert "symbols=2" in repr_str


class TestExchangeCollectorFactory:
    """测试ExchangeCollectorFactory"""
    
    def test_register_collector(self):
        """测试注册采集器"""
        factory = ExchangeCollectorFactory()
        factory.register("test", TestExchangeCollector)
        
        assert "test" in factory._collectors
        assert factory._collectors["test"] == TestExchangeCollector
    
    def test_create_collector(self):
        """测试创建采集器"""
        factory = ExchangeCollectorFactory()
        factory.register("test", TestExchangeCollector)
        
        collector = factory.create("test", ["BTCUSDT"])
        assert isinstance(collector, TestExchangeCollector)
        assert collector.exchange_name == "test"
        assert collector.symbols == ["BTCUSDT"]
    
    def test_create_unsupported_exchange(self):
        """测试创建不支持的交易所"""
        factory = ExchangeCollectorFactory()
        
        with pytest.raises(ValueError) as exc_info:
            factory.create("unsupported", ["BTCUSDT"])
        
        assert "Unsupported exchange" in str(exc_info.value)
    
    def test_register_invalid_collector(self):
        """测试注册无效的采集器"""
        factory = ExchangeCollectorFactory()
        
        with pytest.raises(TypeError) as exc_info:
            factory.register("invalid", str)  # 不是BaseExchangeCollector子类
        
        assert "Collector must inherit from BaseExchangeCollector" in str(exc_info.value)
    
    def test_get_supported_exchanges(self):
        """测试获取支持的交易所列表"""
        # 清理之前的状态
        initial_exchanges = set(ExchangeCollectorFactory.get_supported_exchanges())

        # 注册测试采集器
        ExchangeCollectorFactory.register("test1", TestExchangeCollector)
        ExchangeCollectorFactory.register("test2", TestExchangeCollector)

        # 获取当前所有交易所
        current_exchanges = set(ExchangeCollectorFactory.get_supported_exchanges())

        # 验证新注册的交易所存在
        assert "test1" in current_exchanges
        assert "test2" in current_exchanges

        # 验证总数（初始 + 2个新的）
        assert len(current_exchanges) == len(initial_exchanges) + 2


class TestTradeEvent:
    """测试TradeEvent数据模型"""
    
    def test_trade_event_creation(self):
        """测试创建交易事件"""
        trade = TradeEvent(
            exchange="binance",
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            price=50000.0,
            quantity=50.0,
            amount=2500000.0,
            trade_time=1234567890000,
            is_taker=True,
            trade_id="12345",
            raw_data={"test": "data"}
        )
        
        assert trade.exchange == "binance"
        assert trade.symbol == "BTCUSDT"
        assert trade.side == "BUY"
        assert trade.order_type == "MARKET"
        assert trade.price == 50000.0
        assert trade.quantity == 50.0
        assert trade.amount == 2500000.0
        assert trade.trade_time == 1234567890000
        assert trade.is_taker is True
        assert trade.trade_id == "12345"
        assert trade.raw_data == {"test": "data"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
