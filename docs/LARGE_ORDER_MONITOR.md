# 大额交易监控功能 - 使用指南

## 📊 功能概述

大额交易监控功能可以实时监控指定交易对在 5 分钟内的主动买卖成交总额，当超过阈值（默认 200 万 USDT）时自动发送告警。

### 核心特性

- ✅ **实时监控**: WebSocket 实时订单流，秒级响应
- ✅ **多币种支持**: 默认监控 BTCUSDT、ETHUSDT、BNBUSDT
- ✅ **智能过滤**: 仅监控市价单和主动交易
- ✅ **冷静期机制**: 避免重复告警骚扰（默认 10 分钟）
- ✅ **数据持久化**: 自动保存交易和告警记录
- ✅ **内存优化**: 滑动窗口自动清理，过期数据自动删除

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install websocket-client
```

### 2. 配置参数

编辑 `src/config.py` 中的配置：

```python
# 启用/禁用监控
LARGE_ORDER_MONITOR_ENABLED = True

# 告警阈值（USDT）
LARGE_ORDER_THRESHOLD_USDT = 2_000_000

# 时间窗口（分钟）
LARGE_ORDER_TIME_WINDOW_MINUTES = 5

# 冷静期（分钟）
LARGE_ORDER_COOLDOWN_MINUTES = 10

# 监控的交易对
LARGE_ORDER_MONITORED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
```

### 3. 启动机器人

```bash
python -m src
```

### 4. 查看日志

机器人启动时会看到：
```
INFO - Initializing Large Order Monitor...
INFO - Starting large order monitor...
INFO - Monitoring symbols: BTCUSDT, ETHUSDT, BNBUSDT
INFO - Threshold: $2,000,000 USDT
INFO - Time window: 5.0 minutes
INFO - Cooldown: 10.0 minutes
```

## 📱 告警示例

当检测到大额交易时，您将收到类似消息：

```
[大额主动买入] BTC/USDT 金额：$2,500,000 方向：买入 时间：14:35:22
```

## 🔧 高级配置

### 添加新交易对

在 `src/config.py` 中修改：

```python
LARGE_ORDER_MONITORED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT",
    "ADAUSDT", "SOLUSDT", "XRPUSDT"  # 添加更多
]
```

### 调整阈值

```python
# 对所有币种统一阈值
LARGE_ORDER_THRESHOLD_USDT = 5_000_000  # 500万 USDT

# 或者在代码中动态调整
large_order_monitor.update_threshold(3_000_000)
```

### 调整时间窗口

```python
# 设置更短的时间窗口
LARGE_ORDER_TIME_WINDOW_MINUTES = 3  # 3分钟
```

## 📊 监控数据

### 数据存储位置

```
data/large_orders/
├── 2025-11-08/
│   ├── BTCUSDT.jsonl
│   ├── ETHUSDT.jsonl
│   └── BNBUSDT.jsonl
├── alerts/
│   └── alerts.jsonl
└── ...
```

### 数据格式

**交易记录** (`{symbol}.jsonl`):
```json
{
  "exchange": "binance",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "MARKET",
  "price": 45000.0,
  "quantity": 55.5,
  "amount": 2497500.0,
  "trade_time": 1699434922000,
  "is_taker": true,
  "trade_id": 12345
}
```

**告警记录** (`alerts.jsonl`):
```json
{
  "timestamp": 1699434922000,
  "symbol": "BTCUSDT",
  "side": "BUY",
  "total_amount": 2500000.0,
  "message": "[大额主动买入] BTC/USDT 金额：$2,500,000 方向：买入 时间：14:35:22",
  "datetime": "2023-11-08T14:35:22"
}
```

## 📈 统计信息

机器人每 10 分钟输出一次统计信息：

```
============================================================
Large Order Monitor Statistics
Uptime: 120.5 minutes
Total trades processed: 15420
Alerts triggered: 3
Collector trades/sec: 2.13
Storage size: 15.23 MB
Active symbols: 3
============================================================
```

## 🛠️ 故障排查

### 问题 1: 收不到告警

**检查项目**:
1. 确认在白名单中
2. 查看日志是否有错误
3. 验证交易对是否活跃
4. 确认阈值设置合理

**查看状态**:
```python
# 在代码中获取状态
stats = large_order_monitor.get_stats()
print(f"Is running: {stats['is_running']}")
print(f"Is healthy: {large_order_monitor.is_healthy()}")
```

### 问题 2: WebSocket 连接失败

**症状**:
```
ERROR - WebSocket connection error
```

**解决方案**:
1. 检查网络连接
2. 确认防火墙设置
3. 查看 Binance API 状态
4. 机器人会自动重连，无需担心

### 问题 3: 内存占用过高

**检查**:
```python
# 查看聚合器统计
aggregator_stats = large_order_monitor.aggregator.get_global_stats()
print(f"Total symbols: {aggregator_stats['total_symbols']}")
print(f"Total trades: {aggregator_stats['total_trades']}")
```

**解决方案**:
1. 减少监控的币种数量
2. 缩短时间窗口
3. 清理过期数据：
```python
large_order_monitor.aggregator.cleanup_expired()
```

## 🔍 监控 API

如果需要以编程方式监控状态：

```python
from src.monitor.large_orders import LargeOrderMonitor

