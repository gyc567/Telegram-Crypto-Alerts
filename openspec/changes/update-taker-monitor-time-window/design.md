# 吃单监控时间窗口可配置化 - 设计文档

## 📋 概述

本文档详细说明吃单监控时间窗口从1分钟扩展到1小时并实现可配置的实施方案。

---

## 🎯 设计目标

1. **扩展时间窗口**: 从1分钟 → 1小时 (60分钟)
2. **可配置化**: 支持1-1440分钟任意配置
3. **性能优化**: 自适应批处理和内存管理
4. **用户友好**: Telegram命令管理配置

---

## 🏗️ 架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────┐
│                用户层                            │
│  ┌───────────────────────────────────────────┐  │
│  │          Telegram Bot                     │  │
│  │  - /taker_window set 60                  │  │
│  │  - /taker_window list                    │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│                配置管理层                        │
│  ┌───────────────────────────────────────────┐  │
│  │       TakerConfigManager                  │  │
│  │  - validate_window()                     │  │
│  │  - set_window_minutes()                  │  │
│  │  - get_window_options()                  │  │
│  └───────────────────────────────────────────┘  │
│           │                         │           │
│           ▼                         ▼           │
│  ┌──────────────┐         ┌──────────────┐      │
│  │  config.py   │         │   .env      │      │
│  │  (默认配置)   │         │  (持久化)    │      │
│  └──────────────┘         └──────────────┘      │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│                业务逻辑层                        │
│  ┌───────────────────────────────────────────┐  │
│  │        TimeWindowManager                  │  │
│  │  - update_window_size()                  │  │
│  │  - get_active_aggregator()               │  │
│  └───────────────────────────────────────────┘  │
│                       │                         │
│                       ▼                         │
│  ┌───────────────────────────────────────────┐  │
│  │         OrderAggregator                   │  │
│  │  - 自适应批处理大小                       │  │
│  │  - 智能清理间隔                           │  │
│  │  - 内存优化                               │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│                数据存储层                        │
│  ┌───────────────────────────────────────────┐  │
│  │          交易数据窗口                      │  │
│  │  - 热数据: 最近1小时 (内存)               │  │
│  │  - 温数据: 1-8小时 (缓存)                │  │
│  │  - 冷数据: 8-24小时 (磁盘)               │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 2. 关键组件

#### A. TakerConfigManager (配置管理器)
```python
class TakerConfigManager:
    """吃单监控配置管理器"""

    @staticmethod
    def get_window_minutes() -> int:
        """获取当前时间窗口"""
        return TAKER_CUMULATIVE_WINDOW_MINUTES

    @staticmethod
    def set_window_minutes(minutes: int, persist: bool = False) -> bool:
        """设置时间窗口"""
        if not TakerConfigManager.validate_window(minutes):
            return False

        # 更新内存中的配置
        import src.config as config
        config.TAKER_CUMULATIVE_WINDOW_MINUTES = minutes

        # 持久化到文件
        if persist:
            TakerConfigManager._persist_to_file(minutes)

        return True

    @staticmethod
    def validate_window(window_minutes: int) -> bool:
        """验证时间窗口是否合法"""
        return TAKER_MIN_WINDOW_MINUTES <= window_minutes <= TAKER_MAX_WINDOW_MINUTES
```

#### B. TimeWindowManager (窗口管理器)
```python
class TimeWindowManager:
    """时间窗口管理器"""

    def __init__(self):
        self.windows: Dict[int, OrderAggregator] = {}
        self.active_window = self._load_configured_window()
        self._initialize_windows()

    def update_window_size(self, new_window_minutes: int) -> bool:
        """动态更新时间窗口大小"""
        if not self._validate_window_size(new_window_minutes):
            return False

        old_window = self.active_window
        self.active_window = new_window_minutes

        # 创建新的聚合器
        self.windows[new_window_minutes] = OrderAggregator(
            window_minutes=new_window_minutes
        )

        # 清理旧的窗口
        if old_window not in [5, 15, 60]:  # 保留常用窗口
            del self.windows[old_window]

        return True
```

#### C. OrderAggregator (订单聚合器)
```python
class OrderAggregator:
    """订单聚合器 - 支持动态时间窗口"""

    def __init__(self, window_minutes: int = None):
        # 动态加载配置
        if window_minutes is None:
            from src.config import TAKER_CUMULATIVE_WINDOW_MINUTES
            window_minutes = TAKER_CUMULATIVE_WINDOW_MINUTES

        self.window_minutes = window_minutes
        self.window_ms = window_minutes * 60 * 1000

        # 自适应配置
        self.batch_size = self._calculate_batch_size()
        self.cleanup_interval = self._get_cleanup_interval()

    def _calculate_batch_size(self) -> int:
        """根据时间窗口大小动态计算批处理大小"""
        if self.window_minutes >= 240:  # 4小时以上
            return 10000
        elif self.window_minutes >= 60:  # 1小时以上
            return 5000
        elif self.window_minutes >= 15:  # 15分钟以上
            return 2000
        else:  # 15分钟以下
            return 1000
```

