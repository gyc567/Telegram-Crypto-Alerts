# OpenSpec 变更提案：大额交易监控功能 (Large Order Monitoring)

## 📋 提案概览

**提案编号**: CHANGE-2025-0104
**创建日期**: 2025-11-10
**类型**: 功能增强 (Feature Enhancement)
**优先级**: 高 (High)
**状态**: 待审核 (Pending Review)

---

## 🎯 变更目标

实现基于WebSocket的实时大额订单监控系统，通过5分钟滚动窗口监控超过$2,000,000 USD的交易活动，并提供及时的市场异常活动告警。

### 核心功能需求

1. **实时WebSocket监控**
   - 连接到Binance WebSocket实时数据流
   - 支持20+主流加密货币交易对（BTC/USDT、ETH/USDT、BNB/USDT等）
   - 自动重连和错误恢复机制

2. **5分钟滚动窗口聚合**
   - 累积5分钟内的所有交易
   - 分别计算买入和卖出总量
   - 智能去重和内存管理

3. **阈值检测与告警**
   - 默认阈值：$2,000,000 USD
   - 支持动态阈值调整
   - 5分钟冷却期防止重复告警
   - 告警格式：`[大额主动买入] BTC/USDT 金额：$2,500,000 方向：买入 时间：14:35:22`

4. **USD转换**
   - 实时汇率转换
   - 支持6种稳定币（USDT、USDC、BUSD、FDUSD、TUSD、USDP）
   - 智能缓存机制优化性能

---

## 📊 当前状态 vs 目标状态

| 维度 | 当前状态 | 目标状态 |
|------|---------|---------|
| **架构模式** | 轮询模式 (Polling) | 事件驱动模式 (Event-Driven) |
| **数据源** | REST API (每10秒轮询) | WebSocket (实时推送) |
| **CPU使用率** | 20% | 2% (降低80%) |
| **内存使用** | 200MB | 100MB (降低50%) |
| **响应延迟** | 10-15秒 | < 1秒 |
| **系统稳定性** | 95% | 99.5% |
| **监控交易对** | 仅用户配置的交易对 | 20+ 固定交易对 |
| **时间窗口** | 无固定窗口 | 5分钟滚动窗口 |
| **告警阈值** | 动态配置 | $2,000,000 USD 固定阈值 |
| **冷却机制** | 无 | 5分钟每交易对 |

---

## 🏗️ 技术架构

### 1. 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                大额交易监控系统                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   WebSocket  │─────▶│  Order       │                    │
│  │   Manager    │      │  Aggregator  │                    │
│  │  (Binance)   │      │              │                    │
│  └──────────────┘      └──────┬───────┘                    │
│                                 │                            │
│  ┌──────────────┐      ┌───────▼───────┐                    │
│  │   Alert      │◀─────│   Threshold   │                    │
│  │  Dispatcher  │      │    Engine     │                    │
│  │ (Telegram)   │      │               │                    │
│  └──────────────┘      └───────────────┘                    │
│                                 │                            │
│  ┌──────────────┐      ┌───────▼───────┐                    │
│  │     USD      │      │    Error      │                    │
│  │  Converter   │      │   Recovery    │                    │
│  └──────────────┘      └───────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心组件

#### A. BinanceWebSocketClient
```python
class BinanceWebSocketClient:
    """币安WebSocket客户端"""
    def __init__(self, symbols: List[str]):
        self.websocket_url = "wss://stream.binance.com:9443/ws"
        self.symbols = symbols  # 20+ 交易对
        self.recovery = ErrorRecoveryManager()
        self.stats = {
            "trades_received": 0,
            "trades_per_second": 0.0,
            "connection_uptime": 0.0
        }
```

**功能**:
- 建立和维护WebSocket连接
- 订阅多个交易对的数据流
- 解析交易数据为标准化格式
- 自动重连和错误恢复
- 性能统计和监控

