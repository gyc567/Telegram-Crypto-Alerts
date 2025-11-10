# 大额交易监控功能 - 技术规格说明

## 📋 规格概览

**规格编号**: SPEC-2025-0104
**版本**: 1.0.0
**创建日期**: 2025-11-10
**变更类型**: 新增功能 (ADDED)
**依赖关系**: 无

---

## 🎯 规格目标

本规格定义了大额交易监控系统的技术要求、功能规格、性能指标和验收标准。

### 设计目标
- **响应时间**: < 2秒 (从交易到告警)
- **可用性**: 99.5%+
- **数据准确性**: 99.9%+
- **吞吐量**: 支持每秒1000+交易事件
- **资源使用**: CPU < 5%, 内存 < 150MB

---

## 🆕 新增要求 (ADDED Requirements)

### 1. WebSocket实时数据流监控

#### 1.1 WebSocket连接管理
**Requirement**: 系统必须建立和维护到Binance WebSocket的稳定连接，实时接收交易数据。

**实现规格**:
- 连接URL: `wss://stream.binance.com:9443/ws`
- 协议版本: WebSocket v13
- 心跳机制: 每30秒发送ping
- 自动重连: 指数退避 (2s → 5s → 10s → 30s → 60s)
- 最大重连次数: 10次
- 连接超时: 30秒

**数据格式**:
```json
{
  "e": "trade",  // 事件类型
  "E": 123456789,  // 事件时间
  "s": "BNBBTC",   // 交易对
  "p": "0.001",    // 价格
  "q": "100",      // 数量
  "T": 123456785,  // 交易时间
  "m": true        // 是否买方做市商
}
```

#### 1.2 多交易对订阅
**Requirement**: 系统必须同时订阅20+主流交易对的实时数据流。

**支持的交易对**:
```
['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
 'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'MATICUSDT', 'LTCUSDT',
 'AVAXUSDT', 'UNIUSDT', 'ATOMUSDT', 'LINKUSDT', 'ETCUSDT',
 'BCHUSDT', 'FILUSDT', 'TRXUSDT', 'XLMUSDT', 'VETUSDT']
```

**订阅格式**:
```json
{
  "method": "SUBSCRIBE",
  "params": [
    "btcusdt@trade",
    "ethusdt@trade",
    ...
  ],
  "id": 12345
}
```

#### 1.3 消息处理
**Requirement**: 系统必须实时解析WebSocket消息，并转换为标准化的交易事件。

**处理流程**:
1. 接收消息 → 2. JSON解析 → 3. 数据验证 → 4. 创建TradeEvent → 5. 发送事件

**TradeEvent结构**:
```python
@dataclass
class TradeEvent:
    symbol: str          # 交易对 (e.g., "BTCUSDT")
    price: float         # 交易价格
    quantity: float      # 交易数量
    timestamp: int       # 交易时间 (毫秒)
    trade_id: int        # 交易ID
    is_buyer_mark: bool  # 是否买方做市商
    side: str            # BUY or SELL
```

**验证规则**:
- symbol: 必须为字符串，长度3-12字符
- price: 必须为正数，精度不超过8位小数
- quantity: 必须为正数，精度不超过8位小数
- timestamp: 必须在当前时间±5分钟范围内

#### 1.4 错误处理
**Requirement**: 系统必须优雅处理网络错误、连接断开和数据异常。

**错误分类**:
```python
class ConnectionError(Exception):
    """连接错误 - 需要重连"""
    pass

class DataError(Exception):
    """数据错误 - 跳过该条数据"""
    pass

class CriticalError(Exception):
    """严重错误 - 停止系统并告警"""
    pass
```

**处理策略**:
- 网络错误: 指数退避重连 (最多10次)
- 数据错误: 记录日志，跳过该条数据
- 严重错误: 停止系统，通知管理员

**错误恢复流程**:
```
检测错误 → 分类错误类型 → 选择恢复策略 → 执行恢复 → 验证状态
```

### 2. 5分钟滚动窗口聚合

#### 2.1 时间窗口管理
**Requirement**: 系统必须维护一个5分钟(300秒)的滚动时间窗口，实时聚合窗口内的交易数据。

