#!/bin/bash
# ============================================================
# 重启服务并测试脚本
# ============================================================
# 功能：重启所有服务，监控日志，执行健康检查
# 使用方法：sudo bash scripts/server/restart-and-test.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务名称
BACKEND_SERVICE="telegram-backend"
BOT_SERVICE="telegram-bot"

echo "============================================================"
echo "🚀 重启服务并执行测试"
echo "============================================================"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 错误：请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 步骤 1: 停止所有服务
echo "[1/5] 停止现有服务..."
systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
systemctl stop "$BOT_SERVICE" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ 服务已停止${NC}"
echo ""

# 步骤 2: 启动后端服务
echo "[2/5] 启动后端服务..."
systemctl start "$BACKEND_SERVICE"
sleep 3

if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo -e "${GREEN}✅ 后端服务已启动${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    echo "   查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50"
    exit 1
fi
echo ""

# 步骤 3: 启动 Bot 服务
echo "[3/5] 启动 Bot 服务..."
systemctl start "$BOT_SERVICE"
sleep 3

if systemctl is-active --quiet "$BOT_SERVICE"; then
    echo -e "${GREEN}✅ Bot 服务已启动${NC}"
else
    echo -e "${YELLOW}⚠️  Bot 服务启动失败（可能配置问题，继续测试后端）${NC}"
fi
echo ""

# 步骤 4: 健康检查
echo "[4/5] 执行健康检查..."
echo ""

# 检查后端端口
echo "   检查后端端口 (8000)..."
if ss -tlnp | grep -q ":8000"; then
    echo -e "   ${GREEN}✅ 端口 8000 正在监听${NC}"
else
    echo -e "   ${RED}❌ 端口 8000 未监听${NC}"
fi

# 检查后端健康端点
echo "   检查后端健康状态..."
for i in {1..10}; do
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
        echo -e "   ${GREEN}✅ 后端健康检查通过${NC}"
        echo "   响应: $HEALTH_RESPONSE"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "   ${RED}❌ 后端健康检查失败（10 次重试）${NC}"
    else
        sleep 1
    fi
done

# 检查 API 文档端点
echo "   检查 API 文档..."
if curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ API 文档可访问${NC}"
else
    echo -e "   ${YELLOW}⚠️  API 文档不可访问${NC}"
fi

echo ""

# 步骤 5: 显示服务状态和日志
echo "[5/5] 服务状态总结"
echo "============================================================"
echo ""

# 后端状态
echo -e "${BLUE}📊 后端服务状态${NC}"
systemctl status "$BACKEND_SERVICE" --no-pager -l | head -n 15
echo ""

# Bot 状态
echo -e "${BLUE}📊 Bot 服务状态${NC}"
systemctl status "$BOT_SERVICE" --no-pager -l | head -n 15
echo ""

# 显示最近日志
echo "============================================================"
echo -e "${BLUE}📋 最近日志（最后 20 行）${NC}"
echo "============================================================"
echo ""
echo -e "${YELLOW}后端日志:${NC}"
journalctl -u "$BACKEND_SERVICE" -n 20 --no-pager || true
echo ""
echo -e "${YELLOW}Bot 日志:${NC}"
journalctl -u "$BOT_SERVICE" -n 20 --no-pager || true
echo ""

# 最终状态
echo "============================================================"
echo "✅ 重启和测试完成"
echo "============================================================"
echo ""
echo "📝 下一步操作："
echo "   1. 实时监控日志: bash scripts/server/view-logs.sh all -f"
echo "   2. 查看后端日志: bash scripts/server/view-logs.sh backend -f"
echo "   3. 查看 Bot 日志: bash scripts/server/view-logs.sh bot -f"
echo "   4. 测试 API: curl http://localhost:8000/health"
echo "   5. 访问文档: http://localhost:8000/docs"
echo ""

