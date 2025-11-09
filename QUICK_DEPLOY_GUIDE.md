# 🚀 快速部署指南 - Render

> **使用已提供的配置信息进行快速部署**

## 📋 你的配置信息

```
Bot Token: 8321225222:AAH1bDu4UfWrH7L6wjnZKzEQStVcS3Tp1PA
User ID: 5047052833
位置: global
GitHub 仓库: https://github.com/gyc567/Telegram-Crypto-Alerts
```

---

## 🎯 推荐方式：Web 界面部署（最简单）

### 第1步：打开 Render 控制台

1. 访问 [https://dashboard.render.com/create](https://dashboard.render.com/create)
2. 登录你的账号

### 第2步：创建 Web Service

1. 选择 **"Web Service"**
2. 选择 **"Build and deploy from a Git repository"**
3. 如果需要，授权 GitHub
4. 选择你的仓库：`Telegram-Crypto-Alerts`

### 第3步：配置服务

**填写以下信息**：

| 配置项 | 值 |
|--------|-----|
| **Name** | `telegram-crypto-alerts` |
| **Region** | `Singapore (Southeast Asia)` ⭐ 推荐 |
| **Branch** | `main` |
| **Root Directory** | 留空 |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python -m src` |
| **Auto-Deploy** | ✅ 勾选 |

### 第4步：配置环境变量

在 **"Environment"** 部分，添加：

1. 点击 **"Add Environment Variable"**

2. 添加以下变量：

| 变量名 | 值 | 说明 |
|--------|-----|----- |
| `TELEGRAM_BOT_TOKEN` | `8321225222:AAH1bDu4UfWrH7L6wjnZKzEQStVcS3Tp1PA` | Bot Token |
| `TELEGRAM_USER_ID` | `5047052833` | 你的 User ID |
| `LOCATION` | `global` | 位置设置 |
| `TAAPIIO_TIER` | `free` | 免费计划 |

3. 点击 **"Add"** 保存每个变量

### 第5步：创建服务

1. 点击 **"Create Web Service"**
2. 等待 2-3 分钟完成构建
3. 看到 **"Deployed"** 状态表示成功

### 第6步：测试

1. 找到你的 Bot：在 Telegram 搜索 `@gyc567_crypto_alert_bot`（或你设置的用户名）
2. 发送 `/start` 测试
3. 创建测试告警：`/new_alert BTC/USDT PRICE ABOVE 50000`

---

## 💻 备选方式：一键脚本部署

如果你安装了 Render CLI：

```bash
# 进入项目目录
cd /path/to/Telegram-Crypto-Alerts

# 运行部署脚本
./deploy_render.sh
```

**注意**：脚本需要 Render CLI 已安装和登录

---

## 📊 部署过程

### 构建阶段 (~2分钟)

1. 克隆代码
2. 安装依赖：`pip install -r requirements.txt`
3. 编译完成

### 启动阶段 (~1分钟)

1. 运行 `python -m src`
2. 初始化组件
3. 启动 Bot

### 运行阶段

- Bot 持续运行
- 监听 Telegram 消息
- 定期检查告警

---

## ✅ 部署成功标志

1. **状态**: `Active`（绿色）
2. **日志**: 看到初始化信息
3. **Bot 响应**: `/start` 命令有回复
4. **时间**: 持续运行 5+ 分钟

---

## 🔍 验证步骤

### 检查服务状态

1. 访问 [https://dashboard.render.com](https://dashboard.render.com)
2. 点击你的服务
3. 查看 **"Status"** 选项卡

### 查看日志

1. 在服务页面，点击 **"Logs"** 选项卡
2. 正常日志应该类似：
```
[INFO] 初始化 Taapi.io...
[INFO] 启动 Telegram 机器人...
[INFO] 启动 CEX 告警进程...
[INFO] 启动技术指标进程...
[INFO] 等待初始化...
[INFO] 等待命令...
```

### 测试 Bot

1. 在 Telegram 搜索你的 Bot
2. 发送：`/start`
3. 发送：`/help`
4. 发送：`/new_alert BTC/USDT PRICE ABOVE 50000`

---

## ❓ 常见问题

### Q: 构建失败？

**A**: 检查日志，通常是：
- `requirements.txt` 不存在
- 依赖安装失败
- Python 版本问题

**解决方案**：
- 确认文件完整
- 查看错误日志
- 重新部署

### Q: 启动失败？

**A**: 检查：
- 启动命令是否正确：`python -m src`
- 环境变量是否设置
- 是否有语法错误

**解决方案**：
- 检查 `src/` 目录存在
- 验证环境变量
- 查看启动日志

### Q: Bot 无响应？

**A**: 检查：
- Bot Token 是否正确
- User ID 是否正确
- 是否有错误日志

**解决方案**：
- 重新设置环境变量
- 重启服务
- 验证 Token 有效性

### Q: 部署卡住？

**A**: 正常现象，首次部署需要 3-5 分钟

**等待**：不要刷新，耐心等待

**查看进度**：日志选项卡

---

## 🎉 部署后操作

### 立即可以做的

1. **测试 Bot**
   - 发送 `/start`
   - 查看所有命令
   - 创建测试告警

2. **查看监控**
   - Render 控制台
   - 资源使用
   - 错误日志

3. **创建告警**
   - 价格告警：`/new_alert BTC/USDT PRICE ABOVE 50000`
   - 技术指标：`/new_alert BTC/USDT RSI 14 1h ABOVE 70`

### 长期维护

- **更新代码**：推送到 GitHub，Render 自动部署
- **查看日志**：定期检查错误
- **监控使用**：Render 控制台查看免费额度

---

## 📈 性能信息

### 免费计划

- **运行时间**: 750小时/月
- **内存**: 1GB
- **CPU**: 0.5 vCPU
- **存储**: 1GB
- **带宽**: 100GB/月

**足够 24/7 运行**！

### 升级

如需更多资源：
- **Starter**: $7/月 - 0.5 CPU, 0.5GB RAM
- **Standard**: $25/月 - 1 CPU, 2GB RAM

---

## 🔗 快速链接

- **Render 控制台**: [https://dashboard.render.com](https://dashboard.render.com)
- **服务状态**: [https://dashboard.render.com](https://dashboard.render.com)
- **Render 文档**: [https://render.com/docs](https://render.com/docs)
- **Telegram Bot API**: [https://core.telegram.org/bots/api](https://core.telegram.org/bots/api)

---

## 💡 提示

1. **选择 Singapore 地区** - 离中国近，访问快
2. **开启自动部署** - 推送代码自动更新
3. **定期查看日志** - 及时发现问题
4. **备份配置** - 保存环境变量

---

**祝你部署顺利！** 🚀

如果遇到问题，请查看 Render 控制台的日志，或参考项目文档。

---

*最后更新：2025-11-08*
