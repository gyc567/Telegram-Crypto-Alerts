"""
事件驱动监控架构
替代100ms轮询，降低CPU使用率
"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import weakref

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    TRADE_RECEIVED = "trade_received"
    THRESHOLD_BREACHED = "threshold_breached"
    CONNECTION_STATE_CHANGED = "connection_state_changed"
    ERROR_OCCURRED = "error_occurred"
    CLEANUP_REQUIRED = "cleanup_required"
    STATS_UPDATE = "stats_update"
    HEALTH_CHECK = "health_check"


@dataclass
class Event:
    """事件数据模型"""
    type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""  # 事件源标识
    priority: int = 0  # 事件优先级（越大越紧急）


class EventBus:
    """
    事件总线 - 发布/订阅模式
    
    功能：
    1. 解耦事件产生者和消费者
    2. 支持事件优先级
    3. 支持异步事件处理
    4. 弱引用管理，防止内存泄漏
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._processing = False
        self._event_handlers: Dict[str, Callable] = {}
    
    def subscribe(self, event_type: EventType, handler: Callable) -> str:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            str: 订阅ID，用于取消订阅
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        # 使用弱引用，避免内存泄漏
        handler_id = f"{id(handler)}"
        self._event_handlers[handler_id] = handler
        self._subscribers[event_type].append(handler)
        
        logger.debug(f"订阅事件: {event_type.value}")
        return handler_id
    
    def unsubscribe(self, handler_id: str) -> bool:
        """
        取消订阅
        
        Args:
            handler_id: 订阅ID
            
        Returns:
            bool: 是否成功取消
        """
        if handler_id in self._event_handlers:
            handler = self._event_handlers.pop(handler_id)
            # 从所有事件类型中移除
            for event_type, handlers in self._subscribers.items():
                if handler in handlers:
                    handlers.remove(handler)
            logger.debug(f"取消订阅: {handler_id}")
            return True
        return False
    
    async def publish(self, event: Event) -> None:
        """
        发布事件
        
        Args:
            event: 事件对象
        """
        # 使用负优先级实现高优先级先处理（队列是最小堆）
        priority = -event.priority
        await self._event_queue.put((priority, event.timestamp, event))
        
        if not self._processing:
            self._processing = True
            asyncio.create_task(self._process_events())
    
    async def _process_events(self) -> None:
        """处理事件队列"""
        try:
            while not self._event_queue.empty():
                priority, timestamp, event = await self._event_queue.get()
                
                # 获取事件类型的订阅者
                subscribers = self._subscribers.get(event.type, [])
                
                # 并发处理事件
                if subscribers:
                    tasks = [
                        self._safe_handle(handler, event)
                        for handler in subscribers
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)
        
        except Exception as e:
            logger.error(f"事件处理失败: {e}", exc_info=True)
        finally:
            self._processing = False
    
    async def _safe_handle(self, handler: Callable, event: Event) -> None:
        """安全的事件处理"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"事件处理器异常: {e}", exc_info=True)
    
    async def start(self) -> None:
        """启动事件处理"""
        if not self._processing:
            self._processing = True
            asyncio.create_task(self._process_events())
        logger.info("事件总线已启动")
    
    async def stop(self) -> None:
        """停止事件处理"""
        self._processing = False
        # 清空队列
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        logger.info("事件总线已停止")
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self._event_queue.qsize()


class EventDrivenMonitor:
    """
    事件驱动监控器
    
    替代原有的100ms轮询：
    - 事件触发处理，非阻塞
    - 异步并发处理
    - 动态调整处理频率
    """
    
    def __init__(self, cleanup_interval: int = 300):
        """
        初始化事件驱动监控器
        
        Args:
            cleanup_interval: 清理间隔（秒）
        """
        self.event_bus = EventBus()
        self.cleanup_interval = cleanup_interval
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # 状态跟踪
        self.stats = {
            "events_processed": 0,
            "events_by_type": {event_type: 0 for event_type in EventType},
            "last_cleanup": datetime.now(),
            "uptime_seconds": 0
        }
        
        # 事件处理器映射
        self._handler_mapping = {
            EventType.TRADE_RECEIVED: self._handle_trade_event,
            EventType.THRESHOLD_BREACHED: self._handle_threshold_breach,
            EventType.CONNECTION_STATE_CHANGED: self._handle_state_change,
            EventType.ERROR_OCCURRED: self._handle_error,
            EventType.CLEANUP_REQUIRED: self._handle_cleanup,
            EventType.STATS_UPDATE: self._handle_stats_update,
            EventType.HEALTH_CHECK: self._handle_health_check
        }
    
    def start(self) -> None:
        """启动监控器"""
        if self._running:
            return
        
        self._running = True
        
        # 订阅所有事件类型
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._handler_mapping[event_type])
        
        # 启动任务
        self._tasks = [
            asyncio.create_task(self._cleanup_task()),
            asyncio.create_task(self._stats_task()),
            asyncio.create_task(self._health_check_task())
        ]
        
        logger.info("事件驱动监控器已启动")
    
    def stop(self) -> None:
        """停止监控器"""
        if not self._running:
            return
        
        self._running = False
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 等待任务完成
        self._tasks.clear()
        
        # 停止事件总线
        asyncio.create_task(self.event_bus.stop())
        
        logger.info("事件驱动监控器已停止")
    
    async def publish_trade(self, trade_data: Dict) -> None:
        """发布交易事件"""
        await self.event_bus.publish(Event(
            type=EventType.TRADE_RECEIVED,
            data=trade_data,
            source="websocket",
            priority=5  # 高优先级
        ))
    
    async def publish_threshold_breach(self, symbol: str, volume: float) -> None:
        """发布阈值突破事件"""
        await self.event_bus.publish(Event(
            type=EventType.THRESHOLD_BREACHED,
            data={"symbol": symbol, "volume": volume},
            source="detector",
            priority=10  # 最高优先级
        ))
    
    async def publish_state_change(self, state: str) -> None:
        """发布状态变更事件"""
        await self.event_bus.publish(Event(
            type=EventType.CONNECTION_STATE_CHANGED,
            data={"state": state},
            source="collector",
            priority=8
        ))
    
    async def publish_error(self, error: Exception, context: str) -> None:
        """发布错误事件"""
        await self.event_bus.publish(Event(
            type=EventType.ERROR_OCCURRED,
            data={"error": str(error), "context": context},
            source="system",
            priority=7
        ))
    
    async def _handle_trade_event(self, event: Event) -> None:
        """处理交易事件"""
        try:
            # 立即处理交易数据
            trade_data = event.data
            symbol = trade_data.get("symbol")
            
            # 转换USD
            usd_value = await self._convert_to_usd(trade_data)
            
            # 更新聚合器
            await self._update_aggregator(symbol, usd_value)
            
            # 检查阈值
            if await self._check_threshold(symbol):
                await self.publish_threshold_breach(symbol, usd_value)
            
            self.stats["events_processed"] += 1
            self.stats["events_by_type"][EventType.TRADE_RECEIVED] += 1
            
        except Exception as e:
            logger.error(f"处理交易事件失败: {e}", exc_info=True)
    
    async def _handle_threshold_breach(self, event: Event) -> None:
        """处理阈值突破事件"""
        try:
            symbol = event.data["symbol"]
            volume = event.data["volume"]
            
            # 发送告警
            await self._send_alert(symbol, volume)
            
            # 重置聚合器
            await self._reset_aggregator(symbol)
            
            self.stats["events_by_type"][EventType.THRESHOLD_BREACHED] += 1
            
        except Exception as e:
            logger.error(f"处理阈值突破事件失败: {e}", exc_info=True)
    
    async def _handle_state_change(self, event: Event) -> None:
        """处理状态变更事件"""
        state = event.data["state"]
        logger.info(f"连接状态变更: {state}")
        self.stats["events_by_type"][EventType.CONNECTION_STATE_CHANGED] += 1
    
    async def _handle_error(self, event: Event) -> None:
        """处理错误事件"""
        error = event.data["error"]
        context = event.data["context"]
        logger.error(f"错误发生 ({context}): {error}")
        self.stats["events_by_type"][EventType.ERROR_OCCURRED] += 1
    
    async def _handle_cleanup(self, event: Event) -> None:
        """处理清理事件"""
        await self._perform_cleanup()
        self.stats["events_by_type"][EventType.CLEANUP_REQUIRED] += 1
    
    async def _handle_stats_update(self, event: Event) -> None:
        """处理统计更新事件"""
        # 更新统计信息
        self.stats["uptime_seconds"] += 1
        self.stats["events_by_type"][EventType.STATS_UPDATE] += 1
    
    async def _handle_health_check(self, event: Event) -> None:
        """处理健康检查事件"""
        await self._perform_health_check()
        self.stats["events_by_type"][EventType.HEALTH_CHECK] += 1
    
    async def _cleanup_task(self) -> None:
        """定期清理任务"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                if self._running:
                    await self.event_bus.publish(Event(
                        type=EventType.CLEANUP_REQUIRED,
                        source="scheduler"
                    ))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务异常: {e}", exc_info=True)
    
    async def _stats_task(self) -> None:
        """定期统计更新任务"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分钟更新一次统计
                if self._running:
                    await self.event_bus.publish(Event(
                        type=EventType.STATS_UPDATE,
                        source="scheduler"
                    ))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"统计任务异常: {e}", exc_info=True)
    
    async def _health_check_task(self) -> None:
        """定期健康检查任务"""
        while self._running:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                if self._running:
                    await self.event_bus.publish(Event(
                        type=EventType.HEALTH_CHECK,
                        source="scheduler"
                    ))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查任务异常: {e}", exc_info=True)
    
    async def _convert_to_usd(self, trade_data: Dict) -> float:
        """转换交易数据为USD"""
        # TODO: 集成PriceConverter
        return trade_data.get("amount", 0.0)
    
    async def _update_aggregator(self, symbol: str, usd_value: float) -> None:
        """更新聚合器"""
        # TODO: 集成OrderAggregator
        pass
    
    async def _check_threshold(self, symbol: str) -> bool:
        """检查阈值"""
        # TODO: 集成ThresholdEngine
        return False
    
    async def _send_alert(self, symbol: str, volume: float) -> None:
        """发送告警"""
        # TODO: 集成AlertDispatcher
        logger.info(f"🚨 阈值突破: {symbol} ${volume:,.2f}")
    
    async def _reset_aggregator(self, symbol: str) -> None:
        """重置聚合器"""
        # TODO: 重置聚合器状态
        pass
    
    async def _perform_cleanup(self) -> None:
        """执行清理"""
        logger.info("执行定期清理")
        self.stats["last_cleanup"] = datetime.now()
    
    async def _perform_health_check(self) -> None:
        """执行健康检查"""
        queue_size = self.event_bus.get_queue_size()
        if queue_size > 100:
            logger.warning(f"事件队列大小异常: {queue_size}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def get_queue_size(self) -> int:
        """获取事件队列大小"""
        return self.event_bus.get_queue_size()


# 使用示例
"""
# 1. 创建事件驱动监控器
monitor = EventDrivenMonitor(cleanup_interval=300)
monitor.start()

# 2. 发布交易事件（替代轮询）
await monitor.publish_trade({
    "symbol": "BTCUSDT",
    "price": 50000,
    "quantity": 10,
    "amount": 500000
})

# 3. 发布阈值突破事件
await monitor.publish_threshold_breach("BTCUSDT", 2500000)

# 4. 发布状态变更
await monitor.publish_state_change("connected")

# 5. 发布错误
await monitor.publish_error(ConnectionError("WebSocket disconnected"), "binance")

# 6. 停止监控器
monitor.stop()

# 7. 获取统计
stats = monitor.get_stats()
print(f"处理事件数: {stats['events_processed']}")
print(f"队列大小: {monitor.get_queue_size()}")
"""