#### B. OrderAggregator
```python
class OrderAggregator:
    """5分钟滚动窗口聚合器"""
    def __init__(self, window_minutes: int = 5):
        self.window_size_ms = window_minutes * 60 * 1000
        self.data = defaultdict(list)  # {symbol: [trades]}
        self.lock = Lock()  # 线程安全
```

**功能**:
- 维护5分钟滚动时间窗口
- 按买卖方向分别聚合
- 智能去重和内存管理
- 实时计算总量和交易数
- 支持动态阈值更新

#### C. ThresholdEngine
```python
class ThresholdEngine:
    """阈值检测引擎"""
    def __init__(self, threshold_usd: float = 2_000_000, cooldown_minutes: int = 5):
        self.threshold_usd = threshold_usd
        self.cooldowns = {}  # {symbol: datetime}
        self.stats = {
            "threshold_checks": 0,
            "alerts_triggered": 0,
            "alerts_suppressed": 0
        }
```

**功能**:
- 检测聚合数据是否突破阈值
- 智能方向判断（买入/卖出/双向）
- 管理冷却时间防止重复告警
- 触发告警事件
- 统计数据和监控

#### D. AlertDispatcher
```python
class AlertDispatcher:
    """告警调度器"""
    def __init__(self, telegram_bot, rate_limit_per_minute: int = 12):
        self.telegram_bot = telegram_bot
        self.rate_limiter = RateLimiter(rate_limit_per_minute)
        self.alert_queue = asyncio.Queue()
```

**功能**:
- 格式化告警消息
- 管理告警队列
- 速率限制保护
- 异步分发到Telegram
- 失败重试机制

#### E. PriceConverter
```python
class PriceConverter:
    """USD转换器"""
    def __init__(self):
        self.supported_stablecoins = ["USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USDP"]
        self.cache = {}  # 缓存汇率
        self.cache_ttl = 60  # 60秒缓存
```

**功能**:
- 实时汇率获取
- 多稳定币支持
- 智能缓存机制
- 批量转换优化
- 错误处理和降级

---

## 🔄 核心工作流

### 1. WebSocket数据流
```
币安WebSocket → 解析交易数据 → 创建TradeEvent → 发送到聚合器
```

### 2. 聚合流程
```
接收TradeEvent → 转换USD → 添加到时间窗口 → 去旧数据 → 计算总量
```

### 3. 阈值检测
```
聚合数据 → 检查阈值 → 判断方向 → 检查冷却 → 触发告警
```

### 4. 告警分发
```
告警事件 → 格式化消息 → 速率限制 → 发送到Telegram → 记录统计
```

---

## 📈 性能指标

### 目标性能

| 指标 | 当前 | 目标 | 改进 |
|------|------|------|------|
| **CPU使用率** | 20% | 2% | ↓ 80% |
| **内存使用** | 200MB | 100MB | ↓ 50% |
| **响应延迟** | 10-15秒 | < 1秒 | ↓ 90% |
| **系统稳定性** | 95% | 99.5% | ↑ 4.5% |
| **数据准确性** | 95% | 99.9% | ↑ 4.9% |

### 监控交易对
```
BTC/USDT, ETH/USDT, BNB/USDT, ADA/USDT, XRP/USDT,
SOL/USDT, DOT/USDT, DOGE/USDT, MATIC/USDT, LTC/USDT,
AVAX/USDT, UNI/USDT, ATOM/USDT, LINK/USDT, ETC/USDT,
BCH/USDT, FIL/USDT, TRX/USDT, XLM/USDT, VET/USDT
```

### 告警示例
```markdown
[大额主动买入] BTC/USDT
━━━━━━━━━━━━━━━━━━━━
📊 金额：$2,500,000
📈 方向：主动买入
📉 买入量：$1,800,000
📈 卖出量：$700,000
🕐 时间：14:35:22
⏱️ 窗口：5分钟 (14:30-14:35)
🔢 交易数：23笔
━━━━━━━━━━━━━━━━━━━━
阈值：$2,000,000 | 交易所：Binance
```

---

## 🛠️ 技术实现细节

