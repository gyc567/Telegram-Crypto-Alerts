"""
时间窗口管理器
负责管理多时间窗口的吃单监控
"""
from typing import Dict, Optional
from .order_aggregator import OrderAggregator
import logging

logger = logging.getLogger(__name__)


class TimeWindowManager:
    """
    时间窗口管理器
    负责管理多时间窗口的吃单监控
    """

    def __init__(self):
        self.windows: Dict[int, OrderAggregator] = {}
        self.active_window = self._load_configured_window()
        self._initialize_windows()

    def _load_configured_window(self) -> int:
        """加载配置的时间窗口"""
        try:
            from ....config import TAKER_CUMULATIVE_WINDOW_MINUTES
            return TAKER_CUMULATIVE_WINDOW_MINUTES
        except ImportError:
            return 60  # 默认1小时

    def _initialize_windows(self):
        """初始化默认窗口"""
        default_window = self._load_configured_window()
        if default_window not in self.windows:
            self.windows[default_window] = OrderAggregator(window_minutes=default_window)
            logger.info(f"初始化时间窗口管理器，当前窗口：{default_window}分钟")

    def update_window_size(self, new_window_minutes: int) -> bool:
        """动态更新时间窗口大小"""
        if not self._validate_window_size(new_window_minutes):
            logger.error(f"Invalid window size: {new_window_minutes}")
            return False

        old_window = self.active_window
        self.active_window = new_window_minutes

        # 创建新的聚合器
        if new_window_minutes not in self.windows:
            self.windows[new_window_minutes] = OrderAggregator(window_minutes=new_window_minutes)
            logger.info(f"创建新窗口：{new_window_minutes}分钟")

        # 清理旧的窗口 (如果不再需要)
        if old_window not in [5, 15, 60]:  # 保留常用窗口
            if old_window in self.windows:
                del self.windows[old_window]
                logger.info(f"清理旧窗口：{old_window}分钟")

        logger.info(f"窗口更新完成：{old_window} → {new_window_minutes}分钟")
        return True

    def _validate_window_size(self, window: int) -> bool:
        """验证时间窗口大小是否合法"""
        try:
            from ....config import TAKER_MIN_WINDOW_MINUTES, TAKER_MAX_WINDOW_MINUTES
            return TAKER_MIN_WINDOW_MINUTES <= window <= TAKER_MAX_WINDOW_MINUTES
        except ImportError:
            return 1 <= window <= 1440

    def get_active_aggregator(self) -> OrderAggregator:
        """获取当前活跃的聚合器"""
        if self.active_window not in self.windows:
            # 如果活跃窗口不存在，重新创建
            self.windows[self.active_window] = OrderAggregator(window_minutes=self.active_window)
        return self.windows[self.active_window]

    def get_window_summary(self) -> Dict:
        """获取当前窗口摘要"""
        aggregator = self.get_active_aggregator()
        stats = aggregator.get_stats()
        return {
            "active_window_minutes": self.active_window,
            "trade_count": stats.get("total_trades", 0),
            "window_hits": stats.get("window_calculations", 0),
            "memory_usage_mb": self._estimate_memory_usage(),
            "batch_size": aggregator.batch_size,
            "cleanup_interval": aggregator.cleanup_interval,
            "active_symbols": stats.get("active_symbols", 0)
        }

    def _estimate_memory_usage(self) -> float:
        """估算当前内存使用 (MB)"""
        # 简化估算: 每1000个交易约占用1MB
        total_trades = 0
        for window in self.windows.values():
            total_trades += sum(len(w) for w in window.trade_windows.values())
        return total_trades / 1000

    def get_all_windows_info(self) -> Dict:
        """获取所有窗口信息"""
        return {
            "windows": {
                minutes: {
                    "active": minutes == self.active_window,
                    "summary": window.get_all_symbols_summary()
                }
                for minutes, window in self.windows.items()
            },
            "active_window": self.active_window
        }
