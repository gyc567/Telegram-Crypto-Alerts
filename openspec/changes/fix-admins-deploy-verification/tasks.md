# OpenSpec任务清单：生产环境/admins命令验证问题

## 📋 任务概览

**问题ID**: ISSUE-2025-1101
**创建日期**: 2025-11-10
**状态**: 🔴 待开始
**预计工期**: 1-2小时

---

## 🎯 目标

解决生产环境 `/admins` 命令仍报错的问题，确保修复生效。

---

## 📋 任务列表

### 阶段1: 问题确认

#### ⏳ 任务1.1: 验证代码部署状态
- [ ] 检查Git提交状态
  ```bash
  git status
  git log --oneline -3
  ```

- [ ] 确认代码已推送到远程仓库
  ```bash
  git remote -v
  git push origin main
  ```

- [ ] 检查源代码包含修复
  ```bash
  grep -n "len(splt_msg) == 0" src/telegram.py
  ```

#### ⏳ 任务1.2: 分析问题根因
- [ ] 确认这是服务未重启问题
- [ ] 排除代码bug可能性
- [ ] 记录问题根因

---

### 阶段2: 服务重启 (核心任务)

#### ⏳ 任务2.1: 检查当前运行状态
- [ ] 查看运行中的进程
  ```bash
  ps aux | grep -E "python|bot|telegram"
  ```

- [ ] 查看端口占用
  ```bash
  netstat -tuln | grep 443
  # 或
  lsof -i :443
  ```

- [ ] 检查Docker容器 (如果使用)
  ```bash
  docker ps
  docker logs <container_name>
  ```

- [ ] 查看systemd服务 (如果使用)
  ```bash
  systemctl status telegram-bot
  ```

#### ⏳ 任务2.2: 停止现有服务
- [ ] **方式1: 直接杀死进程**
  ```bash
  pkill -f "python.*src"
  ```

- [ ] **方式2: Docker停止**
  ```bash
  docker stop <container_name>
  ```

- [ ] **方式3: Systemd停止**
  ```bash
  sudo systemctl stop telegram-bot
  ```

- [ ] 验证服务已停止
  ```bash
  ps aux | grep python
  # 确认没有相关进程
  ```

#### ⏳ 任务2.3: 重启服务
- [ ] **方式1: Python直接运行**
  ```bash
  cd /path/to/project
  python -m src
  ```

- [ ] **方式2: Docker启动**
  ```bash
  docker start <container_name>
  docker logs -f <container_name>
  ```

- [ ] **方式3: Systemd启动**
  ```bash
  sudo systemctl start telegram-bot
  sudo systemctl status telegram-bot
  ```

- [ ] 验证服务已启动
  ```bash
  ps aux | grep python
  # 确认有新的相关进程
  ```

#### ⏳ 任务2.4: 配置自动重启 (可选)
- [ ] 配置systemd服务自动重启
  ```bash
  sudo systemctl edit telegram-bot
  # 添加 Restart=on-failure
  ```

- [ ] 配置Docker自动重启
  ```bash
  docker run --restart=unless-stopped ...
  ```

- [ ] 配置进程监控 (如supervisor)
  ```ini
  [program:telegram-bot]
  command=python -m src
  autorestart=true
  ```

---

### 阶段3: 功能验证

#### ⏳ 任务3.1: 基础命令测试
- [ ] 测试 `/admins` (无子命令)
  - 预期: 显示管理员列表
  - 验证: 查看机器人响应

- [ ] 测试 `/admins VIEW`
  - 预期: 显示管理员列表
  - 验证: 查看机器人响应

- [ ] 测试 `/admins view` (小写)
  - 预期: 显示管理员列表
  - 验证: 查看机器人响应

#### ⏳ 任务3.2: 功能命令测试
- [ ] 测试 `/admins ADD <user_id>`
  - 预期: 成功添加管理员
  - 验证: 查看机器人响应和用户状态

- [ ] 测试 `/admins REMOVE <user_id>`
  - 预期: 成功移除管理员
  - 验证: 查看机器人响应和用户状态

#### ⏳ 任务3.3: 错误处理测试
- [ ] 测试 `/admins INVALID`
  - 预期: 清晰错误信息
  - 验证: 错误信息正确

- [ ] 测试无权限用户
  - 预期: 权限拒绝消息
  - 验证: 消息内容正确

#### ⏳ 任务3.4: 自动化测试验证
- [ ] 运行 `test_admins_actual.py`
  ```bash
  python3 test_admins_actual.py
  ```

- [ ] 确认所有测试通过
  - 检查测试输出
  - 验证测试结果

---

### 阶段4: 长期改进

#### ⏳ 任务4.1: 添加启动时验证
- [ ] 在 `src/telegram.py` 中添加验证
  ```python
  def on_startup():
      """服务启动时验证关键功能"""
      logger.info("Starting Telegram Crypto Alerts Bot...")
      # 验证admins命令
      try:
          # 这里可以添加测试代码
          logger.info("Admins command validation: OK")
      except Exception as e:
          logger.error(f"Admins command validation failed: {e}")
  ```

- [ ] 在 `__main__.py` 中调用验证
  ```python
  if __name__ == "__main__":
      # 启动时验证
      on_startup()
      # 启动机器人
      ...
  ```

#### ⏳ 任务4.2: 更新部署文档
- [ ] 创建部署检查清单
  - 列出部署后必须验证的命令
  - 包含重启检查点

- [ ] 创建问题排查文档
  - 常见问题及解决方案
  - 日志查看方法

#### ⏳ 任务4.3: 配置监控
- [ ] 设置服务健康检查
  ```bash
  # cron job 每分钟检查
  * * * * * /usr/bin/pgrep -f "python.*src" > /dev/null || echo "Service down" | mail -s "Bot down" admin@example.com
  ```

- [ ] 配置日志轮转
  ```bash
  # logrotate配置
  /var/log/telegram-bot.log {
      daily
      rotate 7
      compress
      delaycompress
      missingok
      notifempty
  }
  ```

---

## 🔍 验收标准

### 必须验收 (P0)
- [ ] 机器人服务已重启
- [ ] `/admins` 命令正常工作
- [ ] `/admins VIEW` 命令正常工作
- [ ] 无IndexError异常
- [ ] 管理员管理功能正常

### 应该验收 (P1)
- [ ] 服务自动重启配置
- [ ] 启动时验证已添加
- [ ] 部署文档已更新
- [ ] 监控告警已配置

### 可以验收 (P2)
- [ ] CI/CD自动测试
- [ ] 完整的故障转移机制
- [ ] 性能监控

---

## 📊 工作量估算

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 阶段1 | 问题确认 | 15分钟 |
| 阶段2 | 服务重启 | 30分钟 |
| 阶段3 | 功能验证 | 30分钟 |
| 阶段4 | 长期改进 | 1天 |
| **总计** | | **2小时-1天** |

---

## ⚠️ 风险与缓解

### 风险1: 服务重启失败
**描述**: 重启过程中可能出现错误
**缓解**:
- 准备回滚方案
- 先在测试环境验证
- 记录原始配置

### 风险2: 数据丢失
**描述**: 重启可能导致未保存数据丢失
**缓解**:
- 确认数据已持久化
- 先停止数据写入
- 备份重要配置

### 风险3: 服务长时间不可用
**描述**: 重启可能需要较长时间
**缓解**:
- 选择低峰期执行
- 准备快速启动脚本
- 通知相关用户

### 风险4: 重复问题
**描述**: 修复后问题可能再次出现
**缓解**:
- 添加自动重启配置
- 配置监控告警
- 建立定期检查机制

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