**窗口配置**:
- 窗口大小: 5分钟 (300秒) = 300,000毫秒
- 窗口类型: 滚动窗口 (sliding window)
- 精度: 毫秒级
- 数据保留: 仅保留当前窗口内数据

**窗口计算**:
```python
window_start = current_time_ms - 5 * 60 * 1000  # 5分钟前
window_end = current_time_ms  # 当前时间
```

**清理策略**:
- 实时清理: 每次添加新交易时立即清理过期数据
- 触发条件: 新交易到达
- 清理范围: 所有交易对
- 清理方式: 基于timestamp过滤

#### 2.2 数据聚合规则
**Requirement**: 系统必须按交易对和方向分别聚合，计算总交易量、买入量、卖出量和交易笔数。

**聚合维度**:
1. **交易对** (symbol): BTCUSDT, ETHUSDT等
2. **方向** (side): BUY, SELL, BOTH

**聚合指标**:
```python
@dataclass
class AggregationResult:
    symbol: str                    # 交易对
    window_minutes: int            # 窗口大小 (分钟)
    total_volume: float            # 总交易量 (USD)
    buy_volume: float              # 买入量 (USD)
    sell_volume: float             # 卖出量 (USD)
    trade_count: int               # 交易笔数
    buy_count: int                 # 买入笔数
    sell_count: int                # 卖出笔数
    threshold_breach: bool         # 是否突破阈值
    threshold_usd: float           # 阈值 (USD)
    timestamp: int                 # 计算时间 (毫秒)
```

**聚合公式**:
```python
buy_volume = sum(trade.usd_value for trade in window if trade.side == "BUY")
sell_volume = sum(trade.usd_value for trade in window if trade.side == "SELL")
total_volume = buy_volume + sell_volume
trade_count = len(window)
```

**去重规则**:
- 去重字段: trade_id
- 去重时机: 添加交易时
- 去重方式: 检查trade_id是否已存在
- 记录统计: 记录去重次数

#### 2.3 USD价值转换
**Requirement**: 系统必须将所有交易转换为USD价值进行聚合。

**支持稳定币**:
- USDT (Tether)
- USDC (USD Coin)
- BUSD (Binance USD)
- FDUSD (First Digital USD)
- TUSD (TrueUSD)
- USDP (Pax Dollar)

**转换策略**:
```python
if quote_currency in ["USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USDP"]:
    # 已经是USD稳定币
    usd_value = price * quantity
elif quote_currency == "USD":
    # 已经是USD
    usd_value = price * quantity
else:
    # 需要转换
    usd_rate = fetch_usd_rate(quote_currency)
    usd_value = price * quantity * usd_rate
```

**汇率获取**:
- 数据源: Binance REST API `/ticker/price`
- 缓存时间: 60秒
- 缓存策略: LRU (最少最近使用)
- 缓存大小: 1000条记录
- 超时时间: 5秒
- 重试次数: 3次

**降级方案**:
1. 尝试实时汇率
2. 失败则使用缓存
3. 失败则使用默认值1.0
4. 记录告警日志

#### 2.4 内存管理
**Requirement**: 系统必须有效管理内存，确保长期稳定运行。

**内存管理策略**:
1. **实时清理**: 添加交易时立即清理过期数据
2. **限制队列大小**: 每个交易对最大保留10000条记录
3. **定期压缩**: 每小时执行一次内存压缩
4. **内存监控**: 实时监控内存使用量

**内存阈值**:
- 警告阈值: 120MB
- 严重阈值: 150MB
- 致命阈值: 200MB (触发降级)

**降级策略**:
- 内存 > 150MB: 减少缓存时间 (60s → 30s)
- 内存 > 180MB: 减少监控交易对 (20 → 10)
- 内存 > 200MB: 停止新交易处理，清理数据

### 3. 阈值检测与告警

#### 3.1 阈值配置
**Requirement**: 系统必须支持可配置的USD阈值，当5分钟窗口内交易量超过阈值时触发告警。

**默认配置**:
- 阈值: $2,000,000 USD
- 窗口: 5分钟
- 冷却时间: 5分钟

