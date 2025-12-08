#!/bin/bash
# ============================================================
# Run Frontend E2E Tests on Server
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Run Playwright E2E tests for frontend
#
# One-click execution: bash scripts/server/run-frontend-tests.sh
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

echo "============================================================"
echo "🧪 运行前端 E2E 测试 (Frontend E2E Tests)"
echo "============================================================"
echo ""

cd "$FRONTEND_DIR"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "[1/4] 安装依赖..."
    npm install
else
    echo "[1/4] 依赖已安装"
fi

# 检查 Playwright
if [ ! -d "node_modules/@playwright/test" ]; then
    echo "[2/4] 安装 Playwright..."
    npm install @playwright/test
    npx playwright install chromium
else
    echo "[2/4] Playwright 已安装"
fi

# 检查前端服务是否运行
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "⚠️  警告: 前端服务未运行在 localhost:3000"
    echo "   测试可能需要前端服务运行"
    echo ""
fi

# 运行测试
echo "[3/4] 运行 E2E 测试..."
echo ""

npm run test:e2e

echo ""
echo "============================================================"
echo "✅ 测试完成"
echo "============================================================"

