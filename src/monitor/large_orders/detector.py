import time
from datetime import datetime
from typing import Callable, Dict, Optional, Tuple

from src.logger import logger


class LargeOrderDetector:
    """
    Detects when trade amounts exceed the threshold within the time window
    Implements cooldown mechanism to prevent spam
    """

    def __init__(
        self,
        threshold_usdt: float = 2_000_000,
        cooldown_minutes: int = 10
    ):
        """
        Initialize the detector

        Args:
            threshold_usdt: Threshold amount in USDT to trigger alert
            cooldown_minutes: Cooldown period in minutes between alerts for the same symbol and side
        """
        self.threshold_usdt = threshold_usdt
        self.cooldown_ms = cooldown_minutes * 60 * 1000  # Convert to milliseconds

        # Track last alert times to implement cooldown
        # {symbol-side: timestamp_ms}
        self.alert_history = {}

        # Statistics
        self.stats = {
            'alerts_triggered': 0,
            'alerts_suppressed': 0,  # Suppressed due to cooldown
            'checks_performed': 0,
        }

        # Alert callback
        self.alert_callback = None

    def set_alert_callback(self, callback: Callable):
        """
        Set callback function for when an alert is triggered

        Args:
            callback: Function to call when alert is triggered
                      Should accept (symbol, side, total_amount, time_window) as arguments
        """
        self.alert_callback = callback

    def check_threshold(
        self,
        symbol: str,
        side: str,
        total_amount: float,
        current_time_ms: int
    ) -> bool:
        """
        Check if the total amount exceeds the threshold

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            total_amount: Total amount in USDT
            current_time_ms: Current timestamp in milliseconds

        Returns:
            True if threshold is exceeded and cooldown has passed
        """
        self.stats['checks_performed'] += 1

        # Check if threshold is exceeded
        if total_amount <= self.threshold_usdt:
            return False

        # Check cooldown
        if self._is_in_cooldown(symbol, side, current_time_ms):
            self.stats['alerts_suppressed'] += 1
            logger.debug(
                f"Alert suppressed for {symbol}-{side} due to cooldown. "
                f"Total: ${total_amount:,.0f}, Threshold: ${self.threshold_usdt:,.0f}"
            )
            return False

        # Threshold exceeded and cooldown passed - trigger alert
        self.stats['alerts_triggered'] += 1
        self._update_alert_history(symbol, side, current_time_ms)

        logger.info(
            f"Large order alert triggered for {symbol}-{side}: "
            f"${total_amount:,.0f} (Threshold: ${self.threshold_usdt:,.0f})"
        )

        # Call alert callback if set
        if self.alert_callback:
            try:
                self.alert_callback(symbol, side, total_amount, current_time_ms)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

        return True

    def _is_in_cooldown(self, symbol: str, side: str, current_time_ms: int) -> bool:
        """
        Check if the symbol-side combination is in cooldown period

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            current_time_ms: Current timestamp in milliseconds

        Returns:
            True if in cooldown period
        """
        key = f"{symbol}-{side}"
        last_alert = self.alert_history.get(key, 0)

        if current_time_ms - last_alert < self.cooldown_ms:
            return True

        return False

    def _update_alert_history(self, symbol: str, side: str, current_time_ms: int):
        """
        Update the alert history with current timestamp

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            current_time_ms: Current timestamp in milliseconds
        """
        key = f"{symbol}-{side}"
        self.alert_history[key] = current_time_ms

    def format_alert_message(
        self,
        symbol: str,
        side: str,
        total_amount: float,
        timestamp_ms: int,
        time_window_minutes: int = 5
    ) -> str:
        """
        Format alert message according to specification

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            total_amount: Total amount in USDT
            timestamp_ms: Timestamp in milliseconds
            time_window_minutes: Time window in minutes

        Returns:
            Formatted alert message
        """
        # Convert symbol format from BTCUSDT to BTC/USDT
        symbol_formatted = f"{symbol[:-4]}/{symbol[-4:]}"

        # Convert side to Chinese
        side_chinese = "买入" if side == "BUY" else "卖出"

        # Format timestamp
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        time_str = dt.strftime("%H:%M:%S")

        # Format amount with thousands separator
        amount_str = f"${total_amount:,.0f}"

        # Format message according to specification
        message = (
            f"[大额主动{side_chinese}] {symbol_formatted} "
            f"金额：{amount_str} "
            f"方向：{side_chinese} "
            f"时间：{time_str}"
        )

        return message

    def should_alert(self, symbol: str, side: str, current_time_ms: int) -> bool:
        """
        Check if an alert should be sent (without triggering it)

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            current_time_ms: Current timestamp in milliseconds

        Returns:
            True if alert should be sent
        """
        # Check cooldown
        if self._is_in_cooldown(symbol, side, current_time_ms):
            return False

        return True

    def get_cooldown_remaining(self, symbol: str, side: str, current_time_ms: int) -> int:
        """
        Get remaining cooldown time in seconds

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            current_time_ms: Current timestamp in milliseconds

        Returns:
            Remaining cooldown time in seconds, 0 if not in cooldown
        """
        key = f"{symbol}-{side}"
        last_alert = self.alert_history.get(key, 0)

        elapsed = current_time_ms - last_alert
        remaining_ms = self.cooldown_ms - elapsed

        if remaining_ms > 0:
            return int(remaining_ms / 1000)

        return 0

    def get_alert_history(self) -> Dict[str, int]:
        """
        Get the alert history

        Returns:
            Dictionary mapping symbol-side to last alert timestamp
        """
        return self.alert_history.copy()

    def clear_alert_history(self, symbol: Optional[str] = None):
        """
        Clear alert history

        Args:
            symbol: Specific symbol to clear, or None to clear all
        """
        if symbol is None:
            self.alert_history.clear()
            logger.info("Cleared all alert history")
        else:
            # Clear entries for this symbol (both BUY and SELL)
            keys_to_remove = [key for key in self.alert_history.keys() if key.startswith(symbol)]
            for key in keys_to_remove:
                del self.alert_history[key]
            logger.info(f"Cleared alert history for symbol: {symbol}")

    def get_stats(self) -> dict:
        """
        Get detector statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'threshold_usdt': self.threshold_usdt,
            'cooldown_minutes': self.cooldown_ms / (60 * 1000),
            'alerts_triggered': self.stats['alerts_triggered'],
            'alerts_suppressed': self.stats['alerts_suppressed'],
            'checks_performed': self.stats['checks_performed'],
            'suppression_rate': (
                self.stats['alerts_suppressed'] / max(1, self.stats['alerts_triggered'] + self.stats['alerts_suppressed'])
            ) * 100
        }

    def update_threshold(self, new_threshold: float):
        """
        Update the threshold amount

        Args:
            new_threshold: New threshold in USDT
        """
        old_threshold = self.threshold_usdt
        self.threshold_usdt = new_threshold
        logger.info(f"Updated threshold from ${old_threshold:,.0f} to ${new_threshold:,.0f}")

    def update_cooldown(self, new_cooldown_minutes: int):
        """
        Update the cooldown period

        Args:
            new_cooldown_minutes: New cooldown in minutes
        """
        old_cooldown = self.cooldown_ms / (60 * 1000)
        self.cooldown_ms = new_cooldown_minutes * 60 * 1000
        logger.info(f"Updated cooldown from {old_cooldown} to {new_cooldown_minutes} minutes")