**可配置参数**:
```python
@dataclass
class ThresholdConfig:
    threshold_usd: float = 2_000_000      # 阈值 (USD)
    window_minutes: int = 5               # 窗口大小 (分钟)
    cooldown_minutes: int = 5             # 冷却时间 (分钟)
    enabled: bool = True                  # 是否启用
```

**动态更新**:
- 更新方式: API调用或配置文件
- 生效时间: 立即生效
- 更新频率: 无限制
- 历史记录: 保存最近10次配置变更

#### 3.2 阈值检查逻辑
**Requirement**: 系统必须实时检查聚合数据，当突破阈值时创建告警事件。

**检查流程**:
1. 获取聚合结果
2. 计算总交易量
3. 对比阈值
4. 判断是否突破
5. 记录统计

**阈值判断**:
```python
def check_threshold(self, aggregation: AggregationResult) -> bool:
    """
    检查是否突破阈值
    条件: total_volume >= threshold_usd
    """
    return aggregation.total_volume >= self.threshold_usd
```

**边界条件**:
- 正好等于阈值: 触发告警 (>=)
- 略低于阈值: 不触发 (预留0.1%缓冲)
- 空数据: 不触发
- 数据不足: 不触发 (至少1笔交易)

#### 3.3 方向判断
**Requirement**: 系统必须智能判断主要交易方向，辅助市场分析。

**判断算法**:
```python
def determine_direction(self, buy_volume: float, sell_volume: float) -> str:
    """
    智能判断交易方向
    规则:
    - 买入占比 > 60%: "买入"
    - 卖出占比 > 60%: "卖出"
    - 双向占比在40%-60%: "双向"
    """
    if buy_volume == 0 and sell_volume == 0:
        return "无交易"
    elif buy_volume == 0:
        return "卖出"
    elif sell_volume == 0:
        return "买入"

    total = buy_volume + sell_volume
    buy_ratio = buy_volume / total

    if buy_ratio > 0.6:
        return "买入"
    elif buy_ratio < 0.4:
        return "卖出"
    else:
        return "双向"
```

**比例阈值**:
- 买入主导: 买入占比 > 60%
- 卖出主导: 卖出占比 > 60%
- 双向均衡: 买卖占比均在40%-60%

#### 3.4 冷却管理
**Requirement**: 系统必须为每个交易对维护独立的冷却时间，防止重复告警。

**冷却机制**:
- 冷却对象: 按交易对(symbol)独立
- 冷却时间: 5分钟
- 触发条件: 阈值突破后
- 抑制范围: 同一交易对的所有后续告警

**冷却状态管理**:
```python
@dataclass
class CooldownState:
    symbol: str              # 交易对
    cooldown_until: datetime # 冷却结束时间
    last_alert: datetime     # 最后告警时间
    alert_count: int         # 冷却期间告警尝试次数
```

**冷却检查**:
```python
def is_in_cooldown(self, symbol: str) -> bool:
    """
    检查交易对是否在冷却期
    """
    if symbol not in self.cooldowns:
        return False

    cooldown_until = self.cooldowns[symbol]
    return datetime.now() < cooldown_until
```

**冷却重置**:
- 自动重置: 冷却时间到期后自动清除
- 手动重置: 管理员可强制清除
- 批量清除: 支持清除所有冷却

#### 3.5 告警事件创建
**Requirement**: 系统必须创建结构化的告警事件，包含所有必要信息。

**事件结构**:
```python
@dataclass
class ThresholdEvent:
    symbol: str              # 交易对
    direction: str           # 方向 (买入/卖出/双向)
    total_volume: float      # 总交易量 (USD)
    buy_volume: float        # 买入量 (USD)
    sell_volume: float       # 卖出量 (USD)
    trade_count: int         # 交易笔数
    threshold_usd: float     # 阈值 (USD)
    window_minutes: int      # 窗口大小 (分钟)
    timestamp: datetime      # 事件时间
    exchange: str = "Binance" # 交易所
    cooldown_until: Optional[datetime] = None  # 冷却结束时间
```

**事件字段说明**:
- symbol: 交易对 (e.g., "BTCUSDT")
- direction: 主要方向 (基于买卖量智能判断)
- total_volume: 5分钟窗口内总交易量
- buy_volume: 买入总量
- sell_volume: 卖出总量
- trade_count: 交易笔数
- threshold_usd: 触发的阈值
- window_minutes: 监控窗口
- timestamp: 事件创建时间
- exchange: 交易所名称

