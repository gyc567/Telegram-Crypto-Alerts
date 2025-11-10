# OpenSpec 技术规格：吃单监控时间窗口可配置化

## 📋 规格概览

**规格编号**: SPEC-2025-0106
**版本**: 1.0.0
**创建日期**: 2025-11-10
**类型**: 功能增强规格
**状态**: 🔴 待实施

---

## 🎯 规格目标

实现吃单监控时间窗口的可配置化管理，将默认时间窗口从1分钟扩展到1小时，支持1-1440分钟任意配置。

---

## 📐 技术规范

### 修改位置

#### 1. 新增配置项
**文件**: `src/config.py`

**新增内容**:
```python
# ==================== 吃单监控配置 ====================

# 累积时间窗口配置
TAKER_CUMULATIVE_WINDOW_MINUTES = 60  # 默认1小时 (60分钟)

# 可选配置选项
TAKER_WINDOW_OPTIONS = [5, 15, 30, 60, 120, 240]  # 支持的时间窗口选项(分钟)
TAKER_MIN_WINDOW_MINUTES = 1  # 最小窗口
TAKER_MAX_WINDOW_MINUTES = 1440  # 最大窗口 (24小时)

# 性能相关
TAKER_CLEANUP_INTERVAL_SECONDS = 300  # 清理间隔 (5分钟)
TAKER_MAX_RETENTION_MINUTES = 1440  # 数据保留最大时间 (24小时)

# 完整配置结构
TAKER_ORDER_CONFIG = {
    # 单笔订单监控
    "single_thresholds": {
        "BTCUSDT": 50,      # BTC数量
        "ETHUSDT": 2000     # ETH数量
    },
    # 累积监控
    "cumulative": {
        "window_minutes": 60,        # 时间窗口
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

#### 2. 修改 OrderAggregator
**文件**: `src/monitor/large_orders/core/order_aggregator.py`

**关键修改**:
```python
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

        # 验证窗口大小
        if not self._validate_window(window_minutes):
            raise ValueError(f"Invalid window size: {window_minutes}")

        self.window_minutes = window_minutes
        self.threshold_usd = threshold_usd
        self.window_ms = window_minutes * 60 * 1000

        # 自适应配置
        self.batch_size = self._calculate_batch_size()
        self.cleanup_interval = self._get_cleanup_interval()

        # 交易对 → 窗口条目队列
        self.trade_windows: Dict[str, deque] = {}
        self.stats = {
            "total_trades": 0,
            "window_calculations": 0,
            "window_resets": 0,
            "cleanup_operations": 0,
            "batch_processing_time": 0
        }

    def _validate_window(self, window_minutes: int) -> bool:
        """验证时间窗口大小是否合法"""
        from src.config import TAKER_MIN_WINDOW_MINUTES, TAKER_MAX_WINDOW_MINUTES
        return TAKER_MIN_WINDOW_MINUTES <= window_minutes <= TAKER_MAX_WINDOW_MINUTES

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

    def _get_cleanup_interval(self) -> int:
        """获取自适应清理间隔"""
        if self.window_minutes >= 240:
            return 600  # 10分钟
        elif self.window_minutes >= 60:
            return 300  # 5分钟
        elif self.window_minutes >= 15:
            return 120  # 2分钟
        else:
            return 60   # 1分钟
