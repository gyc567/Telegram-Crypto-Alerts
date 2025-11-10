# 大额交易监控功能 - 技术设计文档

## 📋 设计概览

**提案编号**: CHANGE-2025-0104
**版本**: 1.0.0
**创建日期**: 2025-11-10
**设计者**: OpenSpec AI助手

---

## 🎯 设计目标

### 性能目标
- **CPU使用率**: 从20%降低到2% (↓80%)
- **内存使用**: 从200MB降低到100MB (↓50%)
- **响应延迟**: 从10-15秒降低到<1秒 (↓90%+)
- **系统稳定性**: 从95%提升到99.5% (↑4.5%)

### 功能目标
- 实时监控20+主流交易对
- 5分钟滚动窗口聚合
- $2,000,000 USD阈值检测
- 5分钟冷却机制
- 自动错误恢复

---

## 🏗️ 架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                大额交易监控系统 (事件驱动)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    事件流    ┌──────────────┐            │
│  │   WebSocket  │────────────▶│     事件     │            │
│  │   管理器     │              │    总线      │            │
│  │              │              │             │            │
│  └──────────────┘              └──────┬──────┘            │
│                                        │                   │
│  ┌──────────────┐              ┌──────▼──────┐            │
│  │  订单聚合器  │◀─────────────│  聚合请求   │            │
│  │              │              │             │            │
│  └──────────────┘              └──────┬──────┘            │
│                                        │                   │
│  ┌──────────────┐              ┌──────▼──────┐            │
│  │  阈值引擎    │◀─────────────│  阈值检查   │            │
│  │              │              │             │            │
│  └──────────────┘              └──────┬──────┘            │
│                                        │                   │
│  ┌──────────────┐              ┌──────▼──────┐            │
│  │  告警调度器  │◀─────────────│   告警事件  │            │
│  │              │              │             │            │
│  └──────────────┘              └──────┬──────┘            │
│                                        │                   │
│  ┌──────────────┐              ┌──────▼──────┐            │
│  │ USD转换器    │◀─────────────│  转换请求   │            │
│  │              │              │             │            │
│  └──────────────┘              └─────────────┘            │
│                                                              │
│  ┌──────────────┐    监控      ┌──────────────┐            │
│  │  错误恢复    │◀─────────────│  错误事件    │            │
│  │  管理器      │              │             │            │
│  └──────────────┘              └─────────────┘            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2. 事件驱动设计

**设计原则**:
- 异步非阻塞处理
- 松耦合组件
- 事件总线通信
- 可扩展架构

**事件类型**:
1. `TradeEvent` - 交易事件
2. `AggregationRequest` - 聚合请求
3. `ThresholdCheck` - 阈值检查
4. `AlertEvent` - 告警事件
5. `ConvertRequest` - 转换请求
6. `ErrorEvent` - 错误事件

---

## 🔧 核心组件设计

### 1. WebSocket管理器 (BinanceWebSocketClient)

#### 类设计
```python
class BinanceWebSocketClient(BaseExchangeCollector):
    """
    币安WebSocket客户端
    负责实时数据获取和事件分发
    """
    def __init__(self, symbols: List[str]):
        self.websocket_url: str = "wss://stream.binance.com:9443/ws"
        self.symbols: List[str] = symbols
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connection_state: ConnectionState = ConnectionState.DISCONNECTED
        self.recovery: ErrorRecoveryManager = ErrorRecoveryManager()
        self.price_converter: PriceConverter = PriceConverter()
        self.subscriptions: Dict[str, str] = {}  # stream_name -> symbol
        self._tasks: List[asyncio.Task] = []
        self.stats: Dict[str, Any] = {
            "trades_received": 0,
            "trades_per_second": 0.0,
            "last_trade_time": None,
            "connection_uptime": 0.0
        }
```

#### 关键方法

**start()**
```python
async def start(self) -> None:
    """启动WebSocket连接和订阅"""
    1. 更新状态为CONNECTING
    2. 建立WebSocket连接
    3. 订阅所有交易对
    4. 启动消息处理任务
    5. 更新状态为CONNECTED
```

**_message_handler()**
```python
async def _message_handler(self) -> None:
    """异步处理WebSocket消息"""
    while self.connection_state == ConnectionState.CONNECTED:
        try:
            message = await self.websocket.recv()
            data = json.loads(message)
            await self._process_message(data)
        except ConnectionClosed:
            await self.recovery.handle_disconnection()
        except Exception as e:
            logger.error(f"消息处理错误: {e}")
```