---

## 📊 数据流设计

### 1. 配置更新流程

```
用户输入
    ↓
/taker_window set 60
    ↓
Telegram命令处理器
    ↓
TakerConfigManager.validate_window(60)
    ↓
TakerConfigManager.set_window_minutes(60, persist=True)
    ↓
┌──────────────┬──────────────┐
│  更新内存    │  持久化到文件 │
│  配置       │  配置        │
└──────┬───────┴──────┬───────┘
       │              │
       ▼              ▼
  OrderAggregator  TimeWindowManager
  重新创建         更新活跃窗口
       │              │
       └──────┬───────┘
              ▼
         新配置生效
```

### 2. 交易处理流程

```
交易数据进入
    ↓
TimeWindowManager.get_active_aggregator()
    ↓
OrderAggregator.add_trade(trade)
    ↓
┌─────────────────────────────────────┐
│  1. 添加到对应交易对窗口              │
│  2. 检查单笔订单阈值                  │
│  3. 更新累积统计                      │
│  4. 检查窗口溢出                     │
│  5. 触发告警 (如果需要)              │
│  6. 批处理和优化                     │
└─────────────────────────────────────┘
    ↓
定期清理过期数据
    ↓
内存使用监控
```

---

## 💾 存储设计

### 1. 内存结构

```python
# 交易对 → 窗口条目队列
self.trade_windows: Dict[str, deque] = {
    "BTCUSDT": deque([
        WindowEntry(
            trade_event=TradeEvent(...),
            usd_value=100000.0,
            timestamp=2025-11-10 14:00:00,
            buy_volume=2.5,
            sell_volume=0
        ),
        ...
    ]),
    "ETHUSDT": deque([...])
}
```

### 2. 分层存储策略

| 数据类型 | 存储位置 | 保留时间 | 说明 |
|----------|----------|----------|------|
| **热数据** | 内存 (RAM) | 最近1小时 | 实时计算和查询 |
| **温数据** | 内存缓存 | 1-8小时 | 统计分析 |
| **冷数据** | 磁盘文件 | 8-24小时 | 历史归档 |
| **归档数据** | 压缩文件 | >24小时 | 长期保存 |

---

## ⚡ 性能优化设计

### 1. 批处理优化

```python
def process_trades_batch(self, trades: List[TradeEvent]):
    """批量处理交易数据"""

    # 1. 按交易对分组
    grouped_trades = self._group_by_symbol(trades)

    # 2. 批量处理每个交易对
    for symbol, symbol_trades in grouped_trades.items():
        # 2.1 批量添加
        self._add_trades_batch(symbol, symbol_trades)

        # 2.2 批量检查阈值
        if self._check_threshold_batch(symbol):
            # 2.3 触发告警
            self._trigger_alert_batch(symbol)

    # 3. 批量清理
    self._cleanup_batch()

    # 4. 更新统计
    self._update_stats_batch()
```

### 2. 内存管理

```python
def cleanup_expired(self):
    """智能清理过期数据"""

    current_time = time.time() * 1000
    cutoff_time = current_time - (self.window_ms * 2)  # 保留2个窗口

    for symbol in list(self.trade_windows.keys()):
        window = self.trade_windows[symbol]

        # 增量清理
        while window and window[0].timestamp < cutoff_time:
            window.popleft()

        # 释放空窗口
        if not window:
            del self.trade_windows[symbol]

    # 内存压力检测
    if self._check_memory_pressure():
        self._aggressive_cleanup()
```

---

## 🔐 安全设计

### 1. 输入验证

```python
def validate_window_size(window: int) -> bool:
    """严格验证时间窗口大小"""

    # 类型检查
    if not isinstance(window, int):
        return False

    # 范围检查
    if not (TAKER_MIN_WINDOW_MINUTES <= window <= TAKER_MAX_WINDOW_MINUTES):
        return False

    # 业务逻辑检查
    if window % 5 != 0:  # 要求是5的倍数
        return False

    return True
```

### 2. 权限控制

```python
@taker_message_handler(commands=["taker_window"])
@self.is_admin  # 仅管理员可执行
def on_taker_window_config(message):
    """管理吃单监控时间窗口 - 需要管理员权限"""
    # 权限检查已在装饰器中完成
    # 业务逻辑处理
    pass
```

### 3. 操作审计

```python
def set_window_minutes(minutes: int, persist: bool = False) -> bool:
    """设置时间窗口 - 记录操作日志"""

    if not self.validate_window(minutes):
        logger.error(f"Invalid window size attempted: {minutes}")
        return False

    # 记录操作审计日志
    logger.info(
        f"Taker window change: "
        f"user={message.from_user.id}, "
        f"old={self.get_window_minutes()}, "
        f"new={minutes}, "
        f"persist={persist}"
    )

    # 执行设置
    import src.config as config
    config.TAKER_CUMULATIVE_WINDOW_MINUTES = minutes

    if persist:
        self._persist_to_file(minutes)

    return True
```