### 4. USD转换与缓存

#### 4.1 稳定币支持
**Requirement**: 系统必须支持主要稳定币的直接转换，无需汇率查询。

**支持稳定币列表**:
- USDT (Tether) - 最广泛使用
- USDC (USD Coin) - Coinbase发行
- BUSD (Binance USD) - Binance发行
- FDUSD (First Digital USD) - 亚洲稳定币
- TUSD (TrueUSD) - 审计稳定币
- USDP (Pax Dollar) - Paxos发行

**识别规则**:
```python
def extract_quote_currency(symbol: str) -> str:
    """
    从交易对提取报价货币
    优先级: 稳定币 > BTC > ETH > 其他
    """
    stablecoins = ["USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USDP"]

    # 优先匹配长稳定币
    for coin in sorted(stablecoins, key=len, reverse=True):
        if symbol.endswith(coin):
            return coin

    # 简单情况: 6字符交易对
    if len(symbol) == 6:
        return symbol[-4:]

    return "UNKNOWN"
```

**转换策略**:
- 稳定币/USD: 直接使用价格 (1:1)
- 其他货币: 查询USD汇率

#### 4.2 汇率查询
**Requirement**: 系统必须从可靠的API获取实时汇率，支持缓存和重试。

**数据源**:
- 主源: Binance REST API
- 端点: `/api/v3/ticker/price`
- URL格式: `https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}`

**查询优先级**:
1. {CURRENCY}USDT (最高优先级)
2. {CURRENCY}BUSD
3. USDT{CURRENCY} (反向，需取倒数)
4. BUSD{CURRENCY} (反向，需取倒数)

**查询示例**:
```python
# 查询BTC的USD汇率
url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
response = {"symbol": "BTCUSDT", "price": "50000.00"}

# 反向查询 (如查询USDT的BTC价格)
url = "https://api.binance.com/api/v3/ticker/price?symbol=USDTBTC"
response = {"symbol": "USDTBTC", "price": "0.00002000"}
usd_rate = 1 / 0.00002000  # 50000 USD per BTC
```

**错误处理**:
- 网络错误: 重试3次，指数退避
- 超时错误: 默认值1.0
- 无数据错误: 记录日志，使用默认值
- 连续失败: 降级到缓存模式

#### 4.3 缓存机制
**Requirement**: 系统必须实现高效的缓存机制，减少API调用并提高响应速度。

**缓存策略**:
- 算法: LRU (Least Recently Used)
- TTL: 60秒
- 最大大小: 1000条记录
- 清理频率: 每100次查询
- 命中率目标: > 90%

**缓存结构**:
```python
CacheEntry = Tuple[float, datetime]  # (rate, timestamp)

{
    "BTCUSDT": (50000.0, 2025-11-10 10:00:00),
    "ETHUSDT": (3000.0, 2025-11-10 10:00:00),
    ...
}
```

**缓存操作**:
```python
def get_cached_rate(self, currency: str) -> Optional[float]:
    """获取缓存的汇率"""
    if currency in self.cache:
        rate, timestamp = self.cache[currency]
        age = (datetime.now() - timestamp).total_seconds()
        if age < self.cache_ttl:
            return rate
    return None

def cache_rate(self, currency: str, rate: float) -> None:
    """缓存汇率"""
    if len(self.cache) >= self.max_cache_size:
        # LRU清理: 删除最久未使用的项
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
        del self.cache[oldest_key]

    self.cache[currency] = (rate, datetime.now())
```

#### 4.4 批量转换
**Requirement**: 系统必须支持批量转换请求，合并相同货币的查询以优化性能。

**批量转换流程**:
1. 收集所有转换请求
2. 按货币分组
3. 并行查询汇率
4. 批量返回结果

**分组示例**:
```python
# 输入
requests = [
    (symbol="BTCUSDT", price=50000, quantity=10),
    (symbol="ETHUSDT", price=3000, quantity=100),
    (symbol="BTCUSDT", price=50100, quantity=5),  # 同货币
]

# 分组
groups = {
    "USDT": [
        (symbol="BTCUSDT", price=50000, quantity=10),
        (symbol="ETHUSDT", price=3000, quantity=100),
        (symbol="BTCUSDT", price=50100, quantity=5),
    ]
}
```

