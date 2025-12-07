#!/bin/bash
# ============================================================
# Check Backend and Frontend Services Running Status
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Check if backend and frontend services are running
# 
# One-click execution: bash scripts/server/check-services-running.sh
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_SERVICE="telegram-backend"
FRONTEND_SERVICE="liaotian-frontend"  # 也可能是 smart-tg-frontend

echo "============================================================"
echo "🔍 检查前后端服务运行状态"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# 1. Backend Service Status
# ============================================================
echo "[1/6] 检查后端服务状态..."
echo "----------------------------------------"

if systemctl list-units --type=service | grep -q "$BACKEND_SERVICE"; then
    if systemctl is-active --quiet "$BACKEND_SERVICE"; then
        echo -e "${GREEN}✅ 后端服务正在运行${NC}"
        systemctl status "$BACKEND_SERVICE" --no-pager -l | head -n 8
    else
        echo -e "${RED}❌ 后端服务未运行${NC}"
        systemctl status "$BACKEND_SERVICE" --no-pager -l | head -n 8 || true
    fi
else
    echo -e "${YELLOW}⚠️  后端服务未配置 (systemd)${NC}"
    echo "检查是否有 uvicorn 进程在运行..."
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        echo -e "${GREEN}✅ 发现 uvicorn 进程在运行${NC}"
        ps aux | grep -E "uvicorn.*app.main:app" | grep -v grep | head -n 2
    else
        echo -e "${RED}❌ 未发现 uvicorn 进程${NC}"
    fi
fi
echo ""

# ============================================================
# 2. Backend Port Status
# ============================================================
echo "[2/6] 检查后端端口 (8000)..."
echo "----------------------------------------"
if ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo -e "${GREEN}✅ 端口 8000 正在监听${NC}"
    ss -tlnp 2>/dev/null | grep ":8000"
else
    echo -e "${RED}❌ 端口 8000 未监听${NC}"
fi
echo ""

# ============================================================
# 3. Backend Health Check
# ============================================================
echo "[3/6] 检查后端健康状态..."
echo "----------------------------------------"
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端健康检查通过${NC}"
    echo "健康检查响应:"
    curl -s http://localhost:8000/health | head -n 5
else
    echo -e "${RED}❌ 后端健康检查失败${NC}"
    echo "服务可能未运行或无法响应"
fi
echo ""

# ============================================================
# 4. Frontend Service Status
# ============================================================
echo "[4/6] 检查前端服务状态..."
echo "----------------------------------------"

# 检查多个可能的前端服务名称
FRONTEND_FOUND=false
for service_name in "$FRONTEND_SERVICE" "smart-tg-frontend" "saas-demo"; do
    if systemctl list-units --type=service | grep -q "$service_name"; then
        FRONTEND_FOUND=true
        if systemctl is-active --quiet "$service_name"; then
            echo -e "${GREEN}✅ 前端服务正在运行 ($service_name)${NC}"
            systemctl status "$service_name" --no-pager -l | head -n 8
            break
        else
            echo -e "${YELLOW}⚠️  前端服务已配置但未运行 ($service_name)${NC}"
            systemctl status "$service_name" --no-pager -l | head -n 5 || true
        fi
    fi
done

if [ "$FRONTEND_FOUND" = false ]; then
    echo -e "${YELLOW}⚠️  前端服务未配置 (systemd)${NC}"
    echo "检查是否有 Node.js/Next.js 进程在运行..."
    
    # 检查常见的 Node.js 进程
    if pgrep -f "node.*next" > /dev/null || pgrep -f "npm.*start" > /dev/null; then
        echo -e "${GREEN}✅ 发现 Node.js 进程在运行${NC}"
        ps aux | grep -E "node.*next|npm.*start" | grep -v grep | head -n 2
    else
        echo -e "${YELLOW}⚠️  未发现 Node.js 进程${NC}"
    fi
fi
echo ""

