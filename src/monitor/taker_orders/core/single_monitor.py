"""
单笔订单监控器
监控 BTC ≥ 50 和 ETH ≥ 2000 的吃单订单
"""
import logging
from typing import Dict, Optional
from datetime import datetime

from ..src.models import TakerAlert
from ...large_orders.src.base import TradeEvent

logger = logging.getLogger(__name__)


class SingleOrderMonitor:
    """
    单笔订单监控器
    
    功能：
    1. 检测 BTC 单笔订单 ≥ 50
    2. 检测 ETH 单笔订单 ≥ 2000
    3. 生成单笔订单告警
    """
    
    def __init__(self, thresholds: Dict[str, float]):
        """
        初始化单笔订单监控器
        
        Args:
            thresholds: 数量阈值字典，例如 {"BTCUSDT": 50, "ETHUSDT": 2000}
        """
        self.thresholds = thresholds
        self.stats = {
            "single_order_alerts": 0,
            "btc_alerts": 0,
            "eth_alerts": 0,
            "total_checked": 0
        }
        
        logger.info(f"SingleOrderMonitor initialized with thresholds: {thresholds}")
    
    def check_threshold(self, trade: TradeEvent) -> Optional[TakerAlert]:
        """
        检查交易是否达到单笔阈值
        
        Args:
            trade: 交易事件
        
        Returns:
            Optional[TakerAlert]: 如果达到阈值返回告警对象，否则返回None
        """
        self.stats["total_checked"] += 1
        
        symbol = trade.symbol
        
        # 检查是否监控此交易对
        if symbol not in self.thresholds:
            return None
        
        # 检查是否为吃单
        if not trade.is_taker:
            return None
        
        threshold = self.thresholds[symbol]
        quantity = trade.quantity
        
        # 检查是否达到阈值
        if quantity >= threshold:
            self.stats["single_order_alerts"] += 1
            
            if symbol == "BTCUSDT":
                self.stats["btc_alerts"] += 1
            elif symbol == "ETHUSDT":
                self.stats["eth_alerts"] += 1
            
            logger.info(f"Single order threshold triggered: {symbol} {quantity} >= {threshold}")
            
            return TakerAlert(
                alert_type="SINGLE_ORDER",
                symbol=symbol,
                direction=trade.side,
                timestamp=trade.trade_time,
                quantity=quantity,
                amount_usd=trade.amount,
                price=trade.price
            )
        
        return None
    
    def get_alert_message(self, alert: TakerAlert) -> str:
        """
        生成单笔告警消息
        
        Args:
            alert: 告警对象
        
        Returns:
            str: 格式化的告警消息
        """
        symbol = alert.symbol
        direction = "主动买入" if alert.direction == "BUY" else "主动卖出"
        time_str = datetime.fromtimestamp(alert.timestamp / 1000).strftime('%H:%M:%S')
        
        if symbol == "BTCUSDT":
            return (
                f"🚨 [吃单监控] {symbol}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 单笔大额吃单告警！\n"
                f"🔄 方向: {direction}\n"
                f"💰 数量: {alert.quantity:.2f} BTC\n"
                f"💵 金额: ${alert.amount_usd:,.2f}\n"
                f"💹 价格: ${alert.price:,.2f}\n"
                f"⏰ 时间: {time_str}"
            )
        elif symbol == "ETHUSDT":
            return (
                f"🚨 [吃单监控] {symbol}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 单笔大额吃单告警！\n"
                f"🔄 方向: {direction}\n"
                f"💰 数量: {alert.quantity:.0f} ETH\n"
                f"💵 金额: ${alert.amount_usd:,.2f}\n"
                f"💹 价格: ${alert.price:,.2f}\n"
                f"⏰ 时间: {time_str}"
            )
        else:
            return f"Unknown symbol: {symbol}"
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
