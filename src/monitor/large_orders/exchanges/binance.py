"""
币安WebSocket客户端实现
实时获取交易数据并转换为标准化格式
"""
import asyncio
import json
import logging
from typing import List, Callable, Optional
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, InvalidURI, InvalidStatus

from ..src.base import BaseExchangeCollector, ConnectionState, TradeEvent
from ..src.error_recovery import ErrorRecoveryManager, ErrorSeverity
from ..src.price_converter import PriceConverter

logger = logging.getLogger(__name__)


class BinanceWebSocketClient(BaseExchangeCollector):
    """
    币安WebSocket客户端
    
    负责：
    1. 建立WebSocket连接
    2. 订阅交易流
    3. 解析交易数据
    4. 转换并发送TradeEvent
    5. 错误处理和重连
    """
    
    def __init__(
        self,
        symbols: List[str],
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        super().__init__("binance", symbols)
        
        # WebSocket配置
        self.websocket_url = "wss://stream.binance.com:9443/ws"
        self.websocket = None
        self.connected = False
        self.subscribed = False
        
        # 错误恢复
        self.recovery = ErrorRecoveryManager(
            exchange_name="binance",
            max_reconnect_attempts=10,
            base_backoff=2.0,
            max_backoff=300.0,
            critical_error_threshold=3
        )
        
        # USD转换器
        self.price_converter = PriceConverter()
        
        # 订阅的任务
        self._tasks: List[asyncio.Task] = []
        
        # 统计数据
        self.stats = {
            "trades_received": 0,
            "trades_per_second": 0.0,
            "last_trade_time": None,
            "connection_uptime": 0.0
        }
        
        logger.info(f"初始化币安WebSocket客户端，监控 {len(symbols)} 个交易对")
    
    async def start(self) -> None:
        """启动WebSocket连接"""
        try:
            self._update_state(ConnectionState.CONNECTING)
            self.recovery.update_state("connecting")
            
            # 建立WebSocket连接
            await self._connect_websocket()
            
            # 订阅交易流
            await self._subscribe_trades()
            
            # 启动消息处理任务
            self._tasks = [
                asyncio.create_task(self._message_handler()),
                asyncio.create_task(self._ping_handler())
            ]
            
            # 设置错误恢复回调
            self.recovery.set_admin_alert_callback(self._send_admin_alert)
            self.recovery.set_state_change_callback(self._on_state_change)
            self.recovery.set_recovery_callback(self._on_connection_recovered)
            
            self.connected = True
            self._update_state(ConnectionState.CONNECTED)
            self.recovery.update_state("connected")
            
            logger.info(f"币安WebSocket连接成功，订阅 {len(self.symbols)} 个交易对")
            
        except Exception as e:
            logger.error(f"启动WebSocket失败: {e}", exc_info=True)
            self._update_state(ConnectionState.FAILED)
            self.recovery.update_state("failed")
            self.recovery.record_error("startup_error", str(e), ErrorSeverity.CRITICAL)
            raise
    
    async def stop(self) -> None:
        """停止WebSocket连接"""
        logger.info("停止币安WebSocket客户端...")
        
        self.connected = False
        self._update_state(ConnectionState.CLOSED)
        self.recovery.update_state("closed")
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 关闭WebSocket连接
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # 关闭USD转换器
        if self.price_converter:
            await self.price_converter.__aexit__(None, None, None)
        
        logger.info("币安WebSocket客户端已停止")
    
    async def reconnect(self) -> None:
        """重新连接WebSocket"""
        logger.info("开始重新连接币安WebSocket...")
        
        # 记录重连尝试
        attempt_num = self.recovery.start_reconnect_attempt()
        
        try:
            # 关闭旧连接
            if self.websocket:
                await self.websocket.close()
            
            # 等待退避时间
            backoff = min(
                2.0 * (2 ** (attempt_num - 1)),
                300.0
            )
            await asyncio.sleep(backoff)
            
            # 重新连接
            await self.start()
            
            # 重连成功
            self.recovery.complete_reconnect_attempt(attempt_num, True)
            logger.info("币安WebSocket重连成功")
            
        except Exception as e:
            # 重连失败
            self.recovery.complete_reconnect_attempt(attempt_num, False, e)
            logger.error(f"币安WebSocket重连失败: {e}")
            
            if self.recovery.should_continue_reconnecting():
                # 继续重连
                await self.reconnect()
            else:
                # 达到最大重连次数
                self._update_state(ConnectionState.FAILED)
                self.recovery.update_state("failed")
                logger.critical("达到最大重连次数，停止重连")
    
    async def _connect_websocket(self) -> None:
        """建立WebSocket连接"""
        try:
            self.websocket = await websockets.connect(
                self.websocket_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            )
            logger.debug("WebSocket连接已建立")
        except InvalidURI:
            raise ValueError(f"无效的WebSocket URI: {self.websocket_url}")
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            raise
    
    async def _subscribe_trades(self) -> None:
        """订阅交易流"""
        try:
            # 构建订阅消息
            streams = [f"{symbol.lower()}@trade" for symbol in self.symbols]
            
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": int(datetime.now().timestamp())
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            self.subscribed = True
            
            logger.debug(f"已订阅 {len(streams)} 个交易流")
            
        except Exception as e:
            logger.error(f"订阅交易流失败: {e}")
            raise
    
    async def _message_handler(self) -> None:
        """处理WebSocket消息"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析错误: {e}")
                except Exception as e:
                    logger.error(f"处理消息错误: {e}", exc_info=True)
                    
        except ConnectionClosed:
            logger.warning("WebSocket连接已关闭")
            if self.connected:
                await self.reconnect()
        except Exception as e:
            logger.error(f"消息处理错误: {e}", exc_info=True)
            if self.connected:
                await self.reconnect()
    
    async def _process_message(self, data: dict) -> None:
        """处理接收到的消息"""
        try:
            # 交易事件
            if data.get("e") == "trade":
                trade = self._parse_trade(data)
                if trade:
                    self._emit_trade(trade)
                    self._update_stats(trade)
            
            # 订阅响应
            elif data.get("result") is None and data.get("id"):
                logger.debug("订阅成功")
            
        except Exception as e:
            logger.error(f"处理消息错误: {e}", exc_info=True)
    
    def _parse_trade(self, data: dict) -> Optional[TradeEvent]:
        """解析交易数据"""
        try:
            symbol = data.get("s", "")
            price = float(data.get("p", 0))
            quantity = float(data.get("q", 0))
            trade_id = str(data.get("t", ""))
            trade_time = data.get("T", 0)
            is_buyer_maker = data.get("m", False)  # True = sell, False = buy
            
            # 判断主动单
            is_taker = True  # 市场单都是taker
            
            # 计算交易额
            amount = price * quantity
            
            # 创建TradeEvent
            trade_event = TradeEvent(
                exchange="binance",
                symbol=symbol,
                side="SELL" if is_buyer_maker else "BUY",
                order_type="MARKET",
                price=price,
                quantity=quantity,
                amount=amount,
                trade_time=trade_time,
                is_taker=is_taker,
                trade_id=trade_id,
                raw_data=data
            )
            
            return trade_event
            
        except Exception as e:
            logger.error(f"解析交易数据失败: {e}")
            return None
    
    async def _ping_handler(self) -> None:
        """定期发送ping"""
        try:
            while self.connected:
                await asyncio.sleep(20)  # 每20秒ping一次
                if self.websocket and self.connected:
                    await self.websocket.ping()
        except Exception as e:
            logger.error(f"Ping错误: {e}")
    
    def _update_stats(self, trade: TradeEvent) -> None:
        """更新统计信息"""
        self.stats["trades_received"] += 1
        self.stats["last_trade_time"] = trade.trade_time
        self.stats["connection_uptime"] = datetime.now().timestamp() - trade.trade_time / 1000
    
    def _send_admin_alert(self, message: str) -> None:
        """发送管理员告警"""
        logger.critical(f"管理员告警: {message}")
        # TODO: 集成Telegram发送
    
    def _on_state_change(self, state: str) -> None:
        """状态变更回调"""
        logger.info(f"状态变更: {state}")
    
    def _on_connection_recovered(self) -> None:
        """连接恢复回调"""
        logger.info("连接已恢复")
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的交易对"""
        return [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
            "SOLUSDT", "DOTUSDT", "DOGEUSDT", "MATICUSDT", "LTCUSDT",
            "AVAXUSDT", "UNIUSDT", "ATOMUSDT", "LINKUSDT", "ETCUSDT",
            "BCHUSDT", "FILUSDT", "TRXUSDT", "XLMUSDT", "VETUSDT",
            "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "SUIUSDT"
        ]
    
    def validate_symbol(self, symbol: str) -> bool:
        """验证交易对"""
        return symbol in self.get_supported_symbols()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **super().get_stats(),
            **self.stats,
            "reconnection_stats": self.recovery.get_status_report()
        }


# 工厂函数
def create_binance_client(symbols: List[str]) -> BinanceWebSocketClient:
    """创建币安WebSocket客户端"""
    return BinanceWebSocketClient(symbols)
