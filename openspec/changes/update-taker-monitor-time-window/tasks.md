# OpenSpec 任务清单：吃单监控时间窗口可配置化

## 📋 任务概览

**任务ID**: TASK-2025-0106
**创建日期**: 2025-11-10
**状态**: 🔴 待开始
**预计工期**: 7天
**优先级**: 高 (High)

---

## 🎯 目标

将吃单监控的累积时间窗口从1分钟更新为1小时（60分钟），并实现完全可配置化管理。

---

## 📋 任务列表

### 阶段1: 配置系统设计 (Day 1)

#### ✅ 任务1.1: 设计配置结构
- [ ] **设计新的配置项**
  ```python
  # 在 src/config.py 中添加
  TAKER_CUMULATIVE_WINDOW_MINUTES = 60  # 默认1小时
  TAKER_WINDOW_OPTIONS = [5, 15, 30, 60, 120, 240]
  TAKER_MIN_WINDOW_MINUTES = 1
  TAKER_MAX_WINDOW_MINUTES = 1440
  ```

- [ ] **创建统一配置结构**
  ```python
  TAKER_ORDER_CONFIG = {
      "single_thresholds": {...},
      "cumulative": {
          "window_minutes": 60,
          "threshold_usd": 1_000_000,
          "min_order_count": 5,
          "cooldown_minutes": 5
      },
      "performance": {
          "cleanup_interval": 300,
          "max_retention": 1440,
          "batch_size": 1000
      }
  }
  ```

- [ ] **设计配置验证机制**
  ```python
  def validate_taker_window(window_minutes: int) -> bool:
      """验证时间窗口是否合法"""
      return TAKER_MIN_WINDOW_MINUTES <= window_minutes <= TAKER_MAX_WINDOW_MINUTES
  ```

#### ✅ 任务1.2: 创建配置管理工具
- [ ] **实现配置加载器**
  ```python
  class TakerConfigLoader:
      @staticmethod
      def get_window_minutes() -> int:
          """动态加载时间窗口配置"""
          pass

      @staticmethod
      def set_window_minutes(minutes: int) -> bool:
          """设置时间窗口（需重启）"""
          pass
  ```

- [ ] **配置热更新支持** (可选)
  ```python
  class ConfigHotReloader:
      """配置热更新管理器"""
      def __init__(self):
          self.subscribers = []

      def subscribe(self, callback):
          """订阅配置变更通知"""
          pass
  ```

#### ✅ 任务1.3: 单元测试
- [ ] 测试配置加载
- [ ] 测试配置验证
- [ ] 测试边界值 (1分钟, 1440分钟)
- [ ] 测试无效值 (-1, 2000)

---

### 阶段2: 核心组件改造 (Day 2-3)

