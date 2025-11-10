# 吃单监控时间窗口可配置化

## 📋 概述

本OpenSpec提案旨在将吃单监控的累积时间窗口从 **1分钟** 扩展到 **1小时** (60分钟)，并实现**完全可配置化**。

---

## 🎯 核心目标

1. **扩展时间窗口**: 1分钟 → 1小时 (默认)
2. **可配置化**: 支持1-1440分钟任意配置
3. **性能优化**: 自适应批处理和内存管理
4. **用户友好**: Telegram命令管理

---

## 📊 主要变更

| 方面 | 当前 | 目标 |
|------|------|------|
| **时间窗口** | 1分钟固定 | 1小时可配置 (默认) |
| **配置方式** | 硬编码 | config.py 统一管理 |
| **命令管理** | 无 | `/taker_window` 管理命令 |
| **性能** | 轻量 | 优化后支持1小时窗口 |
| **内存使用** | ~5MB | ~300MB (可接受) |

---

## 📁 文档结构

```
openspec/changes/update-taker-monitor-time-window/
├── proposal.md              # 详细提案文档
├── tasks.md                 # 实施任务清单
├── design.md                # 架构设计文档
├── README.md               # 本文件
└── specs/enhancement/
    └── spec.md             # 技术规格文档
```

---

## 🔑 关键特性

### 1. 配置化管理
```python
# src/config.py
TAKER_CUMULATIVE_WINDOW_MINUTES = 60  # 默认1小时
TAKER_WINDOW_OPTIONS = [5, 15, 30, 60, 120, 240]  # 可选选项
```

### 2. Telegram 命令
```
/taker_window                # 查看当前配置
/taker_window set 60         # 设置为60分钟
/taker_window set 120        # 设置为2小时
/taker_window list           # 查看所有选项
/taker_window current        # 查看详细配置
```

### 3. 性能优化
- **自适应批处理**: 根据窗口大小动态调整
- **智能清理**: 自动清理过期数据
- **内存管理**: 分层存储策略

---

## 📈 性能指标

| 指标 | 目标值 | 备注 |
|------|--------|------|
| **内存使用** | < 500MB | 1小时窗口 |
| **CPU使用率** | < 10% | 正常负载 |
| **告警延迟** | < 2秒 | 实时性 |
| **批处理性能** | 5000条/秒 | 吞吐量 |
| **可用性** | > 99% | 稳定性 |

---

## 🛠️ 实施计划

| 阶段 | 时间 | 主要任务 |
|------|------|----------|
| **阶段1** | Day 1 | 配置系统设计 |
| **阶段2** | Day 2-3 | 核心组件改造 |
| **阶段3** | Day 4 | Telegram 命令 |
| **阶段4** | Day 5-6 | 测试与优化 |
| **阶段5** | Day 7 | 部署与监控 |
| **总计** | **7天** | |

---

## 📋 验收标准

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

---

## 🔗 相关链接

- **OpenSpec 4.3.4 吃单监控基础**: [add-taker-order-monitoring](../add-taker-order-monitoring/)
- **大额订单监控系统**: [add-large-order-monitor](../add-large-order-monitor/)
- **配置管理指南**: [docs/configuration-management.md](../../docs/configuration-management.md)

---

## 📞 支持

如有问题或建议，请：

1. 查看详细文档:
   - [proposal.md](proposal.md) - 完整提案
   - [design.md](design.md) - 架构设计
   - [specs/enhancement/spec.md](specs/enhancement/spec.md) - 技术规格

2. 查看任务清单:
   - [tasks.md](tasks.md) - 实施计划

---

**提案编号**: CHANGE-2025-0106
**创建日期**: 2025-11-10
**状态**: 🔴 待审核
**优先级**: 高 (High)