**性能优化**:
- 减少API调用次数
- 异步并发查询
- 智能请求合并
- 结果缓存复用

### 5. 告警调度与发送

#### 5.1 消息格式化
**Requirement**: 系统必须生成结构化的Telegram告警消息，包含所有必要信息。

**消息格式**:
```markdown
`[大额交易] BTCUSDT`
📈 方向：买入
💰 金额：$2,500,000
📊 买入：$1,800,000
📊 卖出：$700,000
🕐 时间：14:35:22
⏱️ 窗口：5分钟
🔢 交易数：23笔
━━━━━━━━━━━━━━━━━━━━
阈值：$2,000,000 | 交易所：Binance
```

**格式化规则**:
- 使用Markdown格式 (反引号代码块)
- 表情符号增强可读性
- 数字格式化 (千分位分隔符)
- 方向使用不同表情
- 分隔线增强视觉层次

**表情符号映射**:
```python
DIRECTION_EMOJIS = {
    "买入": "📈",
    "卖出": "📉",
    "双向": "⚖️",
    "无交易": "❌"
}
```

**数字格式化**:
```python
def format_currency(amount: float) -> str:
    """格式化货币"""
    if amount >= 1_000_000_000:
        return f"${amount/1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount/1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.2f}K"
    else:
        return f"${amount:.2f}"
```

#### 5.2 队列管理
**Requirement**: 系统必须使用异步队列管理告警，确保可靠传递和顺序处理。

**队列配置**:
- 队列类型: asyncio.Queue
- 最大容量: 1000条告警
- 队列超时: 1秒
- 处理方式: 先进先出 (FIFO)

**队列状态**:
```python
@dataclass
class QueueStatus:
    size: int                 # 当前队列大小
    max_size: int             # 最大容量
    utilization: float        # 使用率
    total_queued: int         # 总排队数
    total_processed: int      # 总处理数
    dropped: int              # 丢弃数
```

**入队操作**:
```python
async def queue_alert(self, alert: LargeOrderAlert) -> bool:
    """入队告警"""
    try:
        # 速率限制检查
        if not self.rate_limiter.acquire():
            return False

        # 尝试入队
        await self.alert_queue.put(alert)
        self.stats["alerts_queued"] += 1
        return True

    except asyncio.QueueFull:
        self.stats["alerts_dropped"] += 1
        return False
```

**出队操作**:
```python
async def dequeue_alert(self) -> Optional[LargeOrderAlert]:
    """出队告警"""
    try:
        alert = await asyncio.wait_for(
            self.alert_queue.get(),
            timeout=1.0
        )
        return alert
    except asyncio.TimeoutError:
        return None
```

#### 5.3 速率限制
**Requirement**: 系统必须实现速率限制，防止Telegram API限制和用户告警轰炸。

**限流配置**:
- 限流算法: 令牌桶 (Token Bucket)
- 令牌速率: 12个/分钟 (默认值)
- 令牌容量: 12个
- 令牌补充: 每5秒补充1个 (12/60)

**限流实现**:
```python
class RateLimiter:
    def __init__(self, rate: int, per_seconds: int = 60):
        self.rate = rate
        self.per_seconds = per_seconds
        self.tokens = rate  # 初始满桶
        self.last_update = time.time()
        self.lock = Lock()

    def acquire(self) -> bool:
        """获取令牌"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # 补充令牌
            self.tokens = min(
                self.rate,
                self.tokens + elapsed * self.rate / self.per_seconds
            )
            self.last_update = now

            # 消耗令牌
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
```

**溢出处理**:
- 队列满: 丢弃最新告警
- 速率超限: 延迟发送
- 用户退订: 停止发送到该用户
- 系统过载: 降级到摘要模式

#### 5.4 Telegram发送
**Requirement**: 系统必须可靠地将告警发送到Telegram，处理发送失败和重试。

**发送流程**:
1. 获取白名单用户
2. 格式化消息
3. 遍历用户列表
4. 发送消息
5. 记录结果

