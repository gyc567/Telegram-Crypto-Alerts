"""
Base Exchange Collector - 抽象基类设计
支持多交易所扩展：币安、OKX、Coinbase等
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass
class TradeEvent:
    """交易事件数据模型"""
    exchange: str
    symbol: str  # e.g., "BTCUSDT"
    side: str  # "BUY" or "SELL"
    order_type: str  # "MARKET" or "LIMIT"
    price: float
    quantity: float
    amount: float  # total value in quote currency
    trade_time: int  # millisecond timestamp
    is_taker: bool  # True if taker (market order)
    trade_id: str
    raw_data: Dict  # 原始数据，用于调试


class BaseExchangeCollector(ABC):
    """
    交易所采集器抽象基类
    
    设计原则：
    1. 策略模式：每个交易所独立实现
    2. 事件驱动：异步处理交易数据
    3. 线程安全：支持多线程并发
    4. 可观察性：状态变更和错误监控
    """
    
    def __init__(self, exchange_name: str, symbols: List[str]):
        self.exchange_name = exchange_name
        self.symbols = symbols
        self.state = ConnectionState.DISCONNECTED
        self.trade_callback: Optional[Callable[[TradeEvent], None]] = None
        self.state_callback: Optional[Callable[[ConnectionState], None]] = None
        self.error_callback: Optional[Callable[[Exception], None]] = None
        
        # 统计信息
        self.stats = {
            "trades_received": 0,
            "connection_attempts": 0,
            "reconnect_count": 0,
            "last_trade_time": None,
            "uptime_seconds": 0
        }
        
        logger.info(f"Initialized {exchange_name} collector for symbols: {symbols}")
    
    @abstractmethod
    async def start(self) -> None:
        """
        启动WebSocket连接
        
        实现要求：
        1. 建立WebSocket连接
        2. 订阅交易流
        3. 设置重连机制
        4. 更新状态为CONNECTED
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """
        停止WebSocket连接
        
        实现要求：
        1. 优雅关闭连接
        2. 取消订阅
        3. 清理资源
        4. 更新状态为CLOSED
        """
        pass
    
    @abstractmethod
    async def reconnect(self) -> None:
        """
        重新连接
        
        实现要求：
        1. 关闭当前连接
        2. 等待指数退避
        3. 重新建立连接
        4. 更新重连计数
        """
        pass
    
    def set_trade_callback(self, callback: Callable[[TradeEvent], None]) -> None:
        """设置交易事件回调函数"""
        self.trade_callback = callback
    
    def set_state_callback(self, callback: Callable[[ConnectionState], None]) -> None:
        """设置状态变更回调函数"""
        self.state_callback = callback
    
    def set_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """设置错误回调函数"""
        self.error_callback = callback
    
    def _update_state(self, new_state: ConnectionState) -> None:
        """更新连接状态并触发回调"""
        old_state = self.state
        self.state = new_state
        
        logger.info(f"{self.exchange_name}: State changed {old_state.value} -> {new_state.value}")
        
        if self.state_callback:
            self.state_callback(new_state)
    
    def _emit_trade(self, trade: TradeEvent) -> None:
        """发射交易事件"""
        self.stats["trades_received"] += 1
        self.stats["last_trade_time"] = trade.trade_time
        
        if self.trade_callback:
            self.trade_callback(trade)
    
    def _emit_error(self, error: Exception) -> None:
        """发射错误事件"""
        logger.error(f"{self.exchange_name}: {error}", exc_info=True)
        
        if self.error_callback:
            self.error_callback(error)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def get_state(self) -> ConnectionState:
        """获取当前连接状态"""
        return self.state
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.state == ConnectionState.CONNECTED
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """
        获取支持的交易对列表
        
        Returns:
            List[str]: 支持的交易对列表（如["BTCUSDT", "ETHUSDT"]）
        """
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """
        验证交易对是否受支持
        
        Args:
            symbol: 交易对符号（如"BTCUSDT"）
            
        Returns:
            bool: True if supported, False otherwise
        """
        pass
    
    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__}("
                f"exchange={self.exchange_name}, "
                f"state={self.state.value}, "
                f"symbols={len(self.symbols)})>")


class ExchangeCollectorFactory:
    """交易所采集器工厂类"""
    
    _collectors: Dict[str, type] = {}
    
    @classmethod
    def register(cls, exchange_name: str, collector_class: type) -> None:
        """注册交易所采集器"""
        if not issubclass(collector_class, BaseExchangeCollector):
            raise TypeError(f"Collector must inherit from BaseExchangeCollector")
        cls._collectors[exchange_name] = collector_class
        logger.info(f"Registered collector for {exchange_name}: {collector_class.__name__}")
    
    @classmethod
    def create(cls, exchange_name: str, symbols: List[str]) -> BaseExchangeCollector:
        """创建交易所采集器实例"""
        if exchange_name not in cls._collectors:
            raise ValueError(f"Unsupported exchange: {exchange_name}. "
                           f"Supported: {list(cls._collectors.keys())}")
        
        collector_class = cls._collectors[exchange_name]
        collector = collector_class(symbols)
        logger.info(f"Created {exchange_name} collector with {len(symbols)} symbols")
        return collector
    
    @classmethod
    def get_supported_exchanges(cls) -> List[str]:
        """获取支持的交易所列表"""
        return list(cls._collectors.keys())


# 使用示例：
"""
# 1. 注册币安采集器
from src.monitor.large_orders.exchanges.binance import BinanceCollector
ExchangeCollectorFactory.register("binance", BinanceCollector)

# 2. 创建采集器实例
collector = ExchangeCollectorFactory.create("binance", ["BTCUSDT", "ETHUSDT"])

# 3. 设置回调
collector.set_trade_callback(on_trade_received)
collector.set_state_callback(on_state_changed)
collector.set_error_callback(on_error)

# 4. 启动
await collector.start()
"""