**设计要点**:
- 使用`asyncio`实现异步I/O
- 自动重连机制（指数退避）
- 事件回调通知其他组件
- 统计数据实时更新

#### 重连策略
```python
class ErrorRecoveryManager:
    """
    错误恢复管理器
    实现指数退避重连策略
    """
    def __init__(self):
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.base_backoff = 2.0  # 2秒
        self.max_backoff = 300.0  # 5分钟
        self.critical_error_threshold = 3

    async def reconnect(self) -> bool:
        """执行重连"""
        backoff = min(
            self.base_backoff * (2 ** self.reconnect_attempts),
            self.max_backoff
        )
        await asyncio.sleep(backoff)
        self.reconnect_attempts += 1
        return self.reconnect_attempts <= self.max_reconnect_attempts
```

### 2. 订单聚合器 (OrderAggregator)

#### 类设计
```python
class OrderAggregator:
    """
    5分钟滚动窗口聚合器
    负责实时聚合交易数据
    """
    def __init__(self, window_minutes: int = 5):
        self.window_size_ms: int = window_minutes * 60 * 1000
        self.data: Dict[str, List[TradeRecord]] = defaultdict(list)
        self.lock: Lock = Lock()
        self.threshold_usd: float = 2_000_000
        self.stats: Dict[str, Any] = {
            "trades_received": 0,
            "trades_pruned": 0,
            "window_calculations": 0,
            "threshold_breaches": 0
        }
```

#### 数据结构
```python
@dataclass
class TradeRecord:
    """交易记录"""
    symbol: str
    amount: float  # USD价值
    side: str  # BUY/SELL
    timestamp: int  # 毫秒
    trade_id: int
    price: float
    quantity: float
```

#### 关键方法

**add_trade()**
```python
async def add_trade(self, trade_event: TradeEvent, usd_value: float) -> None:
    """添加交易到聚合器"""
    with self.lock:
        # 创建交易记录
        record = TradeRecord(
            symbol=trade_event.symbol,
            amount=usd_value,
            side=trade_event.side,
            timestamp=trade_event.timestamp,
            trade_id=trade_event.trade_id,
            price=trade_event.price,
            quantity=trade_event.quantity
        )

        # 添加到数据存储
        self.data[trade_event.symbol].append(record)

        # 立即清理过期数据
        self._prune_old_trades(trade_event.symbol, trade_event.timestamp)

        # 更新统计
        self.stats["trades_received"] += 1
```

**_prune_old_trades()**
```python
def _prune_old_trades(self, symbol: str, current_time_ms: int) -> None:
    """清理过期交易数据"""
    cutoff_time = current_time_ms - self.window_size_ms
    trades = self.data[symbol]

    # 保留窗口内的交易
    self.data[symbol] = [t for t in trades if t.timestamp > cutoff_time]

    # 统计清理的数量
    pruned = len(trades) - len(self.data[symbol])
    if pruned > 0:
        self.stats["trades_pruned"] += pruned
```

**get_aggregation()**
```python
async def get_aggregation(self, symbol: str, current_time_ms: int) -> Dict[str, Any]:
    """获取聚合结果"""
    with self.lock:
        self.stats["window_calculations"] += 1

        if symbol not in self.data:
            return self._empty_result()

        # 清理过期数据
        self._prune_old_trades(symbol, current_time_ms)

        # 计算聚合
        trades = self.data[symbol]
        buy_volume = sum(t.amount for t in trades if t.side == "BUY")
        sell_volume = sum(t.amount for t in trades if t.side == "SELL")
        total_volume = buy_volume + sell_volume
        trade_count = len(trades)

        # 检查阈值突破
        threshold_breach = total_volume >= self.threshold_usd
        if threshold_breach:
            self.stats["threshold_breaches"] += 1

        return {
            "symbol": symbol,
            "window_minutes": 5,
            "total_volume": total_volume,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "trade_count": trade_count,
            "threshold_breach": threshold_breach,
            "threshold_usd": self.threshold_usd
        }
```

**设计要点**:
- 线程安全（使用Lock）
- 实时数据清理（避免内存泄漏）
- 一次计算多个指标
- 支持动态阈值更新

#### 内存优化策略
1. **实时清理**: 每次添加交易时立即清理过期数据
2. **数据结构优化**: 使用deque代替list（如果需要）
3. **去重机制**: 基于trade_id去重
4. **分桶存储**: 按交易对分桶减少搜索