```

#### 3. 新增 TimeWindowManager
**文件**: `src/monitor/large_orders/core/time_window_manager.py`

**新内容**:
```python
from typing import Dict, Optional
from .order_aggregator import OrderAggregator

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

    def _initialize_windows(self):
        """初始化默认窗口"""
        default_window = self._load_configured_window()
        if default_window not in self.windows:
            self.windows[default_window] = OrderAggregator(window_minutes=default_window)

    def update_window_size(self, new_window_minutes: int) -> bool:
        """动态更新时间窗口大小"""
        if not self._validate_window_size(new_window_minutes):
            return False

        old_window = self.active_window
        self.active_window = new_window_minutes

        # 创建新的聚合器
        self.windows[new_window_minutes] = OrderAggregator(window_minutes=new_window_minutes)

        # 清理旧的窗口 (如果不再需要)
        if old_window not in [5, 15, 60]:  # 保留常用窗口
            del self.windows[old_window]

        return True

    def _validate_window_size(self, window: int) -> bool:
        """验证时间窗口大小是否合法"""
        from src.config import TAKER_MIN_WINDOW_MINUTES, TAKER_MAX_WINDOW_MINUTES
        return TAKER_MIN_WINDOW_MINUTES <= window <= TAKER_MAX_WINDOW_MINUTES

    def get_active_aggregator(self) -> OrderAggregator:
        """获取当前活跃的聚合器"""
        return self.windows[self.active_window]

    def get_window_summary(self) -> Dict:
        """获取当前窗口摘要"""
        aggregator = self.get_active_aggregator()
        return {
            "active_window_minutes": self.active_window,
            "trade_count": aggregator.stats["total_trades"],
            "window_hits": aggregator.stats["window_calculations"],
            "memory_usage_mb": self._estimate_memory_usage(),
            "batch_size": aggregator.batch_size,
            "cleanup_interval": aggregator.cleanup_interval
        }

    def _estimate_memory_usage(self) -> float:
        """估算当前内存使用 (MB)"""
        # 简化估算: 每1000个交易约占用1MB
        total_trades = sum(
            len(window.trade_windows.get(symbol, []))
            for window in self.windows.values()
            for symbol in window.trade_windows
        )
        return total_trades / 1000
```

#### 4. 新增配置管理模块
**文件**: `src/config/taker_config.py`

**新内容**:
```python
"""
吃单监控配置管理模块
负责配置加载、验证和管理
"""

from typing import Optional, List
import logging

from src.config import (
    TAKER_CUMULATIVE_WINDOW_MINUTES,
    TAKER_WINDOW_OPTIONS,
    TAKER_MIN_WINDOW_MINUTES,
    TAKER_MAX_WINDOW_MINUTES,
    TAKER_CLEANUP_INTERVAL_SECONDS,
    TAKER_MAX_RETENTION_MINUTES,
    TAKER_ORDER_CONFIG
)

logger = logging.getLogger(__name__)


class TakerConfigManager:
    """吃单监控配置管理器"""

    @staticmethod
    def get_window_minutes() -> int:
        """获取当前时间窗口（分钟）"""
        return TAKER_CUMULATIVE_WINDOW_MINUTES

    @staticmethod
    def set_window_minutes(minutes: int, persist: bool = False) -> bool:
        """设置时间窗口

        Args:
            minutes: 新的时间窗口(分钟)
            persist: 是否持久化到文件

        Returns:
            bool: 设置是否成功
        """
        if not TakerConfigManager.validate_window(minutes):
            logger.error(f"Invalid window size: {minutes}")
            return False

        # 更新配置
        import src.config as config
        config.TAKER_CUMULATIVE_WINDOW_MINUTES = minutes

        if persist:
            TakerConfigManager._persist_to_file(minutes)

        logger.info(f"Taker window updated to {minutes} minutes")
        return True

    @staticmethod
    def validate_window(window_minutes: int) -> bool:
        """验证时间窗口是否合法

        Args:
            window_minutes: 要验证的窗口大小(分钟)

        Returns:
            bool: 是否合法
        """
        return TAKER_MIN_WINDOW_MINUTES <= window_minutes <= TAKER_MAX_WINDOW_MINUTES

    @staticmethod
    def get_window_options() -> List[int]:
        """获取所有可选的时间窗口选项"""
        return TAKER_WINDOW_OPTIONS.copy()

    @staticmethod
    def get_config_dict() -> dict:
        """获取完整配置字典"""
        return TAKER_ORDER_CONFIG.copy()

    @staticmethod
    def _persist_to_file(minutes: int):
        """持久化配置到文件"""
        # TODO: 实现配置持久化到配置文件
        # 例如: 更新 .env 或 config.json
        logger.info(f"Persisting window size {minutes} to config file")
        pass
