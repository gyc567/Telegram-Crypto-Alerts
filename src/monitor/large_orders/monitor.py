import threading
import time
from typing import List, Optional

from src.logger import logger
from .aggregator import SlidingWindowAggregator
from .collector import BinanceOrderBookCollector
from .detector import LargeOrderDetector
from .notifier import TelegramNotifier
from .storage import FileStorage


class LargeOrderMonitor:
    """
    Main controller for large order monitoring
    Orchestrates data collection, aggregation, detection, and notification
    """

    def __init__(
        self,
        telegram_bot,
        symbols: List[str] = None,
        threshold_usdt: float = 2_000_000,
        time_window_minutes: int = 5,
        cooldown_minutes: int = 10,
        storage_path: str = "data/large_orders"
    ):
        """
        Initialize the monitor

        Args:
            telegram_bot: TelegramBot instance
            symbols: List of trading pairs to monitor
            threshold_usdt: Threshold amount in USDT
            time_window_minutes: Time window in minutes
            cooldown_minutes: Cooldown period in minutes
            storage_path: Path for data storage
        """
        self.telegram_bot = telegram_bot

        # Default symbols to monitor
        if symbols is None:
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        self.symbols = symbols

        # Initialize components
        self.aggregator = SlidingWindowAggregator(
            window_size_seconds=time_window_minutes * 60
        )

        self.detector = LargeOrderDetector(
            threshold_usdt=threshold_usdt,
            cooldown_minutes=cooldown_minutes
        )

        self.storage = FileStorage(storage_path)

        self.notifier = TelegramNotifier(telegram_bot)

        # Collector will be initialized when start() is called
        self.collector = None

        # Control flags
        self.is_running = False
        self.main_thread = None

        # Statistics
        self.start_time = 0
        self.stats = {
            'uptime_seconds': 0,
            'total_trades_processed': 0,
            'alerts_triggered': 0,
            'last_alert_time': 0,
        }

        # Set up the alert callback
        self.detector.set_alert_callback(self._on_alert_triggered)

    def _on_alert_triggered(self, symbol: str, side: str, total_amount: float, timestamp_ms: int):
        """
        Callback when an alert is triggered

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            total_amount: Total amount in USDT
            timestamp_ms: Timestamp in milliseconds
        """
        try:
            # Format alert message
            message = self.detector.format_alert_message(
                symbol, side, total_amount, timestamp_ms, 5
            )

            # Save to storage
            self.storage.save_alert(symbol, side, total_amount, timestamp_ms, message)

            # Send notification
            self.notifier.send_alert(message, [], symbol, side, total_amount)

            # Update stats
            self.stats['alerts_triggered'] += 1
            self.stats['last_alert_time'] = timestamp_ms

        except Exception as e:
            logger.error(f"Error processing alert: {e}")

    def _on_trade_received(self, trade: dict):
        """
        Callback when a new trade is received from the collector

        Args:
            trade: Trade data dictionary
        """
        try:
            # Add trade to aggregator
            self.aggregator.add_trade(trade)

            # Save to storage
            self.storage.save_trade(trade)

            # Update stats
            self.stats['total_trades_processed'] += 1

        except Exception as e:
            logger.error(f"Error processing trade: {e}")

    def start(self):
        """
        Start the large order monitor
        """
        if self.is_running:
            logger.warning("Monitor is already running")
            return

        logger.info("Starting large order monitor...")
        logger.info(f"Monitoring symbols: {', '.join(self.symbols)}")
        logger.info(f"Threshold: ${self.detector.threshold_usdt:,.0f} USDT")
        logger.info(f"Time window: {self.aggregator.window_size_ms / 1000 / 60:.0f} minutes")
        logger.info(f"Cooldown: {self.detector.cooldown_ms / 1000 / 60:.0f} minutes")

        try:
            # Initialize and start the collector
            self.collector = BinanceOrderBookCollector(
                symbols=self.symbols,
                on_trade_callback=self._on_trade_received
            )
            self.collector.start()

            # Set running flag
            self.is_running = True
            self.start_time = time.time()

            # Start main monitoring loop in a separate thread
            self.main_thread = threading.Thread(target=self._run, daemon=True)
            self.main_thread.start()

            logger.info("Large order monitor started successfully")

        except Exception as e:
            logger.error(f"Error starting monitor: {e}")
            self.stop()

    def _run(self):
        """
        Main monitoring loop
        Runs in a separate thread
        """
        logger.info("Monitor main loop started")

        last_cleanup = time.time()
        last_stats_log = time.time()

        while self.is_running:
            try:
                current_time_ms = int(time.time() * 1000)

                # Check each symbol for threshold violations
                for symbol in self.symbols:
                    # Check BUY direction
                    buy_total = self.aggregator.get_5min_total(symbol, 'BUY', current_time_ms)
                    if buy_total > 0:
                        self.detector.check_threshold(symbol, 'BUY', buy_total, current_time_ms)

                    # Check SELL direction
                    sell_total = self.aggregator.get_5min_total(symbol, 'SELL', current_time_ms)
                    if sell_total > 0:
                        self.detector.check_threshold(symbol, 'SELL', sell_total, current_time_ms)

                # Periodic cleanup (every 5 minutes)
                if time.time() - last_cleanup > 300:
                    self.aggregator.cleanup_expired(max_age_seconds=3600)  # 1 hour
                    self.storage.cleanup_old_data(days_to_keep=7)
                    last_cleanup = time.time()

                # Log statistics (every 10 minutes)
                if time.time() - last_stats_log > 600:
                    self._log_stats()
                    last_stats_log = time.time()

                # Sleep for 100ms before next check
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(1)

        logger.info("Monitor main loop stopped")

    def stop(self):
        """
        Stop the large order monitor
        """
        logger.info("Stopping large order monitor...")

        self.is_running = False

        # Stop the collector
        if self.collector:
            self.collector.stop()
            self.collector = None

        # Wait for main thread to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=5)

        # Log final statistics
        self._log_stats()

        logger.info("Large order monitor stopped")

    def _log_stats(self):
        """
        Log current statistics
        """
        current_time = time.time()
        uptime = current_time - self.start_time

        collector_stats = self.collector.get_stats() if self.collector else {}
        detector_stats = self.detector.get_stats()
        aggregator_stats = self.aggregator.get_global_stats()
        notifier_stats = self.notifier.get_stats()
        storage_stats = self.storage.get_storage_stats()

        logger.info(
            "=" * 60 + "\n"
            "Large Order Monitor Statistics\n"
            f"Uptime: {uptime / 60:.1f} minutes\n"
            f"Total trades processed: {self.stats['total_trades_processed']}\n"
            f"Alerts triggered: {self.stats['alerts_triggered']}\n"
            f"Collector trades/sec: {collector_stats.get('trades_processed', 0) / max(1, uptime):.2f}\n"
            f"Storage size: {storage_stats.get('total_size_mb', 0):.2f} MB\n"
            f"Active symbols: {len(self.symbols)}\n"
            + "=" * 60
        )

    def get_stats(self) -> dict:
        """
        Get comprehensive monitor statistics

        Returns:
            Dictionary with all statistics
        """
        current_time = time.time()
        uptime = current_time - self.start_time if self.start_time > 0 else 0

        collector_stats = self.collector.get_stats() if self.collector else {}
        detector_stats = self.detector.get_stats()
        aggregator_stats = self.aggregator.get_global_stats()
        notifier_stats = self.notifier.get_stats()
        storage_stats = self.storage.get_storage_stats()

        return {
            'is_running': self.is_running,
            'uptime_seconds': uptime,
            'monitored_symbols': self.symbols,
            'collector': collector_stats,
            'aggregator': aggregator_stats,
            'detector': detector_stats,
            'notifier': notifier_stats,
            'storage': storage_stats,
            'monitor': {
                'total_trades_processed': self.stats['total_trades_processed'],
                'alerts_triggered': self.stats['alerts_triggered'],
                'last_alert_time': self.stats['last_alert_time'],
            }
        }

    def is_healthy(self) -> bool:
        """
        Check if the monitor is healthy

        Returns:
            True if running and collector is connected
        """
        if not self.is_running:
            return False

        if self.collector and not self.collector.is_connected():
            return False

        return True

    def add_symbol(self, symbol: str):
        """
        Add a new symbol to monitor

        Args:
            symbol: Trading pair to add
        """
        symbol = symbol.upper()
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            logger.info(f"Added symbol to monitor: {symbol}")
        else:
            logger.warning(f"Symbol already being monitored: {symbol}")

    def remove_symbol(self, symbol: str):
        """
        Remove a symbol from monitoring

        Args:
            symbol: Trading pair to remove
        """
        symbol = symbol.upper()
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            self.aggregator.clear_symbol(symbol)
            logger.info(f"Removed symbol from monitor: {symbol}")
        else:
            logger.warning(f"Symbol not being monitored: {symbol}")

    def update_threshold(self, new_threshold: float):
        """
        Update the alert threshold

        Args:
            new_threshold: New threshold in USDT
        """
        old_threshold = self.detector.threshold_usdt
        self.detector.update_threshold(new_threshold)
        logger.info(f"Updated threshold from ${old_threshold:,.0f} to ${new_threshold:,.0f}")

    def update_cooldown(self, new_cooldown_minutes: int):
        """
        Update the cooldown period

        Args:
            new_cooldown_minutes: New cooldown in minutes
        """
        old_cooldown = self.detector.cooldown_ms / (60 * 1000)
        self.detector.update_cooldown(new_cooldown_minutes)
        logger.info(f"Updated cooldown from {old_cooldown} to {new_cooldown_minutes} minutes")

    def clear_alert_history(self, symbol: Optional[str] = None):
        """
        Clear alert history

        Args:
            symbol: Specific symbol to clear, or None to clear all
        """
        self.detector.clear_alert_history(symbol)
        logger.info(f"Cleared alert history for {symbol if symbol else 'all symbols'}")
