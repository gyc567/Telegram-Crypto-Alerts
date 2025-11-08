import json
import threading
import time
from collections import defaultdict
from datetime import datetime
from typing import Callable, Dict, List, Optional

import requests
import websocket
from src.logger import logger


class BinanceOrderBookCollector:
    """
    Collects real-time trade data from Binance WebSocket
    Filters for market orders and active trades (taker trades)
    """

    def __init__(self, symbols: List[str], on_trade_callback: Callable):
        """
        Initialize the collector

        Args:
            symbols: List of trading pairs to monitor (e.g., ['BTCUSDT', 'ETHUSDT'])
            on_trade_callback: Callback function to process each trade
        """
        self.symbols = [s.upper() for s in symbols]
        self.on_trade_callback = on_trade_callback

        self.ws = None
        self.is_running = False
        self.thread = None
        self.reconnect_interval = 5  # seconds
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0

        # Statistics
        self.stats = {
            'trades_processed': 0,
            'connection_errors': 0,
            'last_trade_time': 0,
        }

    def _get_websocket_url(self) -> str:
        """Generate WebSocket URL for multiple streams"""
        streams = '/'.join([f"{symbol.lower()}@trade" for symbol in self.symbols])
        return f"wss://stream.binance.com:9443/stream?streams={streams}"

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)

            if 'stream' in data and 'data' in data['stream']:
                trade_data = data['data']

                # Parse trade information
                trade = self._parse_trade(trade_data)
                if trade:
                    self.on_trade_callback(trade)
                    self.stats['trades_processed'] += 1
                    self.stats['last_trade_time'] = trade['trade_time']

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
        self.stats['connection_errors'] += 1

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close"""
        logger.warning("WebSocket connection closed")
        if self.is_running:
            logger.info("Attempting to reconnect...")
            self._reconnect()

    def _on_open(self, ws):
        """Handle WebSocket connection open"""
        logger.info(f"WebSocket connected to Binance for symbols: {', '.join(self.symbols)}")
        self.reconnect_attempts = 0

    def _parse_trade(self, data: dict) -> Optional[dict]:
        """
        Parse trade data from Binance WebSocket

        Args:
            data: Raw trade data from WebSocket

        Returns:
            Parsed trade data or None if invalid
        """
        try:
            symbol = data.get('s', '')
            price = float(data.get('p', 0))
            quantity = float(data.get('q', 0))
            trade_time = int(data.get('T', 0))
            is_buyer_maker = data.get('m', False)  # True if trade is from buyer (taker)

            # Skip if not a market order (trades don't have order type in @trade stream)
            # We need to filter by checking if it's a taker trade (market orders are typically taker trades)
            # For @trade stream, 'm' = True means buyer is market maker, False means taker (market order)
            # Actually, 'm' = True means trade is from buyer, and taker is the one who takes liquidity
            # For a market order to exist, there must be a taker

            # We want active trades (taker trades)
            # In Binance, 'm' = False means buyer is taker (market order buy)
            # 'm' = True means seller is taker (market order sell)
            side = 'BUY' if not data.get('m', True) else 'SELL'

            # Calculate USDT amount
            # For most pairs, if symbol ends with USDT, we can use price directly
            amount = price * quantity

            return {
                'exchange': 'binance',
                'symbol': symbol,
                'side': side,
                'order_type': 'MARKET',  # @trade stream only contains executed trades
                'price': price,
                'quantity': quantity,
                'amount': amount,  # Amount in quote currency
                'trade_time': trade_time,
                'is_taker': True,  # All trades in @trade stream are executed, so taker is involved
                'trade_id': data.get('t', 0)
            }
        except Exception as e:
            logger.error(f"Error parsing trade data: {e}")
            return None

    def _reconnect(self):
        """Attempt to reconnect with exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached. Stopping collector.")
            return

        self.reconnect_attempts += 1
        wait_time = min(60, self.reconnect_interval * (2 ** (self.reconnect_attempts - 1)))
        logger.info(f"Reconnecting in {wait_time} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        time.sleep(wait_time)

        if self.is_running:
            self.start()

    def start(self):
        """Start the WebSocket collector in a separate thread"""
        if self.is_running:
            logger.warning("Collector is already running")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Binance order book collector started")

    def _run(self):
        """Main WebSocket connection loop"""
        websocket_url = self._get_websocket_url()

        while self.is_running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.ws = websocket.WebSocketApp(
                    websocket_url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    on_open=self._on_open
                )

                # Run with 10 second timeout
                self.ws.run_forever(ping_interval=10, ping_timeout=5)

                if self.is_running:
                    time.sleep(self.reconnect_interval)

            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                if self.is_running:
                    time.sleep(self.reconnect_interval)

    def stop(self):
        """Stop the WebSocket collector"""
        logger.info("Stopping Binance order book collector...")
        self.is_running = False

        if self.ws:
            self.ws.close()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        logger.info("Binance order book collector stopped")

    def get_stats(self) -> dict:
        """Get collector statistics"""
        return self.stats.copy()

    def is_connected(self) -> bool:
        """Check if collector is running and connected"""
        return self.is_running and (self.thread and self.thread.is_alive())