### 1. WebSocket管理
- **连接URL**: `wss://stream.binance.com:9443/ws`
- **订阅格式**: `{symbol}@trade` stream
- **心跳机制**: 每30秒发送ping
- **重连策略**: 指数退避 (2s → 5s → 10s → 30s → 60s)
- **最大重试**: 10次，失败后告警

### 2. 数据聚合
- **时间窗口**: 5分钟滚动窗口
- **去重策略**: 基于trade_id去重
- **内存管理**: 自动清理过期数据
- **线程安全**: 使用Lock保证并发安全

### 3. USD转换
- **价格源**: Binance REST API `/ticker/price`
- **缓存策略**: 60秒TTL，LRU缓存
- **稳定币识别**: 自动识别报价货币
- **降级方案**: 转换失败时使用缓存价格

### 4. 错误恢复
- **网络错误**: 自动重连，指数退避
- **API错误**: 记录日志，触发告警
- **数据错误**: 跳过异常数据，继续处理
- **系统错误**: 优雅降级，告警通知

### 5. 监控与告警
- **连接状态**: 实时监控WebSocket状态
- **性能统计**: 每秒交易数、CPU、内存
- **错误统计**: 连接失败、重连次数
- **管理员通知**: 系统异常时通知管理员

---

## 📋 依赖项

### 外部依赖
- **websockets**: WebSocket客户端库
- **asyncio**: 异步I/O框架
- **Binance REST API**: 价格查询
- **Telegram Bot API**: 消息发送

### 内部依赖
- **BaseAlertProcess**: 告警处理器基类
- **TelegramBot**: Telegram机器人实例
- **user_configuration**: 用户配置管理
- **logger**: 日志系统

### 系统要求
- **Python版本**: 3.8+
- **内存**: 最少512MB可用内存
- **网络**: 稳定的互联网连接
- **并发**: 支持异步I/O

---

## 🔒 安全考虑

### 1. 连接安全
- 使用WSS (WebSocket Secure) 加密连接
- 验证SSL证书有效性
- 连接超时保护 (30秒)

### 2. 数据验证
- 验证WebSocket消息格式
- 检查交易数据完整性
- 防止恶意数据注入

### 3. 速率限制
- WebSocket消息限流
- Telegram告警限流 (12条/分钟)
- 防止消息轰炸

### 4. 错误处理
- 不信任外部数据
- 优雅降级处理
- 记录详细错误日志

---

## 🧪 测试策略

### 1. 单元测试
- **WebSocket客户端**: 连接、订阅、消息解析
- **聚合器**: 数据聚合、时间窗口、内存管理
- **阈值引擎**: 阈值检测、冷却管理
- **告警调度**: 消息格式、速率限制
- **USD转换**: 汇率转换、缓存机制

### 2. 集成测试
- **端到端流程**: 从WebSocket到Telegram
- **并发测试**: 多交易对同时处理
- **性能测试**: 高频交易数据处理
- **错误恢复**: 网络中断、数据异常

### 3. 压力测试
- **大交易量**: 模拟20+交易对高并发
- **长时间运行**: 24小时连续运行
- **内存泄漏**: 监控内存使用趋势
- **稳定性**: 99.5%可用性验证

### 4. Mock测试
- **WebSocket**: 模拟币安WebSocket数据
- **REST API**: 模拟价格查询响应
- **Telegram**: 模拟消息发送
- **错误场景**: 网络中断、API失败

---

## 📦 部署方案

### 1. 环境变量
```bash
# WebSocket配置 (可选，默认使用生产环境)
BINANCE_WS_URL=wss://stream.binance.com:9443/ws

# 告警配置
LARGE_ORDER_THRESHOLD=2000000  # $2M USD
LARGE_ORDER_COOLDOWN=5          # 5分钟
LARGE_ORDER_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT  # 监控交易对

# 性能配置
MAX_WEBSOCKET_RECONNECT=10      # 最大重连次数
RATE_LIMIT_PER_MINUTE=12        # Telegram告警限流
```

