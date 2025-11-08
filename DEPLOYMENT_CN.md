# 🌏 Telegram-Crypto-Alerts 中国大陆/香港部署指南

> **特别版** - 针对中国大陆和香港用户的免费云服务器部署指南

## 📋 目录
- [项目简介](#-项目简介)
- [推荐平台](#-推荐平台)
- [方案一：Render 部署（推荐⭐⭐⭐⭐⭐）](#-方案一render-部署推荐)
- [方案二：Fly.io 部署（备用⭐⭐⭐⭐）](#-方案二flyio-部署备用)
- [方案三：Koyeb 部署（新兴⭐⭐⭐）](#-方案三koyeb-部署新兴)
- [方案四：Northflank 部署（现代⭐⭐⭐）](#-方案四northflank-部署现代)
- [方案五：Oracle Cloud（老牌稳定⭐⭐⭐）](#-方案五oracle-cloud老牌稳定)
- [访问测试](#-访问测试)
- [性能对比](#-性能对比)
- [常见问题](#-常见问题)
- [总结](#-总结)

---

## 🌟 项目简介

**Telegram-Crypto-Alerts** 是一个加密货币价格和技术指标告警机器人，支持：
- 📊 实时监控加密货币价格
- 📈 30+ 技术指标告警
- 📱 Telegram 通知推送
- ⏰ 24/7 持续运行

---

## 🎯 推荐平台

针对中国大陆和香港用户，我们精选了 5 个最佳选择：

| 平台 | 访问难度 | 免费额度 | 优势 | 推荐度 |
|------|----------|----------|------|--------|
| **Render** | 🌏 全球 CDN，中国友好 | 750小时/月 | 最稳定、访问好 | ⭐⭐⭐⭐⭐ |
| **Fly.io** | 🌏 有香港节点 | 256MB RAM | 亚太节点、速度快 | ⭐⭐⭐⭐ |
| **Koyeb** | 🌏 欧洲平台，CDN 加速 | 每月 1000 请求 | 新兴、现代化 | ⭐⭐⭐ |
| **Northflank** | 🌏 全球化部署 | 每月 1000 分钟 | 界面友好、简单 | ⭐⭐⭐ |
| **Oracle Cloud** | 🌏 甲骨文云，访问稳定 | 永久免费 | 资源最多、永久免费 | ⭐⭐⭐ |

### 为什么选择这些平台？

1. **访问友好** - 在中国大陆和香港都可以正常访问
2. **免费额度足够** - 足以支持 24/7 运行
3. **有 CLI 工具** - 支持本地直接部署
4. **简单易用** - 对新手友好

---

## 🏆 方案一：Render 部署（推荐）

> **Render** 是目前最适合中国大陆用户的云平台

### 优势
- ✅ 全球 CDN 加速，中国大陆访问友好
- ✅ 每月 750 小时免费（超过 Railway 的 500 小时）
- ✅ 稳定可靠的云平台
- ✅ 简单易用的 Web 界面
- ✅ 自动部署和更新
- ✅ 强大的日志系统

### 部署步骤

#### 第1步：注册 Render 账号

1. 打开 [https://render.com](https://render.com)
2. 点击 **"Get Started for Free"**
3. 选择 **"Continue with Email"**（推荐，避免 GitHub 访问问题）
4. 使用邮箱注册（建议用 Gmail、Outlook 等国际邮箱）

> 💡 **提示**：如果 GitHub 访问慢，可以直接用邮箱注册

#### 第2步：安装 Render CLI（可选）

如果想使用 CLI 部署：

**macOS**：
```bash
brew install render-cli
```

**Windows**：
```powershell
scoop bucket add extras
scoop install render
```

**验证安装**：
```bash
render --version
```

#### 第3步：创建 Telegram Bot

1. 在 Telegram 中搜索 **"@BotFather"**
2. 发送 `/newbot` 命令
3. 设置 bot 名称和用户名
4. 复制 **Bot Token**

#### 第4步：获取 User ID

1. 在 Telegram 中搜索 **"@userinfobot"**
2. 发送 `/start` 命令
3. 复制 **User ID**（数字）

#### 第5步：上传项目到 GitHub

如果还没有 GitHub 仓库：

1. 创建新仓库
2. 上传项目代码：
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/Telegram-Crypto-Alerts.git
git push -u origin main
```

#### 第6步：在 Render 上创建服务

1. 登录 Render 控制台
2. 点击 **"New +"** → **"Web Service"**
3. 选择 **"Build and deploy from a Git repository"**
4. 如果用邮箱注册，点击 **"Import from GitHub"** 并授权
5. 选择你的仓库

#### 第7步：配置 Web Service

| 配置项 | 值 | 说明 |
|--------|----|----- |
| **Name** | `telegram-crypto-alerts` | 服务名 |
| **Region** | Singapore | 选择新加坡（离中国近） |
| **Branch** | `main` | 分支名 |
| **Root Directory** | 空 | 根目录 |
| **Runtime** | `Python 3` | 选择 Python |
| **Build Command** | `pip install -r requirements.txt` | 安装依赖 |
| **Start Command** | `python -m src` | 启动命令 |

> 🎯 **重要**：选择 **Singapore** 区域，在中国访问最快

#### 第8步：配置环境变量

在 **"Environment"** 区域，添加以下变量：

| 变量名 | 值 | 说明 |
|--------|----|----- |
| `TELEGRAM_BOT_TOKEN` | 你的 Bot Token | 从 BotFather 获得 |
| `TELEGRAM_USER_ID` | 你的 User ID | 从 userinfobot 获得 |
| `LOCATION` | `us` 或 `global` | 根据位置选择 |
| `TAAPIIO_TIER` | `free` | 默认值 |

#### 第9步：创建服务

1. 点击 **"Create Web Service"**
2. 等待 5-10 分钟部署完成
3. 看到 **"Deployed"** 状态表示成功

#### 第10步：测试机器人

1. 在 Telegram 搜索你的机器人
2. 发送 `/start` 测试
3. 发送 `/help` 查看命令

**创建测试告警**：
```
/new_alert BTC/USDT PRICE ABOVE 50000
```

### 常见问题

**Q: 构建失败？**
A: 检查 `requirements.txt` 是否存在，确保所有依赖正确

**Q: 访问慢？**
A: 在服务设置中修改 Region 为 Singapore

**Q: 如何更新？**
A: 推送代码到 GitHub，Render 自动部署

---

## 🚀 方案二：Fly.io 部署（备用）

> **Fly.io** 有香港节点，中国大陆访问速度最快

### 优势
- ✅ 亚太地区有节点（香港、新加坡）
- ✅ 较低的延迟
- ✅ 支持 Docker 部署
- ✅ 免费额度：256MB RAM + 3GB 存储
- ✅ CLI 工具强大

### 部署步骤

#### 第1步：注册 Fly.io

1. 打开 [https://fly.io](https://fly.io)
2. 点击 **"Sign up"**
3. 使用 GitHub 账号登录

#### 第2步：安装 Fly CLI

**macOS/Linux**：
```bash
curl -L https://fly.io/install.sh | sh
```

**Windows**（需要 WSL）：
```bash
# 在 WSL 中运行
curl -L https://fly.io/install.sh | sh
```

**验证安装**：
```bash
flyctl --version
```

#### 第3步：登录 Fly.io
```bash
flyctl auth login
```

#### 第4步：准备 Dockerfile

在项目根目录创建 `Dockerfile.fly.io`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

CMD ["python3", "-m", "src"]
```

#### 第5步：初始化应用
```bash
flyctl apps create telegram-crypto-alerts
```

#### 第6步：配置 fly.toml

Fly CLI 会自动生成配置文件，修改关键部分：

```toml
# fly.toml
app = "telegram-crypto-alerts"

[build]
  dockerfile = "Dockerfile.fly.io"

[env]
  PORT = "8080"

[[services]]
  internal_port = 8080
  processes = ["app"]

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

#### 第7步：部署
```bash
flyctl deploy
```

#### 第8步：配置环境变量
```bash
flyctl secrets set TELEGRAM_BOT_TOKEN=你的Token
flyctl secrets set TELEGRAM_USER_ID=你的UserID
flyctl secrets set LOCATION=global
```

#### 第9步：测试
```bash
flyctl status
```

---

## 💫 方案三：Koyeb 部署（新兴）

> **Koyeb** 是法国新兴云平台，全球化部署

### 优势
- ✅ 欧洲平台，中国大陆部分地区可访问
- ✅ 现代化界面和 CLI
- ✅ Docker 原生支持
- ✅ 全球边缘计算
- ✅ 每月 1000 免费请求

### 部署步骤

#### 第1步：注册 Koyeb

1. 打开 [https://www.koyeb.com](https://www.koyeb.com)
2. 点击 **"Start for free"**
3. 使用 GitHub 登录

#### 第2步：安装 Koyeb CLI

**macOS**：
```bash
brew install koyeb/koyeb/koyeb
```

**Linux**：
```bash
curl -sL https://github.com/koyeb/koyeb-cli/releases/latest/download/koyeb-linux-amd.tgz | tar -xz
sudo mv koyeb /usr/local/bin/
```

**Windows**（需要 WSL）：
```bash
# 在 WSL 中运行
curl -sL https://github.com/koyeb/koyeb-cli/releases/latest/download/koyeb-linux-amd.tgz | tar -xz
sudo mv koyeb /usr/local/bin/
```

#### 第3步：创建应用

1. 登录 Koyeb 控制台
2. 点击 **"Create Service"**
3. 选择 **"Deploy from GitHub"**
4. 选择你的仓库

#### 第4步：配置服务

| 配置项 | 值 | 说明 |
|--------|----|----- |
| **Name** | `telegram-crypto-alerts` | 服务名 |
| **Git Repository** | 选择你的仓库 | GitHub 仓库 |
| **Branch** | `main` | 分支 |
| **Build Command** | `pip install -r requirements.txt` | 构建命令 |
| **Run Command** | `python -m src` | 运行命令 |

#### 第5步：环境变量

在 **"Environment"** 选项卡添加：
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_USER_ID`
- `LOCATION`
- `TAAPIIO_TIER=free`

#### 第6步：部署

1. 点击 **"Deploy"**
2. 等待完成

---

## 🎨 方案四：Northflank 部署（现代）

> **Northflank** 是现代化的云平台，界面友好

### 优势
- ✅ 现代化 Web 界面
- ✅ 简单易用
- ✅ 免费额度：1000 分钟/月
- ✅ 自动扩缩容
- ✅ 中国大陆访问情况良好

### 部署步骤

#### 第1步：注册 Northflank

1. 打开 [https://www.northflank.com](https://www.northflank.com)
2. 点击 **"Start Free"**
3. 使用 GitHub 登录

#### 第2步：创建新项目

1. 点击 **"Create"** → **"From Git"**
2. 选择 GitHub 仓库
3. 选择分支

#### 第3步：配置构建

| 配置项 | 值 |
|--------|----|
| **Name** | `telegram-crypto-alerts` |
| **Source** | 选择你的仓库 |
| **Branch** | `main` |
| **Type** | `Service` |
| **Stack** | `Python` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python -m src` |

#### 第4步：环境变量

在 **"Environment"** 选项卡添加所需变量

#### 第5步：部署

1. 点击 **"Create & Deploy"**
2. 等待完成

---

## 🏛️ 方案五：Oracle Cloud（老牌稳定）

> **Oracle Cloud** - 甲骨文云，资源最充足

### 优势
- ✅ 2 vCPU + 1GB RAM + 47GB 存储
- ✅ 永久免费
- ✅ 中国大陆访问稳定
- ✅ 完全控制

### 部署步骤

#### 第1步：注册 Oracle Cloud

1. 打开 [https://www.oracle.com/cloud/free](https://www.oracle.com/cloud/free)
2. 点击 **"Start for free"**
3. 完成注册（需要信用卡验证）

#### 第2步：创建 Compute Instance

1. 登录 Oracle Cloud 控制台
2. 左侧菜单 → **"Compute"** → **"Instances"**
3. 点击 **"Create Instance"**
4. 选择：
   - **Image**: Ubuntu 20.04 LTS
   - **Shape**: VM.Standard.E2.1.Micro
   - **SSH Key**: 生成新密钥

#### 第3步：连接服务器
```bash
chmod 400 your_private_key.pem
ssh -i your_private_key.pem ubuntu@YOUR_PUBLIC_IP
```

#### 第4步：安装依赖
```bash
sudo apt update
sudo apt install python3 python3-pip git -y
```

#### 第5步：部署项目
```bash
cd /home/ubuntu
git clone https://github.com/YOUR_USERNAME/Telegram-Crypto-Alerts.git
cd Telegram-Crypto-Alerts
pip3 install -r requirements.txt
```

#### 第6步：配置环境变量
```bash
nano .env
```

#### 第7步：运行
```bash
python3 -m src
```

---

## 🧪 访问测试

### 测试各平台访问速度

| 平台 | 中国大陆 | 香港 | 速度 |
|------|----------|------|------|
| **Render** | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Fly.io** | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Koyeb** | ⚠️ | ✅ | ⭐⭐⭐ |
| **Northflank** | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Oracle Cloud** | ✅ | ✅ | ⭐⭐⭐ |

### 访问测试命令

**测试延迟**：
```bash
# Linux/macOS
ping render.com
ping fly.io
ping koyeb.com
ping northflank.com
ping oracle.com

# Windows
ping render.com
```

**测试下载速度**（以 Render 为例）：
```bash
curl -I https://telegram-crypto-alerts.onrender.com
```

---

## 📊 性能对比

### 免费额度对比

| 平台 | 内存 | 存储 | 运行时间 | 地区 |
|------|------|------|----------|------|
| **Render** | 1GB | N/A | 750小时/月 | 全球 |
| **Fly.io** | 256MB | 3GB | 无限制 | 全球+香港 |
| **Koyeb** | 512MB | N/A | 1000请求/月 | 全球 |
| **Northflank** | 1GB | N/A | 1000分钟/月 | 全球 |
| **Oracle Cloud** | 1GB | 47GB | 24/7 | 全球 |

### 功能对比

| 特性 | Render | Fly.io | Koyeb | Northflank | Oracle |
|------|--------|--------|-------|------------|--------|
| **CLI 工具** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **自动部署** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **日志系统** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Docker 支持** | ❌ | ✅ | ✅ | ❌ | ✅ |
| **Web 界面** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **自定义域名** | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## ❓ 常见问题

### Q1: 平台访问慢怎么办？

**A**: 解决方案：
1. 使用 VPN（香港/新加坡节点）
2. 选择离中国近的地域（如 Singapore、Tokyo）
3. 尝试不同平台（Render 通常最快）

### Q2: GitHub 访问慢怎么办？

**A**: 解决方案：
1. 使用镜像站（如 fastgit.org）
2. 直接用邮箱注册平台（Render 支持）
3. 使用国内代码托管（Gitee）
4. 提前下载代码本地存储

### Q3: 推荐哪个平台？

**A**: 推荐顺序：
1. **Render** - 最好用、最稳定
2. **Fly.io** - 速度最快（有香港节点）
3. **Koyeb** - 现代化、新兴
4. **Northflank** - 界面友好
5. **Oracle Cloud** - 资源最多

### Q4: 如何迁移到其他平台？

**A**: 步骤：
1. 导出环境变量
2. 在新平台重新创建服务
3. 导入环境变量
4. 测试功能

### Q5: 可以用国内云平台吗？

**A**: 为什么不推荐：
- 阿里云、腾讯云等没有完全免费方案
- 需要实名认证
- 价格较高
- 技术门槛高

### Q6: 部署失败怎么办？

**A**: 排查步骤：
1. 查看构建日志
2. 检查 `requirements.txt`
3. 验证环境变量
4. 测试本地运行

### Q7: 如何监控应用？

**A**: 各平台都提供：
- Web 界面日志
- 实时状态
- 性能指标

### Q8: 机器人没有响应？

**A**: 检查清单：
- 环境变量是否正确
- Bot Token 是否有效
- 是否有错误日志
- 网络是否正常

---

## 💡 选择建议

### 🎯 根据你的情况选择

**完全新手** → **Render**
- 最简单的界面
- 最好的文档
- 最多的教程

**追求速度** → **Fly.io**
- 有香港节点
- 延迟最低
- 速度最快

**喜欢新事物** → **Koyeb**
- 现代化设计
- 最新技术
- 欧洲平台

**想要稳定** → **Oracle Cloud**
- 大厂保障
- 资源最多
- 永久免费

**需要简单** → **Northflank**
- 界面清晰
- 操作简单
- 现代化

### 📋 最终推荐

**首选**：**Render**
- ✅ 在中国大陆访问最好
- ✅ 免费额度最多（750小时）
- ✅ 最稳定可靠
- ✅ 界面最友好

**备选**：**Fly.io**
- ✅ 香港节点
- ✅ 速度快
- ✅ Docker 支持

---

## 📈 总结

### ✅ 本文档适合的用户
- 中国大陆和香港用户
- Railway 访问受限的用户
- 需要稳定云服务的用户
- 新手和经验用户

### 🎯 最佳选择
**Render** - 简单、稳定、访问好

### 📊 关键优势
- 所有平台在中国大陆都可访问
- 免费额度足够 24/7 运行
- 有 CLI 工具支持
- 对新手友好

### 🚀 下一步
1. 选择一个平台
2. 按照文档步骤部署
3. 测试机器人功能
4. 享受加密货币告警服务

---

## 🔗 链接汇总

### 平台官网
- [Render](https://render.com) - 推荐首选
- [Fly.io](https://fly.io) - 速度最快
- [Koyeb](https://www.koyeb.com) - 现代化
- [Northflank](https://www.northflank.com) - 界面友好
- [Oracle Cloud](https://www.oracle.com/cloud/free) - 资源最多

### 工具下载
- [GitHub Desktop](https://desktop.github.com)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 学习资源
- [Telegram Bot 官方文档](https://core.telegram.org/bots/api)
- [Python 入门教程](https://www.runoob.com/python/)

---

**祝你部署顺利！** 🎉

如果遇到问题，可以：
1. 查看各平台的官方文档
2. 在评论区提问
3. 参考其他用户的经验

---

*最后更新：2025-11-08*
