import time
from typing import List

from src.logger import logger
from ..models import CEXAlert


class TelegramNotifier:
    """
    Sends large order alerts via Telegram
    Integrates with the existing Telegram bot system
    """

    def __init__(self, telegram_bot):
        """
        Initialize the notifier

        Args:
            telegram_bot: TelegramBot instance
        """
        self.telegram_bot = telegram_bot
        self.stats = {
            'alerts_sent': 0,
            'alerts_failed': 0,
        }

    def send_alert(
        self,
        message: str,
        channel_ids: List[str],
        symbol: str,
        side: str,
        amount: float
    ):
        """
        Send a large order alert

        Args:
            message: Formatted alert message
            channel_ids: List of Telegram channel/user IDs
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            amount: Total amount
        """
        try:
            # Get whitelisted users
            from ..user_configuration import get_whitelist

            whitelisted_users = get_whitelist()

            if not whitelisted_users:
                logger.warning("No whitelisted users found, cannot send alert")
                return

            # Send to all whitelisted users
            success_count = 0
            fail_count = 0

            for user_id in whitelisted_users:
                try:
                    # Send the alert message
                    self.telegram_bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown" if message.startswith('[') else None
                    )
                    success_count += 1
                    logger.debug(f"Alert sent to user {user_id}")

                    # Add a small delay to avoid rate limiting
                    time.sleep(0.05)

                except Exception as e:
                    fail_count += 1
                    logger.error(f"Failed to send alert to user {user_id}: {e}")

            # Update stats
            if success_count > 0:
                self.stats['alerts_sent'] += 1
            if fail_count > 0:
                self.stats['alerts_failed'] += fail_count

            logger.info(
                f"Large order alert sent: {symbol}-{side} ${amount:,.0f}. "
                f"Success: {success_count}, Failed: {fail_count}"
            )

        except Exception as e:
            self.stats['alerts_failed'] += 1
            logger.error(f"Error sending alert: {e}")

    def get_stats(self) -> dict:
        """
        Get notifier statistics

        Returns:
            Dictionary with statistics
        """
        return self.stats.copy()

    def send_test_alert(self, user_id: str):
        """
        Send a test alert to verify the system

        Args:
            user_id: Telegram user ID
        """
        test_message = (
            "[测试] 大额交易监控系统运行正常\n"
            "时间: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n"
            "如果你看到这条消息，说明系统配置正确。"
        )

        try:
            self.telegram_bot.send_message(chat_id=user_id, text=test_message)
            logger.info(f"Test alert sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send test alert: {e}")