### 3. 阈值检测引擎 (ThresholdEngine)

#### 类设计
```python
class ThresholdEngine:
    """
    阈值检测引擎
    负责检测聚合数据并触发告警
    """
    def __init__(self, threshold_usd: float = 2_000_000, cooldown_minutes: int = 5):
        self.threshold_usd: float = threshold_usd
        self.cooldown_minutes: int = cooldown_minutes
        self.cooldowns: Dict[str, datetime] = {}
        self.alert_callback: Optional[Callable] = None
        self.stats: Dict[str, Any] = {
            "threshold_checks": 0,
            "alerts_triggered": 0,
            "alerts_suppressed": 0,
            "cooldowns_active": 0
        }
```

#### 关键方法

**check_aggregation()**
```python
async def check_aggregation(self, symbol: str, aggregation_data: Dict) -> Optional[ThresholdEvent]:
    """检查聚合数据是否突破阈值"""
    self.stats["threshold_checks"] += 1

    # 检查阈值
    if not aggregation_data.get("threshold_breach", False):
        return None

    # 获取聚合信息
    total_volume = aggregation_data.get("total_volume", 0.0)
    buy_volume = aggregation_data.get("buy_volume", 0.0)
    sell_volume = aggregation_data.get("sell_volume", 0.0)
    trade_count = aggregation_data.get("trade_count", 0)

    # 决定主要方向
    direction = self._determine_direction(buy_volume, sell_volume)

    # 检查冷却
    if await self._is_in_cooldown(symbol):
        self.stats["alerts_suppressed"] += 1
        return None

    # 创建阈值事件
    event = ThresholdEvent(
        symbol=symbol,
        direction=direction,
        total_volume=total_volume,
        buy_volume=buy_volume,
        sell_volume=sell_volume,
        trade_count=trade_count,
        threshold_usd=self.threshold_usd,
        window_minutes=aggregation_data.get("window_minutes", 5),
        timestamp=datetime.now()
    )

    # 设置冷却
    await self._set_cooldown(symbol)

    # 触发告警
    self.stats["alerts_triggered"] += 1
    if self.alert_callback:
        if asyncio.iscoroutinefunction(self.alert_callback):
            await self.alert_callback(event)
        else:
            self.alert_callback(event)

    return event
```

**_determine_direction()**
```python
def _determine_direction(self, buy_volume: float, sell_volume: float) -> str:
    """智能判断交易方向"""
    diff_ratio = abs(buy_volume - sell_volume) / max(buy_volume + sell_volume, 1)

    # 如果买卖差距小于10%，认为是双向
    if diff_ratio < 0.1:
        return "双向"

    return "买入" if buy_volume > sell_volume else "卖出"
```

**_is_in_cooldown()**
```python
async def _is_in_cooldown(self, symbol: str) -> bool:
    """检查是否在冷却期"""
    if symbol not in self.cooldowns:
        return False

    cooldown_until = self.cooldowns[symbol]
    return datetime.now() < cooldown_until
```

**_set_cooldown()**
```python
async def _set_cooldown(self, symbol: str) -> None:
    """设置冷却时间"""
    self.cooldowns[symbol] = datetime.now() + timedelta(minutes=self.cooldown_minutes)
    self.stats["cooldowns_active"] = len(self.cooldowns)
```

**设计要点**:
- 异步回调支持
- 智能方向判断
- 独立冷却管理
- 统计数据收集

### 4. USD转换器 (PriceConverter)

#### 类设计
```python
class PriceConverter:
    """
    USD转换器
    负责将各种货币转换为USD
    """
    def __init__(self):
        self.supported_stablecoins: Set[str] = {
            "USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USDP"
        }
        self.cache: Dict[str, Tuple[float, datetime]] = {}
        self.cache_ttl: int = 60  # 60秒
        self.lock: Lock = Lock()
        self.stats: Dict[str, Any] = {
            "conversions": 0,
            "cache_hits": 0,
            "api_calls": 0
        }
```

#### 关键方法

**convert_to_usd()**
```python
async def convert_to_usd(self, symbol: str, price: float, quantity: float) -> float:
    """转换交易为USD价值"""
    self.stats["conversions"] += 1

    # 获取报价货币 (如USDT, BTC等)
    quote_currency = self._extract_quote_currency(symbol)

    # 如果已经是USD或稳定币，直接计算
    if quote_currency in self.supported_stablecoins or quote_currency == "USD":
        return price * quantity

    # 获取USD汇率
    usd_rate = await self._get_usd_rate(quote_currency)

    # 计算USD价值
    usd_value = price * quantity * usd_rate

    return usd_value
```

