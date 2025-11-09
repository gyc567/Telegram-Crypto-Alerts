# Large Order Monitoring - OpenSpec Change Proposal Summary

## Change ID
`add-large-order-monitor`

## Overview
This proposal adds real-time monitoring for large cryptocurrency trades (> $2M USD in 5 minutes) to the Telegram-Crypto-Alerts bot.

## Created Files

### 1. Proposal Document
**File:** `openspec/changes/add-large-order-monitor/proposal.md`
- Complete change proposal with motivation, scope, and requirements
- ADDED requirements for WebSocket monitoring, threshold detection, and alert generation
- Design overview and architecture components
- Success criteria and testing strategy
- Timeline: 27-39 days

### 2. Implementation Tasks
**File:** `openspec/changes/add-large-order-monitor/tasks.md`
- Phase 1: Core Infrastructure (Tasks 1.1-1.4)
- Phase 2: Binance Integration (Tasks 2.1-2.3)
- Phase 3: Configuration & Management (Tasks 3.1-3.3)
- Phase 4: Testing & Validation (Tasks 4.1-4.3)
- Phase 5: Documentation & Deployment (Tasks 5.1-5.2)
- Total: 76 detailed tasks

### 3. Technical Design
**File:** `openspec/changes/add-large-order-monitor/design.md`
- Detailed architecture with component diagrams
- WebSocket Manager, Order Aggregator, Threshold Engine
- Alert Dispatcher, Price Converter
- Code structure and class designs
- Data models and error handling

### 4. Spec Delta
**File:** `openspec/changes/add-large-order-monitor/spec-delta.md`
- Summary of changes
- Implementation requirements
- Success criteria
- Risk assessment and rollout plan

### 5. Specification
**File:** `openspec/specs/large-order-monitoring/monitoring.md`
- ADDED Requirements:
  - WebSocket Order Flow Monitoring
  - 5-Minute Volume Threshold Detection
  - Telegram Alert Generation
  - USD Conversion
  - Cooldown Management
- Each requirement includes detailed scenarios

## Key Features

### Monitoring Conditions
- **Threshold:** 5-minute market order volume > $2,000,000 USD
- **Data Source:** Binance WebSocket real-time order stream
- **Alert Format:** `[大额主动买入] BTC/USDT 金额：$2,500,000 方向：买入 时间：14:35:22`
- **Cooldown:** 5 minutes per symbol to prevent spam
- **Exchange Support:** Phase 1 (Binance), Phase 2 (OKX), Phase 3 (Coinbase)

### Technical Specifications
- WebSocket connection with auto-reconnection
- Rolling 5-minute window for volume accumulation
- USD conversion for all trading pairs
- Support for 20+ major trading pairs
- < 1 second latency (trade to alert)
- 99.5% uptime target

## Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Large Order Monitor System               │
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
└─────────────────────────────────────────────────────────────┘
```

## Implementation Files Needed

### New Files to Create
1. `src/large_order_monitor/websocket_manager.py` - WebSocket client
2. `src/large_order_monitor/models.py` - Data models
3. `src/large_order_monitor/threshold_engine.py` - Threshold detection
4. `src/large_order_monitor/alert_dispatcher.py` - Alert formatting
5. `src/large_order_monitor/price_converter.py` - USD conversion
6. `src/large_order_monitor/exchanges/binance.py` - Binance integration
7. `src/large_order_monitor/multi_pair_monitor.py` - Multi-pair monitoring
8. `src/large_order_monitor/config.py` - Configuration
9. `src/alert_processes/large_order.py` - Alert process integration
10. `tests/test_large_order_monitor/` - Test suite

### Files to Modify
1. `src/__main__.py` - Initialize monitoring process
2. `src/telegram.py` - Add commands
3. `src/config.py` - Add configuration constants
4. `README.md` - Document new feature

## Success Criteria

- [ ] WebSocket connection to Binance established
- [ ] 5-minute volume tracking accurate
- [ ] Alerts trigger at $2M threshold
- [ ] Telegram messages formatted correctly
- [ ] 5-minute cooldown per symbol
- [ ] Support for 20+ trading pairs
- [ ] Auto-reconnect on disconnection
- [ ] Configuration via environment variables
- [ ] 99.5% uptime
- [ ] < 1 second latency (trade to alert)

## Next Steps

1. **Review Proposal:** Team review of proposal and specifications
2. **Approve Change:** Get approval to proceed
3. **Begin Implementation:** Start with Phase 1 (Core Infrastructure)
4. **Develop Incrementally:** Implement in phases with testing
5. **Deploy Gradually:** Roll out to 10% then 100% of users

## Timeline

- **Phase 1 (Core):** 5-7 days
- **Phase 2 (Binance):** 7-10 days
- **Phase 3 (Integration):** 5-7 days
- **Phase 4 (Testing):** 7-10 days
- **Phase 5 (Docs/Deploy):** 3-5 days

**Total Estimated Effort:** 27-39 days

## OpenSpec Integration

This proposal is integrated with OpenSpec for spec-driven development:
- Change tracked in `openspec/changes/add-large-order-monitor/`
- Requirements documented in `openspec/specs/large-order-monitoring/`
- Tasks managed in `tasks.md`
- Technical design in `design.md`
- All documentation follows OpenSpec conventions

---

**Status:** Ready for Review  
**Date Created:** 2025-11-09  
**Version:** 1.0.0

