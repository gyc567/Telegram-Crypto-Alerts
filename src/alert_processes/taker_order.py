"""
吃单告警处理进程
集成到告警系统，处理吃单监控告警
"""
import logging
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from .base import BaseAlertProcess
from ..monitor.taker_orders.src.tracker import TakerOrderTracker
from ..monitor.taker_orders.src.models import TakerAlert
from ..monitor.taker_orders.core.single_monitor import SingleOrderMonitor
from ..monitor.taker_orders.core.cumulative_monitor import CumulativeMonitor
from ..monitor.large_orders.exchanges.binance import BinanceWebSocketClient
from ..monitor.large_orders.src.base import TradeEvent
from ..config import (
    TAKER_ORDER_MONITOR_ENABLED,
    TAKER_ORDER_MONITORED_SYMBOLS,
    TAKER_ORDER_SINGLE_THRESHOLDS,
    TAKER_ORDER_CUMULATIVE_CONFIG,
    TAKER_ORDER_COOLDOWN_CONFIG,
)
from ..user_configuration import get_whitelist

if TYPE_CHECKING:
    from ..telegram import TelegramBot

logger = logging.getLogger(__name__)


class TakerOrderAlertProcess(BaseAlertProcess):
    """
    吃单告警处理进程
    
    功能：
    1. 启动 WebSocket 监控
    2. 处理交易事件
    3. 生成并发送告警
    4. 记录告警历史
    """
    
    def __init__(self, bot: "TelegramBot"):
        """
        初始化吃单告警处理进程
        
        Args:
            bot: Telegram Bot 实例
        """
        super().__init__(telegram_bot=bot)
        self.bot = bot
        
        # 事件循环引用（稍后设置）
        self.event_loop = None
        
        # 检查是否启用
        if not TAKER_ORDER_MONITOR_ENABLED:
            logger.warning("Taker order monitoring is disabled in config")
            return
        
        # 初始化追踪器
        self.tracker = TakerOrderTracker(
            symbols=TAKER_ORDER_MONITORED_SYMBOLS,
            single_thresholds=TAKER_ORDER_SINGLE_THRESHOLDS,
            cumulative_config=TAKER_ORDER_CUMULATIVE_CONFIG,
            cooldown_config=TAKER_ORDER_COOLDOWN_CONFIG
        )
        
        # 设置回调
        self.tracker.set_alert_callback(self._handle_alert)
        
        # 初始化 WebSocket 客户端（复用现有的 Binance 客户端）
        self.ws_client = BinanceWebSocketClient(
            symbols=TAKER_ORDER_MONITORED_SYMBOLS
        )
        
        # 设置交易事件回调
        self.ws_client.set_trade_callback(self._on_trade_event)
        
        # 告警历史
        self.alert_history = []
        self.max_history_size = 100
        
        # 监控格式化器（用于生成消息）
        self.single_formatter = SingleOrderMonitor(TAKER_ORDER_SINGLE_THRESHOLDS)
        self.cumulative_formatter = CumulativeMonitor(TAKER_ORDER_CUMULATIVE_CONFIG)
        
        logger.info("TakerOrderAlertProcess initialized")
    
    def poll_all_alerts(self) -> None:
        """轮询所有告警（吃单监控无需轮询）"""
        pass
    
    def poll_user_alerts(self, tg_user_id: str) -> None:
        """轮询用户告警（吃单监控无需轮询）"""
        pass
    
    def tg_alert(self, post: str, channel_ids: list[str], pair: str):
        """
        发送 Telegram 告警
        
        Args:
            post: 告警消息
            channel_ids: 用户ID列表
            pair: 交易对（用于兼容基类接口，实际未使用）
        """
        for user_id in channel_ids:
            try:
                self.bot.send_message(user_id, post)
                logger.debug(f"Alert sent to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send alert to {user_id}: {e}")
    
    async def tg_alert_async(self, alert_message: str) -> None:
        """
        异步发送 Telegram 告警（内部使用，非阻塞）
        
        Args:
            alert_message: 告警消息
        """
        whitelist = get_whitelist()
        loop = asyncio.get_running_loop()
        
        for user_id in whitelist:
            try:
                # 使用executor在线程池中执行同步调用，避免阻塞事件循环
                await loop.run_in_executor(
                    None,
                    self.bot.send_message,
                    user_id,
                    alert_message
                )
                logger.debug(f"Alert sent to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send alert to {user_id}: {e}")
    
    def run(self):
        """启动监控进程"""
        if not TAKER_ORDER_MONITOR_ENABLED:
            logger.warning("Taker order monitoring is disabled, skipping")
            return
        
        logger.warning(f"TakerOrderAlertProcess started at {datetime.now()} UTC+0")
        
        # 创建事件循环并启动 WebSocket 客户端
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        
        try:
            self.event_loop.run_until_complete(self._async_run())
        except KeyboardInterrupt:
            logger.info("TakerOrderAlertProcess interrupted by user")
        except Exception as e:
            logger.error(f"TakerOrderAlertProcess error: {e}", exc_info=True)
        finally:
            self.event_loop.close()
    
    async def _async_run(self):
        """异步运行主循环"""
        try:
            # 确保事件循环引用已设置（在WebSocket启动前）
            if not self.event_loop:
                self.event_loop = asyncio.get_running_loop()
                logger.debug("Event loop reference captured")
            
            # 启动 WebSocket 客户端
            await self.ws_client.start()
            logger.info("Taker order WebSocket client started")
            
            # 保持运行
            while True:
                await asyncio.sleep(60)  # 每分钟清理一次过期数据
                self._cleanup_history()
                
        except Exception as e:
            logger.error(f"Error in async run: {e}", exc_info=True)
        finally:
            # 停止 WebSocket 客户端
            await self.ws_client.stop()
    
    def _on_trade_event(self, trade: TradeEvent) -> None:
        """
        处理交易事件（同步回调，线程安全）
        
        Args:
            trade: 交易事件
        """
        try:
            if self.event_loop and self.event_loop.is_running():
                # 使用线程安全的方式调度协程到事件循环
                asyncio.run_coroutine_threadsafe(
                    self._process_trade_async(trade),
                    self.event_loop
                )
            else:
                logger.warning("Event loop not running, cannot process trade")
        except Exception as e:
            logger.error(f"Error processing trade: {e}", exc_info=True)
    
    async def _process_trade_async(self, trade: TradeEvent) -> None:
        """
        异步处理交易事件
        
        Args:
            trade: 交易事件
        """
        try:
            await self.tracker.process_trade(trade)
        except Exception as e:
            logger.error(f"Error in async trade processing: {e}", exc_info=True)
    
    async def _handle_alert(self, alert: TakerAlert) -> None:
        """
        处理告警
        
        Args:
            alert: 告警对象
        """
        # 生成消息
        if alert.alert_type == "SINGLE_ORDER":
            message = self.single_formatter.get_alert_message(alert)
        else:
            message = self.cumulative_formatter.get_alert_message(alert)
        
        # 发送告警
        await self.tg_alert_async(message)
        
        # 记录历史
        self.alert_history.append({
            "alert": alert,
            "message": message,
            "sent_at": datetime.now()
        })
        
        logger.info(f"Alert handled: {alert}")
    
    def _cleanup_history(self) -> None:
        """清理告警历史"""
        if len(self.alert_history) > self.max_history_size:
            self.alert_history = self.alert_history[-self.max_history_size:]
            logger.debug(f"Alert history cleaned up, kept last {self.max_history_size} entries")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "tracker_stats": self.tracker.get_stats(),
            "alert_history_size": len(self.alert_history),
            "enabled": TAKER_ORDER_MONITOR_ENABLED,
            "symbols": TAKER_ORDER_MONITORED_SYMBOLS
        }
    
    def get_alert_history(self, limit: int = 10) -> list:
        """
        获取告警历史
        
        Args:
            limit: 返回的最大记录数
        
        Returns:
            list: 告警历史记录
        """
        return self.alert_history[-limit:]
