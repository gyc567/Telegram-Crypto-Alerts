# OpenSpec 变更提案：吃单监控时间窗口可配置化 (1小时窗口)

## 📋 提案概览

**提案编号**: CHANGE-2025-0106
**创建日期**: 2025-11-10
**类型**: 功能增强 (Feature Enhancement)
**优先级**: 高 (High)
**状态**: 🔴 待审核 (Pending Review)

---

## 🎯 变更目标

将吃单监控的累积时间窗口从 **1分钟** 更新为 **1小时**，并实现**完全可配置**，允许管理员根据需要调整时间窗口大小。

### 核心需求

1. **时间窗口扩展**
   - 当前：1分钟滚动窗口（根据OpenSpec 4.3.4提案）
   - 目标：1小时滚动窗口（60分钟）
   - 用途：捕获更长周期的吃单活动模式

2. **配置化管理**
   - 通过 `src/config.py` 配置时间窗口
   - 支持运行时动态调整
   - 支持Telegram命令管理

3. **兼容性保障**
   - 不影响现有大额订单监控（5分钟窗口）
   - 不影响单笔订单监控
   - 保持独立配置

---

## 📊 当前状态 vs 目标状态

| 维度 | 当前状态 | 目标状态 |
|------|---------|---------|
| **累积窗口** | 1分钟固定 | 1小时可配置 (默认) |
| **配置位置** | 硬编码在代码中 | `src/config.py` 统一管理 |
| **动态调整** | 不支持 | 支持运行时调整 |
| **命令管理** | 无 | `/taker_window` 管理命令 |
| **告警格式** | "60秒" | "1小时" (或自定义) |
| **数据保留** | 短期 | 中期 (1-2小时) |
| **性能影响** | 轻量 | 中等 (需优化) |

---

## 🏗️ 技术架构

### 1. 配置结构设计

#### A. 新增配置项
```python
# src/config.py
# ==================== 吃单监控配置 ====================

# 累积时间窗口配置
TAKER_CUMULATIVE_WINDOW_MINUTES = 60  # 默认1小时 (60分钟)

# 可选配置选项
TAKER_WINDOW_OPTIONS = [5, 15, 30, 60, 120, 240]  # 支持的时间窗口选项 (分钟)
TAKER_MIN_WINDOW_MINUTES = 1  # 最小窗口
TAKER_MAX_WINDOW_MINUTES = 1440  # 最大窗口 (24小时)

# 性能相关
TAKER_CLEANUP_INTERVAL_SECONDS = 300  # 清理间隔 (5分钟)
TAKER_MAX_RETENTION_MINUTES = 1440  # 数据保留最大时间 (24小时)
```

#### B. 统一配置管理
```python
# src/config.py - 完整配置
TAKER_ORDER_CONFIG = {
    # 单笔订单监控
    "single_thresholds": {
        "BTCUSDT": 50,      # BTC数量
        "ETHUSDT": 2000     # ETH数量
    },
    # 累积监控
    "cumulative": {
        "window_minutes": 60,        # 时间窗口 (新配置)
        "threshold_usd": 1_000_000,  # $1M USD阈值
        "min_order_count": 5,        # 最小订单数
        "cooldown_minutes": 5        # 冷却时间
    },
    # 性能配置
    "performance": {
        "cleanup_interval": 300,     # 清理间隔(秒)
        "max_retention": 1440,       # 最大保留时间(分钟)
        "batch_size": 1000           # 批处理大小
    }
}
```

### 2. 核心组件修改

#### A. OrderAggregator 增强
```python
# src/monitor/large_orders/core/order_aggregator.py
class OrderAggregator:
    def __init__(
        self,
        window_minutes: int = None,  # None表示使用配置默认值
        threshold_usd: float = 2_000_000
    ):
        # 动态加载配置
        if window_minutes is None:
            from src.config import TAKER_CUMULATIVE_WINDOW_MINUTES
            window_minutes = TAKER_CUMULATIVE_WINDOW_MINUTES

        self.window_minutes = window_minutes
        self.window_ms = window_minutes * 60 * 1000
        self.threshold_usd = threshold_usd

        # 自适应批量处理
        self.batch_size = self._calculate_batch_size()
        self.cleanup_interval = self._get_cleanup_interval()

    def _calculate_batch_size(self) -> int:
        """根据时间窗口大小动态计算批处理大小"""
        if self.window_minutes >= 60:
            return 5000  # 1小时窗口使用更大的批处理
        elif self.window_minutes >= 15:
            return 2000
        else:
            return 1000

    def _get_cleanup_interval(self) -> int:
        """获取自适应清理间隔"""
        if self.window_minutes >= 60:
            return 300  # 5分钟清理一次
        elif self.window_minutes >= 15:
            return 120  # 2分钟清理一次
        else:
            return 60   # 1分钟清理一次
```

