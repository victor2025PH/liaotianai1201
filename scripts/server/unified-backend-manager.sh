#!/bin/bash
# ============================================================
# 统一后端管理脚本
# 功能：依赖安装、服务启动/重启、健康检查、日志查看
# 使用方法: 
#   bash scripts/server/unified-backend-manager.sh [command] [options]
# 
# 命令：
#   install    - 安装/修复依赖
#   start      - 启动后端服务
#   restart    - 重启后端服务
#   stop       - 停止后端服务
#   status     - 查看服务状态
#   logs       - 查看日志
#   health     - 健康检查
#   fix        - 自动修复（安装依赖 + 重启）
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
BACKEND_DIR=""
PYTHON3_PATH=$(which python3)
BACKEND_NAME="backend"
BACKEND_PORT=8000

# 查找后端目录
find_backend_dir() {
    if [ -d "$PROJECT_ROOT/admin-backend" ]; then
        BACKEND_DIR="$PROJECT_ROOT/admin-backend"
    elif [ -d "$PROJECT_ROOT/backend" ]; then
        BACKEND_DIR="$PROJECT_ROOT/backend"
    else
        echo -e "${RED}❌ 未找到后端目录${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 找到后端目录: $BACKEND_DIR${NC}"
}

# 安装依赖
install_deps() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}📦 安装后端依赖${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    find_backend_dir
    cd "$BACKEND_DIR" || exit 1
    
    # 核心包列表
    CORE_PACKAGES=(
        "uvicorn"
        "fastapi"
        "starlette"
        "pydantic"
        "python-multipart"
        "requests"
    )
    
    echo ""
    echo "安装核心包..."
    for PACKAGE in "${CORE_PACKAGES[@]}"; do
        echo -n "  - $PACKAGE ... "
        if pip3 install "$PACKAGE" --user --break-system-packages 2>/dev/null; then
            echo -e "${GREEN}✅${NC}"
        elif sudo pip3 install "$PACKAGE" --break-system-packages 2>/dev/null; then
            echo -e "${GREEN}✅ (sudo)${NC}"
        else
            echo -e "${YELLOW}⚠️  失败${NC}"
        fi
    done
    
    # 安装 requirements.txt
    if [ -f "requirements.txt" ]; then
        echo ""
        echo "安装 requirements.txt..."
        pip3 install -r requirements.txt --user --break-system-packages 2>/dev/null || \
        sudo pip3 install -r requirements.txt --break-system-packages 2>/dev/null || \
        echo -e "${YELLOW}⚠️  部分依赖安装失败${NC}"
    fi
    
    # 验证关键包
    echo ""
    echo "验证关键包..."
    python3 -c "import uvicorn; print(f'✅ uvicorn: {uvicorn.__version__}')" || {
        echo -e "${RED}❌ uvicorn 导入失败${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
}

# 启动服务
start_service() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}🚀 启动后端服务${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    find_backend_dir
    
    # 检查是否已在运行
    if pm2 list | grep -q "$BACKEND_NAME.*online"; then
        echo -e "${YELLOW}⚠️  后端服务已在运行${NC}"
        pm2 list | grep "$BACKEND_NAME"
        return 0
    fi
    
    # 删除旧进程
    if pm2 list | grep -q "$BACKEND_NAME"; then
        echo "删除旧进程..."
        pm2 delete "$BACKEND_NAME" 2>/dev/null || true
        sleep 2
    fi
    
    # 启动服务
    if [ -f "$BACKEND_DIR/app/main.py" ]; then
        echo "启动后端服务 (app.main:app)..."
        pm2 start "$PYTHON3_PATH" \
            --name "$BACKEND_NAME" \
            --interpreter none \
            --cwd "$BACKEND_DIR" \
            --update-env \
            --env PORT=$BACKEND_PORT \
            --env PYTHONPATH="$BACKEND_DIR" \
            --env PYTHONUNBUFFERED=1 \
            --error "$BACKEND_DIR/logs/${BACKEND_NAME}-error.log" \
            --output "$BACKEND_DIR/logs/${BACKEND_NAME}-out.log" \
            -- -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT || {
            echo -e "${RED}❌ 后端启动失败${NC}"
            return 1
        }
    else
        echo -e "${RED}❌ 未找到启动文件 (app/main.py)${NC}"
        return 1
    fi
    
    sleep 3
    pm2 save
    echo -e "${GREEN}✅ 后端服务已启动${NC}"
    pm2 list | grep "$BACKEND_NAME"
}

# 重启服务
restart_service() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}🔄 重启后端服务${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    if pm2 list | grep -q "$BACKEND_NAME"; then
        pm2 restart "$BACKEND_NAME" --update-env
        sleep 3
        echo -e "${GREEN}✅ 后端服务已重启${NC}"
        pm2 list | grep "$BACKEND_NAME"
    else
        echo -e "${YELLOW}⚠️  后端服务未运行，尝试启动...${NC}"
        start_service
    fi
}

