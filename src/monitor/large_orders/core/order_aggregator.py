"""
订单聚合器
负责5分钟滚动窗口的订单量统计
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import logging

from ..src.base import TradeEvent

logger = logging.getLogger(__name__)


@dataclass
class WindowEntry:
    """窗口条目"""
    trade_event: TradeEvent
    usd_value: float
    timestamp: datetime
    buy_volume: float = 0.0
    sell_volume: float = 0.0


class OrderAggregator:
    """
    订单聚合器
    
    负责：
    1. 维护5分钟滚动窗口
    2. 累加买卖订单量
    3. 转换订单为USD
    4. 检测窗口溢出
    5. 清理过期数据
    """
    
    def __init__(
        self,
        window_minutes: int = 5,
        threshold_usd: float = 2_000_000
    ):
        self.window_minutes = window_minutes
        self.threshold_usd = threshold_usd
        self.window_ms = window_minutes * 60 * 1000  # 转换为毫秒
        
        # 交易对 → 窗口条目队列
        self.trade_windows: Dict[str, deque] = {}
        
        # 统计信息
        self.stats = {
            "trades_processed": 0,
            "alerts_triggered": 0,
            "window_resets": 0,
            "cleanup_count": 0
        }
        
        logger.info(f"初始化订单聚合器：{window_minutes}分钟窗口，${threshold_usd:,.0f}阈值")
    
    async def add_trade(self, symbol: str, trade_event: TradeEvent, usd_value: float) -> None:
        """
        添加交易到聚合器
        
        Args:
            symbol: 交易对
            trade_event: 交易事件
            usd_value: USD价值
        """
        try:
            # 创建窗口条目
            window_entry = WindowEntry(
                trade_event=trade_event,
                usd_value=usd_value,
                timestamp=datetime.now(),
                buy_volume=usd_value if trade_event.side == "BUY" else 0.0,
                sell_volume=usd_value if trade_event.side == "SELL" else 0.0
            )
            
            # 初始化交易对窗口
            if symbol not in self.trade_windows:
                self.trade_windows[symbol] = deque()
            
            # 添加到窗口
            self.trade_windows[symbol].append(window_entry)
            
            # 清理过期数据
            await self._cleanup_window(symbol)
            
            # 检查阈值
            await self._check_threshold(symbol)
            
            self.stats["trades_processed"] += 1
            
        except Exception as e:
            logger.error(f"添加交易失败: {e}", exc_info=True)
    
    async def _cleanup_window(self, symbol: str) -> None:
        """清理过期数据"""
        try:
            if symbol not in self.trade_windows:
                return
            
            window = self.trade_windows[symbol]
            if not window:
                return
            
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(minutes=self.window_minutes)
            
            # 移除过期条目
            removed_count = 0
            while window and window[0].timestamp < cutoff_time:
                window.popleft()
                removed_count += 1
            
            if removed_count > 0:
                self.stats["cleanup_count"] += removed_count
                logger.debug(f"清理 {symbol} 过期数据: {removed_count} 条")
            
        except Exception as e:
            logger.error(f"清理窗口失败: {e}", exc_info=True)
    
    async def _check_threshold(self, symbol: str) -> Optional[Dict]:
        """
        检查阈值是否突破
        
        Returns:
            Dict if threshold breached, None otherwise
        """
        try:
            if symbol not in self.trade_windows:
                return None
            
            window = self.trade_windows[symbol]
            if not window:
                return None
            
            # 计算当前窗口总交易量
            total_volume = sum(entry.usd_value for entry in window)
            buy_volume = sum(entry.buy_volume for entry in window)
            sell_volume = sum(entry.sell_volume for entry in window)
            
            # 检查是否突破阈值
            if total_volume >= self.threshold_usd:
                # 决定主要方向
                if buy_volume > sell_volume:
                    direction = "买入"
                elif sell_volume > buy_volume:
                    direction = "卖出"
                else:
                    direction = "双向"
                
                # 创建告警信息
                alert_info = {
                    "symbol": symbol,
                    "direction": direction,
                    "total_volume": total_volume,
                    "buy_volume": buy_volume,
                    "sell_volume": sell_volume,
                    "trade_count": len(window),
                    "window_minutes": self.window_minutes,
                    "threshold_usd": self.threshold_usd,
                    "timestamp": datetime.now()
                }
                
                self.stats["alerts_triggered"] += 1
                logger.warning(
                    f"阈值突破: {symbol} ${total_volume:,.0f} "
                    f"(买入: ${buy_volume:,.0f}, 卖出: ${sell_volume:,.0f})"
                )
                
                return alert_info
            
            return None
            
        except Exception as e:
            logger.error(f"检查阈值失败: {e}", exc_info=True)
            return None
    
    async def reset_window(self, symbol: str) -> None:
        """
        重置交易对窗口
        
        Args:
            symbol: 交易对
        """
        try:
            if symbol in self.trade_windows:
                self.trade_windows[symbol].clear()
                self.stats["window_resets"] += 1
                logger.debug(f"重置 {symbol} 窗口")
            
        except Exception as e:
            logger.error(f"重置窗口失败: {e}", exc_info=True)
    
    def get_window_summary(self, symbol: str) -> Optional[Dict]:
        """
        获取交易对窗口摘要
        
        Args:
            symbol: 交易对
            
        Returns:
            Dict with window summary
        """
        try:
            if symbol not in self.trade_windows:
                return None
            
            window = self.trade_windows[symbol]
            if not window:
                return {
                    "symbol": symbol,
                    "trade_count": 0,
                    "total_volume": 0.0,
                    "buy_volume": 0.0,
                    "sell_volume": 0.0,
                    "oldest_trade": None,
                    "newest_trade": None,
                    "window_minutes": self.window_minutes
                }
            
            # 计算总交易量
            total_volume = sum(entry.usd_value for entry in window)
            buy_volume = sum(entry.buy_volume for entry in window)
            sell_volume = sum(entry.sell_volume for entry in window)
            
            # 获取时间范围
            oldest_trade = window[0].timestamp if window else None
            newest_trade = window[-1].timestamp if window else None
            
            # 计算窗口覆盖率
            if window:
                time_span = (newest_trade - oldest_trade).total_seconds()
                coverage = min(100.0, (time_span / (self.window_minutes * 60)) * 100)
            else:
                coverage = 0.0
            
            return {
                "symbol": symbol,
                "trade_count": len(window),
                "total_volume": total_volume,
                "buy_volume": buy_volume,
                "sell_volume": sell_volume,
                "oldest_trade": oldest_trade,
                "newest_trade": newest_trade,
                "time_span_seconds": time_span if window else 0,
                "window_coverage": coverage,
                "window_minutes": self.window_minutes,
                "threshold_usd": self.threshold_usd,
                "threshold_breach": total_volume >= self.threshold_usd
            }
            
        except Exception as e:
            logger.error(f"获取窗口摘要失败: {e}", exc_info=True)
            return None
    
    def get_all_symbols_summary(self) -> List[Dict]:
        """获取所有交易对窗口摘要"""
        return [
            self.get_window_summary(symbol)
            for symbol in self.trade_windows.keys()
            if self.get_window_summary(symbol) is not None
        ]
    
    def update_threshold(self, new_threshold: float) -> None:
        """
        更新阈值
        
        Args:
            new_threshold: 新的USD阈值
        """
        self.threshold_usd = new_threshold
        logger.info(f"更新阈值: ${new_threshold:,.0f}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "active_symbols": len(self.trade_windows),
            "total_trades_in_windows": sum(len(window) for window in self.trade_windows.values())
        }
    
    async def cleanup_all(self) -> None:
        """清理所有窗口"""
        try:
            for symbol in self.trade_windows.keys():
                await self._cleanup_window(symbol)
            
            logger.info(f"清理所有窗口，共 {len(self.trade_windows)} 个交易对")
            
        except Exception as e:
            logger.error(f"清理所有窗口失败: {e}", exc_info=True)
