"""
吃单监控数据模型
定义告警数据结构和配置
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime


@dataclass
class TakerAlert:
    """吃单告警数据模型"""
    alert_type: str  # "SINGLE_ORDER" or "CUMULATIVE"
    symbol: str
    direction: str  # "BUY" or "SELL"
    timestamp: int  # millisecond timestamp
    
    # 单笔订单告警字段
    quantity: Optional[float] = None
    amount_usd: Optional[float] = None
    price: Optional[float] = None
    
    # 累积告警字段
    order_count: Optional[int] = None
    total_amount_usd: Optional[float] = None
    avg_amount_usd: Optional[float] = None
    time_range: Optional[Tuple[int, int]] = None  # (start_time, end_time) in seconds
    
    # 告警控制
    cooldown_until: Optional[int] = None
    
    def __str__(self) -> str:
        if self.alert_type == "SINGLE_ORDER":
            return f"TakerAlert(SINGLE, {self.symbol}, {self.direction}, {self.quantity})"
        else:
            return f"TakerAlert(CUMULATIVE, {self.symbol}, {self.direction}, {self.order_count} orders)"
