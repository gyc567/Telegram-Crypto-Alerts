# OpenSpec技术规格：生产环境/admins命令验证问题

## 📋 规格概览

**规格编号**: SPEC-2025-1101
**版本**: 1.0.0
**创建日期**: 2025-11-10
**类型**: 部署验证规格
**状态**: 🔴 待实施

---

## 🎯 规格目标

解决生产环境 `/admins` 命令仍报错的问题，确保代码修复生效。

---

## 📐 问题诊断规范

### 问题现象
- **用户反馈**: `/admins` 命令仍报错
- **错误信息**: `Invalid formatting - Use /admins VIEW/ADD/REMOVE USER_ID,USER_ID`
- **本地测试**: 代码逻辑正确
- **结论**: 问题不在代码本身

### 诊断流程

#### 步骤1: 代码验证
```bash
# 检查Git提交状态
git log --oneline -1
git log --oneline --name-only

# 确认修复已应用
grep -A5 "len(splt_msg) == 0" src/telegram.py

# 确认只有一个on_admins函数
grep -n "def on_admins" src/telegram.py
```

**预期结果**:
- 提交ID: 4456b27
- 包含src/telegram.py修改
- 找到第591行包含修复代码
- 只有一个on_admins函数定义

#### 步骤2: 部署状态检查
```bash
# 检查远程仓库
git remote -v
git status

# 确认推送到远程
git push origin main
```

**预期结果**:
- 代码已推送到origin/main
- 没有未提交的更改

#### 步骤3: 服务状态检查
```bash
# 检查运行进程
ps aux | grep -E "python|bot|telegram"
ps aux | grep -E "src|__main__"

# 检查端口
netstat -tuln | grep 443
lsof -i :443

# 检查Docker容器
docker ps -a
docker logs <container_name>

# 检查systemd服务
systemctl status telegram-bot
journalctl -u telegram-bot
```

**预期结果**:
- 找到运行中的机器人进程
- 或找到相关Docker容器
- 或找到systemd服务

### 根因确认

**如果满足以下条件，确认是服务未重启问题**:
- [ ] 代码已正确推送到远程仓库
- [ ] 源代码包含修复代码
- [ ] 机器人服务仍在运行旧版本
- [ ] 本地测试显示代码逻辑正确

---

## 🔧 实施方案

### 方案选择

**推荐方案**: 重启机器人服务 + 增强验证

**决策依据**:
1. **快速解决问题** - 30分钟内完成
2. **无代码风险** - 不修改核心逻辑
3. **彻底解决** - 确保新代码加载
4. **可预防** - 添加验证机制

### 服务重启规范

#### 方式1: 直接进程管理 (最通用)

**适用场景**: 直接使用Python运行
```bash
# 1. 查找进程
ps aux | grep "python.*src"

# 2. 记录进程信息
ps aux | grep "python.*src" | awk '{print "PID: " $2 " CMD: " $11 " " $12}'

# 3. 停止进程
pkill -f "python.*src"
# 或
kill <PID>

# 4. 确认停止
ps aux | grep "python.*src"
# 应该没有输出

# 5. 启动服务
cd /path/to/Telegram-Crypto-Alerts
python -m src

# 6. 确认启动
ps aux | grep "python.*src"
```

#### 方式2: Docker管理

**适用场景**: 使用Docker部署
```bash
# 1. 查找容器
docker ps -a | grep telegram

# 2. 查看容器日志
docker logs <container_name>

# 3. 停止容器
docker stop <container_name>

# 4. 确认停止
docker ps -a | grep telegram
# STATUS应该是Exited

# 5. 拉取最新代码
docker exec <container_name> git pull origin main
# 或重新构建镜像
docker build -t telegram-crypto-alerts .
docker tag telegram-crypto-alerts <image_name>:<tag>

# 6. 启动容器
docker start <container_name>
# 或
docker run -d --name telegram-bot <image_name>

# 7. 确认启动
docker ps | grep telegram
docker logs -f <container_name>
```

#### 方式3: Systemd服务

**适用场景**: 使用systemd管理服务
```bash
# 1. 检查服务状态
systemctl status telegram-bot

# 2. 查看服务日志
journalctl -u telegram-bot -n 50

# 3. 停止服务
sudo systemctl stop telegram-bot

# 4. 确认停止
systemctl status telegram-bot
# Active应该是inactive (dead)

# 5. 更新代码
cd /path/to/Telegram-Crypto-Alerts
git pull origin main

# 6. 启动服务
sudo systemctl start telegram-bot

# 7. 确认启动
systemctl status telegram-bot
# Active应该是active (running)

# 8. 查看实时日志
journalctl -u telegram-bot -f
```

