import time
from collections import defaultdict
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional

from src.logger import logger


class SlidingWindowAggregator:
    """
    Aggregates trade data using a sliding time window
    Tracks trade amounts within a specified time period (default: 5 minutes)
    """

    def __init__(self, window_size_seconds: int = 300):
        """
        Initialize the aggregator

        Args:
            window_size_seconds: Size of the sliding window in seconds (default: 300 = 5 minutes)
        """
        self.window_size_ms = window_size_seconds * 1000  # Convert to milliseconds
        self.data = defaultdict(list)  # {symbol: [{amount, side, timestamp, trade_id}, ...]}
        self.lock = Lock()  # Thread-safe lock
        self.stats = {
            'trades_received': 0,
            'trades_pruned': 0,
            'window_calculations': 0,
        }

    def add_trade(self, trade: dict):
        """
        Add a new trade to the aggregator

        Args:
            trade: Trade data dictionary containing:
                - symbol: Trading pair (e.g., 'BTCUSDT')
                - amount: Trade amount in quote currency (e.g., USDT)
                - side: 'BUY' or 'SELL'
                - trade_time: Trade timestamp in milliseconds
                - trade_id: Unique trade identifier
        """
        with self.lock:
            symbol = trade['symbol']
            trade_record = {
                'amount': trade['amount'],
                'side': trade['side'],
                'timestamp': trade['trade_time'],
                'trade_id': trade.get('trade_id', 0)
            }

            # Add trade to the symbol's data
            self.data[symbol].append(trade_record)
            self.stats['trades_received'] += 1

            # Prune old trades immediately to keep memory usage low
            self._prune_old_trades(symbol, trade['trade_time'])

    def _prune_old_trades(self, symbol: str, current_time_ms: int):
        """
        Remove trades outside the sliding window

        Args:
            symbol: Trading pair to prune
            current_time_ms: Current timestamp in milliseconds
        """
        cutoff_time = current_time_ms - self.window_size_ms
        trades = self.data[symbol]

        # Count trades before pruning
        old_count = len(trades)

        # Keep only trades within the window
        self.data[symbol] = [t for t in trades if t['timestamp'] > cutoff_time]

        # Update stats
        pruned = old_count - len(self.data[symbol])
        if pruned > 0:
            self.stats['trades_pruned'] += pruned

    def get_5min_total(self, symbol: str, side: str, current_time_ms: int) -> float:
        """
        Get total amount for a symbol and side within the time window

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            current_time_ms: Current timestamp in milliseconds

        Returns:
            Total amount of trades in the window
        """
        with self.lock:
            self.stats['window_calculations'] += 1

            if symbol not in self.data:
                return 0.0

            # Prune old trades before calculation
            self._prune_old_trades(symbol, current_time_ms)

            trades = self.data[symbol]
            cutoff_time = current_time_ms - self.window_size_ms

            # Sum all trades of the specified side within the window
            total = sum(
                trade['amount']
                for trade in trades
                if trade['side'] == side and trade['timestamp'] > cutoff_time
            )

            return total

    def get_latest_trade_age(self, symbol: str) -> int:
        """
        Get age of the latest trade for a symbol in seconds

        Args:
            symbol: Trading pair

        Returns:
            Age in seconds, or -1 if no trades
        """
        with self.lock:
            if symbol not in self.data or not self.data[symbol]:
                return -1

            latest_time = max(trade['timestamp'] for trade in self.data[symbol])
            current_time_ms = int(time.time() * 1000)
            age_ms = current_time_ms - latest_time

            return age_ms / 1000  # Convert to seconds

    def get_symbol_stats(self, symbol: str) -> dict:
        """
        Get statistics for a specific symbol

        Args:
            symbol: Trading pair

        Returns:
            Dictionary with symbol statistics
        """
        with self.lock:
            if symbol not in self.data:
                return {
                    'symbol': symbol,
                    'total_trades': 0,
                    'buy_amount': 0.0,
                    'sell_amount': 0.0,
                    'oldest_trade_age': -1,
                    'newest_trade_age': -1
                }

            trades = self.data[symbol]
            current_time_ms = int(time.time() * 1000)
            cutoff_time = current_time_ms - self.window_size_ms

            # Calculate totals within window
            buy_amount = sum(
                trade['amount']
                for trade in trades
                if trade['side'] == 'BUY' and trade['timestamp'] > cutoff_time
            )

            sell_amount = sum(
                trade['amount']
                for trade in trades
                if trade['side'] == 'SELL' and trade['timestamp'] > cutoff_time
            )

            if trades:
                oldest_trade = min(trades, key=lambda t: t['timestamp'])
                newest_trade = max(trades, key=lambda t: t['timestamp'])
                oldest_age = (current_time_ms - oldest_trade['timestamp']) / 1000
                newest_age = (current_time_ms - newest_trade['timestamp']) / 1000
            else:
                oldest_age = -1
                newest_age = -1

            return {
                'symbol': symbol,
                'total_trades': len(trades),
                'buy_amount': buy_amount,
                'sell_amount': sell_amount,
                'oldest_trade_age': oldest_age,
                'newest_trade_age': newest_age
            }

    def get_all_symbols(self) -> List[str]:
        """
        Get list of all symbols currently being tracked

        Returns:
            List of trading pairs
        """
        with self.lock:
            return list(self.data.keys())

    def get_global_stats(self) -> dict:
        """
        Get global statistics across all symbols

        Returns:
            Dictionary with global statistics
        """
        with self.lock:
            return {
                'total_symbols': len(self.data),
                'total_trades': self.stats['trades_received'],
                'trades_pruned': self.stats['trades_pruned'],
                'window_calculations': self.stats['window_calculations']
            }

    def clear_symbol(self, symbol: str):
        """
        Clear all data for a specific symbol

        Args:
            symbol: Trading pair to clear
        """
        with self.lock:
            if symbol in self.data:
                del self.data[symbol]
                logger.info(f"Cleared data for symbol: {symbol}")

    def clear_all(self):
        """Clear all aggregated data"""
        with self.lock:
            self.data.clear()
            logger.info("Cleared all aggregated data")

    def cleanup_expired(self, max_age_seconds: int = 3600):
        """
        Clean up symbols that have no recent activity

        Args:
            max_age_seconds: Maximum age in seconds before considered expired
        """
        with self.lock:
            current_time_ms = int(time.time() * 1000)
            expired_symbols = []

            for symbol in self.data:
                latest_age = self.get_latest_trade_age(symbol)
                if latest_age > max_age_seconds:
                    expired_symbols.append(symbol)

            for symbol in expired_symbols:
                self.clear_symbol(symbol)
                logger.info(f"Cleaned up expired symbol: {symbol}")

            return len(expired_symbols)