```

#### 5. 新增 Telegram 命令
**文件**: `src/telegram.py` (新增命令处理器)

**新内容**:
```python
@taker_message_handler(commands=["taker_window"])
@self.is_admin
def on_taker_window_config(message):
    """管理吃单监控时间窗口配置"""
    splt_msg = self.split_message(message.text)
    from src.config.taker_config import TakerConfigManager

    try:
        if len(splt_msg) == 0:
            # 显示当前配置
            show_current_window_config(message, TakerConfigManager)

        elif splt_msg[0].lower() == "set":
            # 设置新窗口
            if len(splt_msg) < 2:
                self.reply_to(
                    message,
                    "❌ 格式错误。使用: /taker_window set <分钟数>\n"
                    f"示例: /taker_window set 60"
                )
                return

            try:
                new_window = int(splt_msg[1])
            except ValueError:
                self.reply_to(
                    message,
                    f"❌ 无效值: {splt_msg[1]}。请输入数字。"
                )
                return

            if TakerConfigManager.set_window_minutes(new_window):
                self.reply_to(
                    message,
                    f"✅ 吃单监控窗口已更新为 {new_window} 分钟\n"
                    f"💡 更改将在下次重启后生效"
                )
            else:
                self.reply_to(
                    message,
                    f"❌ 设置失败: 无效的窗口大小\n"
                    f"允许范围: {TAKER_MIN_WINDOW_MINUTES}-{TAKER_MAX_WINDOW_MINUTES} 分钟"
                )

        elif splt_msg[0].lower() == "list":
            # 列出可用选项
            show_window_options(message, TakerConfigManager)

        elif splt_msg[0].lower() == "current":
            # 显示当前配置详细信息
            show_current_window_details(message, TakerConfigManager)

        else:
            # 无效子命令
            self.reply_to(
                message,
                "❌ 无效子命令。\n\n"
                "可用命令:\n"
                "/taker_window - 查看当前配置\n"
                "/taker_window set <minutes> - 设置时间窗口\n"
                "/taker_window list - 查看可用选项\n"
                "/taker_window current - 查看详细配置\n"
            )

    except Exception as exc:
        logger.error(f"Error in taker_window command: {exc}")
        self.reply_to(
            message,
            f"❌ 执行出错: {str(exc)}"
        )


def show_current_window_config(message, config_manager):
    """显示当前时间窗口配置"""
    current = config_manager.get_window_minutes()
    options = config_manager.get_window_options()

    msg = "📊 **吃单监控时间窗口配置**\n\n"
    msg += f"🔹 **当前配置**: {current} 分钟\n"
    msg += f"🔹 **可用选项**: {', '.join(map(str, options))} 分钟\n\n"
    msg += "💡 **使用示例**:\n"
    msg += f"`/taker_window set 60` - 设置为1小时\n\n"
    msg += "📖 **帮助**:\n"
    msg += "/taker_window list - 查看所有选项\n"
    msg += "/taker_window current - 查看详细配置"

    self.reply_to(message, msg)


def show_window_options(message, config_manager):
    """显示所有可用时间窗口选项"""
    options = config_manager.get_window_options()
    options.sort()

    msg = "📋 **可用时间窗口选项**\n\n"

    for option in options:
        if option == config_manager.get_window_minutes():
            msg += f"✅ **{option} 分钟** (当前配置)\n"
        else:
            msg += f"⚪ **{option} 分钟**\n"

    msg += f"\n💡 **设置命令**: `/taker_window set <分钟数>`\n"
    msg += f"📖 **范围**: {TAKER_MIN_WINDOW_MINUTES}-{TAKER_MAX_WINDOW_MINUTES} 分钟"

    self.reply_to(message, msg)


