#!/bin/bash
# 诊断和修复 502 Bad Gateway 错误

echo "=========================================="
echo "🔍 诊断和修复 502 Bad Gateway 错误"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
SERVICE_NAME="luckyred-api"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查后端服务状态
echo "[1/8] 检查后端服务状态..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "  ${GREEN}✅ 后端服务正在运行${NC}"
    systemctl status $SERVICE_NAME --no-pager | head -8
else
    echo -e "  ${RED}❌ 后端服务未运行${NC}"
    echo "  尝试启动服务..."
    sudo systemctl start $SERVICE_NAME
    sleep 3
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "  ${GREEN}✅ 服务已成功启动${NC}"
    else
        echo -e "  ${RED}❌ 服务启动失败${NC}"
    fi
fi
echo ""

# 2. 检查端口 8000
echo "[2/8] 检查端口 8000..."
if ss -tlnp | grep -q ":8000"; then
    echo -e "  ${GREEN}✅ 端口 8000 正在监听${NC}"
    ss -tlnp | grep ":8000"
else
    echo -e "  ${RED}❌ 端口 8000 未被监听${NC}"
    echo "  后端服务可能未启动或监听地址不正确"
fi
echo ""

# 3. 测试本地后端健康检查
echo "[3/8] 测试本地后端健康检查 (http://localhost:8000/health)..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8000/health 2>/dev/null)
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo -e "  ${GREEN}✅ 健康检查通过 (HTTP $HEALTH_RESPONSE)${NC}"
    curl -s http://localhost:8000/health | head -3
else
    echo -e "  ${RED}❌ 健康检查失败 (HTTP $HEALTH_RESPONSE)${NC}"
    if [ -z "$HEALTH_RESPONSE" ]; then
        echo "  无法连接到后端服务，可能是服务未启动或崩溃"
    fi
fi
echo ""

# 4. 检查 Nginx 配置
echo "[4/8] 检查 Nginx 配置..."
if [ -f "/etc/nginx/sites-available/aikz.usdt2026.cc" ]; then
    echo -e "  ${GREEN}✅ Nginx 配置文件存在${NC}"
    echo "  检查 proxy_pass 配置..."
    if grep -q "proxy_pass.*127.0.0.1:8000" /etc/nginx/sites-available/aikz.usdt2026.cc; then
        echo -e "  ${GREEN}✅ proxy_pass 配置正确${NC}"
    else
        echo -e "  ${YELLOW}⚠️  proxy_pass 配置可能不正确${NC}"
    fi
else
    echo -e "  ${RED}❌ Nginx 配置文件不存在${NC}"
fi

# 检查 Nginx 配置语法
echo "  检查 Nginx 配置语法..."
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo -e "  ${GREEN}✅ Nginx 配置语法正确${NC}"
else
    echo -e "  ${RED}❌ Nginx 配置语法错误${NC}"
    sudo nginx -t 2>&1 | tail -5
fi
echo ""

# 5. 检查 Nginx 服务状态
echo "[5/8] 检查 Nginx 服务状态..."
if systemctl is-active --quiet nginx; then
    echo -e "  ${GREEN}✅ Nginx 正在运行${NC}"
else
    echo -e "  ${RED}❌ Nginx 未运行${NC}"
    echo "  尝试启动 Nginx..."
    sudo systemctl start nginx
fi
echo ""

# 6. 查看后端日志（最近的错误）
echo "[6/8] 查看后端日志（最近 30 行）..."
sudo journalctl -u $SERVICE_NAME -n 30 --no-pager | tail -20
echo ""

# 7. 检查后端进程
echo "[7/8] 检查后端进程..."
BACKEND_PIDS=$(pgrep -f "gunicorn.*app.main:app\|uvicorn.*app.main:app")
if [ -n "$BACKEND_PIDS" ]; then
    echo -e "  ${GREEN}✅ 找到后端进程${NC}"
    ps aux | grep -E "gunicorn|uvicorn" | grep -v grep | head -3
else
    echo -e "  ${RED}❌ 未找到后端进程${NC}"
    echo "  后端服务可能已崩溃"
fi
echo ""

# 8. 尝试修复
echo "[8/8] 尝试修复..."
FIXED=false

# 如果服务未运行，尝试重启
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "  重启后端服务..."
    sudo systemctl restart $SERVICE_NAME
    sleep 5
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "  ${GREEN}✅ 后端服务已重启${NC}"
        FIXED=true
    else
        echo -e "  ${RED}❌ 后端服务重启失败${NC}"
        echo "  查看详细错误："
        sudo journalctl -u $SERVICE_NAME -n 20 --no-pager | grep -i error | tail -5
    fi
fi

# 如果后端进程不存在但服务状态显示运行，可能是服务配置问题
if [ -z "$BACKEND_PIDS" ] && systemctl is-active --quiet $SERVICE_NAME; then
    echo "  后端服务状态异常，强制重启..."
    sudo systemctl stop $SERVICE_NAME
    sleep 2
    sudo systemctl start $SERVICE_NAME
    sleep 5
    FIXED=true
fi

# 重新加载 Nginx（如果配置更改）
if sudo nginx -t &>/dev/null; then
    echo "  重新加载 Nginx 配置..."
    sudo systemctl reload nginx
    echo -e "  ${GREEN}✅ Nginx 配置已重新加载${NC}"
fi

echo ""

# 最终验证
echo "=========================================="
echo "📊 最终验证"
echo "=========================================="
echo ""

# 再次检查健康端点
echo "再次检查后端健康状态..."
sleep 2
FINAL_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8000/health 2>/dev/null)
if [ "$FINAL_HEALTH" = "200" ]; then
    echo -e "${GREEN}✅ 后端服务正常 (HTTP $FINAL_HEALTH)${NC}"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
    echo ""
    echo -e "${GREEN}✅ 502 错误应该已修复！${NC}"
else
    echo -e "${RED}❌ 后端服务仍然不可用 (HTTP $FINAL_HEALTH)${NC}"
    echo ""
    echo "建议执行以下操作："
    echo "1. 查看详细日志: sudo journalctl -u $SERVICE_NAME -f"
    echo "2. 检查后端代码: cd $BACKEND_DIR"
    echo "3. 手动启动测试: cd $BACKEND_DIR && source venv/bin/activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
fi
echo ""