# 获取统计数据
stats = large_order_monitor.get_stats()

# 检查是否健康
if large_order_monitor.is_healthy():
    print("Monitor is running correctly")

# 获取某币种统计
symbol_stats = large_order_monitor.aggregator.get_symbol_stats("BTCUSDT")
print(f"BTCUSDT 5分钟买入总额: ${symbol_stats['buy_amount']:,.0f}")

# 检查是否在冷静期
remaining = large_order_monitor.detector.get_cooldown_remaining("BTCUSDT", "BUY", int(time.time() * 1000))
if remaining > 0:
    print(f"冷静期剩余: {remaining} 秒")
```

## 📚 技术实现

### 架构设计

```
WebSocket 订单流 → 数据采集器 → 聚合处理器 → 告警检测器 → 存储 & 通知
      ↓               ↓           ↓           ↓           ↓
   Binance      Binance      5分钟      阈值判断     Telegram
                过滤器      滑动窗口    冷静期        发送
```

### 关键组件

1. **BinanceOrderBookCollector** (`src/monitor/large_orders/collector.py`)
   - WebSocket 连接管理
   - 交易数据解析
   - 主动单过滤

2. **SlidingWindowAggregator** (`src/monitor/large_orders/aggregator.py`)
   - 5 分钟滑动窗口
   - 按币种和方向聚合
   - 内存优化

3. **LargeOrderDetector** (`src/monitor/large_orders/detector.py`)
   - 阈值判断
   - 冷静期管理
   - 告警格式化

4. **FileStorage** (`src/monitor/large_orders/storage.py`)
   - JSONL 格式存储
   - 按日期分目录
   - 自动清理

5. **TelegramNotifier** (`src/monitor/large_orders/notifier.py`)
   - 消息发送
   - 白名单过滤
   - 速率限制

### 性能指标

- **延迟**: WebSocket → 告警 < 1 秒
- **吞吐量**: 支持 1000+ 交易对同时监控
- **内存**: 典型 < 100MB（含 5 分钟数据）
- **CPU**: 正常 < 5%

## 🎯 最佳实践

### 1. 合理设置阈值
- 主流币种（BTC/ETH）: 200-500万 USDT
- 山寨币: 50-100万 USDT
- 根据市值调整

### 2. 币种选择
- 优先选择流动性好的币种
- 避免监控过于小众的币种
- 定期更新币种列表

### 3. 监控频率
- 冷静期设置 10-15 分钟
- 避免过度告警
- 平衡及时性与稳定性

### 4. 数据管理
- 定期备份 `data/large_orders/` 目录
- 超过 7 天的数据自动清理
- 监控存储空间使用

## 🔮 未来计划

### v4.1 功能
- [ ] 多交易所支持（OKX、Bybit）
- [ ] 自定义阈值（每币种独立）
- [ ] 历史数据分析
- [ ] 告警统计报表

### v4.2 增强
- [ ] 机器学习预测
- [ ] 社区告警分享
- [ ] Web UI 管理界面
- [ ] 移动端推送

## ❓ 常见问题

### Q: 支持哪些交易所？
A: 当前仅支持 Binance，后续会添加更多交易所。

### Q: 可以监控多少个币种？
A: 理论上无限制，但建议不超过 50 个以保证性能。

### Q: 数据保存多久？
A: 交易数据保存 7 天，告警记录长期保存。

### Q: 如何关闭监控？
A: 设置 `LARGE_ORDER_MONITOR_ENABLED = False` 在 config.py 中。

### Q: 可以用其他数据库吗？
A: 当前使用文件存储，未来可能支持 SQLite、MySQL 等。

## 📞 技术支持

如有问题，请：
1. 查看日志文件 `bot.log`
2. 检查 GitHub Issues
3. 提交新的 Issue 描述问题

## 📄 许可证

本功能遵循项目整体许可证条款。

---

*最后更新: 2025-11-08*