def show_current_window_details(message, config_manager):
    """显示当前配置详细信息"""
    current = config_manager.get_window_minutes()
    config = config_manager.get_config_dict()

    msg = "📊 **吃单监控配置详情**\n\n"
    msg += f"```\n"
    msg += f"时间窗口: {current} 分钟\n"
    msg += f"阈值: ${config['cumulative']['threshold_usd']:,} USD\n"
    msg += f"最小订单数: {config['cumulative']['min_order_count']}\n"
    msg += f"冷却时间: {config['cumulative']['cooldown_minutes']} 分钟\n"
    msg += f"```\n\n"

    msg += f"📈 **性能配置**:\n"
    msg += f"```\n"
    msg += f"清理间隔: {config['performance']['cleanup_interval']} 秒\n"
    msg += f"最大保留: {config['performance']['max_retention']} 分钟\n"
    msg += f"批处理大小: {config['performance']['batch_size']}\n"
    msg += f"```"

    self.reply_to(message, msg)
```

---

## 🔧 实施规范

### 配置管理流程

#### 1. 启动时加载配置
```python
# src/monitor/large_orders/monitor.py
def __init__(self):
    # 加载吃单监控配置
    from src.config.taker_config import TakerConfigManager
    self.taker_config = TakerConfigManager()

    # 创建聚合器
    self.taker_aggregator = OrderAggregator(
        window_minutes=self.taker_config.get_window_minutes()
    )
```

#### 2. 运行时动态更新
```python
# 支持运行时更新 (可选高级功能)
def update_taker_window(new_minutes: int) -> bool:
    """更新吃单监控时间窗口"""
    if not self.taker_config.validate_window(new_minutes):
        return False

    # 停止当前聚合器
    self.taker_aggregator.stop()

    # 创建新的聚合器
    self.taker_aggregator = OrderAggregator(window_minutes=new_minutes)

    # 启动新聚合器
    self.taker_aggregator.start()

    # 更新配置
    self.taker_config.set_window_minutes(new_minutes, persist=True)

    return True
```

### 性能优化规范

#### 1. 批处理优化
```python
def process_batch(self, trades: List[TradeEvent]):
    """批量处理交易数据"""
    batch = self._group_trades_by_symbol(trades)

    for symbol, symbol_trades in batch.items():
        # 批量添加到窗口
        self._add_trades_to_window(symbol, symbol_trades)

        # 批量检查阈值
        if self._check_threshold_batch(symbol):
            self._trigger_alert(symbol)

    # 批量清理
    self._cleanup_batch()
```

#### 2. 内存管理
```python
def cleanup_expired(self):
    """清理过期的交易数据"""
    current_time = time.time() * 1000
    cutoff_time = current_time - (self.window_ms * 2)  # 保留2个窗口的数据

    for symbol in list(self.trade_windows.keys()):
        window = self.trade_windows[symbol]
        while window and window[0].timestamp < cutoff_time:
            window.popleft()

        # 如果窗口为空，删除以释放内存
        if not window:
            del self.trade_windows[symbol]

    self.stats["cleanup_operations"] += 1
```

---

## 🧪 测试规范

### 配置测试

```python
# tests/test_taker_config.py
def test_config_loading():
    """测试配置加载"""
    from src.config.taker_config import TakerConfigManager

    window = TakerConfigManager.get_window_minutes()
    assert window == 60  # 默认1小时

def test_config_validation():
    """测试配置验证"""
    from src.config.taker_config import TakerConfigManager

    # 有效值
    assert TakerConfigManager.validate_window(1) == True
    assert TakerConfigManager.validate_window(60) == True
    assert TakerConfigManager.validate_window(1440) == True

    # 无效值
    assert TakerConfigManager.validate_window(0) == False
    assert TakerConfigManager.validate_window(2000) == False
    assert TakerConfigManager.validate_window(-10) == False
```

### 功能测试

```python
# tests/test_taker_window.py
def test_taker_window_command():
    """测试 /taker_window 命令"""
    from src.telegram import TelegramBot

    # 模拟消息
    message = MockMessage("/taker_window")
    bot = TelegramBot()

    # 执行命令
    result = bot.on_taker_window_config(message)

    # 验证响应
    assert "当前配置" in result
    assert "60 分钟" in result

def test_set_taker_window():
    """测试设置时间窗口"""
    from src.config.taker_config import TakerConfigManager

    # 设置新窗口
    result = TakerConfigManager.set_window_minutes(120)

    # 验证
    assert result == True
    assert TakerConfigManager.get_window_minutes() == 120