**用户管理**:
```python
def get_whitelisted_users() -> List[int]:
    """获取白名单用户ID"""
    try:
        whitelist_path = get_whitelist_file_path()
        with open(whitelist_path, 'r') as f:
            users = json.load(f)
            return users
    except Exception as e:
        logger.error(f"获取白名单失败: {e}")
        return []
```

**发送实现**:
```python
async def send_to_users(self, message: str, users: List[int]) -> Dict[str, int]:
    """发送消息到用户"""
    results = {"success": 0, "failed": 0}

    for user_id in users:
        try:
            self.telegram_bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            results["success"] += 1
            await asyncio.sleep(0.05)  # 防止过快发送

        except Exception as e:
            results["failed"] += 1
            logger.error(f"发送失败 user={user_id}: {e}")

    return results
```

**失败重试**:
- 重试次数: 3次
- 重试间隔: 1s, 3s, 10s (指数退避)
- 重试条件: 网络错误、超时
- 跳过条件: 用户不存在、权限拒绝
- 最终处理: 记录失败日志

#### 5.5 统计与监控
**Requirement**: 系统必须收集详细的统计信息，用于监控和优化。

**统计指标**:
```python
@dataclass
class AlertStats:
    # 队列统计
    alerts_queued: int = 0           # 入队总数
    alerts_dequeued: int = 0         # 出队总数
    alerts_sent: int = 0             # 发送成功数
    alerts_failed: int = 0           # 发送失败数
    alerts_dropped: int = 0          # 丢弃数

    # 用户统计
    unique_users: int = 0            # 唯一用户数
    messages_per_user: Dict[int, int] = field(default_factory=dict)

    # 性能统计
    avg_send_latency: float = 0.0    # 平均发送延迟
    max_queue_size: int = 0          # 最大队列大小
    queue_full_count: int = 0        # 队列满次数
    rate_limited_count: int = 0      # 速率限制次数
```

**统计更新**:
```python
def update_stats(self, stat_name: str, value: float):
    """更新统计"""
    with self.stats_lock:
        if stat_name in self.stats:
            self.stats[stat_name] = value

def increment_stats(self, stat_name: str, amount: int = 1):
    """增加统计"""
    with self.stats_lock:
        if stat_name in self.stats:
            self.stats[stat_name] += amount
```

**健康检查**:
```python
def get_health_status(self) -> Dict[str, Any]:
    """获取健康状态"""
    return {
        "status": "healthy" if self._is_healthy() else "unhealthy",
        "queue_size": self.alert_queue.qsize(),
        "queue_capacity": self.alert_queue.maxsize,
        "queue_utilization": self.alert_queue.qsize() / self.alert_queue.maxsize,
        "alerts_sent_last_hour": self._get_recent_count("alerts_sent", 3600),
        "alerts_failed_last_hour": self._get_recent_count("alerts_failed", 3600),
        "rate_limiter_available": self.rate_limiter.tokens
    }
```

---

## 🔄 修改要求 (MODIFIED Requirements)

### 1. 主应用集成 (MODIFIED in __main__.py)

#### 1.1 启动流程修改
**Requirement**: 主应用必须初始化并启动大额交易监控进程，与现有告警进程并行运行。

**添加代码位置**: `src/__main__.py`

**修改内容**:
```python
# 现有代码...
from src.alert_processes.large_order import get_large_order_monitor

# 现有代码...
# 在组件初始化部分添加
large_order_monitor = None
if getenv("ENABLE_LARGE_ORDER_MONITORING", "false").lower() == "true":
    try:
        # 初始化大额交易监控
        large_order_monitor = await get_large_order_monitor()
        logger.info("大额交易监控已初始化")
    except Exception as e:
        logger.error(f"大额交易监控初始化失败: {e}", exc_info=True)

# 现有代码...
# 在主线程守护循环前启动监控
if large_order_monitor:
    asyncio.create_task(large_order_monitor.run())
    logger.info("大额交易监控已启动")

# 现有代码...
# 在优雅关闭时添加
if large_order_monitor:
    await large_order_monitor.stop()
    logger.info("大额交易监控已停止")
```

