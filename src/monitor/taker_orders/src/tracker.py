"""
吃单订单追踪器
整合单笔监控和累积监控，提供统一接口
"""
import logging
from typing import Dict, List, Optional, Callable
import asyncio

from .models import TakerAlert
from ..core.single_monitor import SingleOrderMonitor
from ..core.cumulative_monitor import CumulativeMonitor
from ...large_orders.src.base import TradeEvent
from ...large_orders.src.price_converter import PriceConverter
from ...common.cooldown import CooldownManager

logger = logging.getLogger(__name__)


class TakerOrderTracker:
    """
    吃单订单追踪器
    
    功能：
    1. 接收交易事件
    2. 检测单笔大额吃单
    3. 检测累积吃单活动
    4. 管理告警冷却
    5. 触发告警回调
    """
    
    def __init__(
        self,
        symbols: List[str],
        single_thresholds: Dict[str, float],
        cumulative_config: Dict,
        cooldown_config: Dict
    ):
        """
        初始化追踪器
        
        Args:
            symbols: 监控的交易对列表
            single_thresholds: 单笔阈值配置
            cumulative_config: 累积监控配置
            cooldown_config: 冷却配置
        """
        self.symbols = symbols
        self.single_thresholds = single_thresholds
        self.cumulative_config = cumulative_config
        self.cooldown_config = cooldown_config
        
        # 初始化监控器
        self.single_monitor = SingleOrderMonitor(single_thresholds)
        self.cumulative_monitor = CumulativeMonitor(cumulative_config)
        
        # 初始化冷却管理器（两个独立的管理器）
        self.single_cooldown = CooldownManager(
            default_duration=cooldown_config["single_order"]
        )
        self.cumulative_cooldown = CooldownManager(
            default_duration=cooldown_config["cumulative"]
        )
        
        # 回调函数
        self.alert_callback: Optional[Callable[[TakerAlert], None]] = None
        
        # 统计
        self.stats = {
            "trades_processed": 0,
            "single_alerts": 0,
            "cumulative_alerts": 0,
            "alerts_blocked_by_cooldown": 0
        }
        
        logger.info(
            f"TakerOrderTracker initialized for symbols: {symbols}"
        )
    
    def set_alert_callback(self, callback: Callable[[TakerAlert], None]) -> None:
        """设置告警回调函数"""
        self.alert_callback = callback
    
    async def process_trade(self, trade: TradeEvent) -> None:
        """
        处理交易事件
        
        Args:
            trade: 交易事件
        """
        # 检查是否监控此交易对
        if trade.symbol not in self.symbols:
            return
        
        # 检查是否为吃单
        if not trade.is_taker:
            return
        
        self.stats["trades_processed"] += 1
        
        # 1. 检查单笔订单阈值
        single_alert = self.single_monitor.check_threshold(trade)
        if single_alert:
            await self._handle_single_alert(single_alert)
        
        # 2. 添加到累积监控
        current_time = int(trade.trade_time / 1000)
        self.cumulative_monitor.add_trade(trade)
        
        # 3. 检查累积阈值
        for direction in self.cumulative_config["directions"]:
            cumulative_alert = self.cumulative_monitor.check_threshold(
                trade.symbol,
                direction,
                current_time
            )
            if cumulative_alert:
                await self._handle_cumulative_alert(cumulative_alert)
    
    async def _handle_single_alert(self, alert: TakerAlert) -> None:
        """
        处理单笔订单告警
        
        Args:
            alert: 告警对象
        """
        # 检查冷却
        cooldown_key = alert.symbol
        if self.single_cooldown.is_in_cooldown(cooldown_key):
            self.stats["alerts_blocked_by_cooldown"] += 1
            logger.debug(f"Single alert blocked by cooldown: {cooldown_key}")
            return
        
        # 发送告警
        if self.alert_callback:
            try:
                await self._safe_callback(alert)
                self.stats["single_alerts"] += 1
                
                # 设置冷却
                self.single_cooldown.set_cooldown(cooldown_key)
                logger.info(f"Single alert sent: {alert}")
            except Exception as e:
                logger.error(f"Error in alert callback: {e}", exc_info=True)
    
    async def _handle_cumulative_alert(self, alert: TakerAlert) -> None:
        """
        处理累积告警
        
        Args:
            alert: 告警对象
        """
        # 检查冷却
        cooldown_key = f"{alert.symbol}_{alert.direction}"
        if self.cumulative_cooldown.is_in_cooldown(cooldown_key):
            self.stats["alerts_blocked_by_cooldown"] += 1
            logger.debug(f"Cumulative alert blocked by cooldown: {cooldown_key}")
            return
        
        # 发送告警
        if self.alert_callback:
            try:
                await self._safe_callback(alert)
                self.stats["cumulative_alerts"] += 1
                
                # 设置冷却
                self.cumulative_cooldown.set_cooldown(cooldown_key)
                logger.info(f"Cumulative alert sent: {alert}")
            except Exception as e:
                logger.error(f"Error in alert callback: {e}", exc_info=True)
    
    async def _safe_callback(self, alert: TakerAlert) -> None:
        """
        安全地调用回调函数
        
        Args:
            alert: 告警对象
        """
        if asyncio.iscoroutinefunction(self.alert_callback):
            await self.alert_callback(alert)
        else:
            self.alert_callback(alert)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        stats["single_monitor"] = self.single_monitor.get_stats()
        stats["cumulative_monitor"] = self.cumulative_monitor.get_stats()
        stats["single_cooldown"] = self.single_cooldown.get_stats()
        stats["cumulative_cooldown"] = self.cumulative_cooldown.get_stats()
        return stats
    
    def get_window_info(self, symbol: str, direction: str) -> Dict:
        """
        获取累积窗口信息
        
        Args:
            symbol: 交易对
            direction: 方向
        
        Returns:
            Dict: 窗口信息
        """
        return self.cumulative_monitor.get_window_info(symbol, direction)