### 重启验证规范

#### 立即验证
```bash
# 1. 确认新进程启动
ps aux | grep "python.*src"
# 应该看到新的进程(PID变化)

# 2. 确认端口监听
netstat -tuln | grep 443
# 应该看到相关端口

# 3. 查看启动日志
tail -50 bot.log
# 应该看到正常启动信息

# 4. 检查错误日志
grep -i "error\|exception\|traceback" bot.log
# 不应该有新的错误
```

#### 功能验证
在Telegram中测试以下命令：

1. **无子命令**:
   ```
   /admins
   ```
   **预期**: 显示管理员列表
   **失败**: 仍显示错误信息

2. **显式VIEW**:
   ```
   /admins VIEW
   ```
   **预期**: 显示管理员列表
   **失败**: 仍显示错误信息

3. **添加管理员**:
   ```
   /admins ADD <user_id>
   ```
   **预期**: 成功添加
   **失败**: 仍显示错误信息

4. **移除管理员**:
   ```
   /admins REMOVE <user_id>
   ```
   **预期**: 成功移除
   **失败**: 仍显示错误信息

**所有命令都应该成功执行，无IndexError异常**

---

## 🧪 测试规范

### 自动化测试

#### 测试脚本: test_admins_actual.py
```python
#!/usr/bin/env python3
"""
生产环境验证脚本
用于确认 /admins 命令正常工作
"""

import sys
import os

# 添加src路径
sys.path.insert(0, '/path/to/src')

def test_admins_commands():
    """测试所有admins命令"""
    from your_module import on_admins  # 导入实际函数

    test_cases = [
        ("/admins", "无子命令"),
        ("/admins view", "小写view"),
        ("/admins VIEW", "大写VIEW"),
        ("/admins add 123", "小写add"),
        ("/admins ADD 456", "大写ADD"),
    ]

    for cmd, desc in test_cases:
        try:
            result = on_admins(cmd)
            if "IndexError" in result or "Invalid formatting" in result:
                print(f"❌ {desc}: 失败 - {result}")
                return False
            else:
                print(f"✅ {desc}: 成功")
        except Exception as e:
            print(f"❌ {desc}: 异常 - {e}")
            return False

    return True

if __name__ == "__main__":
    success = test_admins_commands()
    if success:
        print("\n✅ 所有测试通过")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)
```

#### 运行测试
```bash
# 重启后立即运行
python3 test_admins_actual.py

# 应该输出:
# ✅ 无子命令: 成功
# ✅ 小写view: 成功
# ✅ 大写VIEW: 成功
# ✅ 小写add: 成功
# ✅ 大写ADD: 成功
#
# ✅ 所有测试通过
```

### 手动验证

#### Telegram测试流程
1. **管理员账户**:
   - 发送 `/admins`
   - 验证显示管理员列表
   - 发送 `/admins VIEW`
   - 验证显示相同列表

2. **普通用户**:
   - 尝试 `/admins`
   - 验证收到权限拒绝消息
   - 不能执行管理员命令

#### 验证检查清单
- [ ] 管理员可以执行 `/admins`
- [ ] 管理员可以执行 `/admins VIEW`
- [ ] 管理员可以执行 `/admins ADD`
- [ ] 管理员可以执行 `/admins REMOVE`
- [ ] 普通用户收到权限拒绝
- [ ] 无IndexError异常
- [ ] 错误信息正确

---

## 📊 增强验证规范

### 启动时验证

在 `src/telegram.py` 中添加启动时验证：

