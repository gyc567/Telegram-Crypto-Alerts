#!/bin/bash

# Render 一键部署脚本
# 使用方法: ./deploy_render.sh

echo "🚀 开始部署 Telegram-Crypto-Alerts 到 Render..."
echo ""

# 配置信息
SERVICE_NAME="telegram-crypto-alerts"
REGION="singapore"
BRANCH="main"
RUNTIME="python3"
BUILD_CMD="pip install -r requirements.txt"
START_CMD="python -m src"
GITHUB_REPO="https://github.com/gyc567/Telegram-Crypto-Alerts"

# Telegram 配置
TELEGRAM_BOT_TOKEN="8321225222:AAH1bDu4UfWrH7L6wjnZKzEQStVcS3Tp1PA"
TELEGRAM_USER_ID="5047052833"
LOCATION="global"
TAAPIIO_TIER="free"

echo "📋 部署配置:"
echo "   服务名: $SERVICE_NAME"
echo "   地区: $REGION"
echo "   分支: $BRANCH"
echo "   仓库: $GITHUB_REPO"
echo ""

# 检查是否已登录 Render
echo "🔐 检查 Render 登录状态..."
if ! command -v render &> /dev/null; then
    echo "❌ Render CLI 未安装"
    echo ""
    echo "安装方法:"
    echo "  macOS: brew install render-cli"
    echo "  或下载: https://github.com/renderinc/render-cli/releases"
    echo ""
    echo "🔗 替代方案: 使用 Web 界面部署"
    echo "  1. 打开 https://dashboard.render.com/create"
    echo "  2. 选择 'Web Service'"
    echo "  3. 选择 'Build and deploy from GitHub'"
    echo "  4. 使用上述配置信息"
    echo ""
    exit 1
fi

# 检查登录状态
if ! render whoami &> /dev/null; then
    echo "❌ 未登录 Render"
    echo "请先运行: render login"
    exit 1
fi

echo "✅ 已登录 Render"
echo ""

# 创建服务
echo "🔨 创建 Web Service..."
render web create \
  --name "$SERVICE_NAME" \
  --region "$REGION" \
  --branch "$BRANCH" \
  --runtime "$RUNTIME" \
  --build-command "$BUILD_CMD" \
  --start-command "$START_CMD" \
  --auto-deploy

if [ $? -eq 0 ]; then
    echo "✅ 服务创建成功"
else
    echo "❌ 服务创建失败"
    exit 1
fi

echo ""

# 等待服务创建完成
echo "⏳ 等待服务初始化 (30秒)..."
sleep 30

# 配置环境变量
echo "⚙️ 配置环境变量..."

render secret set --service "$SERVICE_NAME" TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
render secret set --service "$SERVICE_NAME" TELEGRAM_USER_ID="$TELEGRAM_USER_ID"
render secret set --service "$SERVICE_NAME" LOCATION="$LOCATION"
render secret set --service "$SERVICE_NAME" TAAPIIO_TIER="$TAAPIIO_TIER"

echo "✅ 环境变量配置完成"
echo ""

# 触发部署
echo "🚀 触发部署..."
render service deploy "$SERVICE_NAME"

echo ""
echo "✅ 部署请求已提交"
echo ""
echo "⏳ 等待部署完成 (5-10分钟)..."
echo "   你可以运行以下命令查看日志:"
echo "   render service logs $SERVICE_NAME --follow"
echo ""
echo "🔗 或访问 https://dashboard.render.com 查看状态"
echo ""
echo "部署信息:"
echo "   服务名: $SERVICE_NAME"
echo "   仓库: $GITHUB_REPO"
echo "   分支: $BRANCH"
echo "   地区: $REGION"
echo ""
echo "🎉 部署完成! 请在 5-10 分钟后测试你的 Bot"
