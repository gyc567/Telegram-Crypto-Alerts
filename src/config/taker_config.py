"""
吃单监控配置管理模块
负责配置加载、验证和管理
"""

from typing import Optional, List
import logging

# 导入配置常量
try:
    from src.config import (
        TAKER_CUMULATIVE_WINDOW_MINUTES,
        TAKER_WINDOW_OPTIONS,
        TAKER_MIN_WINDOW_MINUTES,
        TAKER_MAX_WINDOW_MINUTES,
        TAKER_CLEANUP_INTERVAL_SECONDS,
        TAKER_MAX_RETENTION_MINUTES,
        TAKER_ORDER_CONFIG
    )
except ImportError:
    # 如果直接运行测试，使用相对导入
    from . import (
        TAKER_CUMULATIVE_WINDOW_MINUTES,
        TAKER_WINDOW_OPTIONS,
        TAKER_MIN_WINDOW_MINUTES,
        TAKER_MAX_WINDOW_MINUTES,
        TAKER_CLEANUP_INTERVAL_SECONDS,
        TAKER_MAX_RETENTION_MINUTES,
        TAKER_ORDER_CONFIG
    )

logger = logging.getLogger(__name__)


class TakerConfigManager:
    """吃单监控配置管理器"""

    @staticmethod
    def get_window_minutes() -> int:
        """获取当前时间窗口（分钟）"""
        return TAKER_CUMULATIVE_WINDOW_MINUTES

    @staticmethod
    def set_window_minutes(minutes: int, persist: bool = False) -> bool:
        """设置时间窗口

        Args:
            minutes: 新的时间窗口(分钟)
            persist: 是否持久化到文件

        Returns:
            bool: 设置是否成功
        """
        if not TakerConfigManager.validate_window(minutes):
            logger.error(f"Invalid window size: {minutes}")
            return False

        # 更新配置
        import sys
        import os
        # 动态更新模块级别的变量
        config_module = sys.modules['src.config']
        if hasattr(config_module, 'TAKER_CUMULATIVE_WINDOW_MINUTES'):
            config_module.TAKER_CUMULATIVE_WINDOW_MINUTES = minutes

        # 更新global变量
        globals()['TAKER_CUMULATIVE_WINDOW_MINUTES'] = minutes

        if persist:
            TakerConfigManager._persist_to_file(minutes)

        logger.info(f"Taker window updated to {minutes} minutes")
        return True

    @staticmethod
    def validate_window(window_minutes: int) -> bool:
        """验证时间窗口是否合法

        Args:
            window_minutes: 要验证的窗口大小(分钟)

        Returns:
            bool: 是否合法
        """
        # 类型检查
        if not isinstance(window_minutes, int):
            return False

        # 范围检查
        if not (TAKER_MIN_WINDOW_MINUTES <= window_minutes <= TAKER_MAX_WINDOW_MINUTES):
            return False

        # 业务逻辑检查
        if window_minutes % 5 != 0:  # 要求是5的倍数
            return False

        return True

    @staticmethod
    def get_window_options() -> List[int]:
        """获取所有可选的时间窗口选项"""
        return TAKER_WINDOW_OPTIONS.copy()

    @staticmethod
    def get_config_dict() -> dict:
        """获取完整配置字典"""
        return TAKER_ORDER_CONFIG.copy()

    @staticmethod
    def _persist_to_file(minutes: int):
        """持久化配置到文件"""
        # TODO: 实现配置持久化到配置文件
        # 例如: 更新 .env 或 config.json
        logger.info(f"Persisting window size {minutes} to config file")
        pass
