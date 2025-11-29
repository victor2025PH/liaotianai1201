#!/bin/bash
# 完整诊断和修复 502 错误

set -e

echo "========================================"
echo "502 错误诊断和修复"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅${NC} $1"; }
error() { echo -e "${RED}❌${NC} $1"; }
info() { echo -e "${BLUE}ℹ️${NC} $1"; }
warn() { echo -e "${YELLOW}⚠️${NC} $1"; }

# 1. 检查后端服务
echo "[1] 检查后端服务..."
info "检查端口 8000..."
if curl -s --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
    success "后端服务正在运行"
    BACKEND_OK=true
else
    error "后端服务未运行"
    BACKEND_OK=false
    
    # 检查进程
    info "检查后端进程..."
    if ps aux | grep uvicorn | grep -v grep; then
        warn "发现 uvicorn 进程但无法连接"
    else
        warn "未发现后端进程"
    fi
fi
echo ""

# 2. 检查前端服务
echo "[2] 检查前端服务..."
info "检查端口 3000..."
if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    success "前端服务正在运行"
    FRONTEND_OK=true
else
    error "前端服务未运行"
    FRONTEND_OK=false
    
    # 检查进程
    info "检查前端进程..."
    if ps aux | grep -E 'next|node.*3000' | grep -v grep; then
        warn "发现前端进程但无法连接"
    else
        warn "未发现前端进程"
    fi
fi
echo ""

# 3. 检查 Nginx 配置
echo "[3] 检查 Nginx 配置..."
if sudo systemctl is-active --quiet nginx; then
    success "Nginx 正在运行"
else
    error "Nginx 未运行"
    info "尝试启动 Nginx..."
    sudo systemctl start nginx
    sleep 2
fi

info "检查 Nginx 配置..."
NGINX_CONFIG="/etc/nginx/sites-enabled/default"
if [ -f "$NGINX_CONFIG" ]; then
    info "配置文件存在: $NGINX_CONFIG"
    if sudo nginx -t 2>&1 | grep -q "successful"; then
        success "Nginx 配置语法正确"
    else
        error "Nginx 配置有错误"
        sudo nginx -t
    fi
else
    warn "配置文件不存在: $NGINX_CONFIG"
fi
echo ""

# 4. 修复后端服务
if [ "$BACKEND_OK" = false ]; then
    echo "[4] 修复后端服务..."
    
    cd ~/liaotian/admin-backend || { error "无法进入后端目录"; exit 1; }
    
    # 激活虚拟环境
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        error "虚拟环境不存在"
        exit 1
    fi
    
    # 检查是否有运行的进程
    info "停止现有的后端进程..."
    pkill -f "uvicorn.*app.main:app" || true
    sleep 2
    
    # 启动后端服务
    info "启动后端服务..."
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/backend.pid
    
    success "后端服务已启动 (PID: $BACKEND_PID)"
    
    # 等待启动
    info "等待后端服务启动..."
    for i in {1..10}; do
        if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
            success "后端服务已就绪"
            BACKEND_OK=true
            break
        fi
        sleep 2
    done
    
    if [ "$BACKEND_OK" = false ]; then
        error "后端服务启动失败"
        info "查看日志: tail -50 /tmp/backend.log"
    fi
    echo ""
fi

# 5. 修复前端服务
if [ "$FRONTEND_OK" = false ]; then
    echo "[5] 修复前端服务..."
    
    cd ~/liaotian/saas-demo || { error "无法进入前端目录"; exit 1; }
    
    # 检查是否有运行的进程
    info "停止现有的前端进程..."
    pkill -f "next.*dev\|node.*3000" || true
    sleep 2
    
    # 检查 .next 目录
    if [ ! -d ".next" ]; then
        info "构建前端..."
        npm run build
    fi
    
    # 启动前端服务
    info "启动前端服务..."
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/frontend.pid
    
    success "前端服务已启动 (PID: $FRONTEND_PID)"
    
    # 等待启动
    info "等待前端服务启动..."
    for i in {1..15}; do
        if curl -s --max-time 2 http://localhost:3000 > /dev/null 2>&1; then
            success "前端服务已就绪"
            FRONTEND_OK=true
            break
        fi
        sleep 2
    done
    
    if [ "$FRONTEND_OK" = false ]; then
        warn "前端服务可能仍在启动中"
        info "查看日志: tail -50 /tmp/frontend.log"
    fi
    echo ""
fi

# 6. 重新加载 Nginx
echo "[6] 重新加载 Nginx..."
sudo systemctl reload nginx || sudo systemctl restart nginx
sleep 2

if sudo systemctl is-active --quiet nginx; then
    success "Nginx 已重新加载"
else
    error "Nginx 重新加载失败"
    sudo systemctl status nginx --no-pager | head -20
fi
echo ""

# 7. 最终验证
echo "[7] 最终验证..."
echo ""

info "检查后端服务..."
if curl -s --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
    success "后端服务正常"
else
    error "后端服务仍然无法访问"
fi

info "检查前端服务..."
if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    success "前端服务正常"
else
    error "前端服务仍然无法访问"
fi

info "检查 Nginx..."
if curl -s --max-time 5 http://localhost > /dev/null 2>&1; then
    success "Nginx 正常"
else
    warn "Nginx 可能有问题"
fi
echo ""

echo "========================================"
echo "诊断和修复完成"
echo "========================================"
echo ""
echo "服务状态:"
echo "  后端: http://localhost:8000/health"
echo "  前端: http://localhost:3000"
echo ""
echo "日志文件:"
echo "  后端: /tmp/backend.log"
echo "  前端: /tmp/frontend.log"
echo ""
echo "如果问题仍然存在，请检查日志文件"
