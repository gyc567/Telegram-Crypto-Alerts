"""
累积监控器
监控 1分钟内累积吃单 ≥ $1M USD + ≥5笔订单
"""
import logging
from collections import defaultdict
from typing import Dict, Optional, Tuple, List
from datetime import datetime

from ..src.models import TakerAlert
from ...large_orders.src.base import TradeEvent

logger = logging.getLogger(__name__)


class CumulativeMonitor:
    """
    累积监控器
    
    功能：
    1. 维护 1分钟滚动窗口
    2. 按交易对和方向聚合吃单
    3. 检测累积金额 ≥ $1M USD + 订单数 ≥ 5笔
    4. 生成累积告警
    """
    
    def __init__(self, config: Dict):
        """
        初始化累积监控器
        
        Args:
            config: 配置字典，包含：
                - window_size: 窗口大小（秒）
                - threshold_usd: 金额阈值（USD）
                - min_order_count: 最少订单数
                - directions: 监控方向列表
        """
        self.window_size = config["window_size"]
        self.threshold_usd = config["threshold_usd"]
        self.min_order_count = config["min_order_count"]
        self.directions = config["directions"]
        
        # 时间窗口：{symbol_direction: [trade_data, ...]}
        self.time_windows = defaultdict(list)
        
        self.stats = {
            "cumulative_alerts": 0,
            "buy_alerts": 0,
            "sell_alerts": 0,
            "total_trades_added": 0,
            "window_cleanups": 0
        }
        
        logger.info(
            f"CumulativeMonitor initialized: "
            f"window={self.window_size}s, "
            f"threshold=${self.threshold_usd:,.0f}, "
            f"min_orders={self.min_order_count}"
        )
    
    def add_trade(self, trade: TradeEvent) -> None:
        """
        添加交易到时间窗口
        
        Args:
            trade: 交易事件
        """
        # 只处理吃单
        if not trade.is_taker:
            return
        
        current_time = int(trade.trade_time / 1000)  # 转换为秒
        
        # 添加到对应方向的窗口
        window_key = f"{trade.symbol}_{trade.side}"
        self.time_windows[window_key].append({
            "trade": trade,
            "timestamp": current_time,
            "amount_usd": trade.amount  # 已经是USD金额
        })
        
        self.stats["total_trades_added"] += 1
        
        # 清理过期数据
        self.cleanup_windows(current_time)
    
    def cleanup_windows(self, current_time: int) -> None:
        """
        清理所有窗口中的过期数据
        
        Args:
            current_time: 当前时间戳（秒）
        """
        cutoff_time = current_time - self.window_size
        
        for window_key in list(self.time_windows.keys()):
            trades = self.time_windows[window_key]
            # 保留窗口内的交易
            self.time_windows[window_key] = [
                t for t in trades
                if t["timestamp"] > cutoff_time
            ]
            
            # 删除空窗口
            if not self.time_windows[window_key]:
                del self.time_windows[window_key]
                self.stats["window_cleanups"] += 1
    
    def check_threshold(
        self,
        symbol: str,
        direction: str,
        current_time: int
    ) -> Optional[TakerAlert]:
        """
        检查指定交易对和方向是否达到累积阈值
        
        Args:
            symbol: 交易对
            direction: 方向 ("BUY" or "SELL")
            current_time: 当前时间戳（秒）
        
        Returns:
            Optional[TakerAlert]: 如果达到阈值返回告警对象，否则返回None
        """
        window_key = f"{symbol}_{direction}"
        trades = self.time_windows.get(window_key, [])
        
        # 检查订单数量
        if len(trades) < self.min_order_count:
            return None
        
        # 计算总金额
        total_amount_usd = sum(t["amount_usd"] for t in trades)
        
        # 检查金额阈值
        if total_amount_usd < self.threshold_usd:
            return None
        
        # 达到阈值，生成告警
        self.stats["cumulative_alerts"] += 1
        
        if direction == "BUY":
            self.stats["buy_alerts"] += 1
        else:
            self.stats["sell_alerts"] += 1
        
        avg_amount = total_amount_usd / len(trades)
        start_time = current_time - self.window_size
        
        logger.info(
            f"Cumulative threshold triggered: {symbol} {direction} "
            f"{len(trades)} orders, ${total_amount_usd:,.2f}"
        )
        
        return TakerAlert(
            alert_type="CUMULATIVE",
            symbol=symbol,
            direction=direction,
            timestamp=int(current_time * 1000),  # 转换回毫秒
            order_count=len(trades),
            total_amount_usd=total_amount_usd,
            avg_amount_usd=avg_amount,
            time_range=(start_time, current_time)
        )
    
    def get_alert_message(self, alert: TakerAlert) -> str:
        """
        生成累积告警消息
        
        Args:
            alert: 告警对象
        
        Returns:
            str: 格式化的告警消息
        """
        direction = "主动买入" if alert.direction == "BUY" else "主动卖出"
        start_time = datetime.fromtimestamp(alert.time_range[0]).strftime('%H:%M:%S')
        end_time = datetime.fromtimestamp(alert.time_range[1]).strftime('%H:%M:%S')
        
        return (
            f"⚡ [吃单监控] {alert.symbol}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📈 累积吃单活动告警！\n"
            f"⏱️  时间范围: {start_time}-{end_time} (60秒)\n"
            f"🔄 方向: {direction}\n"
            f"📊 订单数: {alert.order_count}笔\n"
            f"💰 总金额: ${alert.total_amount_usd:,.2f}\n"
            f"📉 平均金额: ${alert.avg_amount_usd:,.2f}"
        )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        stats["active_windows"] = len(self.time_windows)
        return stats
    
    def get_window_info(self, symbol: str, direction: str) -> Dict:
        """
        获取指定窗口的信息
        
        Args:
            symbol: 交易对
            direction: 方向
        
        Returns:
            Dict: 窗口信息，包含订单数和总金额
        """
        window_key = f"{symbol}_{direction}"
        trades = self.time_windows.get(window_key, [])
        
        total_amount = sum(t["amount_usd"] for t in trades)
        
        return {
            "order_count": len(trades),
            "total_amount_usd": total_amount,
            "avg_amount_usd": total_amount / len(trades) if trades else 0
        }