**_extract_quote_currency()**
```python
def _extract_quote_currency(self, symbol: str) -> str:
    """从交易对中提取报价货币"""
    # BTCUSDT -> USDT
    # ETHBTC -> BTC
    if len(symbol) == 6:
        return symbol[-4:]  # 简单的6字符交易对
    else:
        # 处理更复杂的交易对
        for stablecoin in sorted(self.supported_stablecoins, key=len, reverse=True):
            if symbol.endswith(stablecoin):
                return stablecoin
        return symbol[-4:]  # 默认返回后4位
```

**_get_usd_rate()**
```python
async def _get_usd_rate(self, currency: str) -> float:
    """获取货币对USD的汇率"""
    with self.lock:
        # 检查缓存
        if currency in self.cache:
            rate, timestamp = self.cache[currency]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return rate

        # 获取新汇率
        rate = await self._fetch_usd_rate(currency)

        # 更新缓存
        self.cache[currency] = (rate, datetime.now())

        return rate
```

**_fetch_usd_rate()**
```python
async def _fetch_usd_rate(self, currency: str) -> float:
    """从Binance API获取汇率"""
    self.stats["api_calls"] += 1

    # 尝试多种交易对获取汇率
    pairs = [f"{currency}USDT", f"{currency}BUSD", f"USDT{currency}"]

    for pair in pairs:
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data["price"])

                        # 如果是反向交易对 (如USDTBTC)，取倒数
                        if pair.startswith("USDT"):
                            return 1.0 / price if price > 0 else 1.0

                        return price
        except Exception as e:
            logger.debug(f"获取 {pair} 汇率失败: {e}")
            continue

    # 所有尝试都失败，返回默认值
    logger.warning(f"无法获取 {currency} 的USD汇率，使用默认值1.0")
    return 1.0
```

**设计要点**:
- 多层缓存机制
- 支持多种稳定币
- 容错和降级策略
- 性能统计追踪

### 5. 告警调度器 (AlertDispatcher)

#### 类设计
```python
class AlertDispatcher:
    """
    告警调度器
    负责格式化、队列管理和发送告警
    """
    def __init__(self, telegram_bot, rate_limit_per_minute: int = 12):
        self.telegram_bot = telegram_bot
        self.rate_limiter: RateLimiter = RateLimiter(rate_limit_per_minute)
        self.alert_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.running: bool = False
        self.worker_task: Optional[asyncio.Task] = None
        self.stats: Dict[str, Any] = {
            "alerts_queued": 0,
            "alerts_sent": 0,
            "alerts_failed": 0,
            "queue_size": 0
        }
```

#### 关键方法

**dispatch_alert()**
```python
async def dispatch_alert(self, alert: LargeOrderAlert) -> bool:
    """分发告警到队列"""
    try:
        # 检查速率限制
        if not self.rate_limiter.acquire():
            logger.warning("告警速率限制触发")
            return False

        # 添加到队列
        await self.alert_queue.put(alert)
        self.stats["alerts_queued"] += 1
        self.stats["queue_size"] = self.alert_queue.qsize()

        return True

    except asyncio.QueueFull:
        logger.error("告警队列已满")
        self.stats["alerts_failed"] += 1
        return False
```

**_process_queue()**
```python
async def _process_queue(self) -> None:
    """处理告警队列"""
    self.running = True

    while self.running:
        try:
            # 从队列获取告警
            alert = await asyncio.wait_for(
                self.alert_queue.get(),
                timeout=1.0
            )

            # 发送告警
            success = await self._send_alert(alert)

            if success:
                self.stats["alerts_sent"] += 1
            else:
                self.stats["alerts_failed"] += 1

            # 更新队列大小
            self.stats["queue_size"] = self.alert_queue.qsize()

        except asyncio.TimeoutError:
            # 超时正常，继续循环
            continue
        except Exception as e:
            logger.error(f"处理告警队列错误: {e}")
            await asyncio.sleep(1)
```

