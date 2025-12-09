#!/bin/bash
# ============================================================
# 日志查看脚本
# ============================================================
# 功能：快速查看 FastAPI 后端和 Telegram Bot 的日志
# 使用方法：bash scripts/server/view-logs.sh [service] [options]
# ============================================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务名称
BACKEND_SERVICE="telegram-backend"
BOT_SERVICE="telegram-bot"

# 显示帮助信息
show_help() {
    echo "============================================================"
    echo "📋 日志查看工具"
    echo "============================================================"
    echo ""
    echo "用法: $0 [service] [options]"
    echo ""
    echo "服务:"
    echo "  backend    查看后端日志 (默认)"
    echo "  bot        查看 Bot 日志"
    echo "  all        查看所有服务日志"
    echo ""
    echo "选项:"
    echo "  -f, --follow    实时跟踪日志（类似 tail -f）"
    echo "  -n, --lines N  显示最后 N 行（默认 50）"
    echo "  -e, --error    仅显示错误日志"
    echo "  -s, --since    显示指定时间之后的日志（例如: 1h, 30m, 2024-01-01）"
    echo "  -h, --help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                    # 查看后端最后 50 行日志"
    echo "  $0 backend -f         # 实时跟踪后端日志"
    echo "  $0 bot -n 100        # 查看 Bot 最后 100 行日志"
    echo "  $0 all -e             # 查看所有服务的错误日志"
    echo "  $0 backend -s 1h     # 查看后端最近 1 小时的日志"
    echo ""
}

# 解析参数
SERVICE="backend"
FOLLOW=false
LINES=50
ERROR_ONLY=false
SINCE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        backend|bot|all)
            SERVICE="$1"
            shift
            ;;
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -e|--error)
            ERROR_ONLY=true
            shift
            ;;
        -s|--since)
            SINCE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 查看单个服务日志
view_service_logs() {
    local service=$1
    local service_name=""
    
    case $service in
        backend)
            service_name="$BACKEND_SERVICE"
            ;;
        bot)
            service_name="$BOT_SERVICE"
            ;;
        *)
            echo -e "${RED}❌ 未知服务: $service${NC}"
            exit 1
            ;;
    esac
    
    echo "============================================================"
    echo -e "${BLUE}📋 $service_name 日志${NC}"
    echo "============================================================"
    echo ""
    
    # 构建 journalctl 命令
    local cmd="sudo journalctl -u $service_name"
    
    if [ -n "$SINCE" ]; then
        cmd="$cmd --since \"$SINCE\""
    fi
    
    if [ "$ERROR_ONLY" = true ]; then
        cmd="$cmd -p err"
    fi
    
    if [ "$FOLLOW" = true ]; then
        cmd="$cmd -f"
    else
        cmd="$cmd -n $LINES"
    fi
    
    # 执行命令
    eval $cmd
}

# 查看所有服务日志
view_all_logs() {
    echo "============================================================"
    echo -e "${BLUE}📋 所有服务日志${NC}"
    echo "============================================================"
    echo ""
    
    local cmd="sudo journalctl"
    
    # 添加服务过滤
    cmd="$cmd -u $BACKEND_SERVICE -u $BOT_SERVICE"
    
    if [ -n "$SINCE" ]; then
        cmd="$cmd --since \"$SINCE\""
    fi
    
    if [ "$ERROR_ONLY" = true ]; then
        cmd="$cmd -p err"
    fi
    
    if [ "$FOLLOW" = true ]; then
        cmd="$cmd -f"
    else
        cmd="$cmd -n $LINES"
    fi
    
    # 执行命令
    eval $cmd
}

# 主逻辑
case $SERVICE in
    backend|bot)
        view_service_logs "$SERVICE"
        ;;
    all)
        view_all_logs
        ;;
    *)
        echo -e "${RED}❌ 未知服务: $SERVICE${NC}"
        show_help
        exit 1
        ;;
esac