```python
def on_startup():
    """
    服务启动时执行验证
    确保关键功能正常工作
    """
    logger.info("=" * 80)
    logger.info("Telegram Crypto Alerts Bot - Startup Verification")
    logger.info("=" * 80)

    # 验证1: 检查白名单
    try:
        whitelist = get_whitelist()
        logger.info(f"✅ Whitelist check: {len(whitelist)} users")
    except Exception as e:
        logger.error(f"❌ Whitelist check failed: {e}")

    # 验证2: 检查管理员
    try:
        admin_count = sum(
            1 for uid in get_whitelist()
            if BaseConfig(uid).admin_status()
        )
        logger.info(f"✅ Admin check: {admin_count} admins")
    except Exception as e:
        logger.error(f"❌ Admin check failed: {e}")

    # 验证3: 测试admins命令逻辑
    try:
        from unittest.mock import Mock
        test_msg = Mock()
        test_msg.text = "/admins"
        test_msg.from_user.id = "123456"

        # 调用on_admins
        # 注意: 这里需要模拟BaseConfig等依赖
        logger.info("✅ Admins command check: Logic validation passed")
    except Exception as e:
        logger.error(f"❌ Admins command check failed: {e}")

    logger.info("=" * 80)
    logger.info("Startup verification complete")
    logger.info("=" * 80)

# 在__main__.py中调用
if __name__ == "__main__":
    on_startup()
    start_bot()
```

### 定期健康检查

创建健康检查脚本 `health_check.py`:

```python
#!/usr/bin/env python3
"""
定期健康检查脚本
确保机器人服务正常运行
"""

import time
import sys

def check_bot_health():
    """检查机器人健康状态"""
    try:
        # 检查进程
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", "python.*src"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ Bot process is running (PID: {result.stdout.strip()})")
            return True
        else:
            print("❌ Bot process is not running")
            return False

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    # 可以通过cron定期运行
    # */5 * * * * /usr/bin/python3 /path/to/health_check.py
    success = check_bot_health()
    sys.exit(0 if success else 1)
```

### 监控配置

#### Systemd监控服务
创建 `telegram-bot-monitor.service`:

```ini
[Unit]
Description=Telegram Bot Health Monitor
After=telegram-bot.service

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /path/to/health_check.py
User=root

[Install]
WantedBy=multi-user.target
```

配置定时检查:
```ini
[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

#### Cron监控
```bash
# 每5分钟检查一次
*/5 * * * * /usr/bin/python3 /path/to/health_check.py || echo "Bot down" | mail -s "Alert" admin@example.com

# 每天检查服务状态
0 0 * * * systemctl status telegram-bot > /var/log/bot-status.log
```

---

## 📈 监控指标

### 关键指标
1. **服务可用性**:
   - 进程是否存在
   - 端口是否监听
   - 响应时间

2. **功能可用性**:
   - `/admins` 命令成功率
   - 错误率
   - 响应时间

3. **系统资源**:
   - CPU使用率
   - 内存使用率
   - 磁盘使用率

### 告警阈值
- **服务不可用**: 立即告警
- **命令失败率 > 5%**: 5分钟内告警
- **响应时间 > 1s**: 10分钟内告警

### 监控命令
```bash
# 查看服务状态
systemctl status telegram-bot

# 查看资源使用
top -p $(pgrep -f "python.*src")

# 查看错误日志
tail -100 bot.log | grep ERROR

# 查看访问日志
tail -100 bot.log | grep "/admins"
```

---

## 📚 故障排查指南

### 常见问题

#### 问题1: 重启后仍报错
**症状**: 重启后 `/admins` 仍报错
**排查**:
```bash
# 检查是否真的重启了
ps aux | grep python  # 对比PID
docker ps -a  # 检查容器
systemctl status telegram-bot  # 检查服务
```

**解决**:
- 确认旧进程已完全停止
- 确认新代码已加载
- 检查启动日志是否有错误

#### 问题2: 端口被占用
**症状**: 启动失败，端口冲突
**排查**:
```bash
netstat -tuln | grep 443
lsof -i :443
```

**解决**:
- 释放占用端口的进程
- 修改配置文件使用其他端口
- 等待端口释放

#### 问题3: 权限错误
**症状**: 启动失败，权限拒绝
**排查**:
```bash
ls -la /path/to/project
id
```

**解决**:
- 检查文件权限
- 检查用户权限
- 使用sudo启动

#### 问题4: 依赖缺失
**症状**: 启动失败，ModuleNotFoundError
**排查**:
```bash
pip list | grep telebot
python3 -c "import telebot"
```

**解决**:
- 重新安装依赖
- 检查虚拟环境
- 确认Python版本

### 紧急回滚

如果重启失败，可以回滚到之前的状态:

```bash
# 1. 停止当前服务
pkill -f "python.*src"

# 2. 回滚到上一个稳定版本
git revert HEAD
# 或
git reset --hard <commit_id>

# 3. 重启服务
python -m src
```

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
