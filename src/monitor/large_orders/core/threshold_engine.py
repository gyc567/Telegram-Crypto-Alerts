"""
阈值引擎
负责检测订单量阈值突破并触发告警
"""
import asyncio
from typing import Dict, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThresholdEvent:
    """阈值突破事件"""
    symbol: str
    direction: str  # "买入" or "卖出"
    total_volume: float
    buy_volume: float
    sell_volume: float
    trade_count: int
    threshold_usd: float
    window_minutes: int
    timestamp: datetime
    cooldown_until: Optional[datetime] = None


class ThresholdEngine:
    """
    阈值引擎
    
    负责：
    1. 监控聚合器输出
    2. 检测阈值突破
    3. 管理冷却时间
    4. 触发告警事件
    5. 防止重复告警
    """
    
    def __init__(
        self,
        threshold_usd: float = 2_000_000,
        cooldown_minutes: int = 5
    ):
        self.threshold_usd = threshold_usd
        self.cooldown_minutes = cooldown_minutes
        
        # 冷却管理: symbol → datetime
        self.cooldowns: Dict[str, datetime] = {}
        
        # 告警回调函数
        self.alert_callback: Optional[Callable[[ThresholdEvent], None]] = None
        
        # 统计信息
        self.stats = {
            "threshold_checks": 0,
            "alerts_triggered": 0,
            "alerts_suppressed": 0,
            "cooldowns_active": 0
        }
        
        logger.info(f"初始化阈值引擎：${threshold_usd:,.0f}阈值，{cooldown_minutes}分钟冷却")
    
    def set_alert_callback(self, callback: Callable[[ThresholdEvent], None]) -> None:
        """设置告警回调函数"""
        self.alert_callback = callback
        logger.info("告警回调已设置")
    
    async def check_aggregation(
        self,
        symbol: str,
        aggregation_data: Dict
    ) -> Optional[ThresholdEvent]:
        """
        检查聚合数据是否突破阈值
        
        Args:
            symbol: 交易对
            aggregation_data: 聚合数据
            
        Returns:
            ThresholdEvent if threshold breached, None otherwise
        """
        try:
            self.stats["threshold_checks"] += 1
            
            # 检查阈值
            if not aggregation_data.get("threshold_breach", False):
                return None
            
            # 获取聚合信息
            total_volume = aggregation_data.get("total_volume", 0.0)
            buy_volume = aggregation_data.get("buy_volume", 0.0)
            sell_volume = aggregation_data.get("sell_volume", 0.0)
            trade_count = aggregation_data.get("trade_count", 0)
            window_minutes = aggregation_data.get("window_minutes", 5)
            
            # 决定主要方向
            if buy_volume > sell_volume:
                direction = "买入"
            elif sell_volume > buy_volume:
                direction = "卖出"
            else:
                direction = "双向"
            
            # 创建阈值事件
            event = ThresholdEvent(
                symbol=symbol,
                direction=direction,
                total_volume=total_volume,
                buy_volume=buy_volume,
                sell_volume=sell_volume,
                trade_count=trade_count,
                threshold_usd=self.threshold_usd,
                window_minutes=window_minutes,
                timestamp=datetime.now()
            )
            
            # 检查冷却
            if await self._is_in_cooldown(symbol):
                self.stats["alerts_suppressed"] += 1
                logger.info(f"抑制告警: {symbol} 处于冷却期")
                return None
            
            # 记录冷却
            await self._set_cooldown(symbol)
            
            # 触发告警
            self.stats["alerts_triggered"] += 1
            logger.warning(
                f"阈值突破: {symbol} {direction} "
                f"${total_volume:,.0f} (阈值: ${self.threshold_usd:,.0f})"
            )
            
            # 调用告警回调
            if self.alert_callback:
                try:
                    if asyncio.iscoroutinefunction(self.alert_callback):
                        await self.alert_callback(event)
                    else:
                        self.alert_callback(event)
                except Exception as e:
                    logger.error(f"告警回调失败: {e}", exc_info=True)
            
            return event
            
        except Exception as e:
            logger.error(f"检查阈值失败: {e}", exc_info=True)
            return None
    
    async def _is_in_cooldown(self, symbol: str) -> bool:
        """检查是否在冷却期"""
        try:
            if symbol not in self.cooldowns:
                return False
            
            cooldown_until = self.cooldowns[symbol]
            now = datetime.now()
            
            if now < cooldown_until:
                return True
            else:
                # 冷却已过期，清理
                del self.cooldowns[symbol]
                return False
            
        except Exception as e:
            logger.error(f"检查冷却失败: {e}", exc_info=True)
            return False
    
    async def _set_cooldown(self, symbol: str) -> None:
        """设置冷却时间"""
        try:
            cooldown_until = datetime.now() + timedelta(minutes=self.cooldown_minutes)
            self.cooldowns[symbol] = cooldown_until
            self.stats["cooldowns_active"] += 1
            
            logger.debug(f"设置冷却: {symbol} 冷却至 {cooldown_until}")
            
        except Exception as e:
            logger.error(f"设置冷却失败: {e}", exc_info=True)
    
    def get_cooldown_status(self, symbol: str) -> Optional[Dict]:
        """
        获取交易对冷却状态
        
        Args:
            symbol: 交易对
            
        Returns:
            Dict with cooldown info
        """
        try:
            if symbol not in self.cooldowns:
                return {
                    "symbol": symbol,
                    "in_cooldown": False,
                    "remaining_seconds": 0,
                    "cooldown_until": None
                }
            
            cooldown_until = self.cooldowns[symbol]
            now = datetime.now()
            
            if now < cooldown_until:
                remaining = (cooldown_until - now).total_seconds()
                return {
                    "symbol": symbol,
                    "in_cooldown": True,
                    "remaining_seconds": remaining,
                    "cooldown_until": cooldown_until
                }
            else:
                # 冷却已过期
                del self.cooldowns[symbol]
                return {
                    "symbol": symbol,
                    "in_cooldown": False,
                    "remaining_seconds": 0,
                    "cooldown_until": None
                }
            
        except Exception as e:
            logger.error(f"获取冷却状态失败: {e}", exc_info=True)
            return None
    
    def get_all_cooldowns(self) -> List[Dict]:
        """获取所有活跃的冷却"""
        try:
            now = datetime.now()
            active_cooldowns = []
            
            for symbol, cooldown_until in self.cooldowns.items():
                if now < cooldown_until:
                    remaining = (cooldown_until - now).total_seconds()
                    active_cooldowns.append({
                        "symbol": symbol,
                        "remaining_seconds": remaining,
                        "cooldown_until": cooldown_until
                    })
                else:
                    # 清理过期冷却
                    del self.cooldowns[symbol]
            
            return active_cooldowns
            
        except Exception as e:
            logger.error(f"获取所有冷却失败: {e}", exc_info=True)
            return []
    
    def clear_cooldown(self, symbol: str) -> bool:
        """
        清除冷却
        
        Args:
            symbol: 交易对
            
        Returns:
            bool: 是否成功清除
        """
        try:
            if symbol in self.cooldowns:
                del self.cooldowns[symbol]
                self.stats["cooldowns_active"] = max(0, self.stats["cooldowns_active"] - 1)
                logger.info(f"清除冷却: {symbol}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"清除冷却失败: {e}", exc_info=True)
            return False
    
    def clear_all_cooldowns(self) -> int:
        """清除所有冷却"""
        try:
            count = len(self.cooldowns)
            self.cooldowns.clear()
            self.stats["cooldowns_active"] = 0
            logger.info(f"清除所有冷却: {count} 个")
            return count
            
        except Exception as e:
            logger.error(f"清除所有冷却失败: {e}", exc_info=True)
            return 0
    
    def update_threshold(self, new_threshold: float) -> None:
        """更新阈值"""
        self.threshold_usd = new_threshold
        logger.info(f"更新阈值: ${new_threshold:,.0f}")
    
    def update_cooldown(self, new_cooldown_minutes: int) -> None:
        """更新冷却时间"""
        self.cooldown_minutes = new_cooldown_minutes
        logger.info(f"更新冷却时间: {new_cooldown_minutes} 分钟")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        active_cooldowns = len(self.cooldowns)
        
        return {
            **self.stats,
            "current_cooldowns": active_cooldowns,
            "threshold_usd": self.threshold_usd,
            "cooldown_minutes": self.cooldown_minutes
        }
