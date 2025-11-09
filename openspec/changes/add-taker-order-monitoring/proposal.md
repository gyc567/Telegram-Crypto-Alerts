# OpenSpec 变更提案：4.3.4 吃单监控 (Taker Order Monitoring)

## 📋 提案概览

**提案编号**: CHANGE-2025-0105
**创建日期**: 2025-11-09
**类型**: 功能增强 (Feature Enhancement)
**优先级**: 高 (High)
**状态**: 待审核 (Pending Review)

---

## 🎯 变更目标

实现吃单监控功能，追踪大额单笔吃单订单和累积吃单活动，提供及时的市场异常活动告警。

### 核心功能需求

1. **单笔订单监控**
   - BTC 单笔订单数量 ≥ 50 时触发告警
   - ETH 单笔订单数量 ≥ 2000 时触发告警
   - 区分主动买入和主动卖出

2. **累积监控**
   - 1分钟时间窗口内，美元价值 > $1,000,000 的吃单
   - 同一方向（买/卖）订单数量 ≥ 5 笔
   - 计算总金额和平均金额

3. **告警格式**
   ```
   [吃单监控] BTC/USDT
   时间范围: 14:35:00-14:36:00 (60秒)
   方向: 主动买入
   订单数: 7笔
   总金额: $1,250,000
   平均金额: $178,571
   ```

---

## 📊 当前状态 vs 目标状态

| 维度 | 当前状态 | 目标状态 |
|------|---------|---------|
| 监控范围 | 大额订单聚合（5分钟窗口） | 吃单监控（1分钟窗口） |
| 粒度 | 累积交易量 | 单笔订单 + 累积活动 |
| 交易对 | BTC/USDT, ETH/USDT, BNB/USDT | BTC/USDT, ETH/USDT |
| 阈值 | $2,000,000 USD | 单笔: 50 BTC / 2000 ETH<br>累积: $1,000,000 USD (≥5笔) |
| 时间窗口 | 5分钟 | 1分钟（累积监控） |
| 订单类型 | 市价单（主动/被动） | 吃单（taker_orders） |
| 冷却时间 | 10分钟 | 5分钟 |

---

## 🏗️ 技术架构

### 1. 数据源
- **Binance WebSocket**: 用户成交记录 (userDataStream)
- **Trade Events**: 实时交易数据
- **Order Type**: 过滤 taker orders (主动成交)

### 2. 核心组件

#### A. TakerOrderTracker
```python
class TakerOrderTracker:
    """吃单订单追踪器"""
    def __init__(self, symbols: List[str]):
        self.single_order_thresholds = {
            "BTCUSDT": 50,      # BTC数量
            "ETHUSDT": 2000     # ETH数量
        }
        self.cumulative_window = 60  # 1分钟窗口
        self.cumulative_threshold = 1000000  # $1M USD
        self.min_order_count = 5
```

#### B. OrderTypeClassifier
```python
class OrderTypeClassifier:
    """订单类型分类器"""
    def classify_taker_orders(self, trade_event: TradeEvent) -> bool:
        """判断是否为吃单（主动成交）"""
        # 逻辑：比较买单/卖单深度变化
        # 吃单：从深度表中移除流动性
        # 挂单：为深度表添加流动性
```

#### C. CumulativeAnalyzer
```python
class CumulativeAnalyzer:
    """累积分析器"""
    def __init__(self):
        self.time_windows = defaultdict(list)

    def add_trade(self, trade: TradeEvent):
        # 添加到1分钟滚动窗口
        # 聚合同方向订单
        # 检查是否达到 $1M USD + 5笔阈值
```

### 3. 与大额订单监控的差异

| 特性 | 大额订单监控 | 吃单监控 |
|------|-------------|---------|
| 监控对象 | 所有市价单 | 吃单（主动成交） |
| 数据粒度 | 累积交易量 | 单笔订单 + 累积活动 |
| 聚合窗口 | 5分钟 | 1分钟 |
| 区分度 | 买卖方向 | 吃单/挂单 + 买卖方向 |
| 应用场景 | 市场操纵检测 | 智能资金追踪 |

---

## 📝 实施计划

### 阶段1: 核心架构 (3-4天)
- [ ] 创建 TakerOrderTracker 类
- [ ] 实现 OrderTypeClassifier 分类器
- [ ] 集成到现有监控框架
- [ ] 单元测试 (TDD)

