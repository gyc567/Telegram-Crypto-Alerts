"""
通用冷却管理器 - 用于防止告警轰炸
支持多种冷却策略和独立的冷却键
"""
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CooldownManager:
    """
    冷却管理器
    
    功能：
    1. 支持多个独立的冷却键（如不同的交易对、告警类型）
    2. 可配置冷却时间
    3. 自动清理过期的冷却记录
    4. 线程安全（使用时间戳比较）
    
    使用示例：
    ```python
    cooldown = CooldownManager(default_duration=300)  # 5分钟冷却
    
    # 检查是否在冷却中
    if not cooldown.is_in_cooldown("BTCUSDT_SELL"):
        send_alert()
        cooldown.set_cooldown("BTCUSDT_SELL")
    
    # 使用自定义冷却时间
    cooldown.set_cooldown("ETHUSDT_BUY", duration=60)
    ```
    """
    
    def __init__(self, default_duration: int = 300):
        """
        初始化冷却管理器
        
        Args:
            default_duration: 默认冷却时间（秒）
        """
        self.default_duration = default_duration
        self.cooldowns: Dict[str, float] = {}  # key -> expiry_timestamp
        self.stats = {
            "total_cooldowns_set": 0,
            "total_cooldowns_expired": 0,
            "active_cooldowns": 0
        }
        
        logger.info(f"CooldownManager initialized with default duration: {default_duration}s")
    
    def is_in_cooldown(self, key: str) -> bool:
        """
        检查指定键是否在冷却期内
        
        Args:
            key: 冷却键（例如："BTCUSDT", "BTCUSDT_cumulative"）
        
        Returns:
            bool: True 表示在冷却期内，False 表示可以发送告警
        """
        current_time = time.time()
        
        # 检查是否有冷却记录
        if key not in self.cooldowns:
            return False
        
        expiry_time = self.cooldowns[key]
        
        # 检查是否已过期
        if current_time >= expiry_time:
            # 已过期，清理记录
            del self.cooldowns[key]
            self.stats["total_cooldowns_expired"] += 1
            self.stats["active_cooldowns"] = len(self.cooldowns)
            return False
        
        # 仍在冷却期内
        return True
    
    def set_cooldown(self, key: str, duration: Optional[int] = None) -> None:
        """
        设置冷却期
        
        Args:
            key: 冷却键
            duration: 冷却时间（秒），如果为None则使用默认值
        """
        cooldown_duration = duration if duration is not None else self.default_duration
        expiry_time = time.time() + cooldown_duration
        
        self.cooldowns[key] = expiry_time
        self.stats["total_cooldowns_set"] += 1
        self.stats["active_cooldowns"] = len(self.cooldowns)
        
        logger.debug(f"Cooldown set for '{key}': {cooldown_duration}s")
    
    def get_remaining_time(self, key: str) -> float:
        """
        获取剩余冷却时间
        
        Args:
            key: 冷却键
        
        Returns:
            float: 剩余时间（秒），如果不在冷却期则返回0
        """
        if key not in self.cooldowns:
            return 0.0
        
        current_time = time.time()
        expiry_time = self.cooldowns[key]
        remaining = expiry_time - current_time
        
        return max(0.0, remaining)
    
    def clear_cooldown(self, key: str) -> None:
        """
        清除指定键的冷却
        
        Args:
            key: 冷却键
        """
        if key in self.cooldowns:
            del self.cooldowns[key]
            self.stats["active_cooldowns"] = len(self.cooldowns)
            logger.debug(f"Cooldown cleared for '{key}'")
    
    def clear_all(self) -> None:
        """清除所有冷却记录"""
        count = len(self.cooldowns)
        self.cooldowns.clear()
        self.stats["active_cooldowns"] = 0
        logger.info(f"Cleared {count} cooldown records")
    
    def cleanup_expired(self) -> int:
        """
        清理所有已过期的冷却记录
        
        Returns:
            int: 清理的记录数量
        """
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self.cooldowns.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            del self.cooldowns[key]
        
        if expired_keys:
            self.stats["total_cooldowns_expired"] += len(expired_keys)
            self.stats["active_cooldowns"] = len(self.cooldowns)
            logger.debug(f"Cleaned up {len(expired_keys)} expired cooldowns")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def __repr__(self) -> str:
        return f"CooldownManager(default={self.default_duration}s, active={len(self.cooldowns)})"