**_send_alert()**
```python
async def _send_alert(self, alert: LargeOrderAlert) -> bool:
    """发送告警到Telegram"""
    try:
        # 格式化消息
        message = self._format_alert_message(alert)

        # 获取白名单用户
        from src.user_configuration import get_whitelist
        whitelisted_users = get_whitelist()

        if not whitelisted_users:
            logger.warning("没有白名单用户")
            return False

        # 发送告警到所有用户
        success_count = 0
        fail_count = 0

        for user_id in whitelisted_users:
            try:
                self.telegram_bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown"
                )
                success_count += 1

                # 小延迟防止速率限制
                await asyncio.sleep(0.05)

            except Exception as e:
                fail_count += 1
                logger.error(f"发送告警到用户 {user_id} 失败: {e}")

        logger.info(
            f"大额交易告警已发送: {alert.symbol}-{alert.direction} "
            f"${alert.total_volume:,.0f}. "
            f"成功: {success_count}, 失败: {fail_count}"
        )

        return success_count > 0

    except Exception as e:
        logger.error(f"发送告警错误: {e}", exc_info=True)
        return False
```

**_format_alert_message()**
```python
def _format_alert_message(self, alert: LargeOrderAlert) -> str:
    """格式化告警消息"""
    direction_emoji = "📈" if alert.direction == "买入" else "📉" if alert.direction == "卖出" else "⚖️"

    message = f"""`[大额交易] {alert.symbol}`
{direction_emoji} 方向：{alert.direction}
💰 金额：${alert.total_volume:,.0f}
📊 买入：${alert.buy_volume:,.0f}
📊 卖出：${alert.sell_volume:,.0f}
🕐 时间：{alert.timestamp.strftime('%H:%M:%S')}
⏱️ 窗口：{alert.window_minutes}分钟
🔢 交易数：{alert.trade_count}笔
━━━━━━━━━━━━━━━━━━━━
阈值：${alert.threshold_usd:,.0f} | 交易所：{alert.exchange}`"""

    return message
```

**设计要点**:
- 异步队列处理
- 速率限制保护
- 批量发送优化
- 失败重试机制

---

## 🔄 事件流设计

### 1. 交易事件流

```
┌──────────────────┐
│   Binance WebSocket    │
│     发送交易数据     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  解析交易数据     │
│  创建TradeEvent  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  USD价值转换     │
│  PriceConverter  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  添加到聚合器     │
│ OrderAggregator  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  获取聚合结果     │
│  检查阈值突破     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  检查冷却时间     │
│ ThresholdEngine  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  创建告警事件     │
│  发送告警消息     │
│ AlertDispatcher  │
└──────────────────┘
```

### 2. 错误恢复流

```
┌──────────────────┐
│  WebSocket断开   │
│  连接错误         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  检测错误类型     │
│ ErrorRecovery    │
└────────┬─────────┘
         │
         ▼
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌────────┐
│可恢复  │  │严重   │
│错误    │  │错误   │
└────┬───┘  └───┬────┘
     │         │
     ▼         ▼
┌──────────────────┐
│  执行重连       │
│指数退避策略     │
│  恢复连接       │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│  重新订阅       │
│  恢复监控       │
└──────────────────┘
```

---

## 📊 性能优化策略

### 1. 内存优化

#### 策略1: 实时数据清理
```python
def _prune_old_trades(self, symbol: str, current_time_ms: int):
    """每次添加交易时立即清理过期数据"""
    cutoff_time = current_time_ms - self.window_size_ms
    # 只保留窗口内的数据
    self.data[symbol] = [t for t in self.data[symbol] if t.timestamp > cutoff_time]
```

#### 策略2: 去重机制
```python
def _add_trade_with_dedup(self, trade: TradeRecord):
    """基于trade_id去重"""
    existing_trades = self.data[trade.symbol]
    # 检查是否已存在
    if any(t.trade_id == trade.trade_id for t in existing_trades):
        return  # 跳过重复交易
    existing_trades.append(trade)
```

#### 策略3: 压缩存储
```python
# 使用更紧凑的数据结构
from collections import deque

# deque比list更节省内存，且append/pop高效
self.data[symbol] = deque(maxlen=10000)  # 设置最大长度
```

### 2. CPU优化

#### 策略1: 异步I/O
```python
# 所有I/O操作都使用async/await
async def fetch_price(self, symbol: str) -> float:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

#### 策略2: 批量处理
```python
async def batch_convert(self, conversions: List[ConversionRequest]) -> List[float]:
    """批量转换，减少API调用次数"""
    # 合并相同货币的请求
    currency_groups = defaultdict(list)
    for req in conversions:
        currency_groups[req.currency].append(req)

    # 批量查询
    results = []
    for currency, reqs in currency_groups.items():
        rate = await self._get_usd_rate(currency)
        for req in reqs:
            results.append(req.amount * rate)

    return results
```

#### 策略3: 缓存优化
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_symbol_info(symbol: str) -> SymbolInfo:
    """缓存交易对信息"""
    return self._fetch_symbol_info(symbol)
```

### 3. 网络优化

#### 策略1: 连接复用
```python
class BinanceWebSocketClient:
    def __init__(self):
        # 复用WebSocket连接
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100)
        )
```

#### 策略2: 心跳机制
```python
async def _ping_handler(self):
    """定期发送ping保持连接"""
    while self.connected:
        try:
            await self.websocket.ping()
            await asyncio.sleep(30)  # 30秒ping一次
        except Exception as e:
            logger.error(f"Ping失败: {e}")
            break
```

#### 策略3: 批量订阅
```python
# 一次性订阅所有交易对
streams = [f"{symbol.lower()}@trade" for symbol in self.symbols]
subscribe_msg = {
    "method": "SUBSCRIBE",
    "params": streams,
    "id": int(time.time())
}
```

---

## 🛡️ 错误处理设计

### 1. 错误分类

```python
class ErrorSeverity(Enum):
    LOW = 1      # 可忽略，记录日志
    MEDIUM = 2   # 重试一次
    HIGH = 3     # 指数退避重试
    CRITICAL = 4 # 立即告警管理员
```

### 2. 错误恢复策略

```python
class ErrorRecoveryManager:
    """
    错误恢复管理器
    """
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.last_error_time = {}
        self.error_threshold = 5  # 5次错误后认为严重

    async def handle_error(self, error: Exception, context: str) -> bool:
        """处理错误并决定恢复策略"""
        error_type = self._classify_error(error)

        if error_type == ErrorSeverity.LOW:
            logger.warning(f"低优先级错误 ({context}): {error}")
            return True

        elif error_type == ErrorSeverity.MEDIUM:
            await asyncio.sleep(1)
            return True

        elif error_type == ErrorSeverity.HIGH:
            return await self._exponential_backoff_retry(context)

        else:  # CRITICAL
            await self._send_admin_alert(error, context)
            return False

    def _classify_error(self, error: Exception) -> ErrorSeverity:
        """分类错误类型"""
        if isinstance(error, ConnectionError):
            return ErrorSeverity.HIGH
        elif isinstance(error, TimeoutError):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, ValueError):
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.HIGH
```

### 3. 降级策略

```python
async def convert_to_usd(self, symbol: str, price: float, quantity: float) -> float:
    """USD转换降级策略"""
    try:
        # 尝试实时转换
        return await self._convert_with_live_rate(symbol, price, quantity)
    except Exception as e:
        logger.warning(f"实时转换失败，使用缓存: {e}")
        try:
            # 尝试使用缓存
            return await self._convert_with_cache(symbol, price, quantity)
        except Exception as e:
            logger.warning(f"缓存转换失败，使用默认值: {e}")
            # 使用默认值：1.0（假设已经是USD）
            return price * quantity
```

---

## 📈 监控与指标

### 1. 关键性能指标 (KPI)

```python
@dataclass
class PerformanceMetrics:
    """性能指标"""
    # WebSocket指标
    ws_connections_total: int = 0
    ws_disconnections_total: int = 0
    ws_reconnects_total: int = 0
    ws_uptime_seconds: float = 0.0

    # 交易处理指标
    trades_received_total: int = 0
    trades_processed_total: int = 0
    trades_per_second: float = 0.0

    # 告警指标
    alerts_triggered_total: int = 0
    alerts_suppressed_total: int = 0
    alerts_sent_total: int = 0
    alerts_failed_total: int = 0

    # 资源使用指标
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    queue_size: int = 0

    # 错误指标
    errors_total: int = 0
    critical_errors_total: int = 0
```

### 2. 指标收集

```python
class MetricsCollector:
    """
    指标收集器
    """
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.lock = Lock()

    def update_metric(self, metric_name: str, value: float):
        """更新指标"""
        with self.lock:
            if hasattr(self.metrics, metric_name):
                setattr(self.metrics, metric_name, value)

    def increment_counter(self, counter_name: str, amount: int = 1):
        """增加计数器"""
        with self.lock:
            if hasattr(self.metrics, counter_name):
                current = getattr(self.metrics, counter_name)
                setattr(self.metrics, counter_name, current + amount)
```

### 3. 健康检查

```python
async def health_check(self) -> Dict[str, Any]:
    """健康检查"""
    return {
        "status": "healthy" if self._is_healthy() else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": self.get_uptime(),
        "websocket": {
            "connected": self.connected,
            "reconnects": self.recovery.reconnect_attempts
        },
        "alerts": {
            "queued": self.alert_queue.qsize(),
            "sent_last_hour": self.stats["alerts_sent"]
        },
        "resources": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_mb": psutil.virtual_memory().used / 1024 / 1024
        }
    }
```

---

## 🔐 安全性设计

### 1. 输入验证

```python
def validate_trade_event(self, data: Dict) -> Optional[TradeEvent]:
    """验证交易事件数据"""
    required_fields = ["s", "p", "q", "T", "m"]  # symbol, price, qty, time, isBuyerMaker

    # 检查必需字段
    for field in required_fields:
        if field not in data:
            logger.warning(f"缺少字段: {field}")
            return None

    # 类型验证
    try:
        return TradeEvent(
            symbol=data["s"],
            price=float(data["p"]),
            quantity=float(data["q"]),
            timestamp=int(data["T"]),
            is_buyer_mark=data["m"]
        )
    except (ValueError, TypeError) as e:
        logger.warning(f"数据类型错误: {e}")
        return None
```

### 2. 速率限制

```python
class RateLimiter:
    """
    速率限制器
    令牌桶算法
    """
    def __init__(self, rate: int, per_seconds: int = 60):
        self.rate = rate
        self.per_seconds = per_seconds
        self.tokens = rate
        self.last_update = time.time()
        self.lock = Lock()

    def acquire(self) -> bool:
        """获取令牌"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # 添加令牌
            self.tokens = min(
                self.rate,
                self.tokens + elapsed * self.rate / self.per_seconds
            )
            self.last_update = now

            # 检查是否有令牌
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
```

### 3. 敏感信息保护

```python
# 隐藏敏感信息
def sanitize_message(self, message: str) -> str:
    """清理敏感信息"""
    # 移除可能的API密钥
    message = re.sub(r'[a-zA-Z0-9]{32,}', '***', message)
    # 移除可能的令牌
    message = re.sub(r'Bearer\s+[a-zA-Z0-9\-_]+', 'Bearer ***', message)
    return message