### 2. 依赖安装
```bash
pip install websockets asyncio
```

### 3. 启动方式
```python
# 在__main__.py中启动
from src.alert_processes.large_order import get_large_order_monitor

# 创建并启动监控
monitor = await get_large_order_monitor()
await monitor.run()
```

### 4. 监控命令
```bash
# 查看监控状态
/large_order_status

# 查看监控交易对
/large_order_symbols

# 查看/清除告警（管理员）
/large_order_alerts

# 查看配置（管理员）
/large_order_config
```

---

## 🎯 验收标准

### 功能验收
- [ ] WebSocket成功连接币安数据流
- [ ] 正确聚合5分钟窗口内交易数据
- [ ] 准确检测$2,000,000阈值突破
- [ ] 正确判断交易方向（买入/卖出/双向）
- [ ] 5分钟冷却机制正常工作
- [ ] 告警消息格式正确
- [ ] USD转换准确无误
- [ ] 支持20+交易对监控

### 性能验收
- [ ] CPU使用率 < 5%
- [ ] 内存使用 < 150MB
- [ ] 响应延迟 < 2秒
- [ ] 系统可用性 > 99%
- [ ] 数据准确性 > 99.9%

### 稳定性验收
- [ ] 24小时连续运行无崩溃
- [ ] 网络中断自动恢复
- [ ] WebSocket重连机制有效
- [ ] 错误日志记录完整

### 兼容性验收
- [ ] Python 3.8+ 兼容
- [ ] 与现有告警系统共存
- [ ] 不影响其他告警功能
- [ ] 优雅关闭机制

---

## 📅 实施计划

### 阶段1: 核心基础设施 (5-7天)
1. 创建BinanceWebSocketClient类
2. 实现WebSocket连接和订阅
3. 实现数据解析和标准化
4. 添加错误恢复机制
5. 基础单元测试

### 阶段2: 聚合与检测 (7-10天)
1. 实现5分钟滚动窗口聚合器
2. 实现阈值检测引擎
3. 实现冷却管理机制
4. 实现USD转换功能
5. 性能优化和压力测试

### 阶段3: 告警与集成 (5-7天)
1. 实现告警调度器
2. 集成Telegram发送
3. 添加管理命令
4. 完善日志和监控
5. 端到端测试

### 阶段4: 测试与验证 (7-10天)
1. 全面的单元测试
2. 集成测试和压力测试
3. 性能基准测试
4. 稳定性验证
5. 文档完善

### 阶段5: 部署与文档 (3-5天)
1. 生产环境部署
2. 监控配置
3. 运行手册编写
4. 用户指南
5. 故障排除文档

**总预计时间**: 27-39天

---

## 🚀 未来扩展

### 短期扩展 (v3.3)
- [ ] 支持更多交易所 (OKX, Coinbase)
- [ ] 自定义阈值配置
- [ ] 告警历史查询
- [ ] 交易对白名单管理

### 中期扩展 (v4.0)
- [ ] 机器学习异常检测
- [ ] 多时间框架分析
- [ ] 交易量预测
- [ ] Web管理界面

### 长期扩展 (v4.5+)
- [ ] 链上数据集成
- [ ] DeFi协议监控
- [ ] 社交情绪分析
- [ ] 社区交易信号

---

## 📚 相关文档

- [币安WebSocket API文档](https://binance-docs.github.io/apidocs/spot/en/#trade-streams)
- [WebSockets库文档](https://websockets.readthedocs.io/)
- [项目整体架构](../CLAUDE.md)
- [告警处理器设计](../src/alert_processes/CLAUDE.md)

---

## 👥 贡献者

- **架构设计**: OpenSpec AI助手
- **实现**: 开发团队
- **测试**: QA团队
- **文档**: 技术写作团队

---

## 📝 变更日志

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|---------|------|
| 2025-11-10 | 1.0.0 | 初始提案创建 | OpenSpec |

---

**提案状态**: 🟡 待审核
**下一步**: 技术评审 → 架构设计 → 实施计划

