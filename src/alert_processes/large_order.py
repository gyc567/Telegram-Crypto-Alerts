"""
大额订单监控进程
整合所有组件，实现完整的大额订单监控功能
"""
import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime

from ..monitor.large_orders.exchanges.binance import create_binance_client
from ..monitor.large_orders.core.order_aggregator import OrderAggregator
from ..monitor.large_orders.core.threshold_engine import ThresholdEngine, ThresholdEvent
from ..monitor.large_orders.core.alert_dispatcher import AlertDispatcher, LargeOrderAlert
from ..monitor.large_orders.src.price_converter import PriceConverter
from .base import BaseAlertProcess

logger = logging.getLogger(__name__)


class LargeOrderMonitorProcess(BaseAlertProcess):
    """
    大额订单监控进程
    
    整合：
    1. 币安WebSocket客户端
    2. 订单聚合器
    3. 阈值引擎
    4. 告警调度器
    5. USD转换器
    """
    
    def __init__(
        self,
        telegram_bot=None,
        symbols: Optional[List[str]] = None,
        threshold_usd: float = 2_000_000,
        window_minutes: int = 5,
        cooldown_minutes: int = 5,
        rate_limit_per_minute: int = 12
    ):
        super().__init__(telegram_bot)
        
        # 默认交易对
        self.symbols = symbols or [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
            "SOLUSDT", "DOTUSDT", "DOGEUSDT", "MATICUSDT", "LTCUSDT",
            "AVAXUSDT", "UNIUSDT", "ATOMUSDT", "LINKUSDT", "ETCUSDT",
            "BCHUSDT", "FILUSDT", "TRXUSDT", "XLMUSDT", "VETUSDT"
        ]
        
        # 核心组件
        self.binance_client = None
        self.order_aggregator = OrderAggregator(
            window_minutes=window_minutes,
            threshold_usd=threshold_usd
        )
        self.threshold_engine = ThresholdEngine(
            threshold_usd=threshold_usd,
            cooldown_minutes=cooldown_minutes
        )
        self.alert_dispatcher = AlertDispatcher(
            telegram_bot=telegram_bot,
            rate_limit_per_minute=rate_limit_per_minute
        )
        self.price_converter = PriceConverter()
        
        # 状态
        self.running = False
        self.connected = False
        
        # 统计信息
        self.stats = {
            "trades_processed": 0,
            "alerts_sent": 0,
            "alerts_suppressed": 0,
            "uptime_seconds": 0,
            "last_alert_time": None,
            "start_time": None
        }
        
        logger.info(f"初始化大额订单监控进程：{len(self.symbols)} 个交易对")
    
    async def initialize(self) -> None:
        """初始化组件"""
        try:
            # 创建币安客户端
            self.binance_client = create_binance_client(self.symbols)
            
            # 设置事件回调
            self.binance_client.set_trade_callback(self.on_trade_received)
            self.binance_client.set_state_callback(self.on_state_changed)
            self.binance_client.set_error_callback(self.on_error_occurred)
            
            # 设置阈值引擎回调
            self.threshold_engine.set_alert_callback(self.on_threshold_breach)
            
            # 启动告警队列处理器
            await self.alert_dispatcher.start_queue_processor()
            
            logger.info("大额订单监控进程初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}", exc_info=True)
            raise
    
    async def run(self) -> None:
        """运行监控进程"""
        try:
            logger.info("启动大额订单监控进程...")
            self.running = True
            self.stats["start_time"] = datetime.now()
            
            # 初始化组件
            await self.initialize()
            
            # 启动币安WebSocket客户端
            await self.binance_client.start()
            self.connected = True
            
            logger.info("大额订单监控进程运行中...")
            
            # 主循环
            while self.running:
                try:
                    await asyncio.sleep(1)
                    self.stats["uptime_seconds"] = (
                        datetime.now() - self.stats["start_time"]
                    ).total_seconds()
                    
                except asyncio.CancelledError:
                    logger.info("监控进程被取消")
                    break
                except Exception as e:
                    logger.error(f"主循环错误: {e}", exc_info=True)
                    await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"监控进程运行失败: {e}", exc_info=True)
            raise
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """停止监控进程"""
        logger.info("停止大额订单监控进程...")
        
        self.running = False
        self.connected = False
        
        # 停止币安客户端
        if self.binance_client:
            await self.binance_client.stop()
        
        # 停止告警队列处理器
        await self.alert_dispatcher.stop_queue_processor()
        
        # 关闭USD转换器
        if self.price_converter:
            await self.price_converter.__aexit__(None, None, None)
        
        logger.info("大额订单监控进程已停止")
    
    async def on_trade_received(self, trade_event) -> None:
        """处理接收到的交易"""
        try:
            # 转换交易为USD
            usd_value = await self.price_converter.convert_to_usd(
                trade_event.symbol,
                trade_event.price,
                trade_event.quantity
            )
            
            if usd_value > 0:
                # 添加到聚合器
                await self.order_aggregator.add_trade(
                    trade_event.symbol,
                    trade_event,
                    usd_value
                )
                
                self.stats["trades_processed"] += 1
                
        except Exception as e:
            logger.error(f"处理交易失败: {e}", exc_info=True)
    
    async def on_state_changed(self, state: str) -> None:
        """处理状态变更"""
        logger.info(f"状态变更: {state}")
        self.connected = state == "connected"
    
    async def on_error_occurred(self, error: Exception) -> None:
        """处理错误"""
        logger.error(f"WebSocket错误: {error}", exc_info=True)
    
    async def on_threshold_breach(self, event: ThresholdEvent) -> None:
        """处理阈值突破"""
        try:
            # 创建告警
            alert = LargeOrderAlert(
                symbol=event.symbol,
                direction=event.direction,
                total_volume=event.total_volume,
                buy_volume=event.buy_volume,
                sell_volume=event.sell_volume,
                trade_count=event.trade_count,
                threshold_usd=event.threshold_usd,
                window_minutes=event.window_minutes,
                timestamp=event.timestamp,
                exchange="Binance"
            )
            
            # 发送告警
            success = await self.alert_dispatcher.dispatch_alert(alert)
            
            if success:
                self.stats["alerts_sent"] += 1
                self.stats["last_alert_time"] = datetime.now()
                
                # 重置聚合器窗口
                await self.order_aggregator.reset_window(event.symbol)
            else:
                self.stats["alerts_suppressed"] += 1
            
        except Exception as e:
            logger.error(f"处理阈值突破失败: {e}", exc_info=True)
    
    def get_status(self) -> Dict:
        """获取监控状态"""
        return {
            "running": self.running,
            "connected": self.connected,
            "symbols_count": len(self.symbols),
            "stats": {
                **self.stats,
                "start_time": self.stats["start_time"].isoformat() if self.stats["start_time"] else None,
                "last_alert_time": self.stats["last_alert_time"].isoformat() if self.stats["last_alert_time"] else None
            },
            "components": {
                "binance_client": self.binance_client.get_stats() if self.binance_client else {},
                "order_aggregator": self.order_aggregator.get_stats(),
                "threshold_engine": self.threshold_engine.get_stats(),
                "alert_dispatcher": self.alert_dispatcher.get_stats()
            }
        }
    
    def get_symbol_summaries(self) -> List[Dict]:
        """获取所有交易对摘要"""
        return self.order_aggregator.get_all_symbols_summary()
    
    def get_cooldowns(self) -> List[Dict]:
        """获取活跃冷却"""
        return self.threshold_engine.get_all_cooldowns()
    
    async def enable(self) -> None:
        """启用监控"""
        if not self.running:
            asyncio.create_task(self.run())
            logger.info("大额订单监控已启用")
    
    async def disable(self) -> None:
        """禁用监控"""
        if self.running:
            await self.stop()
            logger.info("大额订单监控已禁用")
    
    def update_threshold(self, new_threshold: float) -> None:
        """更新阈值"""
        self.order_aggregator.update_threshold(new_threshold)
        self.threshold_engine.update_threshold(new_threshold)
        logger.info(f"阈值已更新: ${new_threshold:,.0f}")
    
    def update_cooldown(self, new_cooldown_minutes: int) -> None:
        """更新冷却时间"""
        self.threshold_engine.update_cooldown(new_cooldown_minutes)
        logger.info(f"冷却时间已更新: {new_cooldown_minutes} 分钟")
    
    def clear_cooldowns(self) -> int:
        """清除所有冷却"""
        count = self.threshold_engine.clear_all_cooldowns()
        logger.info(f"已清除 {count} 个冷却")
        return count
    
    def get_uptime(self) -> str:
        """获取运行时间"""
        if not self.stats["start_time"]:
            return "0:00:00"
        
        uptime = datetime.now() - self.stats["start_time"]
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"


# 单例实例
_large_order_monitor: Optional[LargeOrderMonitorProcess] = None


async def get_large_order_monitor() -> LargeOrderMonitorProcess:
    """获取大额订单监控实例"""
    global _large_order_monitor
    
    if _large_order_monitor is None:
        _large_order_monitor = LargeOrderMonitorProcess()
    
    return _large_order_monitor
