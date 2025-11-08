# 🚀 Telegram-Crypto-Alerts 免费云服务器部署指南

> **小白友好版** - 一步步教你将加密货币告警机器人部署到免费云服务器

## 📋 目录
- [项目简介](#-项目简介)
- [为什么选择这些免费云服务器？](#-为什么选择这些免费云服务器)
- [方案一：Railway 部署（推荐⭐⭐⭐⭐⭐）](#-方案一railway-部署推荐)
- [方案二：Render 部署（备选⭐⭐⭐）](#-方案二render-部署备选)
- [方案三：Oracle Cloud 部署（高级⭐⭐）](#-方案三oracle-cloud-部署高级)
- [配置说明](#-配置说明)
- [验证部署成功](#-验证部署成功)
- [常见问题解答](#-常见问题解答)
- [费用说明](#-费用说明)
- [总结](#-总结)

---

## 🌟 项目简介

**Telegram-Crypto-Alerts** 是一个加密货币价格和技术指标告警机器人。

### 它能做什么？
- 📊 实时监控加密货币价格变动
- 📈 监控技术指标（RSI、MACD、布林带等）
- 📱 通过 Telegram 发送告警通知
- ⏰ 支持 30+ 种技术指标
- 💰 支持多种交易对

### 需要准备什么？
- ✅ Telegram 账号
- ✅ Telegram Bot Token（免费）
- ✅ GitHub 账号（免费）
- ✅ 邮箱（注册云服务器用）

---

## 💡 为什么选择这些免费云服务器？

我们选择了三个最适合小白的免费云服务器方案：

| 平台 | 免费额度 | CLI支持 | 难度 | 推荐度 |
|------|----------|---------|------|--------|
| **Railway** | 500小时/月 | ✅ | ⭐ | ⭐⭐⭐⭐⭐ |
| **Render** | 750小时/月 | ✅ | ⭐⭐ | ⭐⭐⭐ |
| **Oracle Cloud** | 永久免费 | ❌ | ⭐⭐⭐⭐ | ⭐⭐ |

**推荐理由**：
- 🚀 **Railway**: 最简单，CLI工具最好用，有中文文档
- 🎯 **Render**: 稳定可靠，GitHub集成好
- 💪 **Oracle**: 资源最充足，但配置复杂

---

## 🏆 方案一：Railway 部署（推荐）

> **Railway** 是最适合新手的云平台，有强大的 CLI 工具和简洁的界面

### 优势
- ✅ 每月 500 小时免费运行时间（足够 24x7 运行）
- ✅ 一键部署，支持 GitHub 集成
- ✅ 强大的 CLI 工具
- ✅ 简单易用的 Web 界面
- ✅ 免费 SSL 证书
- ✅ 自动部署更新

### 部署步骤

#### 第1步：注册 Railway 账号

1. 打开 [https://railway.app](https://railway.app) （请使用 VPN 如果无法访问）
2. 点击 **"Login"** → 选择 **"Login with GitHub"**
3. 使用 GitHub 账号登录

#### 第2步：安装 Railway CLI

打开终端（macOS/Linux/Windows），运行以下命令：

**macOS（使用 Homebrew）**：
```bash
brew install railway
```

**Windows（使用 npm）**：
```bash
npm install -g @railway/cli
```

**Linux/macOS（直接安装）**：
```bash
curl -fsSL https://railway.app/install.sh | sh
```

**验证安装**：
```bash
railway --version
```
应该看到类似 `railway/1.x.x` 的版本信息

#### 第3步：创建 Telegram Bot

1. 在 Telegram 中搜索 **"@BotFather"**
2. 发送 `/newbot` 命令
3. 按提示输入 bot 名称（例如：`My Crypto Alert Bot`）
4. 输入用户名（必须以 `bot` 结尾，例如：`my_crypto_alert_bot`）
5. 复制 BotFather 给你的 **Bot Token**（格式类似：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）

> 📝 **保存这个 Token！** 部署时需要用到

#### 第4步：获取你的 Telegram User ID

1. 在 Telegram 中搜索 **"@userinfobot"**
2. 发送 `/start` 命令
3. 机器人会返回你的信息，包含 **User ID**（一串数字）
4. 复制这个数字

#### 第5步：准备项目

1. 将项目上传到你的 GitHub：
```bash
# 在项目目录下
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/Telegram-Crypto-Alerts.git
git push -u origin main
```

2. 登录 Railway，点击 **"New Project"**
3. 选择 **"Deploy from GitHub repo"**
4. 选择你的项目仓库

#### 第6步：配置环境变量

1. 在 Railway 项目页面，点击 **"Variables"** 选项卡
2. 点击 **"New Variable"** 添加以下变量：

| 变量名 | 值 | 说明 |
|--------|----|----- |
| `TELEGRAM_BOT_TOKEN` | 你的 Bot Token | 从 BotFather 获得 |
| `TELEGRAM_USER_ID` | 你的 User ID | 从 userinfobot 获得 |
| `LOCATION` | `us` 或 `global` | 你的地理位置 |
| `TAAPIIO_APIKEY` | （可选）| Taapi.io API Key |
| `TAAPIIO_TIER` | `free` | 你的订阅等级 |

> 💡 **提示**：TAAPIIO_APIKEY 是可选的，没有的话机器人也能运行基本功能

#### 第7步：部署

1. 在 Railway 页面，点击 **"Deploy"** 选项卡
2. 你会看到部署进度
3. 等待 2-3 分钟，部署完成

#### 第8步：获取 Optional Taapi.io API Key（推荐）

Taapi.io 提供技术指标数据，更推荐使用：

1. 打开 [https://taapi.io](https://taapi.io)
2. 点击 **"Get API Key"** 注册免费账号
3. 免费版限制：每 20 秒 1 个请求
4. 在 Railway 的 Variables 中添加 `TAAPIIO_APIKEY`

### 部署成功验证

1. 打开 Railway 控制台，进入你的项目
2. 点击 **"Settings"** → **"Domains"**
3. 记录显示的域名（如果有用的话）

#### 测试机器人

1. 在 Telegram 中搜索你的机器人
2. 发送 `/start` 命令
3. 机器人应该回应欢迎信息
4. 发送 `/help` 查看可用命令

**测试告警**：
```
/new_alert BTC/USDT PRICE ABOVE 50000
```

如果收到确认消息，说明部署成功！🎉

### 常见 Railway 部署问题

**Q: 部署失败怎么办？**
A: 查看 Railway 控制台的 **"Logs"** 选项卡，通常是环境变量配置错误

**Q: 如何更新代码？**
A: 只需要将代码推送到 GitHub，Railway 会自动部署

**Q: 如何查看日志？**
A: Railway 控制台 → **"Logs"** 选项卡

**Q: 如何停止服务？**
A: Railway 控制台 → **"Settings"** → **"Danger"** → **"Stop Project"**

---

## 🎯 方案二：Render 部署（备选）

> **Render** 是另一个优秀的云平台，稳定可靠

### 优势
- ✅ 每月 750 小时免费（更多免费时间）
- ✅ 支持自动部署
- ✅ 简单易用
- ✅ 免费 SSL

### 部署步骤

#### 第1步：注册 Render 账号
1. 打开 [https://render.com](https://render.com)
2. 点击 **"Get Started for Free"**
3. 使用 GitHub 账号登录

#### 第2步：创建 Web Service
1. 点击 **"New +"** → **"Web Service"**
2. 选择 **"Build and deploy from a Git repository"**
3. 连接你的 GitHub 仓库

#### 第3步：配置构建
1. **Name**: 填写项目名（例如：`telegram-crypto-alerts`）
2. **Region**: 选择离你最近的区域
3. **Branch**: `main`
4. **Root Directory**: 留空
5. **Runtime**: `Python 3`
6. **Build Command**: `pip install -r requirements.txt`
7. **Start Command**: `python -m src`

#### 第4步：配置环境变量
1. 滚动到 **"Environment"** 部分
2. 添加与 Railway 相同的变量（见上表）

#### 第5步：部署
1. 点击 **"Create Web Service"**
2. 等待 5-10 分钟部署完成

### 测试
1. 在 Telegram 中搜索你的机器人
2. 发送 `/start` 测试

---

## 💪 方案三：Oracle Cloud 部署（高级）

> **Oracle Cloud** 提供真正的云服务器，资源最充足，但配置较复杂

### 优势
- ✅ 永久免费
- ✅ 2 个 AMD CPU
- ✅ 1GB 内存
- ✅ 47GB 存储
- ✅ 完整 root 权限

### 准备条件
- 需要信用卡（不会扣费，只是验证）
- 需要手机验证
- 配置相对复杂（建议有一定 Linux 基础）

### 部署步骤

#### 第1步：注册 Oracle Cloud
1. 打开 [https://www.oracle.com/cloud/free](https://www.oracle.com/cloud/free)
2. 点击 **"Start for free"**
3. 完成注册（需要信用卡验证）

#### 第2步：创建 Compute Instance
1. 登录 Oracle Cloud 控制台
2. 左侧菜单 → **"Compute"** → **"Instances"**
3. 点击 **"Create Instance"**
4. 选择 **"Always Free-eligible"** 镜像
5. 选择 **Ubuntu 20.04 LTS**
6. 选择 **VM.Standard.E2.1.Micro**（免费版）
7. 生成 SSH 密钥对
8. 点击 **"Create"**

#### 第3步：连接服务器
```bash
# 下载私钥到本地（.pem 文件）
chmod 400 your_private_key.pem
ssh -i your_private_key.pem ubuntu@YOUR_PUBLIC_IP
```

#### 第4步：在服务器上安装依赖
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python
sudo apt install python3 python3-pip git -y

# 安装项目依赖
cd /home/ubuntu
git clone https://github.com/YOUR_USERNAME/Telegram-Crypto-Alerts.git
cd Telegram-Crypto-Alerts
pip3 install -r requirements.txt
```

#### 第5步：配置环境变量
```bash
# 创建 .env 文件
nano .env
```

添加内容：
```
TELEGRAM_BOT_TOKEN=你的BotToken
TELEGRAM_USER_ID=你的UserID
LOCATION=us
TAAPIIO_TIER=free
```

#### 第6步：运行项目
```bash
# 测试运行
python3 -m src

# 后台运行
nohup python3 -m src > bot.log 2>&1 &
```

#### 第7步：设置开机自启（可选）
```bash
# 创建 systemd 服务
sudo nano /etc/systemd/system/crypto-alerts.service
```

内容：
```ini
[Unit]
Description=Crypto Alerts Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Telegram-Crypto-Alerts
ExecStart=/usr/bin/python3 -m src
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable crypto-alerts
sudo systemctl start crypto-alerts
sudo systemctl status crypto-alerts
```

### 常见问题

**Q: 无法连接服务器？**
A: 检查 Oracle Cloud 安全组设置，确保允许 SSH（端口 22）

**Q: 如何更新代码？**
A: 登录服务器，运行 `git pull` 重新部署

**Q: 如何查看日志？**
A: `tail -f bot.log` 或 `sudo systemctl status crypto-alerts`

---

## ⚙️ 配置说明

### 必需的环境变量

| 变量名 | 必需 | 示例值 | 获取方式 |
|--------|------|--------|----------|
| `TELEGRAM_BOT_TOKEN` | ✅ | `1234567890:ABC...` | BotFather |
| `TELEGRAM_USER_ID` | ✅ | `123456789` | userinfobot |
| `LOCATION` | ✅ | `us` 或 `global` | 根据你所在地区 |
| `TAAPIIO_APIKEY` | ❌ | `eyJ...` | taapi.io |
| `TAAPIIO_TIER` | ❌ | `free` | 默认值即可 |

### Bot Token 和 User ID 详细获取

#### 获取 Bot Token
1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot`
3. 设置名称和用户名
4. 复制 Bot Token（格式：`1234567890:ABC...`）

#### 获取 User ID
1. 在 Telegram 搜索 `@userinfobot`
2. 发送 `/start`
3. 复制返回的数字

### Taapi.io API Key（可选）

**为什么需要？**
- Taapi.io 提供 30+ 技术指标数据
- 免费版限制：每 20 秒 1 个请求
- 没有也能运行，但只能监控价格

**如何获取？**
1. 打开 [https://taapi.io](https://taapi.io)
2. 点击 **"Get API Key"**
3. 注册账号（用邮箱）
4. 登录后查看 API Key
5. 复制到 `TELEGRAM_BOT_TOKEN` 变量

---

## ✅ 验证部署成功

### 检查清单

- [ ] 成功部署到云平台
- [ ] 在 Telegram 找到你的机器人
- [ ] 发送 `/start` 有响应
- [ ] 发送 `/help` 有响应
- [ ] 成功创建测试告警

### 测试命令

**1. 基础功能测试**
```
/start
/help
/info
```

**2. 创建价格告警**
```
/new_alert BTC/USDT PRICE ABOVE 50000
```

**3. 列出告警**
```
/list_alerts
```

**4. 删除告警**
```
/delete_alert 1
```

### 日志查看

#### Railway
- 控制台 → **"Logs"** 选项卡

#### Render
- 控制台 → **"Logs"** 选项卡

#### Oracle Cloud
```bash
tail -f bot.log
```

### 预期日志

正常运行时应该看到类似日志：
```
[INFO] 初始化 Taapi.io...
[INFO] 启动 Telegram 机器人...
[INFO] 启动 CEX 告警进程...
[INFO] 启动技术指标进程...
[INFO] 等待初始化...
```

如果看到错误信息，检查环境变量配置。

---

## ❓ 常见问题解答

### Q1: 机器人没有响应？

**可能原因**：
- ❌ 环境变量配置错误
- ❌ Bot Token 不正确
- ❌ 程序崩溃

**解决方法**：
1. 检查环境变量是否正确
2. 重新验证 Bot Token
3. 查看日志排查错误

### Q2: 部署失败？

**Railway/Render**：
- 检查 `requirements.txt` 是否存在
- 检查是否有语法错误
- 查看构建日志

**Oracle Cloud**：
- 检查系统依赖是否安装
- 检查 Python 版本
- 查看应用日志

### Q3: 如何更新代码？

**Railway/Render**：
1. 更新 GitHub 仓库
2. 云平台自动部署

**Oracle Cloud**：
1. 登录服务器
2. 运行 `git pull`
3. 重启服务

### Q4: 告警没有触发？

**检查清单**：
- [ ] 告警条件是否合理
- [ ] 监控的交易对是否存在
- [ ] 网络连接是否正常
- [ ] 是否有速率限制

### Q5: 如何停止服务？

**Railway**：
- 控制台 → Settings → Stop

**Render**：
- 控制台 → Settings → Stop

**Oracle Cloud**：
```bash
sudo systemctl stop crypto-alerts
```

### Q6: 免费额度用完了怎么办？

**Railway**：
- 升级付费计划
- 或者创建新账号

**Render**：
- 升级付费计划
- 或者暂停服务一段时间

**Oracle Cloud**：
- 免费额度永久有效，通常不会用完

### Q7: 可以部署多个机器人吗？

**可以**！每个机器人需要：
- 不同的 Bot Token
- 不同的 GitHub 仓库
- 独立的环境变量

### Q8: 如何备份数据？

**配置备份**：
- 导出环境变量到本地

**告警配置**：
- 机器人在本地存储，白名单在 `whitelist/users/`

### Q9: 如何迁移到新平台？

1. 导出环境变量
2. 在新平台重新部署
3. 导入环境变量
4. 测试功能

### Q10: 机器人安全吗？

- ✅ 机器人不会存储敏感信息
- ✅ 白名单机制防止滥用
- ✅ 环境变量加密存储
- ✅ 建议定期更新 Bot Token

---

## 💰 费用说明

### 完全免费方案

| 平台 | 成本 | 限制 |
|------|------|------|
| **Railway** | $0/月 | 500小时/月 |
| **Render** | $0/月 | 750小时/月 |
| **Oracle Cloud** | $0/月 | 永久免费 |

### 付费升级（可选）

| 平台 | 付费计划 | 价格 | 优势 |
|------|----------|------|------|
| Railway | Pro | $5/月 | 无限制运行时间 |
| Render | Starter | $7/月 | 无限制运行时间 |
| Oracle Cloud | - | - | 已经是永久免费 |

### 实际成本分析

**典型用户**：
- 每天运行 24 小时
- 一个月 30 天 = 720 小时
- **Railway**: 需要付费（500小时不够）
- **Render**: 可以免费（750小时够用）
- **Oracle Cloud**: 完全免费

**结论**：
- 轻度使用（<500小时/月）: Railway
- 中度使用（500-750小时/月）: Render
- 重度使用（>750小时/月）: Oracle Cloud

---

## 📊 性能对比

### 三种方案对比

| 特性 | Railway | Render | Oracle Cloud |
|------|---------|--------|--------------|
| **部署难度** | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **免费额度** | 500小时 | 750小时 | 永久免费 |
| **CLI 支持** | ✅ 优秀 | ✅ 良好 | ❌ 无 |
| **自动部署** | ✅ | ✅ | ❌ 手动 |
| **资源** | 1 vCPU, 1GB RAM | 1 vCPU, 1GB RAM | 2 vCPU, 1GB RAM |
| **稳定性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

### 推荐策略

**新手首选**：Railway
- 最简单的 CLI 工具
- 文档清晰
- 社区活跃

**稳定首选**：Render
- 最稳定的平台
- 最多免费时间
- 专业的云服务

**资源首选**：Oracle Cloud
- 最多免费资源
- 完全免费
- 需要技术基础

---

## 🎉 总结

恭喜！你已经学会了三种免费部署 Telegram-Crypto-Alerts 的方法：

### 推荐部署路径

1. **第一次部署** → 选择 **Railway**
   - 简单、快速、CLI 工具友好
   - 适合学习和小规模使用

2. **稳定运行** → 考虑 **Render**
   - 更多免费时间
   - 更稳定可靠

3. **大规模使用** → 升级到 **Oracle Cloud**
   - 永久免费
   - 更多资源

### 下一步

- [ ] 部署你的第一个机器人
- [ ] 测试各种告警功能
- [ ] 根据使用情况选择合适平台
- [ ] 考虑升级付费计划
- [ ] 分享给朋友使用

### 学习资源

- [Telegram Bot API 官方文档](https://core.telegram.org/bots/api)
- [Railway 官方文档](https://docs.railway.app)
- [Render 官方文档](https://render.com/docs)
- [Oracle Cloud 文档](https://docs.oracle.com/en-us/iaas/)

### 获得帮助

- 项目 GitHub Issues
- Railway Discord 社区
- Render 社区论坛
- Oracle Cloud 社区

---

**祝你部署顺利！** 🚀

如果遇到问题，请参考常见问题解答或查看项目文档。

---

*最后更新：2025-11-08*
