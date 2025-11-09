以下是一份专门为「小白新手用户」编写的 **《Telegram Crypto Alerts 项目 Replit + UptimeRobot 部署文档》**，即使你完全不会编程，也能一步步完成部署。文档基于搜索结果整理，并结合常见 Telegram 加密币提醒机器人项目的通用结构（如 ）进行适配。

---

# 🧭 Telegram Crypto Alerts 项目部署文档
**适用人群：零基础新手**
**部署平台：Replit + UptimeRobot（完全免费）**

---

## 🧱 第 0 步：准备工作（先做完这些）

### ✅ 你需要先准备好以下 3 个东西：

| 项目 | 获取方式 |
|------|----------|
| Telegram Bot 的 Token | 在 Telegram 里搜索 `@BotFather`，创建机器人，他会给你一个 token（一串类似 `123456:ABC-DEF...` 的字符） |
| Telegram 聊天 ID（Chat ID） | 打开 [https://web.telegram.org](https://web.telegram.org)，找到你想接收提醒的聊天，复制链接中的数字，或者用 `@userinfobot` 获取 |
| GitHub 项目地址 | 本项目地址：[https://github.com/gyc567/Telegram-Crypto-Alerts](https://github.com/gyc567/Telegram-Crypto-Alerts)（如打不开，可手动下载源码） |

---

## 🧑‍💻 第 1 步：注册 Replit 账号

1. 打开 [https://replit.com](https://replit.com)
2. 点击右上角 **Sign Up**，用邮箱注册账号（也可以用 Google/GitHub 登录）
3. 注册成功后，点击右上角的 **+ Create Repl** 按钮

---

## 🧪 第 2 步：创建项目并上传代码

### 方法一：直接导入 GitHub 项目（推荐）

1. 在创建页面选择 **Import from GitHub**
2. 粘贴项目地址：`https://github.com/gyc567/Telegram-Crypto-Alerts`
3. 语言选择 **Python**
4. 点击 **Import**

> 如果导入失败，用方法二：手动上传

### 方法二：手动上传（备用）

1. 创建一个新的 Python 项目
2. 打开项目后，在左侧文件栏点击 **Upload**，把项目所有 `.py` 文件上传上来
3. 确保根目录有 `main.py` 或 `bot.py` 等入口文件

---

## 🔧 第 3 步：安装依赖包

1. 在项目根目录下创建一个文件，命名为：`requirements.txt`
2. 粘贴以下内容（这是大多数 Telegram 加密币提醒机器人所需的依赖）：

```
python-telegram-bot
requests
flask
python-dotenv
```

3. Replit 会自动识别并安装这些依赖（如果没有自动安装，点击左侧的 **Packages**，搜索并手动安装）

---

## 🔐 第 4 步：设置环境变量（隐藏你的 Token）

1. 在 Replit 左侧找到 **Secrets（环境变量）** 按钮（锁图标）
2. 添加以下变量：

| 名称 | 值（示例） |
|------|-------------|
| `TELEGRAM_TOKEN` | `123456:ABC-DEF...`（你从 BotFather 获取的） |
| `CHAT_ID` | `-1001234567890`（你的聊天 ID） |
| `COIN_GECKO_API_KEY`（可选） | 如果你用了 CoinGecko API，可以在这里填 |

> ⚠️ 注意：不要把 Token 写在代码里！用 `os.getenv("TELEGRAM_TOKEN")` 的方式读取

---

## 🧪 第 5 步：添加 Keep-Alive 脚本（防止 Replit 休眠）

1. 创建一个文件，命名为：`keep_alive.py`
2. 粘贴以下代码（来自 ）：

```python
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
```

3. 在你的主程序（如 `main.py` 或 `bot.py`）顶部添加以下代码：

```python
from keep_alive import keep_alive
keep_alive()
```

---

## ▶️ 第 6 步：运行项目

1. 点击页面上方的绿色 **Run** 按钮
2. 如果看到控制台输出 `Bot is running...` 或类似信息，说明运行成功
3. 打开右侧的 **Webview**，你应该能看到页面显示 “Bot is alive!”

---

## 🌍 第 7 步：设置 UptimeRobot（防止 Replit 休眠）

1. 打开 [https://uptimerobot.com](https://uptimerobot.com)，注册一个免费账号
2. 登录后点击 **Add New Monitor**
3. 设置如下：

| 项目 | 内容 |
|------|------|
| Monitor Type | HTTP(s) |
| URL | 粘贴你 Replit 项目的 Web 地址（如 `https://your-project.your-username.repl.co`） |
| Monitoring Interval | 每 5 分钟 |
| Friendly Name | 随便写，比如 “Telegram Bot Keep Alive” |

4. 保存后，UptimeRobot 会每 5 分钟访问一次你的项目，防止它休眠

---

## ✅ 第 8 步：测试机器人

1. 打开 Telegram，找到你创建的机器人
2. 发送 `/start` 或你设定的命令
3. 如果收到回复或价格提醒，说明部署成功！

---

## 🧹 常见问题（FAQ）

| 问题 | 解决方法 |
|------|----------|
| Replit 项目休眠了 | 确保 UptimeRobot 设置正确，并且 Web 地址能访问 |
| 机器人不回复消息 | 检查 `TELEGRAM_TOKEN` 和 `CHAT_ID` 是否设置正确 |
| 报错 `ModuleNotFoundError` | 检查 `requirements.txt` 是否包含所需库，并重新运行 |

---

## 🎉 恭喜你！部署完成 🎉

你现在拥有了一个 **24/7 在线运行的 Telegram 加密币提醒机器人**，完全免费，且无需自己维护服务器！

---

如需后续添加更多功能（如价格阈值提醒、图表分析等），可以继续修改代码并重新部署。

如需我帮你检查代码或写具体的主程序结构，也可以继续问我！
