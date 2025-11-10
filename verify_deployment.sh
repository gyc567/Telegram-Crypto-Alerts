#!/bin/bash
#
# Telegram Bot 部署验证脚本
# 用于快速检查和修复 /admins 命令问题
#
# 使用方法:
#   chmod +x verify_deployment.sh
#   ./verify_deployment.sh
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# 检查是否在项目目录
check_project_directory() {
    if [ ! -f "src/telegram.py" ]; then
        print_error "未找到 src/telegram.py，请在项目根目录运行此脚本"
        exit 1
    fi
    print_success "项目目录检查通过"
}

# 检查代码部署状态
check_code_deployment() {
    print_header "1. 检查代码部署状态"

    # 检查Git提交
    COMMIT=$(git log --oneline -1 2>/dev/null || echo "")
    if [[ $COMMIT == *"4456b27"* ]]; then
        print_success "最新提交: $COMMIT"
        print_success "代码已正确部署"
    else
        print_warning "当前提交: $COMMIT"
        print_warning "代码部署可能不完整"
        echo "  建议: git pull origin main"
    fi

    # 检查修复代码
    if grep -q "len(splt_msg) == 0" src/telegram.py; then
        print_success "修复代码存在"
        LINE=$(grep -n "len(splt_msg) == 0" src/telegram.py | head -1)
        print_info "位置: 第$LINE"
    else
        print_error "修复代码缺失"
        echo "  建议: git pull origin main"
    fi
}

# 检查服务状态
check_service_status() {
    print_header "2. 检查服务状态"

    # 检查Python进程
    PROCESS_COUNT=$(ps aux | grep -E "python.*src" | grep -v grep | wc -l)
    if [ $PROCESS_COUNT -gt 0 ]; then
        print_success "发现 $PROCESS_COUNT 个机器人进程"
        ps aux | grep -E "python.*src" | grep -v grep | while read line; do
            echo "  $line"
        done
    else
        print_warning "未发现运行中的机器人进程"
        echo "  建议: python -m src"
    fi

    # 检查Docker容器
    if command -v docker &> /dev/null; then
        CONTAINER_COUNT=$(docker ps -a | grep telegram | wc -l)
        if [ $CONTAINER_COUNT -gt 0 ]; then
            print_info "发现 $CONTAINER_COUNT 个Telegram相关容器"
            docker ps -a | grep telegram
        fi
    fi

    # 检查systemd服务
    if systemctl list-units --type=service | grep -q telegram-bot; then
        SERVICE_STATUS=$(systemctl is-active telegram-bot 2>/dev/null || echo "unknown")
        if [ "$SERVICE_STATUS" = "active" ]; then
            print_success "systemd服务状态: active"
        else
            print_warning "systemd服务状态: $SERVICE_STATUS"
        fi
    fi
}

# 检查服务日志
check_service_logs() {
    print_header "3. 检查服务日志"

    if [ -f "bot.log" ]; then
        LOG_SIZE=$(du -h bot.log | cut -f1)
        print_info "日志文件大小: $LOG_SIZE"

        # 查找最近的启动信息
        if grep -q "Starting" bot.log 2>/dev/null; then
            LAST_START=$(grep "Starting" bot.log | tail -1)
            print_info "最近启动: $LAST_START"
        fi

        # 查找错误
        ERROR_COUNT=$(grep -i "error\|exception\|traceback" bot.log 2>/dev/null | wc -l)
        if [ $ERROR_COUNT -gt 0 ]; then
            print_warning "日志中发现 $ERROR_COUNT 个错误/异常"
            echo "  最近5个错误:"
            grep -i "error\|exception" bot.log 2>/dev/null | tail -5 | sed 's/^/    /'
        else
            print_success "日志中无错误信息"
        fi
    else
        print_warning "未找到 bot.log 文件"
    fi
}