#### B. 新型时间窗口管理器
```python
# src/monitor/large_orders/core/time_window_manager.py
class TimeWindowManager:
    """
    时间窗口管理器
    负责管理多时间窗口的吃单监控
    """

    def __init__(self):
        self.windows: Dict[int, OrderAggregator] = {}
        self.active_window = self._load_configured_window()
        self._initialize_windows()

    def _load_configured_window(self) -> int:
        """加载配置的时间窗口"""
        from src.config import TAKER_CUMULATIVE_WINDOW_MINUTES
        return TAKER_CUMULATIVE_WINDOW_MINUTES

    def update_window_size(self, new_window_minutes: int) -> bool:
        """动态更新时间窗口大小"""
        if self._validate_window_size(new_window_minutes):
            self.active_window = new_window_minutes
            self._reinitialize_windows()
            return True
        return False

    def _validate_window_size(self, window: int) -> bool:
        """验证时间窗口大小是否合法"""
        from src.config import TAKER_MIN_WINDOW_MINUTES, TAKER_MAX_WINDOW_MINUTES
        return TAKER_MIN_WINDOW_MINUTES <= window <= TAKER_MAX_WINDOW_MINUTES
```

### 3. Telegram 命令扩展

#### A. 新增命令
```python
# src/telegram.py

@taker_message_handler(commands=["taker_window"])
@self.is_admin
def on_taker_window_config(message):
    """管理吃单监控时间窗口"""
    splt_msg = self.split_message(message.text)

    if len(splt_msg) == 0:
        # 显示当前配置
        show_current_window_config(message)
    elif splt_msg[0].lower() == "set":
        # 设置新窗口
        new_window = int(splt_msg[1])
        if set_taker_window(new_window):
            self.reply_to(message, f"✅ 吃单监控窗口已更新为 {new_window} 分钟")
        else:
            self.reply_to(message, f"❌ 设置失败：无效的窗口大小")
    elif splt_msg[0].lower() == "list":
        # 列出可用选项
        show_window_options(message)
    else:
        self.reply_to(message, "用法: /taker_window [set/list]")
```

#### B. 命令格式
```
/taker_window                # 查看当前配置
/taker_window set 60         # 设置为60分钟
/taker_window set 120        # 设置为2小时
/taker_window list           # 列出所有可用选项
```

---

## 📝 实施计划

### 阶段1: 配置系统设计 (1天)
- [ ] 在 `src/config.py` 中添加吃单监控时间窗口配置
- [ ] 设计配置验证机制
- [ ] 创建配置管理工具函数
- [ ] 单元测试 (配置加载、验证)

### 阶段2: 核心组件改造 (2天)
- [ ] 修改 `OrderAggregator` 支持动态时间窗口
- [ ] 实现 `TimeWindowManager` 管理器
- [ ] 优化内存管理和数据清理
- [ ] 性能测试 (内存、CPU)

### 阶段3: Telegram 命令 (1天)
- [ ] 实现 `/taker_window` 命令
- [ ] 添加配置验证和错误处理
- [ ] 集成到机器人命令系统
- [ ] 文档更新

### 阶段4: 测试与优化 (2天)
- [ ] 集成测试 (端到端)
- [ ] 性能基准测试
- [ ] 内存泄漏检测
- [ ] 用户验收测试

### 阶段5: 部署与监控 (1天)
- [ ] 灰度部署
- [ ] 监控告警配置
- [ ] 回滚方案准备
- [ ] 文档和培训

**总预计时间**: 7天

---

## 🔌 集成点

### 1. 与现有监控系统
```python
# src/monitor/large_orders/monitor.py
class LargeOrderMonitor:
    def __init__(self):
        # 大额订单监控 (5分钟窗口)
        self.large_order_aggregator = OrderAggregator(window_minutes=5)

        # 吃单监控 (1小时窗口，可配置)
        self.taker_aggregator = OrderAggregator(window_minutes=None)  # 使用配置默认值

    async def process_trade(self, trade: TradeEvent):
        # 并行处理
        await asyncio.gather(
            self.large_order_aggregator.add_trade(trade),
            self.taker_aggregator.add_trade(trade)
        )
```

### 2. 配置热更新
```python
# src/config.py
class TakerConfig:
    """吃单监控配置管理器"""

    @staticmethod
    def get_window_minutes() -> int:
        """获取当前时间窗口（支持运行时更新）"""
        # TODO: 从Redis或数据库加载，支持热更新
        return TAKER_CUMULATIVE_WINDOW_MINUTES

    @staticmethod
    def set_window_minutes(minutes: int) -> bool:
        """设置时间窗口（需重启或热更新）"""
        if not TakerConfig._validate_window(minutes):
            return False
        # TODO: 更新配置并通知所有实例
        return True
```

### 3. 监控指标
```python
# src/monitor/metrics.py
class TakerMonitorMetrics:
    """吃单监控指标"""

    def __init__(self):
        self.window_size = self._load_window_size()
        self.trade_count = 0
        self.window_hits = 0
        self.memory_usage = 0

    def record_trade(self, trade):
        self.trade_count += 1
        if self._is_window_full(trade.timestamp):
            self.window_hits += 1
```