#### 1.2 配置管理修改
**Requirement**: 主应用必须加载大额交易监控的相关配置。

**配置变量**:
```python
# 新增环境变量
ENABLE_LARGE_ORDER_MONITORING = "false"  # 启用/禁用
LARGE_ORDER_THRESHOLD = "2000000"        # 阈值 (USD)
LARGE_ORDER_COOLDOWN = "5"               # 冷却时间 (分钟)
LARGE_ORDER_SYMBOLS = ""                 # 监控交易对 (逗号分隔)
RATE_LIMIT_PER_MINUTE = "12"             # 告警速率限制

# 读取配置
threshold_usd = float(getenv("LARGE_ORDER_THRESHOLD", "2000000"))
cooldown_minutes = int(getenv("LARGE_ORDER_COOLDOWN", "5"))
symbols = getenv("LARGE_ORDER_SYMBOLS", "").split(",") if getenv("LARGE_ORDER_SYMBOLS") else None
rate_limit = int(getenv("RATE_LIMIT_PER_MINUTE", "12"))
```

#### 1.3 优雅关闭修改
**Requirement**: 主应用关闭时必须优雅地停止大额交易监控进程。

**关闭流程**:
```python
async def shutdown():
    """优雅关闭"""
    logger.info("开始关闭应用...")

    # 停止大额交易监控
    if large_order_monitor:
        logger.info("停止大额交易监控...")
        await large_order_monitor.stop()
        logger.info("大额交易监控已停止")

    # 停止其他组件...
    # ...

    logger.info("应用已关闭")
```

### 2. Telegram命令扩展 (MODIFIED in telegram.py)

#### 2.1 新增命令
**Requirement**: 必须添加大额交易监控相关的管理命令。

**新增命令列表**:
```python
# 在命令注册部分添加
user_commands = [
    # 现有命令...
    {"command": "large_order_status", "description": "查看大额交易监控状态"},
    {"command": "large_order_symbols", "description": "查看监控的交易对"},
    {"command": "large_order_alerts", "description": "查看/清除告警 (管理员)"},
    {"command": "large_order_config", "description": "查看监控配置 (管理员)"},
]

# 在消息处理器中添加
@self.message_handler(commands=["large_order_status"])
@self.is_whitelisted
def on_large_order_status(message):
    """查看监控状态"""
    # 实现...

@self.message_handler(commands=["large_order_symbols"])
@self.is_whitelisted
def on_large_order_symbols(message):
    """查看监控交易对"""
    # 实现...

@self.message_handler(commands=["large_order_alerts"])
@self.is_admin  # 管理员专用
def on_large_order_alerts(message):
    """查看/清除告警"""
    # 实现...

@self.message_handler(commands=["large_order_config"])
@self.is_admin  # 管理员专用
def on_large_order_config(message):
    """查看配置"""
    # 实现...
```

#### 2.2 权限控制
**Requirement**: 某些管理命令必须限制为管理员使用。

**权限判断**:
```python
# 检查是否管理员
ADMIN_USER_IDS = [123456789, 987654321]  # 管理员用户ID列表

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS

# 使用装饰器
def is_admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        message = args[0]
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ 此命令仅管理员可用")
            return
        return func(*args, **kwargs)
    return wrapper
```

---

## 🗑️ 移除要求 (REMOVED Requirements)

### 1. 无移除要求

本次变更未移除任何现有功能或接口。所有变更均为新增或修改，不影响现有功能。

---

## 📊 性能要求

### 响应时间要求
- **WebSocket连接建立**: < 3秒
- **交易数据处理**: < 100ms
- **USD转换**: < 50ms (缓存命中)
- **阈值检查**: < 10ms
- **告警发送**: < 2秒
- **总延迟**: < 2秒 (从交易到告警)

### 吞吐量要求
- **交易事件处理**: 1000+ 交易/秒
- **告警发送**: 100+ 告警/分钟
- **WebSocket消息**: 5000+ 消息/秒
- **USD转换查询**: 100+ 查询/分钟

### 资源使用要求
- **CPU使用率**: < 5%
- **内存使用**: < 150MB
- **网络带宽**: < 10Mbps
- **磁盘I/O**: < 1MB/秒