### 阶段2: 数据流处理 (2-3天)
- [ ] WebSocket 数据过滤（仅吃单）
- [ ] 单笔订单阈值检测
- [ ] 1分钟滚动窗口实现
- [ ] 累积聚合算法

### 阶段3: 告警系统 (2天)
- [ ] 告警消息格式化
- [ ] 冷却机制（5分钟）
- [ ] 集成到 Telegram 机器人
- [ ] 新增命令: `/taker_status`, `/taker_symbols`

### 阶段4: 测试与优化 (2天)
- [ ] 集成测试
- [ ] 性能测试（延迟 < 500ms）
- [ ] 误报率优化
- [ ] 文档更新

---

## 🔌 集成点

### 1. 与现有大额订单监控
```python
# src/monitor/large_orders/core/
class UnifiedMonitor:
    def __init__(self):
        self.large_order_monitor = LargeOrderMonitor()  # 5分钟窗口
        self.taker_monitor = TakerOrderMonitor()        # 1分钟窗口

    async def process_trade(self, trade: TradeEvent):
        # 并行处理两种监控
        await asyncio.gather(
            self.large_order_monitor.handle(trade),
            self.taker_monitor.handle(trade)
        )
```

### 2. 配置管理
```python
# src/config.py
TAKER_ORDER_CONFIG = {
    "single_thresholds": {
        "BTCUSDT": 50,      # BTC数量
        "ETHUSDT": 2000     # ETH数量
    },
    "cumulative_threshold": 1000000,  # $1M USD
    "min_order_count": 5,
    "window_size": 60,     # 1分钟
    "cooldown": 300        # 5分钟
}
```

### 3. Telegram 命令扩展
```
/taker_status     - 查看吃单监控状态
/taker_symbols    - 查看监控的交易对
/taker_alerts     - 查看吃单告警历史（管理员）
/taker_config     - 查看吃单监控配置（管理员）
```

---

## ⚠️ 风险评估

| 风险项 | 可能性 | 影响 | 缓解措施 |
|--------|--------|------|---------|
| WebSocket 性能瓶颈 | 中 | 高 | 事件驱动架构，异步处理 |
| 误报率过高 | 中 | 中 | 动态阈值调整，机器学习过滤 |
| 与现有监控冲突 | 低 | 中 | 独立实例，并行运行 |
| API 限流 | 中 | 中 | 请求聚合，指数退避 |
| 订单分类准确率 | 中 | 高 | 多重验证机制，回退策略 |

---

## 📈 预期收益

1. **市场洞察**
   - 识别智能资金动向
   - 检测大额吃单活动
   - 辅助交易决策

2. **技术价值**
   - 完善监控体系
   - 提供多维度数据
   - 增强用户体验

3. **商业价值**
   - 差异化功能
   - 提高用户粘性
   - 潜在付费增值服务

---

## 🧪 验收标准

### 功能性验收
- [ ] BTC 单笔订单 ≥ 50 触发告警
- [ ] ETH 单笔订单 ≥ 2000 触发告警
- [ ] 1分钟内吃单 ≥ $1M USD + ≥5笔触发告警
- [ ] 告警延迟 < 500ms
- [ ] 冷却机制生效（5分钟）

### 非功能性验收
- [ ] CPU 使用率 < 5%
- [ ] 内存使用 < 200MB
- [ ] 误报率 < 3%
- [ ] 告警送达率 = 100%
- [ ] 系统可用性 > 99.5%

### 测试验收
- [ ] 单元测试覆盖 > 90%
- [ ] 集成测试通过率 100%
- [ ] 性能测试达标
- [ ] 端到端测试验证

---

## 📚 相关文档

- [大额订单监控设计](src/monitor/large_orders/README.md)
- [WebSocket 集成指南](docs/websocket-integration.md)
- [告警系统文档](docs/alert-system.md)
- [性能优化指南](docs/performance-optimization.md)

---

## 👥 干系人

**发起人**: 项目所有者
**审核人**: 架构师、技术负责人
**实施人**: 开发团队
**测试人**: QA 团队
**运维人**: DevOps 团队

---

## 🔗 相关变更

- **依赖**: 大额订单监控系统 (CHANGE-2025-0104)
- **前置**: WebSocket 基础架构升级
- **后续**: 智能告警优化 (CHANGE-2025-0106)

---

*此提案基于 OpenSpec 规范驱动开发流程创建*