---

## ⚠️ 风险评估

| 风险项 | 可能性 | 影响 | 缓解措施 |
|--------|--------|------|----------|
| **内存使用增加** | 高 | 高 | 优化数据结构和清理机制 |
| **性能下降** | 中 | 中 | 批处理和异步优化 |
| **配置错误** | 中 | 中 | 严格的配置验证和回滚 |
| **向后兼容性** | 低 | 中 | 保持API兼容，添加弃用警告 |
| **数据丢失** | 低 | 高 | 持久化存储和备份机制 |

---

## 📈 性能影响分析

### 内存使用估算

| 时间窗口 | 数据保留 | 预估内存 | 交易对数 | 备注 |
|----------|----------|---------|---------|------|
| 1分钟 | 2分钟 | ~5MB | BTC/ETH | 当前状态 |
| 15分钟 | 30分钟 | ~50MB | BTC/ETH | 轻量级 |
| 60分钟 | 2小时 | ~200MB | BTC/ETH | 可接受 |
| 240分钟 | 8小时 | ~800MB | BTC/ETH | 重度，需优化 |

### 性能优化策略

1. **分层存储**
   - 热数据: 最近1小时 (内存)
   - 温数据: 1-8小时 (内存缓存)
   - 冷数据: 8-24小时 (磁盘)

2. **批处理优化**
   - 1小时窗口: 批处理大小5000
   - 定期批量计算而非逐个计算
   - 使用numpy向量化操作

3. **智能清理**
   - 增量清理 (仅清理过期数据)
   - 定期全量清理
   - 内存压力检测和自动清理

---

## 🧪 验收标准

### 功能性验收
- [ ] 时间窗口可配置（1-1440分钟）
- [ ] `/taker_window set <minutes>` 命令正常工作
- [ ] 1小时窗口下告警正常触发
- [ ] 配置验证和错误处理正常
- [ ] 向后兼容 (保持现有功能)

### 非功能性验收
- [ ] 内存使用 < 500MB (1小时窗口)
- [ ] CPU使用率 < 10%
- [ ] 告警延迟 < 2秒
- [ ] 批量处理性能: 5000条/秒
- [ ] 系统可用性 > 99%

### 测试验收
- [ ] 单元测试覆盖 > 90%
- [ ] 集成测试: 所有命令正常
- [ ] 性能测试: 1小时窗口基准
- [ ] 压力测试: 10000 TPS
- [ ] 故障恢复测试

---

## 📊 监控指标

### 关键指标
```python
# 监控仪表板指标
METRICS = {
    "taker_window_size_minutes": "当前时间窗口大小",
    "taker_trade_count": "吃单交易总数",
    "taker_window_hits": "窗口溢出次数",
    "taker_memory_usage_mb": "内存使用(MB)",
    "taker_cleanup_count": "清理操作次数",
    "taker_batch_processing_time": "批处理耗时(ms)"
}
```

### 告警阈值
- 内存使用 > 1GB: 警告
- CPU使用率 > 20%: 警告
- 窗口溢出率 > 10%: 警告
- 批处理耗时 > 5s: 警告

---

## 📚 相关文档

- [OpenSpec 4.3.4 吃单监控提案](openspec/changes/add-taker-order-monitoring/)
- [大额订单监控设计](docs/large-order-monitor.md)
- [配置管理指南](docs/configuration-management.md)
- [性能优化指南](docs/performance-optimization.md)
- [Telegram 命令扩展](docs/telegram-commands.md)

---

## 👥 干系人

**发起人**: 项目所有者
**审核人**: 架构师、技术负责人
**实施人**: 开发团队
**测试人**: QA 团队
**运维人**: DevOps 团队

---

## 🔗 相关变更

- **前置**: OpenSpec 4.3.4 吃单监控基础实现 (CHANGE-2025-0105)
- **依赖**: 大额订单监控系统 (CHANGE-2025-0104)
- **后续**: 智能告警优化 (CHANGE-2025-0107)
- **相关**: 配置管理系统升级 (CHANGE-2025-0108)

---

## 💰 成本估算

| 成本项 | 人天 | 备注 |
|--------|------|------|
| 开发成本 | 5人天 | 核心功能开发 |
| 测试成本 | 2人天 | 功能 + 性能测试 |
| 部署成本 | 1人天 | 灰度 + 监控 |
| 运维成本 | 1人天 | 培训 + 文档 |
| **总成本** | **9人天** | |

### ROI 分析
- **开发成本**: 9人天
- **预期收益**: 提升用户体验，支持更长时间周期的市场分析
- **长期价值**: 增强系统可配置性和扩展性
- **投资回报期**: 2-3个月

---

*此提案基于 OpenSpec 规范驱动开发流程创建*