---

## 📈 监控设计

### 1. 关键指标

```python
class TakerMetrics:
    """吃单监控指标"""

    def __init__(self):
        self.metrics = {
            # 配置指标
            "window_size_minutes": 0,
            "window_size_bytes": 0,

            # 性能指标
            "trade_count_total": 0,
            "trade_count_per_minute": 0,
            "window_hits_total": 0,
            "window_hit_rate": 0.0,

            # 内存指标
            "memory_usage_mb": 0,
            "memory_usage_trend": [],

            # 处理性能
            "batch_processing_time_avg": 0,
            "batch_processing_time_max": 0,
            "cleanup_operations": 0,

            # 错误指标
            "errors_total": 0,
            "errors_by_type": defaultdict(int)
        }
```

### 2. 告警规则

```python
ALERT_RULES = {
    "memory_high": {
        "condition": "memory_usage_mb > 1000",
        "severity": "warning",
        "message": "吃单监控内存使用过高: {memory_usage_mb}MB",
        "cooldown": 300  # 5分钟
    },

    "hit_rate_high": {
        "condition": "window_hit_rate > 0.1",
        "severity": "warning",
        "message": "吃单窗口溢出率过高: {window_hit_rate:.2%}",
        "cooldown": 300
    },

    "processing_slow": {
        "condition": "batch_processing_time_avg > 5000",
        "severity": "warning",
        "message": "吃单批处理耗时过长: {batch_processing_time_avg}ms",
        "cooldown": 300
    }
}
```

---

## 🧪 测试设计

### 1. 测试策略

```
单元测试 (90%覆盖率)
    │
    ├── 配置测试
    │   ├── test_config_loading()
    │   ├── test_config_validation()
    │   └── test_config_update()
    │
    ├── 组件测试
    │   ├── test_order_aggregator()
    │   ├── test_time_window_manager()
    │   └── test_taker_config_manager()
    │
    └── 命令测试
        ├── test_taker_window_command()
        ├── test_set_window_command()
        └── test_list_window_command()

集成测试
    │
    ├── test_end_to_end_window_update()
    ├── test_memory_usage_1_hour()
    └── test_performance_batch_processing()

性能测试
    │
    ├── test_memory_benchmark()
    ├── test_cpu_benchmark()
    ├── test_throughput_benchmark()
    └── test_long_running_stability()
```

### 2. 基准测试

```python
def test_memory_benchmark():
    """内存使用基准测试"""

    # 测试不同时间窗口的内存使用
    test_cases = [
        (60, 60000, 300),    # 1小时窗口, 6万笔交易
        (240, 240000, 1200), # 4小时窗口, 24万笔交易
    ]

    for window_minutes, trade_count, expected_memory_mb in test_cases:
        # 创建聚合器
        aggregator = OrderAggregator(window_minutes=window_minutes)

        # 模拟交易
        for i in range(trade_count):
            trade = create_test_trade()
            aggregator.add_trade(trade)

        # 测量内存
        actual_memory_mb = measure_memory_usage(aggregator)

        # 验证
        assert actual_memory_mb <= expected_memory_mb * 1.2, \
            f"内存使用超标: {actual_memory_mb}MB > {expected_memory_mb}MB"
```

---

## 🔄 部署设计

### 1. 灰度部署策略

```
阶段1: 开发环境 (Day 1-2)
    ↓
阶段2: 测试环境 (Day 3-4)
    ↓
阶段3: 预生产环境 (Day 5)
    ↓
阶段4: 生产环境灰度 (Day 6)
    ├── 10% 用户
    ├── 50% 用户
    └── 100% 用户
    ↓
阶段5: 监控和优化 (Day 7)
```

### 2. 回滚策略

```python
# 回滚脚本示例
#!/bin/bash

echo "开始回滚吃单监控时间窗口配置..."

# 1. 停止服务
sudo systemctl stop telegram-bot

# 2. 恢复配置文件
cp /backup/config.py.backup /path/to/src/config.py

# 3. 清理缓存
rm -rf /var/cache/taker_monitor/*

# 4. 重启服务
sudo systemctl start telegram-bot

# 5. 验证服务
curl -f http://localhost:8080/health || exit 1

echo "回滚完成"
```

---

## 📚 相关文档

- **OpenSpec 提案**: [proposal.md](proposal.md)
- **任务清单**: [tasks.md](tasks.md)
- **技术规格**: [specs/enhancement/spec.md](specs/enhancement/spec.md)
- **性能优化**: [docs/performance-optimization.md](docs/performance-optimization.md)
- **监控指南**: [docs/monitoring.md](docs/monitoring.md)

---

**文档版本**: 1.0.0
**最后更新**: 2025-11-10
**作者**: OpenSpec AI助手
