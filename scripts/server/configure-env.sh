#!/bin/bash
# ============================================================
# 配置環境變量腳本
# ============================================================
# 功能：幫助用戶配置 .env 文件
# 使用方法：bash scripts/server/configure-env.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "⚙️  配置環境變量"
echo "============================================================"
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 配置後端 .env
echo "[1/2] 配置後端環境變量..."
cd "$PROJECT_ROOT/admin-backend"

if [ ! -f ".env" ]; then
    echo "創建 .env 文件..."
    cat > .env << 'EOF'
# 應用配置
APP_NAME=Smart TG Admin API
DATABASE_URL=sqlite:///./admin.db
REDIS_URL=redis://localhost:6379/0

# JWT 配置（請修改 SECRET_KEY）
SECRET_KEY=change-me-in-production-use-secure-random-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 管理員默認賬號（首次啟動後請修改）
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123

# OpenAI API 配置
OPENAI_API_KEY=
AI_PROVIDER=openai

# Telegram API 配置
TELEGRAM_API_ID=
TELEGRAM_API_HASH=

# 群組 AI 配置
GROUP_AI_AI_PROVIDER=openai
GROUP_AI_AI_API_KEY=
EOF
    echo -e "${GREEN}✅ .env 文件已創建${NC}"
else
    echo -e "${YELLOW}⚠️  .env 文件已存在，跳過創建${NC}"
fi

# 生成 JWT Secret Key（如果還是默認值）
if grep -q "change-me-in-production" "$PROJECT_ROOT/admin-backend/.env"; then
    echo "生成安全的 JWT Secret Key..."
    if command -v python3 &> /dev/null; then
        NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        # 替換 SECRET_KEY（僅在 Linux/Mac 上）
        if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i "s/SECRET_KEY=change-me-in-production/SECRET_KEY=$NEW_SECRET/" "$PROJECT_ROOT/admin-backend/.env"
            echo -e "${GREEN}✅ JWT Secret Key 已自動生成${NC}"
        else
            echo -e "${YELLOW}⚠️  請手動更新 .env 文件中的 SECRET_KEY${NC}"
            echo "生成的密鑰: $NEW_SECRET"
        fi
    else
        echo -e "${YELLOW}⚠️  Python3 未找到，無法自動生成密鑰${NC}"
    fi
fi

# 2. 配置前端 .env.local
echo ""
echo "[2/2] 配置前端環境變量..."
cd "$PROJECT_ROOT/saas-demo"

if [ ! -f ".env.local" ]; then
    echo "創建 .env.local 文件..."
    cat > .env.local << 'EOF'
# API 基礎 URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_GROUP_AI_API_BASE_URL=http://localhost:8000/api/v1/group-ai

# WebSocket URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/notifications/ws

# 環境
NODE_ENV=development
EOF
    echo -e "${GREEN}✅ .env.local 文件已創建${NC}"
else
    echo -e "${YELLOW}⚠️  .env.local 文件已存在，跳過創建${NC}"
fi

echo ""
echo "============================================================"
echo -e "${GREEN}✅ 環境變量配置完成${NC}"
echo "============================================================"
echo ""
echo "下一步："
echo "  1. 編輯 admin-backend/.env 文件，填入："
echo "     - OPENAI_API_KEY (必需，用於 AI 功能)"
echo "     - TELEGRAM_API_ID 和 TELEGRAM_API_HASH (可選，用於群組 AI)"
echo ""
echo "  2. 如果部署到生產環境，請修改："
echo "     - SECRET_KEY (已自動生成)"
echo "     - ADMIN_DEFAULT_PASSWORD"
echo "     - NEXT_PUBLIC_API_BASE_URL (前端 .env.local)"
echo ""

