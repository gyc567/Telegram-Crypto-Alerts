# OpenSpec任务清单：修复admins VIEW命令错误

## 📋 任务概览

**变更ID**: change-2025-0102
**Bug编号**: BUG-2025-0102
**创建日期**: 2025-11-10
**状态**: 🟡 待开始
**预计工期**: 1-3天

---

## 🎯 目标

修复 `/admins` 和 `/admins VIEW` 命令的 IndexError 问题，使其与其他管理命令保持一致。

---

## 📋 任务列表

### 阶段1: 代码修复

#### ✅ 任务1.1: 分析现有代码
- [x] 检查 `src/telegram.py` 中的 `on_admins` 函数
- [x] 分析 `split_message()` 方法行为
- [x] 确认问题根因
- [x] 参考已修复的 `whitelist` 命令

#### ✅ 任务1.2: 创建修复方案
- [x] 制定修复方案
- [x] 确定代码修改位置
- [x] 设计测试用例

#### ⏳ 任务1.3: 实施代码修复
- [ ] 修改 `src/telegram.py:585-642` 的 `on_admins` 函数
- [ ] 添加长度检查：`if len(splt_msg) == 0 or splt_msg[0].lower() == "view":`
- [ ] 重新组织条件分支
- [ ] 改善错误信息
- [ ] 代码自测

**详细修改**:
```python
# 在 src/telegram.py 的 on_admins 函数中
# 第585-642行

# 原始代码 (有问题)
def on_admins(message):
    splt_msg = self.split_message(message.text)
    try:
        if splt_msg[0].lower() == "add":  # IndexError if empty
            ...
        elif splt_msg[0].lower() == "remove":  # IndexError if empty
            ...
        else:
            # VIEW处理
            ...

# 修复后代码
def on_admins(message):
    splt_msg = self.split_message(message.text)
    try:
        # 新增：处理无子命令和VIEW子命令
        if len(splt_msg) == 0 or splt_msg[0].lower() == "view":
            msg = "Current Administrators:\n\n"
            for user_id in get_whitelist():
                if BaseConfig(user_id).admin_status():
                    msg += f"{user_id}\n"
            self.reply_to(message, msg)

        elif splt_msg[0].lower() == "add":
            new_admins = splt_msg[1].split(",")
            failure_msgs = []
            for i, new_admin in enumerate(new_admins):
                try:
                    if new_admin in get_whitelist():
                        BaseConfig(new_admin).admin_status(new_value=True)
                    else:
                        failure_msgs.append(
                            f"{new_admins.pop(i)} - User is not yet whitelisted"
                        )
                except Exception as exc:
                    failure_msgs.append(f"{new_admins.pop(i)} - {exc}")
            msg = (
                f"Successfully added administrator(s): {', '.join(new_admins)}"
            )
            if len(failure_msgs) > 0:
                msg += "\n\nFailed to add administrator(s):"
                for fail_msg in failure_msgs:
                    msg += f"\n{fail_msg}"
            self.reply_to(message, msg)

        elif splt_msg[0].lower() == "remove":
            rm_admins = splt_msg[1].split(",")
            failure_msgs = []
            for i, admin in enumerate(rm_admins):
                try:
                    if admin in get_whitelist():
                        BaseConfig(admin).admin_status(new_value=False)
                    else:
                        failure_msgs.append(
                            f"{rm_admins.pop(i)} - User is not yet whitelisted"
                        )
                except Exception as exc:
                    failure_msgs.append(f"{rm_admins.pop(i)} - {exc}")
            msg = (
                f"Successfully revoked administrator(s): {', '.join(rm_admins)}"
            )
            if len(failure_msgs) > 0:
                msg += "\n\nFailed to revoke administrator(s):"
                for fail_msg in failure_msgs:
                    msg += f"\n{fail_msg}"
            self.reply_to(message, msg)

        else:
            # 无效子命令
            self.reply_to(
                message,
                "Invalid subcommand. Use VIEW, ADD, or REMOVE.",
            )

    except IndexError:
        # 安全网
        self.reply_to(
            message,
            "Invalid formatting - Use /admins VIEW/ADD/REMOVE USER_ID,USER_ID",
        )
    except Exception as exc:
        self.reply_to(message, f"An unexpected error occurred - {exc}")
```

---

### 阶段2: 测试验证

#### ⏳ 任务2.1: 单元测试
- [ ] 测试 `/admins` 命令
  - 输入: `/admins`
  - 预期: 显示管理员列表，无错误
  - 验证: 查看响应消息

- [ ] 测试 `/admins view` 命令（小写）
  - 输入: `/admins view`
  - 预期: 显示管理员列表，无错误
  - 验证: 查看响应消息

- [ ] 测试 `/admins VIEW` 命令（大写）
  - 输入: `/admins VIEW`
  - 预期: 显示管理员列表，无错误
  - 验证: 查看响应消息

