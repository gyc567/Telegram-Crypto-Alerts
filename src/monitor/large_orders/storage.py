import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.logger import logger


class FileStorage:
    """
    File-based storage for large order data
    Organizes data by date and symbol for easy access and management
    """

    def __init__(self, base_path: str = "data/large_orders"):
        """
        Initialize the storage

        Args:
            base_path: Base directory for storing data
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.max_files_per_day = 1000  # Maximum number of files per day

    def _get_date_path(self, timestamp_ms: int) -> Path:
        """
        Get the directory path for a given timestamp

        Args:
            timestamp_ms: Timestamp in milliseconds

        Returns:
            Path object for the date directory
        """
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        date_str = dt.strftime("%Y-%m-%d")
        return self.base_path / date_str

    def _get_symbol_path(self, timestamp_ms: int, symbol: str) -> Path:
        """
        Get the file path for a symbol and date

        Args:
            timestamp_ms: Timestamp in milliseconds
            symbol: Trading pair (e.g., 'BTCUSDT')

        Returns:
            Path object for the symbol file
        """
        date_path = self._get_date_path(timestamp_ms)
        date_path.mkdir(parents=True, exist_ok=True)
        return date_path / f"{symbol}.jsonl"

    def save_trade(self, trade: dict):
        """
        Save a trade to storage

        Args:
            trade: Trade data dictionary
        """
        try:
            symbol = trade['symbol']
            timestamp_ms = trade['trade_time']
            file_path = self._get_symbol_path(timestamp_ms, symbol)

            # Append trade to file (one JSON per line)
            with open(file_path, 'a', encoding='utf-8') as f:
                json.dump(trade, f, ensure_ascii=False)
                f.write('\n')

        except Exception as e:
            logger.error(f"Error saving trade to storage: {e}")

    def save_alert(self, symbol: str, side: str, total_amount: float, timestamp_ms: int, message: str):
        """
        Save an alert to storage

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            total_amount: Total amount in USDT
            timestamp_ms: Alert timestamp in milliseconds
            message: Alert message
        """
        try:
            # Create alerts directory
            alerts_dir = self.base_path / "alerts"
            alerts_dir.mkdir(parents=True, exist_ok=True)

            # Create alert entry
            alert = {
                'timestamp': timestamp_ms,
                'symbol': symbol,
                'side': side,
                'total_amount': total_amount,
                'message': message,
                'datetime': datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
            }

            # Save to file (one JSON per line)
            with open(alerts_dir / "alerts.jsonl", 'a', encoding='utf-8') as f:
                json.dump(alert, f, ensure_ascii=False)
                f.write('\n')

        except Exception as e:
            logger.error(f"Error saving alert to storage: {e}")

    def get_trades(
        self,
        symbol: str,
        start_time_ms: int,
        end_time_ms: int
    ) -> List[dict]:
        """
        Retrieve trades for a symbol within a time range

        Args:
            symbol: Trading pair
            start_time_ms: Start timestamp in milliseconds
            end_time_ms: End timestamp in milliseconds

        Returns:
            List of trade records
        """
        trades = []

        try:
            # Iterate through all days in the range
            start_date = datetime.fromtimestamp(start_time_ms / 1000).date()
            end_date = datetime.fromtimestamp(end_time_ms / 1000).date()

            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                date_path = self.base_path / date_str
                symbol_file = date_path / f"{symbol}.jsonl"

                if symbol_file.exists():
                    with open(symbol_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                trade = json.loads(line.strip())
                                trade_time = trade.get('trade_time', 0)
                                if start_time_ms <= trade_time <= end_time_ms:
                                    trades.append(trade)
                            except json.JSONDecodeError:
                                continue

                current_date = current_date.__class__(current_date.year, current_date.month, current_date.day + 1)

        except Exception as e:
            logger.error(f"Error retrieving trades from storage: {e}")

        return trades

    def get_alerts(
        self,
        start_time_ms: int,
        end_time_ms: int,
        symbol: Optional[str] = None
    ) -> List[dict]:
        """
        Retrieve alerts within a time range

        Args:
            start_time_ms: Start timestamp in milliseconds
            end_time_ms: End timestamp in milliseconds
            symbol: Optional symbol filter

        Returns:
            List of alert records
        """
        alerts = []

        try:
            alerts_file = self.base_path / "alerts" / "alerts.jsonl"

            if not alerts_file.exists():
                return alerts

            with open(alerts_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        alert = json.loads(line.strip())
                        alert_time = alert.get('timestamp', 0)
                        if start_time_ms <= alert_time <= end_time_ms:
                            if symbol is None or alert.get('symbol') == symbol:
                                alerts.append(alert)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Error retrieving alerts from storage: {e}")

        return alerts

    def cleanup_old_data(self, days_to_keep: int = 7):
        """
        Clean up old data files

        Args:
            days_to_keep: Number of days of data to keep
        """
        try:
            cutoff_date = datetime.now().date().__class__(
                datetime.now().year,
                datetime.now().month,
                datetime.now().day - days_to_keep
            )

            for date_dir in self.base_path.iterdir():
                if date_dir.is_dir() and date_dir.name != "alerts":
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").date()
                        if dir_date < cutoff_date:
                            # Remove directory and all contents
                            import shutil
                            shutil.rmtree(date_dir)
                            logger.info(f"Cleaned up old data directory: {date_dir}")
                    except ValueError:
                        # Skip directories that don't match date format
                        continue

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    def get_storage_stats(self) -> dict:
        """
        Get storage statistics

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            'base_path': str(self.base_path),
            'total_directories': 0,
            'total_files': 0,
            'total_size_bytes': 0,
            'oldest_data_date': None,
            'newest_data_date': None,
        }

        try:
            dates = []
            total_size = 0
            file_count = 0

            for item in self.base_path.rglob('*'):
                if item.is_file() and item.suffix == '.jsonl':
                    file_count += 1
                    total_size += item.stat().st_size

                    # Extract date from path
                    try:
                        date_str = item.parent.name
                        date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        dates.append(date)
                    except ValueError:
                        continue

            stats['total_files'] = file_count
            stats['total_size_bytes'] = total_size
            stats['total_size_mb'] = total_size / (1024 * 1024)

            if dates:
                stats['oldest_data_date'] = min(dates).isoformat()
                stats['newest_data_date'] = max(dates).isoformat()

            # Count directories
            stats['total_directories'] = len([d for d in self.base_path.iterdir() if d.is_dir()])

        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")

        return stats

    def export_data(self, start_date: str, end_date: str, output_file: str):
        """
        Export data within a date range to a single file

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            output_file: Output file path
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            start_ms = int(start.timestamp() * 1000)
            end_ms = int(end.timestamp() * 1000)

            # Get all unique symbols
            symbols = set()
            current_date = start.date()
            while current_date <= end:
                date_str = current_date.strftime("%Y-%m-%d")
                date_path = self.base_path / date_str

                if date_path.exists():
                    for file in date_path.glob("*.jsonl"):
                        symbol = file.stem
                        symbols.add(symbol)

                current_date = current_date.__class__(
                    current_date.year, current_date.month, current_date.day + 1
                )

            # Export data for all symbols
            exported_data = []
            for symbol in symbols:
                trades = self.get_trades(symbol, start_ms, end_ms)
                exported_data.extend(trades)

            # Save to output file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(exported_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(exported_data)} records to {output_file}")

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