```

### 性能测试

```python
# tests/test_taker_performance.py
def test_memory_usage_1_hour_window():
    """测试1小时窗口的内存使用"""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # 创建1小时窗口聚合器
    aggregator = OrderAggregator(window_minutes=60)

    # 模拟10000笔交易
    for i in range(10000):
        trade = create_test_trade()
        aggregator.add_trade(trade)

    final_memory = process.memory_info().rss
    memory_increase_mb = (final_memory - initial_memory) / 1024 / 1024

    # 验证内存使用 < 500MB
    assert memory_increase_mb < 500, f"内存使用过多: {memory_increase_mb}MB"
```

---

## 📊 性能规范

### 内存使用基准

| 时间窗口 | 交易量 | 预期内存 | 备注 |
|----------|--------|---------|------|
| 1分钟 | 1000笔 | ~5MB | 轻量级 |
| 15分钟 | 15000笔 | ~75MB | 可接受 |
| 60分钟 | 60000笔 | ~300MB | 推荐 |
| 240分钟 | 240000笔 | ~1.2GB | 重度，需优化 |

### CPU使用基准

| 操作 | 1小时窗口 | 4小时窗口 | 备注 |
|------|---------|---------|------|
| 单笔交易处理 | <1ms | <2ms | 实时处理 |
| 窗口计算 | <10ms | <50ms | 批量处理 |
| 清理操作 | <100ms | <500ms | 定期执行 |
| 告警触发 | <50ms | <100ms | 同步执行 |

### 批处理性能

- **目标吞吐量**: 5000条/秒 (1小时窗口)
- **批处理大小**: 1000-10000 (根据窗口动态调整)
- **批处理延迟**: <100ms
- **批处理成功率**: >99.9%

---

## 🔍 监控规范

### 关键指标

```python
# src/monitor/metrics/taker_metrics.py
class TakerMonitorMetrics:
    """吃单监控指标收集器"""

    def __init__(self):
        self.window_size = self._load_window_size()
        self.trade_count = 0
        self.window_hits = 0
        self.memory_usage = 0
        self.batch_processing_time = 0
        self.cleanup_operations = 0

    def record_trade(self, trade):
        """记录交易"""
        self.trade_count += 1

    def record_window_hit(self):
        """记录窗口溢出"""
        self.window_hits += 1

    def get_metrics(self):
        """获取所有指标"""
        return {
            "window_size_minutes": self.window_size,
            "trade_count_total": self.trade_count,
            "window_hits_total": self.window_hits,
            "window_hit_rate": self.window_hits / max(1, self.trade_count),
            "memory_usage_mb": self.memory_usage,
            "avg_batch_time_ms": self.batch_processing_time,
            "cleanup_operations": self.cleanup_operations
        }
```

### 告警规则

```yaml
# 监控告警配置
alerts:
  - name: "taker_memory_high"
    condition: "memory_usage_mb > 1000"
    severity: "warning"
    message: "吃单监控内存使用过高: {memory_usage_mb}MB"

  - name: "taker_window_hit_rate_high"
    condition: "window_hit_rate > 0.1"
    severity: "warning"
    message: "吃单窗口溢出率过高: {window_hit_rate:.2%}"

  - name: "taker_batch_time_high"
    condition: "avg_batch_time_ms > 5000"
    severity: "warning"
    message: "吃单批处理耗时过长: {avg_batch_time_ms}ms"
```

---

## 🔐 安全规范

### 配置安全

1. **输入验证**
   - 严格的参数类型检查
   - 范围验证 (1-1440分钟)
   - 防止注入攻击

2. **权限控制**
   - 仅管理员可修改配置
   - 操作日志记录
   - 配置变更审计

3. **配置保护**
   - 敏感配置不记录日志
   - 配置文件权限限制
   - 配置备份和恢复

---

## 📝 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| 1.0.0 | 2025-11-10 | 初始规格创建 | OpenSpec |
| | | | |

---

**规格状态**: 🔴 待实施
**最后更新**: 2025-11-10
**负责人**: OpenSpec AI助手