# 执行重启
perform_restart() {
    print_header "4. 执行服务重启"

    # 询问用户是否继续
    echo "即将重启机器人服务，期间服务会短暂不可用 (1-2分钟)"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "用户取消重启"
        return
    fi

    # 停止现有服务
    print_info "停止现有服务..."

    # 方式1: 直接杀死进程
    PIDS=$(pgrep -f "python.*src" || true)
    if [ -n "$PIDS" ]; then
        echo "正在停止进程: $PIDS"
        kill $PIDS 2>/dev/null || true
        sleep 2

        # 强制杀死 (如果还活着)
        PIDS=$(pgrep -f "python.*src" || true)
        if [ -n "$PIDS" ]; then
            print_warning "强制杀死进程: $PIDS"
            kill -9 $PIDS 2>/dev/null || true
        fi
        print_success "进程已停止"
    else
        print_info "未发现运行中的进程"
    fi

    # 方式2: systemd服务
    if systemctl list-units --type=service | grep -q telegram-bot; then
        print_info "停止systemd服务..."
        sudo systemctl stop telegram-bot
        sleep 2
        print_success "systemd服务已停止"
    fi

    # 方式3: Docker容器
    if command -v docker &> /dev/null; then
        CONTAINERS=$(docker ps -q --filter "name=telegram" || true)
        if [ -n "$CONTAINERS" ]; then
            print_info "停止Docker容器..."
            docker stop $CONTAINERS
            sleep 2
            print_success "Docker容器已停止"
        fi
    fi

    # 确认停止
    sleep 2
    REMAINING=$(ps aux | grep -E "python.*src" | grep -v grep | wc -l)
    if [ $REMAINING -eq 0 ]; then
        print_success "确认所有进程已停止"
    else
        print_error "仍有 $REMAINING 个进程在运行"
        ps aux | grep -E "python.*src" | grep -v grep
    fi

    # 启动服务
    print_info "启动新服务..."

    # 拉取最新代码
    print_info "拉取最新代码..."
    git pull origin main 2>/dev/null || print_warning "代码拉取失败，可能已最新"

    # 启动方式1: 直接运行
    print_info "启动机器人服务..."
    nohup python -m src > bot.log 2>&1 &
    sleep 3

    # 确认启动
    NEW_PIDS=$(pgrep -f "python.*src" || true)
    if [ -n "$NEW_PIDS" ]; then
        print_success "服务启动成功 (PID: $NEW_PIDS)"
    else
        print_error "服务启动失败"
        echo "  检查日志: tail -20 bot.log"
        return 1
    fi

    # 方式2: systemd (可选)
    if systemctl list-units --type=service | grep -q telegram-bot; then
        print_info "启动systemd服务..."
        sudo systemctl start telegram-bot
        sleep 2
    fi

    # 方式3: Docker (可选)
    if command -v docker &> /dev/null; then
        CONTAINERS=$(docker ps -aq --filter "name=telegram" || true)
        if [ -n "$CONTAINERS" ]; then
            print_info "启动Docker容器..."
            docker start $CONTAINERS
            sleep 2
        fi
    fi

    print_success "重启完成"
}

# 验证功能
verify_functionality() {
    print_header "5. 验证功能"

    # 运行自动化测试
    if [ -f "test_admins_actual.py" ]; then
        print_info "运行自动化测试..."
        if python3 test_admins_actual.py; then
            print_success "所有自动化测试通过"
        else
            print_error "自动化测试失败"
        fi
    else
        print_warning "未找到测试脚本，跳过自动化测试"
    fi

    # 检查启动日志
    print_info "检查启动日志..."
    sleep 2
    if [ -f "bot.log" ]; then
        RECENT_LOGS=$(tail -20 bot.log 2>/dev/null || echo "")
        if echo "$RECENT_LOGS" | grep -q "Starting\|Started\|Running"; then
            print_success "服务启动日志正常"
        else
            print_warning "启动日志可能有问题"
            echo "$RECENT_LOGS" | tail -5
        fi
    fi

    # 提示手动测试
    print_header "6. 手动验证"
    print_info "请在Telegram中测试以下命令:"
    echo ""
    echo "  /admins"
    echo "  /admins VIEW"
    echo "  /admins ADD <user_id>"
    echo "  /admins REMOVE <user_id>"
    echo ""
    print_info "预期: 所有命令正常执行，无IndexError"
    echo ""
    read -p "测试完成后按 Enter 键继续..."
}

# 显示检查清单
show_checklist() {
    print_header "部署验证检查清单"

    CHECKLIST=(
        "代码已推送到远程仓库 (commit 4456b27):$(git log --oneline -1 2>/dev/null | grep -q '4456b27' && echo '✅' || echo '❌')"
        "源代码包含修复 (第591行):$(grep -q 'len(splt_msg) == 0' src/telegram.py && echo '✅' || echo '❌')"
        "旧进程已停止:$(ps aux | grep -E 'python.*src' | grep -v grep | wc -l | grep -q '^0$' && echo '✅' || echo '❌')"
        "新进程已启动:$(ps aux | grep -E 'python.*src' | grep -v grep | wc -l | grep -q '^[1-9]' && echo '✅' || echo '❌')"
        "启动日志无错误:$(grep -qi 'error\|exception' bot.log 2>/dev/null && echo '❌' || echo '✅')"
    )

    for item in "${CHECKLIST[@]}"; do
        echo "  $item"
    done

    echo ""
    print_info "详细验证请在Telegram中手动测试 /admins 命令"
}

# 主函数
main() {
    clear
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║   Telegram Bot 部署验证工具 v1.0       ║"
    echo "║   解决 /admins 命令报错问题            ║"
    echo "╚════════════════════════════════════════╝"
    echo ""

    # 检查项目目录
    check_project_directory

    # 检查代码部署
    check_code_deployment

    # 检查服务状态
    check_service_status

    # 检查服务日志
    check_service_logs

    # 询问是否重启
    echo ""
    print_info "发现潜在问题: 生产环境可能未重启"
    read -p "是否立即执行重启? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if perform_restart; then
            verify_functionality
        fi
    fi

    # 显示检查清单
    show_checklist

    print_header "验证完成"
    print_success "如有问题请查看 DEPLOYMENT_VERIFICATION_GUIDE.md"
    echo ""
}

# 运行主函数
main "$@"