# ============================================================
# 5. Frontend Port Status
# ============================================================
echo "[5/6] 检查前端端口 (3000, 3001)..."
echo "----------------------------------------"
FRONTEND_PORT_FOUND=false
for port in 3000 3001 3002; do
    if ss -tlnp 2>/dev/null | grep -q ":$port"; then
        echo -e "${GREEN}✅ 端口 $port 正在监听${NC}"
        ss -tlnp 2>/dev/null | grep ":$port"
        FRONTEND_PORT_FOUND=true
    fi
done

if [ "$FRONTEND_PORT_FOUND" = false ]; then
    echo -e "${RED}❌ 前端端口 (3000, 3001, 3002) 均未监听${NC}"
fi
echo ""

# ============================================================
# 6. Frontend Health Check
# ============================================================
echo "[6/6] 检查前端健康状态..."
echo "----------------------------------------"
FRONTEND_HTTP_OK=false
for port in 3000 3001 3002; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        echo -e "${GREEN}✅ 前端服务在端口 $port 响应正常 (HTTP $HTTP_CODE)${NC}"
        echo "访问地址: http://localhost:$port"
        FRONTEND_HTTP_OK=true
        break
    fi
done

if [ "$FRONTEND_HTTP_OK" = false ]; then
    echo -e "${RED}❌ 前端服务未响应${NC}"
    echo "前端可能未运行或无法访问"
fi
echo ""

# ============================================================
# Summary
# ============================================================
echo "============================================================"
echo "📊 服务状态总结"
echo "============================================================"
echo ""

BACKEND_OK=false
FRONTEND_OK=false

# Check backend
if systemctl is-active --quiet "$BACKEND_SERVICE" 2>/dev/null || pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务: 运行正常${NC}"
        BACKEND_OK=true
    else
        echo -e "${YELLOW}⚠️  后端服务: 进程运行但健康检查失败${NC}"
    fi
else
    echo -e "${RED}❌ 后端服务: 未运行${NC}"
fi

# Check frontend
if systemctl is-active --quiet "$FRONTEND_SERVICE" 2>/dev/null || systemctl is-active --quiet "smart-tg-frontend" 2>/dev/null; then
    FRONTEND_OK=true
elif pgrep -f "node.*next" > /dev/null || pgrep -f "npm.*start" > /dev/null; then
    FRONTEND_OK=true
fi

if [ "$FRONTEND_OK" = true ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        echo -e "${GREEN}✅ 前端服务: 运行正常 (端口 3000)${NC}"
    else
        echo -e "${YELLOW}⚠️  前端服务: 进程运行但 HTTP 响应异常${NC}"
    fi
else
    echo -e "${RED}❌ 前端服务: 未运行${NC}"
fi

echo ""

# ============================================================
# Recommendations
# ============================================================
if [ "$BACKEND_OK" = false ] || [ "$FRONTEND_OK" = false ]; then
    echo "============================================================"
    echo "🔧 建议操作"
    echo "============================================================"
    echo ""
    
    if [ "$BACKEND_OK" = false ]; then
        echo "后端服务未运行，可以执行："
        echo "  sudo systemctl start $BACKEND_SERVICE"
        echo "  或"
        echo "  cd $PROJECT_DIR/admin-backend"
        echo "  source venv/bin/activate"
        echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
        echo ""
    fi
    
    if [ "$FRONTEND_OK" = false ]; then
        echo "前端服务未运行，可以执行："
        echo "  sudo systemctl start $FRONTEND_SERVICE"
        echo "  或"
        echo "  cd $PROJECT_DIR/saas-demo"
        echo "  npm run build && npm start"
        echo ""
    fi
    
    echo "查看服务日志："
    echo "  后端: sudo journalctl -u $BACKEND_SERVICE -n 50"
    echo "  前端: sudo journalctl -u $FRONTEND_SERVICE -n 50"
    echo ""
    echo "诊断服务问题："
    echo "  bash scripts/server/diagnose-service.sh"
    echo ""
fi

echo "============================================================"

