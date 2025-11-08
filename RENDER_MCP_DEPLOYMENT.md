# 🚀 使用 Render MCP 部署指南

> **使用 Render MCP 工具** - Claude Code 的 Render 集成工具部署指南

## 📋 目录
- [Render MCP 工具已安装](#-render-mcp-工具已安装)
- [前提条件](#-前提条件)
- [部署前准备](#-部署前准备)
- [部署步骤](#-部署步骤)
- [MCP 工具使用](#-mcp-工具使用)
- [验证部署](#-验证部署)
- [后续管理](#-后续管理)
- [常见问题](#-常见问题)
- [总结](#-总结)

---

## ✅ Render MCP 工具已安装

Render MCP 工具已经成功安装到你的系统中！

**配置信息**：
- ✅ URL: `https://mcp.render.com/mcp`
- ✅ API Key: `rnd_SZNQ1A0757gBZvbIAUab1TWNPGNz`
- ✅ 配置文件: `/Users/guoyingcheng/.claude.json`
- ✅ 状态: 已配置并激活

**MCP 是什么？**
MCP (Model Context Protocol) 是 Claude Code 的扩展协议，允许 Claude Code 直接与外部服务交互。Render MCP 让 Claude Code 能够直接管理 Render 上的服务。

---

## 📝 前提条件

### 需要的账号

- ✅ **Render 账号** - 已在系统配置
- ✅ **Telegram Bot Token** - 待获取
- ✅ **Telegram User ID** - 待获取
- ✅ **GitHub 仓库** - 待创建/连接

### 项目状态

- ✅ 项目代码 - 已准备完整
- ✅ requirements.txt - 存在
- ✅ src/ 目录 - 存在
- ✅ Dockerfile - 存在
- ✅ 环境配置 - 已准备

---

## 🛠️ 部署前准备

### 第1步：创建 Telegram Bot

1. **在 Telegram 中搜索** `@BotFather`
2. **发送命令** `/newbot`
3. **设置名称** `My Crypto Alert Bot`
4. **设置用户名** `my_crypto_alert_2024_bot`（必须以 bot 结尾）
5. **复制 Bot Token** - 格式类似 `1234567890:ABCdef...`

**保存这个 Token！** 它非常重要，后续部署会用到。

### 第2步：获取 User ID

1. **在 Telegram 中搜索** `@userinfobot`
2. **发送命令** `/start`
3. **复制 User ID** - 一串数字，如 `123456789`

**保存这个 ID！** 这是你的唯一标识。

### 第3步：创建 GitHub 仓库

**方法一：通过网页（推荐）**

1. 打开 [https://github.com/new](https://github.com/new)
2. 填写信息：
   ```
   Repository name: telegram-crypto-alerts
   Description: 加密货币价格和技术指标告警机器人
   Visibility: Public
   ```
3. 点击 **"Create repository"**

**方法二：使用 GitHub Desktop（如果已安装）**

1. 打开 GitHub Desktop
2. 点击 **"Create a New Repository on your hard drive"**
3. 填写信息后点击 **"Create Repository"**
4. 复制项目文件到该目录

### 第4步：上传项目代码

**确保以下文件存在**：
- ✅ `README.md`
- ✅ `requirements.txt`
- ✅ `src/` 目录
- ✅ `Dockerfile`
- ✅ `.env.example`

**然后推送到 GitHub**：
```bash
# 在项目目录中
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/telegram-crypto-alerts.git
git push -u origin main
```

### 第5步：获取可选的 Taapi.io API Key（推荐）

虽然不是必需的，但建议获取：

1. 打开 [https://taapi.io](https://taapi.io)
2. 点击 **"Get API Key"**
3. 注册免费账号（用邮箱）
4. 登录后查看 API Key
5. 复制这个 Key

**免费版限制**：每 20 秒 1 个请求，足够个人使用。

---

## 🎯 部署步骤

### 方式一：使用 Render MCP（推荐）

由于 Render MCP 已安装，Claude Code 可以直接管理 Render 服务。

**Claude Code 将帮助您**：
1. 创建 Render Web Service
2. 配置环境变量
3. 连接 GitHub 仓库
4. 部署应用
5. 监控部署状态

**要开始部署**：
请在 Claude Code 中说：
> "请使用 Render MCP 工具帮我部署这个项目到 Render 云服务器"

**Claude Code 会自动**：
- 使用已配置的 API Key
- 创建 Web Service
- 配置所有必需的环境变量
- 部署项目
- 验证部署成功

### 方式二：使用 Web 界面（备选）

如果不想使用 MCP 工具，也可以通过网页操作：

1. **打开 Render 控制台**
   - 访问 [https://dashboard.render.com](https://dashboard.render.com)
   - 登录你的账号

2. **创建 Web Service**
   - 点击 **"New +"**
   - 选择 **"Web Service"**
   - 选择 **"Build and deploy from a Git repository"**

3. **配置服务**
   ```
   Name: telegram-crypto-alerts
   Region: Singapore (推荐，离中国近)
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python -m src
   ```

4. **添加环境变量**
   ```
   TELEGRAM_BOT_TOKEN=你的BotToken
   TELEGRAM_USER_ID=你的UserID
   LOCATION=global
   TAAPIIO_TIER=free
   ```

5. **部署**
   - 点击 **"Create Web Service"**
   - 等待 3-5 分钟部署完成

### 方式三：使用其他 CLI 工具（高级）

如果你想使用命令行工具：

**选项1：使用 Render 的 Git 部署**
```bash
# 推送到 GitHub 会自动触发部署
git push origin main
```

**选项2：使用 Render API（如果有）**
```bash
# 使用 REST API 创建服务
curl -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## 💻 MCP 工具使用

### MCP 工具优势

| 特性 | Web 界面 | MCP 工具 | Render CLI |
|------|----------|----------|------------|
| **速度** | 中等 | 快 | 快 |
| **自动化** | 手动 | 自动 | 自动 |
| **Claude 集成** | 无 | ✅ 完美 | 无 |
| **易用性** | 简单 | 简单 | 中等 |
| **可重复性** | 差 | 好 | 好 |

### MCP 工具可用功能

通过 Claude Code 的 Render MCP，你可以：

1. **创建服务**
   ```bash
   # Claude Code 会处理
   create_web_service(name="telegram-crypto-alerts")
   ```

2. **配置环境变量**
   ```bash
   # Claude Code 会处理
   set_secrets(service_id, secrets)
   ```

3. **部署服务**
   ```bash
   # Claude Code 会处理
   deploy_service(service_id)
   ```

4. **查看日志**
   ```bash
   # Claude Code 会处理
   get_logs(service_id)
   ```

5. **管理服务**
   ```bash
   # Claude Code 会处理
   restart_service(service_id)
   delete_service(service_id)
   ```

### 使用方法

在 Claude Code 对话中，你只需要说：

```
"帮我部署这个项目到 Render"
"使用 Render MCP 工具部署"
"部署后帮我测试 Bot 功能"
"查看部署状态和日志"
"更新环境变量"
```

**Claude Code 会自动**：
- 理解你的需求
- 使用 Render MCP 工具
- 执行正确的操作
- 报告结果
- 协助解决问题

---

## ✅ 验证部署

### 成功标志

**部署成功后会看到**：
- ✅ 服务状态为 `Active`
- ✅ 没有错误日志
- ✅ 持续运行超过 5 分钟
- ✅ Bot 响应 `/start` 命令

### 测试步骤

1. **在 Telegram 中搜索你的 Bot**
   - 输入：`@你的Bot用户名`

2. **发送测试命令**
   ```
   /start
   /help
   /info
   ```

3. **创建测试告警**
   ```
   /new_alert BTC/USDT PRICE ABOVE 50000
   ```

4. **查看响应**
   - Bot 应该返回确认消息
   - 表示部署成功

### 查看日志

**如果有问题**：

1. **通过 Render 控制台**
   - 访问 [https://dashboard.render.com](https://dashboard.render.com)
   - 选择你的服务
   - 点击 **"Logs"** 选项卡

2. **通过 Claude Code**
   - 说："帮我查看部署日志"
   - Claude Code 会使用 MCP 工具获取日志

3. **常见日志**：
   ```
   [INFO] 初始化 Taapi.io...
   [INFO] 启动 Telegram 机器人...
   [INFO] 启动 CEX 告警进程...
   [INFO] 等待初始化...
   [INFO] 等待命令...
   ```

---

## 🔧 后续管理

### 更新代码

**方法一：通过 GitHub（推荐）**
```bash
# 修改代码后
git add .
git commit -m "Update feature"
git push origin main
# Render 自动部署
```

**方法二：通过 Claude Code**
- 说："帮我更新代码并重新部署"
- Claude Code 会处理所有步骤

### 管理环境变量

**添加新变量**：
1. 访问 Render 控制台
2. 进入服务设置
3. 修改环境变量
4. 重新部署

**或通过 Claude Code**：
- 说："帮我更新 TAAPIIO_APIKEY 环境变量"
- 提供新值
- Claude Code 会更新并重新部署

### 监控服务

**查看状态**：
- Render 控制台 → 服务列表
- 或通过 Claude Code 查询

**常见状态**：
- `Active` - 正常运行 ⭐
- `Deploying` - 正在部署 ⏳
- `Crashed` - 服务崩溃 ❌
- `Stopped` - 已停止 ⏸️

### 扩展功能

**添加自定义域名**：
1. 在服务设置中添加域名
2. 配置 DNS 记录
3. 启用 SSL（自动）

**升级计划**：
- 免费版：750小时/月
- 付费版：$7/月起，无限制

---

## ❓ 常见问题

### Q1: 部署失败怎么办？

**A: 排查步骤**：
1. 查看构建日志
2. 检查 `requirements.txt` 是否有错误
3. 确认所有文件都已上传到 GitHub
4. 验证环境变量配置

**常见错误**：
- `ModuleNotFoundError` - 依赖安装失败
- `Build failed` - 构建命令错误
- `Start command failed` - 启动命令错误

### Q2: Bot 没有响应？

**A: 检查清单**：
- [ ] 环境变量是否正确
- [ ] Bot Token 是否有效
- [ ] User ID 是否正确
- [ ] 服务是否在运行
- [ ] 是否有错误日志

**测试 Token**：
```bash
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Q3: MCP 工具不能工作？

**A: 验证配置**：
```bash
# 检查配置文件
cat /Users/guoyingcheng/.claude.json | grep render
```

**重新安装 MCP**：
```bash
claude mcp add --transport http render https://mcp.render.com/mcp \
  --header "Authorization: Bearer rnd_SZNQ1A0757gBZvbIAUab1TWNPGNz"
```

### Q4: 如何重置服务？

**A: 完全重建**：
1. 删除现有服务
2. 使用 MCP 工具重新创建
3. 配置所有环境变量
4. 重新部署

**或通过 Claude Code**：
- 说："请重建这个 Render 服务"

### Q5: 忘记 API Key 怎么办？

**A: 查看配置**：
- 配置文件：`/Users/guoyingcheng/.claude.json`
- API Key：`rnd_SZNQ1A0757gBZvbIAUab1TWNPGNz`

**获取新 Key**：
- 访问 [https://dashboard.render.com](https://dashboard.render.com)
- 进入账户设置
- 查看 API Keys

### Q6: 如何迁移到其他平台？

**A: 导出配置**：
1. 导出所有环境变量
2. 备份代码
3. 在新平台创建服务
4. 导入配置
5. 测试功能

### Q7: 如何监控使用量？

**A: 查看计费**：
- Render 控制台 → 计费
- 或通过 Claude Code 查询

**免费额度**：
- 750小时/月
- 通常足够 24/7 运行

### Q8: 可以部署多个 Bot 吗？

**A: 是的**：
- 每个 Bot 需要单独的仓库
- 或使用不同的分支
- 创建多个 Render 服务

---

## 📊 对比总结

### 三种部署方式对比

| 方式 | 难度 | 速度 | 自动化 | 推荐度 |
|------|------|------|--------|--------|
| **MCP 工具** | ⭐ | 快 | 高 | ⭐⭐⭐⭐⭐ |
| **Web 界面** | ⭐⭐ | 中 | 低 | ⭐⭐⭐ |
| **CLI 工具** | ⭐⭐⭐ | 快 | 高 | ⭐⭐⭐⭐ |

### 推荐流程

**新手** → 使用 **MCP 工具**（Claude Code 处理一切）
**进阶** → 使用 **Web 界面**（可控性更强）
**专家** → 使用 **CLI 工具**（自动化脚本）

---

## 🎉 总结

### ✅ 已完成

- ✅ Render MCP 工具已安装
- ✅ API Key 已配置
- ✅ 准备部署流程
- ✅ 验证方法已提供

### 🎯 下一步

**立即开始**：
1. 创建 Telegram Bot
2. 获取 User ID
3. 上传代码到 GitHub
4. 通过 Claude Code 部署

**或在 Claude Code 中说**：
> "请帮我部署这个 Telegram-Crypto-Alerts 项目到 Render，使用已配置的 MCP 工具"

### 💡 优势

- 🚀 **自动化** - MCP 工具处理所有步骤
- ⚡ **快速** - 无需手动操作
- 🔧 **灵活** - 随时更新配置
- 📊 **监控** - 实时状态和日志
- 💰 **免费** - 750小时/月

### 📖 更多资源

- [Render 官方文档](https://render.com/docs)
- [Render MCP 文档](https://mcp.render.com/mcp)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [项目 GitHub](https://github.com/hschickdevs/Telegram-Crypto-Alerts)

---

**祝你部署顺利！** 🚀

如果有任何问题，请随时在 Claude Code 中提问，MCP 工具会帮助解决所有问题。

---

*最后更新：2025-11-08*
