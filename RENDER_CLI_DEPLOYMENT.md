# 💻 Render CLI 部署指南 - 小白专用版

> **最详细的 Render CLI 部署教程** - 从零开始，手把手教你用命令行部署 Telegram-Crypto-Alerts

## 📋 目录
- [什么是 Render CLI？](#-什么是-render-cli)
- [准备工作](#-准备工作)
- [步骤一：安装 Render CLI](#-步骤一安装-render-cli)
- [步骤二：注册 Render 账号](#-步骤二注册-render-账号)
- [步骤三：创建 Telegram Bot](#-步骤三创建-telegram-bot)
- [步骤四：获取 User ID](#-步骤四获取-user-id)
- [步骤五：准备项目代码](#-步骤五准备项目代码)
- [步骤六：登录 Render CLI](#-步骤六登录-render-cli)
- [步骤七：初始化项目](#-步骤七初始化项目)
- [步骤八：配置环境变量](#-步骤八配置环境变量)
- [步骤九：部署项目](#-步骤九部署项目)
- [步骤十：验证部署](#-步骤十验证部署)
- [CLI 常用命令](#-cli-常用命令)
- [高级功能](#-高级功能)
- [常见问题](#-常见问题)
- [故障排查](#-故障排查)
- [总结](#-总结)

---

## 🤔 什么是 Render CLI？

**Render CLI** 是 Render 官方提供的命令行工具，让你可以在本地终端直接部署应用到 Render 云服务器。

### 为什么要用 CLI？

| 方式 | CLI 命令行 | Web 界面 |
|------|------------|----------|
| **学习难度** | ⭐⭐⭐⭐⭐ 一次学会，终身受用 | ⭐⭐⭐ 每次都要点点点 |
| **操作速度** | 🚀 10 秒完成部署 | ⏱️ 2-3 分钟操作 |
| **重复部署** | ✅ 一条命令搞定 | ❌ 每次都要重新配置 |
| **自动化** | ✅ 可写脚本自动化 | ❌ 无法自动化 |
| **调试** | ✅ 可查看详细日志 | ✅ 也能看日志 |
| **适合人群** | 开发者、程序员 | 新手、小白 |

**结论**：CLI 更高效、更专业，一次学会终身受用！

---

## 🛠️ 准备工作

### 你需要准备的东西

- ✅ **一台电脑**（Windows、macOS 或 Linux）
- ✅ **网络连接**（能访问 GitHub 和 Render）
- ✅ **Telegram 账号**（用于创建 Bot）
- ✅ **邮箱**（注册 Render 账号）
- ✅ **15 分钟时间**（完整部署流程）

### 你会学会什么

- 🖥️ 如何安装和使用 Render CLI
- 🤖 如何创建 Telegram Bot
- 💻 如何将代码部署到云服务器
- ⚙️ 如何配置环境变量
- 🔍 如何查看日志和调试
- 📊 如何管理部署的应用

### 预期结果

部署完成后，你将拥有：
- ✅ 一个 24/7 运行的加密货币告警机器人
- ✅ 每月 750 小时免费云服务器时间
- ✅ 自动部署和更新能力
- ✅ 专业的部署技能

---

## 🔧 步骤一：安装 Render CLI

Render CLI 是 Render 官方提供的命令行工具。

### macOS 用户

**方法一：使用 Homebrew（推荐）**

```bash
# 1. 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 Render CLI
brew install render-cli

# 3. 验证安装
render --version
```

**方法二：直接下载**

```bash
# 下载并安装
brew install --cask render

# 验证
render --version
```

### Windows 用户

**方法一：使用 Scoop（推荐）**

```powershell
# 1. 安装 Scoop（如果没有）
# 打开 PowerShell（以管理员身份运行）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. 安装 Scoop
irm get.scoop.sh | iex

# 3. 安装 Render CLI
scoop install render

# 4. 验证安装
render --version
```

**方法二：直接下载安装包**

1. 打开 [Render CLI Releases](https://github.com/renderinc/render-cli/releases)
2. 下载最新的 `render-cli-windows-amd64.exe`
3. 重命名为 `render.exe`
4. 放到 `C:\Windows\System32` 目录（或添加到 PATH）
5. 打开新的 CMD/PowerShell 窗口测试
```cmd
render --version
```

### Linux 用户

**Ubuntu/Debian**：
```bash
# 方法一：使用包管理器
curl -fsSL https://render.com/install.sh | sh

# 验证
render --version
```

**CentOS/RHEL**：
```bash
# 下载并安装
curl -L https://github.com/renderinc/render-cli/releases/latest/download/render-linux-amd64.tgz | tar -xz
sudo mv render /usr/local/bin/

# 验证
render --version
```

**验证安装**

打开终端（macOS/Linux）或命令提示符（Windows），运行：

```bash
render --version
```

**预期输出**：
```
render version 0.7.39 (linux/amd64)
```

**如果出现错误**：
- **Windows**: 确保 Render CLI 在 PATH 中
- **macOS**: 确保使用终端而非 Fish shell
- **Linux**: 使用 `sudo` 或检查 `/usr/local/bin` 权限

---

## 📝 步骤二：注册 Render 账号

### 注册流程

1. **打开注册页面**
   - 在浏览器中打开 [https://dashboard.render.com/create](https://dashboard.render.com/create)
   - 或者访问 [https://render.com](https://render.com) 点击 "Get Started"

2. **选择注册方式**
   - 推荐使用 **邮箱注册**（避免 GitHub 访问问题）
   - 点击 **"Continue with Email"**

3. **填写注册信息**
   ```
   Email: 你的邮箱地址
   Password: 设置一个强密码（至少 8 位，包含字母和数字）
   ```
   - 建议使用 Gmail、Outlook 等国际邮箱

4. **验证邮箱**
   - 打开邮箱，找到 Render 发送的验证邮件
   - 点击邮件中的验证链接

5. **登录控制台**
   - 验证后自动登录
   - 看到 Render 控制台界面

**📸 截图位置**：注册完成后，你应该看到类似这样的界面：
```
┌─────────────────────────────────────────┐
│  Render Dashboard                       │
│  ┌─ Welcome to Render!               │ │
│  │  Create your first service...     │ │
│  └─                                  │ │
│  [New +] [Documentation] [Community]    │
└─────────────────────────────────────────┘
```

### 登录 CLI

**在终端中登录**：
```bash
render login
```

**选择登录方式**：
1. 选择 **"Continue with Email"**
2. 输入注册时的邮箱
3. 检查邮箱获取登录链接
4. 在浏览器中点击链接完成登录
5. 终端显示登录成功

**预期输出**：
```
✓ Logged in to Render as your_email@example.com
```

**如果登录失败**：
- 检查邮箱和密码是否正确
- 检查网络连接
- 尝试使用 GitHub 登录：`render login --github`

---

## 🤖 步骤三：创建 Telegram Bot

### 创建 Bot 的步骤

1. **打开 Telegram**
   - 在手机或电脑上打开 Telegram
   - 登录你的账号

2. **搜索 BotFather**
   - 在搜索框输入：`@BotFather`
   - 点击进入 BotFather 聊天窗口

3. **创建新 Bot**
   - 发送命令：`/newbot`
   - BotFather 会询问 Bot 名称

4. **设置 Bot 名称**
   - 输入一个名称，例如：`My Crypto Alert Bot`
   - 这个名称可以重复，不是唯一的

5. **设置用户名**
   - 输入一个用户名，例如：`my_crypto_alert_2024_bot`
   - **重要**：用户名必须以 `bot` 结尾
   - **重要**：用户名必须是唯一的，如果已被占用需要重新输入

6. **获取 Bot Token**
   - 创建成功后，BotFather 会返回一条消息
   - 消息包含类似这样的文本：
   ```
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
   - **复制这个 Token！**（格式：`数字:字母`）

**📸 截图位置**：BotFather 返回的消息类似这样：
```
✅ Done! Congratulations on your new bot. You will find it at
t.me/my_crypto_alert_2024_bot.

Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

For a description of the API, see this page:
https://core.telegram.org/bots/api
```

### 重要提示

- ✅ **保存 Bot Token** - 这是访问 Bot 的密钥，非常重要
- ✅ **用户名唯一** - 如果被占用，尝试添加数字或下划线
- ✅ **可以修改** - 以后可以通过 `/setname` 和 `/setusername` 修改

### 常见问题

**Q: 输入 `/newbot` 没反应？**
A: 确保你是在和 @BotFather 聊天，而不是搜索结果

**Q: 用户名被占用？**
A: 尝试添加数字，如 `my_crypto_alert_2024_bot2`

**Q: 如何找到已创建的 Bot？**
A: 在 Telegram 搜索框输入你的 Bot 用户名

---

## 👤 步骤四：获取 User ID

### User ID 是什么？

User ID 是你在 Telegram 中的唯一标识符，用于授权 Bot 响应你的消息。

### 获取方法

1. **在 Telegram 中搜索**
   - 搜索：`@userinfobot`

2. **启动机器人**
   - 点击进入聊天
   - 发送命令：`/start`

3. **获取 User ID**
   - 机器人会返回你的信息，格式类似：
   ```
   First name: 张三
   Last name: (empty)
   Username: zhangsan123
   ID: 123456789
   ```
   - **复制这个 ID 数字**（如：`123456789`）

**📸 截图位置**：userinfobot 返回的消息类似这样：
```
┌─────────────────────────────────┐
│ User Info Bot                   │
│                                 │
│ First name: 张三                │
│ Last name: (empty)              │
│ Username: zhangsan123           │
│ ID: 123456789                   │
│                                 │
│ Language code: zh-cn            │
│ Is premium: False               │
└─────────────────────────────────┘
```

### 重要提示

- ✅ **ID 是数字** - 不要包含其他字符
- ✅ **保持私密** - 不要将 User ID 分享给他人
- ✅ **用于授权** - 只有这个 ID 的用户可以使用 Bot

---

## 📦 步骤五：准备项目代码

### 创建 GitHub 仓库

**如果你已经有仓库，跳到下一步**

1. **登录 GitHub**
   - 打开 [https://github.com](https://github.com)
   - 登录你的账号

2. **创建新仓库**
   - 点击右上角的 **"+"** 按钮
   - 选择 **"New repository"**

3. **填写仓库信息**
   ```
   Repository name: Telegram-Crypto-Alerts
   Description: 加密货币价格和技术指标告警机器人
   Visibility: Public（公开）
   Initialize: 勾选 "Add a README file"
   ```
   - 点击 **"Create repository"**

### 上传项目代码

**方法一：使用 GitHub Desktop（推荐新手）**

1. **下载 GitHub Desktop**
   - 打开 [https://desktop.github.com](https://desktop.github.com)
   - 下载并安装

2. **克隆仓库**
   - 打开 GitHub Desktop
   - 点击 **"Clone a Repository"**
   - 选择你的仓库
   - 选择本地存储位置

3. **复制项目文件**
   - 将 `Telegram-Crypto-Alerts` 项目中的所有文件
   - 复制到 GitHub Desktop 显示的本地文件夹

4. **提交更改**
   - 在 GitHub Desktop 中，你会看到所有文件
   - 在底部输入提交信息：`Initial commit`
   - 点击 **"Commit to main"**
   - 点击 **"Push origin"**

**方法二：使用命令行**

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/Telegram-Crypto-Alerts.git
cd Telegram-Crypto-Alerts

# 2. 复制项目文件到仓库目录
# （将所有项目文件复制到当前目录）

# 3. 添加文件
git add .

# 4. 提交
git commit -m "Initial commit"

# 5. 推送
git push -u origin main
```

### 验证仓库

1. **在浏览器中打开你的仓库**
   - 访问：`https://github.com/YOUR_USERNAME/Telegram-Crypto-Alerts`

2. **检查文件列表**
   - 应该看到：`README.md`、`requirements.txt`、`src/` 文件夹等

**📸 截图位置**：仓库页面应该显示类似：
```
┌─────────────────────────────────────────┐
│  Telegram-Crypto-Alerts                 │
│  ┌─ Files                             │ │
│  │  📄 README.md                      │ │
│  │  📄 requirements.txt               │ │
│  │  📄 src/                           │ │
│  │  📄 DEPLOYMENT.md                  │ │
│  │  📄 .env.example                   │ │
│  └─                                   │ │
│  Last commit: Initial commit           │
└─────────────────────────────────────────┘
```

### 重要提示

- ✅ **确保所有文件都在** - 特别是 `requirements.txt` 和 `src/` 文件夹
- ✅ **公共仓库** - Render 需要访问你的仓库，设为公开
- ✅ **README 文件** - 包含项目说明

---

## 🔑 步骤六：登录 Render CLI

### 登录过程

1. **打开终端/命令提示符**
   - **macOS**: 按 `Cmd+Space`，输入 `Terminal`
   - **Windows**: 按 `Win+R`，输入 `cmd`
   - **Linux**: 按 `Ctrl+Alt+T`

2. **运行登录命令**
   ```bash
   render login
   ```

3. **选择登录方式**
   ```
   How would you like to authenticate?
   1) Login with GitHub
   2) Login with Email
   3) Login with Google
   4) Cancel
   ```
   - 选择 `2) Login with Email`（推荐）

4. **输入邮箱**
   ```
   Email: your_email@example.com
   ```

5. **获取登录链接**
   ```
   We sent you an email with a login link.
   Please open the link in your browser to complete the login.
   ```

6. **完成登录**
   - 打开邮箱
   - 点击 Render 发送的链接
   - 浏览器会跳转到 Render，确认登录
   - 终端显示：
   ```
   ✓ Logged in to Render as your_email@example.com
   ```

**📸 截图位置**：登录成功后终端显示：
```
✓ Logged in to Render as your_email@example.com

You can now create services on Render.
Run 'render help' to see what you can do.
```

### 验证登录

**检查登录状态**：
```bash
render whoami
```

**预期输出**：
```
your_email@example.com
```

**如果未登录**：
- 再次运行 `render login`
- 检查邮箱是否正确

---

## 🚀 步骤七：初始化项目

### 初始化 Render 服务

**在项目根目录运行**：
```bash
# 确保你在项目目录中
cd /path/to/Telegram-Crypto-Alerts

# 初始化 Render Web Service
render web create
```

### 填写配置信息

**服务类型**：
```
? What type of service would you like to create?
> Web Service
  Background Worker
  Cron Job
```
- 选择 `Web Service`（按回车）

**服务名称**：
```
? Name for this service: telegram-crypto-alerts
```
- 输入服务名，或直接回车使用默认名

**分支**：
```
? Branch to deploy: main
```
- 输入 `main`（或你的分支名）

**根目录**：
```
? Root directory (optional):
```
- 直接回车（留空）

**运行时**：
```
? Runtime:
> Python 3
  Node
  Go
  Ruby
  Java
  .NET
  Other
```
- 选择 `Python 3`（按回车）

**构建命令**：
```
? Build Command: pip install -r requirements.txt
```
- 输入或直接回车（使用默认值）

**启动命令**：
```
? Start Command: python -m src
```
- 输入或直接回车（使用默认值）

**自动部署**：
```
? Deploy automatically from Git? (Y/n) y
```
- 输入 `y`（是，自动部署）

### 选择地区

**地区选择**：
```
? Choose a region for deployment:
  Oregon (US West)
  Frankfurt (EU)
> Singapore (Southeast Asia)  ⭐ 离中国近，推荐
  Ohio (US East)
```
- 选择 `Singapore`（按回车）
- 这是离中国大陆最近的地区，访问速度最快

**📸 截图位置**：选择 Singapore 后：
```
Selected region: Singapore
Creating web service...
```

### 等待创建

```
✓ Created service 'telegram-crypto-alerts'
✓ Service is being deployed in the background
```

**服务创建完成！** 🎉

### 验证服务

**查看服务列表**：
```bash
render services list
```

**预期输出**：
```
ID                                    Name                       Status
srv-xxxxxxxxx                         telegram-crypto-alerts    Deploying
```

**查看服务状态**：
```bash
render services list
```

**查看服务详情**：
```bash
render service create telegram-crypto-alerts
```

---

## ⚙️ 步骤八：配置环境变量

### 环境变量是什么？

环境变量是存储敏感信息的配置项，比如 Bot Token、User ID 等。

### 添加环境变量

**方法一：使用 CLI（推荐）**

```bash
# 1. 添加 Bot Token
render secret set --service telegram-crypto-alerts TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# 2. 添加 User ID
render secret set --service telegram-crypto-alerts TELEGRAM_USER_ID=123456789

# 3. 添加位置
render secret set --service telegram-crypto-alerts LOCATION=global

# 4. 添加 Taapi.io 等级（可选）
render secret set --service telegram-crypto-alerts TAAPIIO_TIER=free
```

**成功提示**：
```
✓ Set secret 'TELEGRAM_BOT_TOKEN' for service 'telegram-crypto-alerts'
✓ Set secret 'TELEGRAM_USER_ID' for service 'telegram-crypto-alerts'
✓ Set secret 'LOCATION' for service 'telegram-crypto-alerts'
✓ Set secret 'TAAPIIO_TIER' for service 'telegram-crypto-alerts'
```

### 验证环境变量

**查看所有环境变量**：
```bash
render secret list --service telegram-crypto-alerts
```

**预期输出**：
```
TELEGRAM_BOT_TOKEN         [set]
TELEGRAM_USER_ID           [set]
LOCATION                   [set]
TAAPIIO_TIER               [set]
```

**重要提示**：
- ✅ **Token 不要有空格** - 确保复制完整
- ✅ **User ID 是纯数字** - 不要有引号
- ✅ **LOCATION 是 `us` 或 `global`** - 根据你的位置选择

### 如果有 Taapi.io API Key

**获取 Taapi.io API Key**（可选，但推荐）：

1. 打开 [https://taapi.io](https://taapi.io)
2. 点击 **"Get API Key"**
3. 注册免费账号
4. 登录后查看 API Key
5. 添加到环境变量：
```bash
render secret set --service telegram-crypto-alerts TAAPIIO_APIKEY=你的APIKey
```

**示例**：
```bash
render secret set --service telegram-crypto-alerts TAAPIIO_APIKEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 环境变量说明

| 变量名 | 必需 | 示例值 | 说明 |
|--------|------|--------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | `123...` | 从 BotFather 获得 |
| `TELEGRAM_USER_ID` | ✅ | `123456789` | 从 userinfobot 获得 |
| `LOCATION` | ✅ | `global` | `us` 或 `global` |
| `TAAPIIO_APIKEY` | ❌ | `eyJ...` | Taapi.io API Key |
| `TAAPIIO_TIER` | ❌ | `free` | 订阅等级 |

---

## 🏗️ 步骤九：部署项目

### 自动部署

Render 会自动检测代码变更并进行部署，但第一次需要手动触发。

**检查部署状态**：
```bash
render service list
```

**预期输出**：
```
Name                   Status       Uptime
telegram-crypto-alerts Deploying    1m 32s
```

**查看部署日志**：
```bash
render service logs telegram-crypto-alerts
```

**查看实时日志**：
```bash
render service logs telegram-crypto-alerts --follow
```

**预期日志**：
```
[Deploy] Building service...
[Install] pip install -r requirements.txt
[Deploy] Build completed
[Start] Starting service
[Bot] 初始化 Taapi.io...
[Bot] 启动 Telegram 机器人...
[Bot] 启动 CEX 告警进程...
[Bot] 等待初始化...
```

**部署成功标志**：
- 看到 `Waiting for initialization...`
- 没有错误信息
- 状态从 `Deploying` 变为 `Active`

### 手动触发部署

如果自动部署没有启动：

```bash
render service deploy telegram-crypto-alerts
```

**预期输出**：
```
✓ Deploying service 'telegram-crypto-alerts'
```

### 部署流程说明

1. **构建阶段**
   - 下载依赖包
   - 安装 Python 库
   - 编译代码

2. **启动阶段**
   - 运行 `python -m src`
   - 初始化所有组件
   - 开始监听

3. **运行阶段**
   - Telegram Bot 持续运行
   - 轮询进程定时检查
   - 等待用户命令

**总耗时**：2-5 分钟

### 查看部署详情

**服务信息**：
```bash
render service show telegram-crypto-alerts
```

**预期输出**：
```
Name:                 telegram-crypto-alerts
Status:               Active
Region:               Singapore
Branch:               main
Runtime:              Python 3
Build Command:        pip install -r requirements.txt
Start Command:        python -m src
```

**访问 URL**（如果有）：
```
Web Service:          https://telegram-crypto-alerts.onrender.com
```

---

## ✅ 步骤十：验证部署

### 测试 Telegram Bot

1. **在 Telegram 中搜索**
   - 输入你的 Bot 用户名
   - 例如：`@my_crypto_alert_2024_bot`

2. **启动 Bot**
   - 点击进入聊天
   - 发送：`/start`

3. **查看响应**
   - Bot 应该返回欢迎信息
   - 格式类似：
   ```
   Welcome to Crypto Alerts Bot!

   Available commands:
   /new_alert - Create a new price alert
   /list_alerts - List your alerts
   /help - Show this help message
   ```

4. **测试帮助命令**
   - 发送：`/help`
   - 查看所有可用命令

### 创建测试告警

**简单价格告警**：
```
/new_alert BTC/USDT PRICE ABOVE 50000
```

**预期响应**：
```
✅ Alert 'alert_1' created successfully!

Alert Details:
- Pair: BTC/USDT
- Condition: PRICE > 50000
- Type: Simple Price Alert
```

**技术指标告警**（如果有 Taapi.io API Key）：
```
/new_alert BTC/USDT RSI 14 1h ABOVE 70
```

**预期响应**：
```
✅ Alert 'alert_2' created successfully!

Alert Details:
- Pair: BTC/USDT
- Indicator: RSI (14, 1h)
- Condition: RSI > 70
```

### 查看告警列表

```
/list_alerts
```

**预期响应**：
```
Your Alerts:

ID: 1 - BTC/USDT - PRICE > 50000
ID: 2 - BTC/USDT - RSI(14,1h) > 70
```

### 验证日志

**在终端中查看日志**：
```bash
render service logs telegram-crypto-alerts
```

**正常日志示例**：
```
[INFO] 初始化 Taapi.io...
[INFO] 启动 Telegram 机器人...
[INFO] 启动 CEX 告警进程...
[INFO] 启动技术指标进程...
[INFO] 等待初始化...
[INFO] 等待命令...
[INFO] 用户 123456789 创建了新告警
[INFO] Alert 'alert_1' created
[INFO] 等待命令...
```

### 检查状态

**服务状态**：
```bash
render service list
```

**预期输出**：
```
Name                   Status    Uptime     Last Deploy
telegram-crypto-alerts Active    5m 23s    2m ago
```

**状态说明**：
- `Deploying` - 正在部署
- `Active` - 正常运行 ⭐
- `Failed` - 部署失败
- `Crashed` - 运行时崩溃

### 成功标志

✅ **部署成功的标志**：
- [x] Bot 响应 `/start` 命令
- [x] 可以创建告警
- [x] 日志显示正常启动
- [x] 服务状态为 `Active`
- [x] 持续运行超过 5 分钟

### 常见问题

**Bot 没有响应？**
- 检查环境变量是否正确
- 查看日志是否有错误
- 确认 Bot Token 有效

**告警创建失败？**
- 检查是否在白名单中
- 查看日志中的错误信息
- 确认告警参数正确

**日志有错误？**
- 常见错误：环境变量缺失
- 解决方案：重新配置环境变量

---

## 💻 CLI 常用命令

### 服务管理

**查看所有服务**：
```bash
render services list
```

**查看服务详情**：
```bash
render service show SERVICE_NAME
```

**重启服务**：
```bash
render service restart SERVICE_NAME
```

**停止服务**：
```bash
render service stop SERVICE_NAME
```

**删除服务**：
```bash
render service delete SERVICE_NAME
```

### 部署管理

**手动部署**：
```bash
render service deploy SERVICE_NAME
```

**查看部署历史**：
```bash
render service history SERVICE_NAME
```

**回滚到上一个版本**：
```bash
render service rollback SERVICE_NAME
```

### 日志管理

**查看日志**：
```bash
render service logs SERVICE_NAME
```

**查看实时日志**：
```bash
render service logs SERVICE_NAME --follow
```

**查看特定时间范围的日志**：
```bash
render service logs SERVICE_NAME --since 1h
render service logs SERVICE_NAME --since 2024-01-01
```

**过滤日志**：
```bash
render service logs SERVICE_NAME | grep "ERROR"
```

### 环境变量管理

**查看所有环境变量**：
```bash
render secret list --service SERVICE_NAME
```

**添加环境变量**：
```bash
render secret set --service SERVICE_NAME KEY=VALUE
```

**删除环境变量**：
```bash
render secret delete --service SERVICE_NAME KEY
```

**批量添加**：
```bash
render secret set --service SERVICE_NAME KEY1=VALUE1 KEY2=VALUE2
```

### 监控和统计

**查看服务状态**：
```bash
render service status SERVICE_NAME
```

**查看资源使用**：
```bash
render service metrics SERVICE_NAME
```

**查看费用**：
```bash
render billing
```

### 其他实用命令

**查看帮助**：
```bash
render help
render COMMAND --help
```

**查看版本**：
```bash
render --version
```

**更新 CLI**：
```bash
# macOS
brew upgrade render-cli

# Windows
scoop update render

# Linux
curl -fsSL https://render.com/install.sh | sh
```

**登录状态**：
```bash
render whoami
render logout
```

---

## 🎯 高级功能

### 自定义域名

如果你有自己的域名：

```bash
# 添加自定义域名
render domain create telegram-crypto-alerts your-domain.com
```

### 扩展配置

**修改环境**：
```bash
render service update SERVICE_NAME --region oregon
render service update SERVICE_NAME --runtime python3.11
```

**修改启动命令**：
```bash
render service update SERVICE_NAME --start-command "python -m src --debug"
```

### 自动部署触发

**每次推送到 GitHub 自动部署**：
- 在 `render.yaml` 中配置：
```yaml
services:
  - type: web
    name: telegram-crypto-alerts
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python -m src
    autoDeploy: true
```

### Webhook 部署

**当代码更新时自动部署**：
```bash
# 创建 webhook
render webhook create SERVICE_NAME
```

### 备份和恢复

**导出环境变量**：
```bash
render secret list --service SERVICE_NAME --format json > backup.json
```

**导入环境变量**：
```bash
render secret set --service NEW_SERVICE_NAME < backup.json
```

---

## ❓ 常见问题

### Q1: CLI 安装失败？

**A: 解决方案**：
- **Windows**: 使用 Scoop 或直接下载 exe
- **macOS**: 确保使用 Homebrew 或下载安装包
- **Linux**: 使用 `curl` 下载或包管理器

**检查 PATH**：
```bash
echo $PATH
which render
```

### Q2: 登录失败？

**A: 解决方案**：
- 检查网络连接
- 尝试不同登录方式：`render login --github`
- 检查邮箱和密码
- 重新安装 CLI

### Q3: 创建服务失败？

**A: 解决方案**：
- 确保在正确的项目目录
- 检查 GitHub 仓库是否存在
- 验证环境变量配置
- 查看错误日志

**常见错误**：
```
Error: Could not find repository
# 解决：确保仓库存在且为公开
```

```
Error: Invalid build command
# 解决：检查 requirements.txt 是否存在
```

### Q4: 部署卡在构建阶段？

**A: 解决方案**：
- 检查 `requirements.txt` 是否有语法错误
- 确保所有依赖都能正常安装
- 查看构建日志：`render service logs SERVICE_NAME --follow`

### Q5: Bot Token 无效？

**A: 验证方法**：
```bash
# 测试 Token 有效性
curl -X GET "https://api.telegram.org/bot<BOT_TOKEN>/getMe"
```

**Token 格式**：`1234567890:ABC...`

### Q6: 忘记服务名？

**A: 查看列表**：
```bash
render services list
```

### Q7: 如何更新代码？

**A: 自动部署**：
- 推送代码到 GitHub
- Render 自动触发部署

**手动部署**：
```bash
render service deploy SERVICE_NAME
```

### Q8: 如何查看完整日志？

**A: 使用 Follow 模式**：
```bash
render service logs SERVICE_NAME --follow
```

### Q9: 如何批量操作？

**A: 使用脚本**：
```bash
# 批量部署多个服务
for service in service1 service2 service3; do
  render service deploy $service
done
```

### Q10: 免费额度用完了？

**A: 检查使用量**：
```bash
render billing
```

**升级方案**：
- 访问 Render 控制台
- 选择付费计划（$7/月起）
- 或暂停服务节省额度

---

## 🔧 故障排查

### 部署失败

**症状**：
- 服务状态为 `Failed`
- 日志显示错误信息

**排查步骤**：
1. 查看详细日志
```bash
render service logs SERVICE_NAME --follow
```

2. 常见错误及解决
```
ModuleNotFoundError: No module named 'telebot'
# 解决：检查 requirements.txt
```

```
Build failed with exit code 1
# 解决：检查依赖安装
```

```
Start command failed
# 解决：检查启动命令和环境变量
```

### Bot 无响应

**症状**：
- Bot 不回应消息
- `/start` 命令无反应

**排查步骤**：
1. 检查环境变量
```bash
render secret list --service SERVICE_NAME
```

2. 查看 Bot 日志
```bash
render service logs SERVICE_NAME | grep "Bot"
```

3. 测试 Token
```bash
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/getMe"
```

4. 检查白名单
```bash
# 在终端中
curl "https://api.telegram.org/bot<BOT_TOKEN>/getChat?chat_id=<USER_ID>"
```

### 服务崩溃

**症状**：
- 服务状态为 `Crashed`
- 需要手动重启

**排查步骤**：
1. 查看崩溃日志
```bash
render service logs SERVICE_NAME --since 1d | grep "ERROR"
```

2. 常见原因
- 内存不足
- 未捕获的异常
- 无限循环

3. 解决方案
- 重启服务：`render service restart SERVICE_NAME`
- 检查代码中的错误处理

### 性能问题

**症状**：
- Bot 响应慢
- 轮询间隔过长

**排查步骤**：
1. 查看资源使用
```bash
render service metrics SERVICE_NAME
```

2. 检查日志
```bash
render service logs SERVICE_NAME | grep "慢"
```

3. 优化建议
- 减少轮询频率
- 使用缓存
- 优化代码

### 网络问题

**症状**：
- 无法访问服务
- 加载缓慢

**排查步骤**：
1. 检查地区设置
```bash
render service show SERVICE_NAME
```

2. 切换到更近的地区
```bash
render service update SERVICE_NAME --region singapore
```

### 环境变量问题

**症状**：
- 变量未生效
- 密码错误

**排查步骤**：
1. 重新设置变量
```bash
render secret delete --service SERVICE_NAME KEY
render secret set --service SERVICE_NAME KEY=VALUE
```

2. 重启服务
```bash
render service restart SERVICE_NAME
```

3. 验证设置
```bash
render secret list --service SERVICE_NAME
```

---

## 📚 总结

### 🎉 恭喜你完成部署！

通过这个教程，你已经学会了：

- ✅ 如何安装和使用 Render CLI
- ✅ 如何创建和配置 Telegram Bot
- ✅ 如何将代码部署到云服务器
- ✅ 如何管理环境变量和日志
- ✅ 如何使用 CLI 进行日常操作

### 🎯 推荐流程

1. **创建 Bot** - 使用 BotFather
2. **获取 ID** - 使用 userinfobot
3. **准备代码** - 上传到 GitHub
4. **登录 CLI** - `render login`
5. **创建服务** - `render web create`
6. **配置变量** - `render secret set`
7. **部署** - 等待自动部署
8. **测试** - 发送 `/start` 给 Bot

### 💡 最佳实践

- **定期更新** - 推送代码自动部署
- **监控日志** - 使用 `render service logs`
- **备份配置** - 导出环境变量
- **测试告警** - 创建测试告警验证
- **阅读文档** - 查看 Render 官方文档

### 🚀 下一步

现在你可以：
- 探索更多 Bot 命令
- 学习技术指标
- 优化 Bot 性能
- 分享给朋友使用
- 学习其他云服务

### 📖 参考资源

- [Render 官方文档](https://render.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Python 学习资源](https://www.runoob.com/python/)
- [Git 教程](https://git-scm.com/book)

### 🆘 获取帮助

如果遇到问题：
1. 查看本文档的常见问题部分
2. 查看 Render 官方文档
3. 在 Render 社区提问
4. 查看项目 GitHub Issues

### 🎓 继续学习

- 学习 Docker 部署
- 学习 CI/CD 流水线
- 学习监控和告警
- 学习性能优化

---

## 📝 快速参考

### 一键部署脚本

创建一个脚本文件 `deploy.sh`：

```bash
#!/bin/bash

# 替换为你的值
SERVICE_NAME="telegram-crypto-alerts"
BOT_TOKEN="YOUR_BOT_TOKEN"
USER_ID="YOUR_USER_ID"

# 设置环境变量
render secret set --service $SERVICE_NAME TELEGRAM_BOT_TOKEN=$BOT_TOKEN
render secret set --service $SERVICE_NAME TELEGRAM_USER_ID=$USER_ID
render secret set --service $SERVICE_NAME LOCATION=global
render secret set --service $SERVICE_NAME TAAPIIO_TIER=free

# 部署
render service deploy $SERVICE_NAME

# 等待部署完成
echo "等待部署完成..."
sleep 60

# 检查状态
render service list
```

**使用脚本**：
```bash
chmod +x deploy.sh
./deploy.sh
```

### 常用命令速查表

| 操作 | 命令 |
|------|------|
| 登录 | `render login` |
| 创建服务 | `render web create` |
| 部署 | `render service deploy NAME` |
| 查看日志 | `render service logs NAME` |
| 重启 | `render service restart NAME` |
| 环境变量 | `render secret set NAME KEY=VALUE` |

### 部署清单

- [ ] 安装 Render CLI
- [ ] 注册 Render 账号
- [ ] 创建 Telegram Bot
- [ ] 获取 User ID
- [ ] 准备 GitHub 仓库
- [ ] 登录 CLI
- [ ] 创建服务
- [ ] 配置环境变量
- [ ] 部署项目
- [ ] 测试 Bot

---

**祝你部署顺利！** 🚀

如有问题，随时查阅本文档或 Render 官方文档。

---

*最后更新：2025-11-08*