### 可用性要求
- **系统可用性**: 99.5%+
- **WebSocket连接率**: 99%+
- **告警送达率**: 99.9%+
- **数据准确率**: 99.9%+

---

## 🧪 测试要求

### 单元测试
**覆盖率要求**: ≥ 85%

**测试模块**:
- [ ] WebSocket客户端 (test_websocket_client.py)
- [ ] 订单聚合器 (test_order_aggregator.py)
- [ ] 阈值引擎 (test_threshold_engine.py)
- [ ] USD转换器 (test_price_converter.py)
- [ ] 告警调度器 (test_alert_dispatcher.py)
- [ ] 错误恢复 (test_error_recovery.py)

**测试场景**:
- [ ] 正常流程测试
- [ ] 边界条件测试
- [ ] 错误处理测试
- [ ] 性能基准测试
- [ ] 内存泄漏测试

### 集成测试
**测试范围**:
- [ ] 端到端流程测试
- [ ] 多交易并发测试
- [ ] WebSocket断开恢复测试
- [ ] 长时间运行测试 (24小时)
- [ ] 高负载测试

### 验收测试
**验收标准**:
- [ ] 所有功能点正常工作
- [ ] 性能指标达标
- [ ] 稳定性测试通过
- [ ] 用户场景测试通过
- [ ] 文档完整准确

---

## 📝 实施检查清单

### 代码实现
- [ ] 1. BinanceWebSocketClient类实现
- [ ] 2. OrderAggregator类实现
- [ ] 3. ThresholdEngine类实现
- [ ] 4. PriceConverter类实现
- [ ] 5. AlertDispatcher类实现
- [ ] 6. ErrorRecoveryManager类实现
- [ ] 7. LargeOrderMonitorProcess类实现
- [ ] 8. 数据模型定义 (TradeEvent, ThresholdEvent, etc.)
- [ ] 9. __main__.py集成
- [ ] 10. telegram.py命令扩展

### 配置管理
- [ ] 11. 环境变量配置
- [ ] 12. 配置文件管理
- [ ] 13. 配置验证
- [ ] 14. 动态配置更新

### 测试覆盖
- [ ] 15. 单元测试编写
- [ ] 16. 集成测试编写
- [ ] 17. 性能测试编写
- [ ] 18. 测试覆盖率报告

### 文档编写
- [ ] 19. API文档
- [ ] 20. 部署文档
- [ ] 21. 用户指南
- [ ] 22. 故障排除文档

### 部署准备
- [ ] 23. 环境变量模板
- [ ] 24. 部署脚本
- [ ] 25. 监控配置
- [ ] 26. 告警设置

---

## 📚 参考实现

### 示例代码

#### WebSocket客户端
```python
# 见: src/monitor/large_orders/exchanges/binance.py
class BinanceWebSocketClient(BaseExchangeCollector):
    async def start(self):
        # 实现WebSocket连接和订阅
        pass
```

#### 订单聚合器
```python
# 见: src/monitor/large_orders/core/order_aggregator.py
class OrderAggregator:
    async def add_trade(self, trade_event: TradeEvent, usd_value: float):
        # 实现交易添加和聚合
        pass
```

#### 阈值引擎
```python
# 见: src/monitor/large_orders/core/threshold_engine.py
class ThresholdEngine:
    async def check_aggregation(self, symbol: str, aggregation_data: Dict):
        # 实现阈值检查
        pass
```

#### USD转换器
```python
# 见: src/monitor/large_orders/src/price_converter.py
class PriceConverter:
    async def convert_to_usd(self, symbol: str, price: float, quantity: float):
        # 实现USD转换
        pass
```

#### 告警调度器
```python
# 见: src/monitor/large_orders/core/alert_dispatcher.py
class AlertDispatcher:
    async def dispatch_alert(self, alert: LargeOrderAlert):
        # 实现告警分发
        pass
```

#### 主进程
```python
# 见: src/alert_processes/large_order.py
class LargeOrderMonitorProcess(BaseAlertProcess):
    async def run(self):
        # 实现主监控循环
        pass
```

---

**规格版本**: 1.0.0
**最后更新**: 2025-11-10
**维护者**: OpenSpec AI助手
**状态**: 🟡 待审核