- [ ] 测试 `/admins ADD 123` 命令
  - 输入: `/admins ADD 123456`
  - 预期: "Successfully added administrator(s): 123456"
  - 验证: 确认用户被设为管理员

- [ ] 测试 `/admins REMOVE 123` 命令
  - 输入: `/admins REMOVE 123456`
  - 预期: "Successfully revoked administrator(s): 123456"
  - 验证: 确认用户被移除管理员权限

- [ ] 测试无效子命令
  - 输入: `/admins INVALID`
  - 预期: "Invalid subcommand. Use VIEW, ADD, or REMOVE."
  - 验证: 查看错误信息

#### ⏳ 任务2.2: 集成测试
- [ ] 测试批量ADD
  - 输入: `/admins ADD 123,456,789`
  - 预期: 所有用户被设为管理员
  - 验证: 确认所有用户都是管理员

- [ ] 测试将非白名单用户设为管理员
  - 输入: `/admins ADD 999999` (999999不在白名单中)
  - 预期: 错误信息提示用户不在白名单中
  - 验证: 查看错误信息

- [ ] 测试空白名单
  - 输入: `/admins VIEW` (当没有管理员时)
  - 预期: 显示空列表或适当提示
  - 验证: 查看响应消息

#### ⏳ 任务2.3: 回归测试
- [ ] 确认 `/admins ADD` 功能正常
- [ ] 确认 `/admins REMOVE` 功能正常
- [ ] 确认其他管理命令不受影响
  - `/whitelist`
  - `/channels`
  - `/large_order_*`
- [ ] 确认错误处理正常
- [ ] 确认权限检查正常

#### ⏳ 任务2.4: 边界测试
- [ ] 测试特殊字符用户ID
- [ ] 测试超大用户ID
- [ ] 测试空参数
- [ ] 测试多空格分隔

---

### 阶段3: 代码审查

#### ⏳ 任务3.1: 自我审查
- [ ] 代码符合项目编码规范
- [ ] 错误处理完善
- [ ] 代码可读性良好
- [ ] 与类似命令保持一致
- [ ] 无性能影响

#### ⏳ 任务3.2: 提交审查
- [ ] 提交代码到审查分支
- [ ] 创建Pull Request
- [ ] 代码审查通过
- [ ] 修复审查反馈问题

#### ⏳ 任务3.3: 文档更新
- [ ] 更新提案状态为 "已修复"
- [ ] 更新测试报告
- [ ] 记录修复细节
- [ ] 更新变更日志

---

### 阶段4: 部署

#### ⏳ 任务4.1: 合并代码
- [ ] 合并到主分支
- [ ] 解决合并冲突（如果有）
- [ ] 确认构建通过

#### ⏳ 任务4.2: 部署到测试环境
- [ ] 部署到测试环境
- [ ] 执行烟囱测试
- [ ] 验证功能正常

#### ⏳ 任务4.3: 部署到生产环境
- [ ] 部署到生产环境
- [ ] 监控错误日志
- [ ] 确认功能正常
- [ ] 向用户通知修复完成

---

## 🔍 验收标准

### 必须验收 (P0)
- [ ] 无 IndexError 异常
- [ ] `/admins` 显示管理员列表
- [ ] `/admins VIEW` 显示管理员列表
- [ ] `/admins ADD` 正常工作
- [ ] `/admins REMOVE` 正常工作

### 应该验收 (P1)
- [ ] 无效子命令有清晰错误信息
- [ ] 与其他命令保持一致
- [ ] 批量操作正常工作
- [ ] 错误处理正常

### 可以验收 (P2)
- [ ] 性能无影响
- [ ] 代码审查通过
- [ ] 测试覆盖完整
- [ ] 文档完整

---

## 📊 工作量估算

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 阶段1 | 代码修复 | 0.5天 |
| 阶段2 | 测试验证 | 1天 |
| 阶段3 | 代码审查 | 0.5天 |
| 阶段4 | 部署 | 1天 |
| **总计** | | **3天** |

---

## ⚠️ 风险与缓解

### 风险1: 回归问题
**描述**: 修改可能影响现有ADD/REMOVE功能
**缓解**: 充分回归测试，参考已修复的whitelist命令

### 风险2: 权限问题
**描述**: is_admin装饰器可能影响测试
**缓解**: 确保测试在管理员账户下执行

### 风险3: 部署问题
**描述**: 部署过程中可能出现服务中断
**缓解**: 使用蓝绿部署或快速回滚方案

---

## 📝 实际执行记录

### 执行进度
- **开始时间**: 待定
- **完成时间**: 待定
- **总耗时**: 待定
- **状态**: 🟡 待开始

### 问题记录
（执行过程中记录遇到的问题和解决方案）

### 经验总结
（完成后总结经验教训）

---

**负责人**: OpenSpec AI助手
**最后更新**: 2025-11-10
**状态**: 🟡 待开始