#### ✅ 任务2.1: 改造OrderAggregator
- [ ] **修改构造函数**
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
  ```

- [ ] **实现自适应批量处理**
  ```python
  def _calculate_batch_size(self) -> int:
      """根据时间窗口大小动态计算批处理大小"""
      if self.window_minutes >= 60:
          return 5000
      elif self.window_minutes >= 15:
          return 2000
      else:
          return 1000
  ```

- [ ] **实现智能清理间隔**
  ```python
  def _get_cleanup_interval(self) -> int:
      """获取自适应清理间隔"""
      if self.window_minutes >= 60:
          return 300  # 5分钟
      elif self.window_minutes >= 15:
          return 120  # 2分钟
      else:
          return 60   # 1分钟
  ```

#### ✅ 任务2.2: 实现TimeWindowManager
- [ ] **创建管理器类**
  ```python
  class TimeWindowManager:
      def __init__(self):
          self.windows: Dict[int, OrderAggregator] = {}
          self.active_window = self._load_configured_window()
  ```

- [ ] **实现窗口更新**
  ```python
  def update_window_size(self, new_window_minutes: int) -> bool:
      """动态更新时间窗口大小"""
      if self._validate_window_size(new_window_minutes):
          self.active_window = new_window_minutes
          self._reinitialize_windows()
          return True
      return False
  ```

- [ ] **实现窗口验证**
  ```python
  def _validate_window_size(self, window: int) -> bool:
      """验证时间窗口大小是否合法"""
      from src.config import TAKER_MIN_WINDOW_MINUTES, TAKER_MAX_WINDOW_MINUTES
      return TAKER_MIN_WINDOW_MINUTES <= window <= TAKER_MAX_WINDOW_MINUTES
  ```

#### ✅ 任务2.3: 内存管理和优化
- [ ] **实现分层存储**
  - 热数据: 最近1小时 (内存)
  - 温数据: 1-8小时 (内存缓存)
  - 冷数据: 8-24小时 (磁盘)

- [ ] **实现智能清理**
  - 增量清理 (仅清理过期数据)
  - 定期全量清理
  - 内存压力检测和自动清理

- [ ] **内存泄漏检测**
  ```python
  def check_memory_leak(self) -> bool:
      """检查是否存在内存泄漏"""
      # TODO: 实现内存使用监控
      pass
  ```

#### ✅ 任务2.4: 性能测试
- [ ] 内存使用测试 (1小时窗口)
- [ ] CPU使用率测试
- [ ] 批量处理性能测试
- [ ] 长时间运行稳定性测试

---

### 阶段3: Telegram 命令 (Day 4)

#### ✅ 任务3.1: 实现 /taker_window 命令
- [ ] **创建命令处理器**
  ```python
  @taker_message_handler(commands=["taker_window"])
  @self.is_admin
  def on_taker_window_config(message):
      splt_msg = self.split_message(message.text)

      if len(splt_msg) == 0:
          # 显示当前配置
          show_current_window_config(message)
      elif splt_msg[0].lower() == "set":
          # 设置新窗口
          new_window = int(splt_msg[1])
          if set_taker_window(new_window):
              self.reply_to(message, f"✅ 吃单监控窗口已更新为 {new_window} 分钟")
      elif splt_msg[0].lower() == "list":
          # 列出可用选项
          show_window_options(message)
  ```

- [ ] **实现子命令函数**
  ```python
  def show_current_window_config(message):
      """显示当前时间窗口配置"""
      pass

  def show_window_options(message):
      """显示所有可用时间窗口选项"""
      pass

  def set_taker_window(new_window: int) -> bool:
      """设置新的时间窗口"""
      pass
  ```

#### ✅ 任务3.2: 配置验证和错误处理
- [ ] **输入验证**
  - 检查参数数量
  - 验证时间窗口范围
  - 验证数值类型

- [ ] **错误处理**
  - 无效参数错误
  - 超出范围错误
  - 配置更新失败错误

- [ ] **用户友好提示**
  ```python
  ERROR_MESSAGES = {
      "invalid_format": "格式错误。使用: /taker_window set <分钟数>",
      "out_of_range": "时间窗口必须在 {min}-{max} 分钟之间",
      "update_failed": "更新失败: {reason}",
      "success": "✅ 吃单监控窗口已更新为 {window} 分钟"
  }
  ```

#### ✅ 任务3.3: 集成测试
- [ ] 测试无参数命令
- [ ] 测试set子命令 (有效值)
- [ ] 测试set子命令 (无效值)
- [ ] 测试list子命令
- [ ] 测试权限检查 (非管理员)

---

### 阶段4: 测试与优化 (Day 5-6)

#### ✅ 任务4.1: 集成测试
- [ ] **端到端测试**
  - 完整的工作流测试
  - 从配置到告警的整个链路

- [ ] **回归测试**
  - 确保现有功能不受影响
  - 大额订单监控正常
  - 单笔订单监控正常

- [ ] **兼容性测试**
  - 向后兼容老配置
  - API兼容性

#### ✅ 任务4.2: 性能基准测试
- [ ] **1小时窗口基准测试**
  - 内存使用 < 500MB
  - CPU使用率 < 10%
  - 告警延迟 < 2秒

- [ ] **压力测试**
  - 10000 TPS 场景测试
  - 长时间运行 (24小时)
  - 内存泄漏检测

- [ ] **批处理性能测试**
  - 5000条/秒 批处理能力
  - 批处理耗时 < 5秒

#### ✅ 任务4.3: 优化调整
- [ ] **根据测试结果优化**
  - 调整批处理大小
  - 优化清理间隔
  - 改进内存管理

- [ ] **性能调优**
  - 代码层面的优化
  - 数据结构的优化
  - 算法优化

#### ✅ 任务4.4: 用户验收测试
- [ ] 准备UAT环境
- [ ] 邀请用户参与测试
- [ ] 收集反馈和修复问题

---

### 阶段5: 部署与监控 (Day 7)

#### ✅ 任务5.1: 灰度部署
- [ ] **准备灰度环境**
  ```bash
  # 部署到测试环境
  deploy --env=staging --features=taker_window_config

  # 验证功能正常
  run_tests --env=staging
  ```

- [ ] **逐步扩大灰度范围**
  - 10% 用户
  - 50% 用户
  - 100% 用户

#### ✅ 任务5.2: 监控告警配置
- [ ] **配置监控指标**
  ```python
  # 监控仪表板
  METRICS = {
      "taker_window_size_minutes": "当前时间窗口大小",
      "taker_trade_count": "吃单交易总数",
      "taker_window_hits": "窗口溢出次数",
      "taker_memory_usage_mb": "内存使用(MB)",
      "taker_batch_processing_time": "批处理耗时(ms)"
  }
  ```

- [ ] **设置告警阈值**
  - 内存使用 > 1GB: 警告
  - CPU使用率 > 20%: 警告
  - 窗口溢出率 > 10%: 警告
  - 批处理耗时 > 5s: 警告

#### ✅ 任务5.3: 回滚方案准备
- [ ] **准备回滚脚本**
  ```bash
  # 快速回滚
  rollback --version=previous --services=taker_monitor
  ```

- [ ] **回滚测试**
  - 测试回滚流程
  - 验证回滚后功能正常
  - 确认数据完整性

#### ✅ 任务5.4: 文档和培训
- [ ] **更新用户文档**
  - `/taker_window` 命令使用说明
  - 时间窗口配置指南
  - 常见问题解答

- [ ] **运维文档**
  - 监控和告警指南
  - 故障排查手册
  - 性能调优指南

- [ ] **开发文档**
  - 架构设计文档
  - 代码注释完善
  - API文档更新

---

## 🔍 验收标准

### 必须验收 (P0)
- [ ] 时间窗口可配置（1-1440分钟）
- [ ] `/taker_window set 60` 命令正常工作
- [ ] 1小时窗口下告警正常触发
- [ ] 配置验证和错误处理正常
- [ ] 向后兼容 (保持现有功能)

### 应该验收 (P1)
- [ ] 内存使用 < 500MB (1小时窗口)
- [ ] CPU使用率 < 10%
- [ ] 告警延迟 < 2秒
- [ ] 批处理性能达标
- [ ] 单元测试覆盖 > 90%

### 可以验收 (P2)
- [ ] 灰度部署成功
- [ ] 监控告警配置完成
- [ ] 回滚方案验证通过
- [ ] 文档完整
- [ ] 用户培训完成

---

## 📊 工作量估算

| 阶段 | 任务 | 人天 | 累计 |
|------|------|------|------|
| 阶段1 | 配置系统设计 | 1 | 1 |
| 阶段2 | 核心组件改造 | 2 | 3 |
| 阶段3 | Telegram 命令 | 1 | 4 |
| 阶段4 | 测试与优化 | 2 | 6 |
| 阶段5 | 部署与监控 | 1 | 7 |
| **总计** | | **7** | **7** |

---

## ⚠️ 风险与缓解

### 风险1: 内存使用增加
**描述**: 1小时窗口可能增加内存使用
**概率**: 高
**影响**: 中
**缓解**:
- 优化数据结构和算法
- 实现智能清理机制
- 分层存储策略
- 监控内存使用并设置告警

### 风险2: 性能下降
**描述**: 更大的时间窗口可能导致性能下降
**概率**: 中
**影响**: 中
**缓解**:
- 批处理优化
- 异步处理
- 定期性能测试
- 性能基准测试

### 风险3: 配置错误
**描述**: 用户可能配置无效的时间窗口
**概率**: 中
**影响**: 低
**缓解**:
- 严格的配置验证
- 清晰的错误信息
- 提供默认值
- 范围限制

### 风险4: 向后兼容性
**描述**: 修改可能影响现有功能
**概率**: 低
**影响**: 高
**缓解**:
- 保持API兼容
- 添加弃用警告
- 充分的回归测试
- 灰度部署

---

## 📝 执行记录

### 执行进度
- **开始时间**: 待定
- **完成时间**: 待定
- **总耗时**: 待定
- **状态**: 🔴 待开始

### 问题记录
（执行过程中记录遇到的问题和解决方案）

### 经验教训
（完成后总结经验教训）

---

**负责人**: OpenSpec AI助手
**最后更新**: 2025-11-10
**状态**: 🔴 待开始
