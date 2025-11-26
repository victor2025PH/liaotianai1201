#!/bin/bash

# 前端功能验证脚本
# 用于检查前端和后端服务是否正常运行

echo "=========================================="
echo "前端功能验证脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查后端服务
echo "1. 检查后端服务..."
BACKEND_URL="${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}"
BACKEND_HEALTH="${BACKEND_URL%/api/v1}/health"

if curl -s -f "$BACKEND_HEALTH" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行正常${NC} ($BACKEND_HEALTH)"
else
    echo -e "${RED}✗ 后端服务无法访问${NC} ($BACKEND_HEALTH)"
    echo "  请确保后端服务已启动："
    echo "  cd admin-backend"
    echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

# 检查前端服务
echo ""
echo "2. 检查前端服务..."
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

if curl -s -f "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务运行正常${NC} ($FRONTEND_URL)"
else
    echo -e "${RED}✗ 前端服务无法访问${NC} ($FRONTEND_URL)"
    echo "  请确保前端服务已启动："
    echo "  cd saas-demo"
    echo "  npm run dev"
    exit 1
fi

# 检查 API 端点
echo ""
echo "3. 检查关键 API 端点..."

# 检查认证端点
AUTH_URL="${BACKEND_URL%/api/v1}/api/v1/auth/login"
if curl -s -f -X POST "$AUTH_URL" -H "Content-Type: application/x-www-form-urlencoded" -d "username=test&password=test" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 认证 API 可访问${NC}"
else
    echo -e "${YELLOW}⚠ 认证 API 需要有效凭证${NC} (这是正常的)"
fi

# 检查健康检查端点
if curl -s -f "$BACKEND_HEALTH" | grep -q "ok"; then
    echo -e "${GREEN}✓ 健康检查端点正常${NC}"
else
    echo -e "${RED}✗ 健康检查端点异常${NC}"
fi

echo ""
echo "=========================================="
echo "服务检查完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 打开浏览器访问: $FRONTEND_URL"
echo "2. 按照验证清单逐项检查功能"
echo "3. 参考文档: admin-backend/前端功能驗證清單.md"
echo ""