# 安全日志
def log_error(self, error: Exception, context: str):
    """安全记录错误日志"""
    safe_error = str(error)[:200]  # 限制长度
    logger.error(
        f"[{context}] 错误: {safe_error}",
        extra={
            "error_type": type(error).__name__,
            "context": context,
            "sanitized": True
        }
    )
```

---

## 🧪 测试设计

### 1. 单元测试策略

```python
class TestOrderAggregator:
    """订单聚合器测试"""

    def test_add_trade(self):
        """测试添加交易"""
        aggregator = OrderAggregator(window_minutes=5)

        # 创建测试交易
        trade = TradeEvent(
            symbol="BTCUSDT",
            price=50000,
            quantity=10,
            timestamp=time.time() * 1000,
            is_buyer_mark=True
        )

        # 添加交易
        asyncio.run(aggregator.add_trade(trade, 500000))

        # 验证聚合结果
        result = asyncio.run(aggregator.get_aggregation("BTCUSDT", time.time() * 1000))
        assert result["total_volume"] == 500000
        assert result["trade_count"] == 1

    def test_window_pruning(self):
        """测试窗口清理"""
        # 模拟5分钟前的交易
        old_time = (time.time() - 300) * 1000
        # 验证旧数据被清理
```

### 2. 集成测试策略

```python
class TestLargeOrderMonitoring:
    """大额交易监控集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end(self):
        """端到端测试"""
        # 1. 启动监控
        monitor = LargeOrderMonitorProcess()
        await monitor.initialize()

        # 2. 模拟交易数据
        await self._simulate_trades(monitor.binance_client, 10)

        # 3. 等待处理
        await asyncio.sleep(2)

        # 4. 验证告警
        assert monitor.stats["alerts_sent"] > 0
```

### 3. 性能测试策略

```python
class TestPerformance:
    """性能测试"""

    def test_high_throughput(self):
        """高吞吐量测试"""
        # 模拟每秒1000笔交易
        start_time = time.time()
        for _ in range(1000):
            trade = create_test_trade()
            aggregator.add_trade(trade, 100000)

        elapsed = time.time() - start_time
        assert elapsed < 1.0  # 应该在1秒内处理1000笔交易

    def test_memory_usage(self):
        """内存使用测试"""
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # 运行24小时
        for _ in range(24 * 60 * 60):
            trade = create_random_trade()
            aggregator.add_trade(trade, random.uniform(1000, 100000))
            time.sleep(1)

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024
        assert memory_increase < 100  # 内存增长小于100MB
```

---

## 📦 部署架构

### 1. 容器化部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制应用
COPY src/ ./src/
COPY config/ ./config/

# 环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "-m", "src"]
```

### 2. 配置管理

```python
@dataclass
class LargeOrderConfig:
    """大额交易监控配置"""
    # WebSocket配置
    binance_ws_url: str = "wss://stream.binance.com:9443/ws"
    max_reconnect_attempts: int = 10
    ping_interval: int = 30

    # 聚合配置
    window_minutes: int = 5
    threshold_usd: float = 2_000_000
    cooldown_minutes: int = 5

    # 告警配置
    rate_limit_per_minute: int = 12
    alert_queue_size: int = 1000

    # USD转换配置
    cache_ttl_seconds: int = 60
    max_cache_size: int = 1000

    @classmethod
    def from_env(cls) -> "LargeOrderConfig":
        """从环境变量加载配置"""
        return cls(
            threshold_usd=float(os.getenv("LARGE_ORDER_THRESHOLD", "2000000")),
            cooldown_minutes=int(os.getenv("LARGE_ORDER_COOLDOWN", "5")),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "12")),
        )
```

### 3. 监控与告警

```python
# Prometheus指标
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
ws_connections = Counter('ws_connections_total', 'WebSocket连接总数', ['status'])
trades_processed = Counter('trades_processed_total', '处理交易总数')
alerts_sent = Counter('alerts_sent_total', '发送告警总数')
ws_uptime = Gauge('ws_uptime_seconds', 'WebSocket运行时间')

# 指标更新
def on_trade_received(trade):
    trades_processed.inc()
    # 其他指标更新...
```

---

## 🔄 扩展性设计

### 1. 多交易所支持

```python
class ExchangeCollectorFactory:
    """交易所收集器工厂"""

    @staticmethod
    def create_collector(exchange: str, symbols: List[str]) -> BaseExchangeCollector:
        if exchange.lower() == "binance":
            return BinanceWebSocketClient(symbols)
        elif exchange.lower() == "okx":
            return OKXWebSocketClient(symbols)
        elif exchange.lower() == "coinbase":
            return CoinbaseWebSocketClient(symbols)
        else:
            raise ValueError(f"不支持的交易所: {exchange}")
```

### 2. 插件系统

```python
class AlertPlugin(ABC):
    """告警插件基类"""

    @abstractmethod
    async def send_alert(self, alert: ThresholdEvent) -> bool:
        """发送告警"""
        pass

class SlackAlertPlugin(AlertPlugin):
    """Slack告警插件"""

    async def send_alert(self, alert: ThresholdEvent) -> bool:
        # 实现Slack告警
        pass

class EmailAlertPlugin(AlertPlugin):
    """邮件告警插件"""

    async def send_alert(self, alert: ThresholdEvent) -> bool:
        # 实现邮件告警
        pass
```

### 3. 配置热更新

```python
class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config = LargeOrderConfig()
        self.subscribers = []

    def update_config(self, new_config: LargeOrderConfig):
        """更新配置"""
        old_config = self.config
        self.config = new_config

        # 通知订阅者
        for callback in self.subscribers:
            callback(old_config, new_config)

    def subscribe(self, callback: Callable):
        """订阅配置变更"""
        self.subscribers.append(callback)
```

---

## 📚 参考资料

- [币安WebSocket API文档](https://binance-docs.github.io/apidocs/spot/en/#trade-streams)
- [WebSockets库文档](https://websockets.readthedocs.io/)
- [asyncio异步编程指南](https://docs.python.org/3/library/asyncio.html)
- [事件驱动架构模式](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Rate Limiter算法](https://en.wikipedia.org/wiki/Token_bucket)

---

**文档版本**: 1.0.0
**最后更新**: 2025-11-10
**维护者**: OpenSpec AI助手