# 停止服务
stop_service() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}🛑 停止后端服务${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    if pm2 list | grep -q "$BACKEND_NAME"; then
        pm2 stop "$BACKEND_NAME"
        pm2 delete "$BACKEND_NAME" 2>/dev/null || true
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  后端服务未运行${NC}"
    fi
}

# 查看状态
show_status() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}📊 后端服务状态${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    echo ""
    echo "PM2 进程列表:"
    pm2 list | grep -E "name|$BACKEND_NAME" || echo "  未找到后端进程"
    
    echo ""
    echo "端口监听状态:"
    if ss -tlnp 2>/dev/null | grep -q ":$BACKEND_PORT "; then
        echo -e "  ${GREEN}✅ 端口 $BACKEND_PORT 正在监听${NC}"
        ss -tlnp 2>/dev/null | grep ":$BACKEND_PORT "
    else
        echo -e "  ${RED}❌ 端口 $BACKEND_PORT 未监听${NC}"
    fi
    
    echo ""
    echo "Python 进程:"
    ps aux | grep -E "uvicorn|python.*main.py" | grep -v grep || echo "  未找到相关进程"
}

# 查看日志
show_logs() {
    local lines=${1:-50}
    
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}📋 后端服务日志 (最近 $lines 行)${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    if pm2 list | grep -q "$BACKEND_NAME"; then
        echo ""
        echo "PM2 日志:"
        pm2 logs "$BACKEND_NAME" --lines "$lines" --nostream
    else
        echo -e "${YELLOW}⚠️  后端服务未运行${NC}"
    fi
    
    # 检查日志文件
    find_backend_dir
    if [ -d "$BACKEND_DIR/logs" ]; then
        echo ""
        echo "日志文件:"
        ls -lh "$BACKEND_DIR/logs/"*.log 2>/dev/null | tail -5 || echo "  无日志文件"
    fi
}

# 健康检查
health_check() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}🏥 后端健康检查${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    # 检查 PM2 状态
    if pm2 list | grep -q "$BACKEND_NAME.*online"; then
        echo -e "${GREEN}✅ PM2 进程运行中${NC}"
    else
        echo -e "${RED}❌ PM2 进程未运行${NC}"
    fi
    
    # 检查端口
    if ss -tlnp 2>/dev/null | grep -q ":$BACKEND_PORT "; then
        echo -e "${GREEN}✅ 端口 $BACKEND_PORT 正在监听${NC}"
    else
        echo -e "${RED}❌ 端口 $BACKEND_PORT 未监听${NC}"
    fi
    
    # 检查 HTTP 响应
    echo ""
    echo "测试 HTTP 响应..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$BACKEND_PORT/docs 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ HTTP 响应正常 (200)${NC}"
    elif [ "$HTTP_CODE" = "000" ]; then
        echo -e "${RED}❌ 无法连接到后端${NC}"
    else
        echo -e "${YELLOW}⚠️  HTTP 响应异常 ($HTTP_CODE)${NC}"
    fi
    
    # 检查依赖
    echo ""
    echo "检查关键依赖..."
    python3 -c "import uvicorn" 2>/dev/null && echo -e "${GREEN}✅ uvicorn${NC}" || echo -e "${RED}❌ uvicorn${NC}"
    python3 -c "import fastapi" 2>/dev/null && echo -e "${GREEN}✅ fastapi${NC}" || echo -e "${RED}❌ fastapi${NC}"
}

# 自动修复
auto_fix() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}🔧 自动修复后端${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    install_deps
    echo ""
    restart_service
    echo ""
    sleep 5
    health_check
}

# 主函数
main() {
    cd "$PROJECT_ROOT" || {
        echo -e "${RED}❌ 无法进入项目目录: $PROJECT_ROOT${NC}"
        exit 1
    }
    
    COMMAND=${1:-help}
    
    case "$COMMAND" in
        install)
            install_deps
            ;;
        start)
            start_service
            ;;
        restart)
            restart_service
            ;;
        stop)
            stop_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        health)
            health_check
            ;;
        fix)
            auto_fix
            ;;
        help|--help|-h)
            echo "使用方法: $0 [command] [options]"
            echo ""
            echo "命令："
            echo "  install    - 安装/修复依赖"
            echo "  start      - 启动后端服务"
            echo "  restart    - 重启后端服务"
            echo "  stop       - 停止后端服务"
            echo "  status     - 查看服务状态"
            echo "  logs [N]   - 查看日志（默认 50 行）"
            echo "  health     - 健康检查"
            echo "  fix        - 自动修复（安装依赖 + 重启）"
            echo ""
            echo "示例："
            echo "  $0 fix              # 自动修复"
            echo "  $0 logs 100        # 查看最近 100 行日志"
            echo "  $0 restart         # 重启服务"
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $COMMAND${NC}"
            echo "使用 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"
