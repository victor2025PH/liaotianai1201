#!/bin/bash
# ============================================================
# 服务管理脚本
# ============================================================
# 功能：快速管理 FastAPI 后端和 Telegram Bot 服务
# 使用方法：sudo bash scripts/server/manage-services.sh [command] [service]
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
    echo "🔧 服务管理工具"
    echo "============================================================"
    echo ""
    echo "用法: sudo $0 [command] [service]"
    echo ""
    echo "命令:"
    echo "  start      启动服务"
    echo "  stop       停止服务"
    echo "  restart    重启服务"
    echo "  status     查看服务状态"
    echo "  enable     启用服务（开机自启）"
    echo "  disable    禁用服务（不开机自启）"
    echo "  logs       查看日志（需要单独运行 view-logs.sh）"
    echo ""
    echo "服务:"
    echo "  backend    后端服务 (FastAPI)"
    echo "  bot        Bot 服务 (Telegram Bot)"
    echo "  all        所有服务"
    echo ""
    echo "示例:"
    echo "  sudo $0 start backend      # 启动后端"
    echo "  sudo $0 restart all       # 重启所有服务"
    echo "  sudo $0 status bot        # 查看 Bot 状态"
    echo ""
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}❌ 错误：请使用 sudo 运行此脚本${NC}"
        exit 1
    fi
}

# 管理单个服务
manage_service() {
    local command=$1
    local service=$2
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
            return 1
            ;;
    esac
    
    case $command in
        start)
            echo -e "${BLUE}🚀 启动 $service_name...${NC}"
            systemctl start "$service_name"
            sleep 2
            if systemctl is-active --quiet "$service_name"; then
                echo -e "${GREEN}✅ $service_name 已启动${NC}"
            else
                echo -e "${RED}❌ $service_name 启动失败${NC}"
                echo "   查看日志: sudo journalctl -u $service_name -n 50"
                return 1
            fi
            ;;
        stop)
            echo -e "${YELLOW}🛑 停止 $service_name...${NC}"
            systemctl stop "$service_name"
            sleep 1
            if ! systemctl is-active --quiet "$service_name"; then
                echo -e "${GREEN}✅ $service_name 已停止${NC}"
            else
                echo -e "${RED}❌ $service_name 停止失败${NC}"
                return 1
            fi
            ;;
        restart)
            echo -e "${BLUE}🔄 重启 $service_name...${NC}"
            systemctl restart "$service_name"
            sleep 2
            if systemctl is-active --quiet "$service_name"; then
                echo -e "${GREEN}✅ $service_name 已重启${NC}"
            else
                echo -e "${RED}❌ $service_name 重启失败${NC}"
                echo "   查看日志: sudo journalctl -u $service_name -n 50"
                return 1
            fi
            ;;
        status)
            echo "============================================================"
            echo -e "${BLUE}📊 $service_name 状态${NC}"
            echo "============================================================"
            systemctl status "$service_name" --no-pager -l
            ;;
        enable)
            echo -e "${BLUE}✅ 启用 $service_name（开机自启）...${NC}"
            systemctl enable "$service_name"
            echo -e "${GREEN}✅ $service_name 已启用${NC}"
            ;;
        disable)
            echo -e "${YELLOW}❌ 禁用 $service_name（不开机自启）...${NC}"
            systemctl disable "$service_name"
            echo -e "${GREEN}✅ $service_name 已禁用${NC}"
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $command${NC}"
            return 1
            ;;
    esac
}

# 管理所有服务
manage_all() {
    local command=$1
    
    echo "============================================================"
    echo -e "${BLUE}🔧 管理所有服务: $command${NC}"
    echo "============================================================"
    echo ""
    
    manage_service "$command" "backend"
    echo ""
    manage_service "$command" "bot"
    echo ""
    
    if [ "$command" = "status" ]; then
        echo "============================================================"
        echo -e "${BLUE}📊 服务状态总结${NC}"
        echo "============================================================"
        
        if systemctl is-active --quiet "$BACKEND_SERVICE"; then
            echo -e "${GREEN}✅ $BACKEND_SERVICE: 运行中${NC}"
        else
            echo -e "${RED}❌ $BACKEND_SERVICE: 未运行${NC}"
        fi
        
        if systemctl is-active --quiet "$BOT_SERVICE"; then
            echo -e "${GREEN}✅ $BOT_SERVICE: 运行中${NC}"
        else
            echo -e "${RED}❌ $BOT_SERVICE: 未运行${NC}"
        fi
    fi
}

# 主逻辑
if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

COMMAND=$1
SERVICE=${2:-"all"}

case $COMMAND in
    start|stop|restart|status|enable|disable)
        check_root
        if [ "$SERVICE" = "all" ]; then
            manage_all "$COMMAND"
        else
            manage_service "$COMMAND" "$SERVICE"
        fi
        ;;
    logs)
        echo -e "${YELLOW}ℹ️  请使用 view-logs.sh 查看日志${NC}"
        echo "   示例: bash scripts/server/view-logs.sh $SERVICE -f"
        ;;
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac

