#!/bin/bash
# ============================================================
# Fix Production Security Configuration
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Fix JWT_SECRET, ADMIN_DEFAULT_PASSWORD, and CORS_ORIGINS
#
# One-click execution: bash scripts/server/fix-security-config.sh
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
ENV_FILE="$BACKEND_DIR/.env"
ENV_EXAMPLE="$BACKEND_DIR/env.example"

echo "============================================================"
echo "🔒 修复生产环境安全配置"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 env.example 是否存在
if [ ! -f "$ENV_EXAMPLE" ]; then
    echo -e "${RED}❌ env.example 文件不存在${NC}"
    echo "请先确保 env.example 文件已从 GitHub 拉取"
    exit 1
fi

# 如果 .env 不存在，从 env.example 复制
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  .env 文件不存在，从 env.example 创建...${NC}"
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo -e "${GREEN}✅ 已创建 .env 文件${NC}"
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

echo ""
echo "============================================================"
echo "📝 当前配置状态"
echo "============================================================"

# 检查当前配置
cd "$BACKEND_DIR"
source venv/bin/activate 2>/dev/null || true

python3 << 'EOF'
import os
import sys
from pathlib import Path

# 读取 .env 文件
env_file = Path(".env")
if env_file.exists():
    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # 检查关键配置
    jwt_secret = env_vars.get('JWT_SECRET', '')
    admin_pass = env_vars.get('ADMIN_DEFAULT_PASSWORD', '')
    cors_origins = env_vars.get('CORS_ORIGINS', '')
    
    print(f"JWT_SECRET: {jwt_secret[:20]}..." if len(jwt_secret) > 20 else f"JWT_SECRET: {jwt_secret}")
    print(f"ADMIN_DEFAULT_PASSWORD: {'已设置' if admin_pass and admin_pass != 'changeme123' else '使用默认值（需要修改）'}")
    print(f"CORS_ORIGINS: {cors_origins[:50]}..." if len(cors_origins) > 50 else f"CORS_ORIGINS: {cors_origins}")
else:
    print("❌ .env 文件不存在")
    sys.exit(1)
EOF

echo ""
echo "============================================================"
echo "🔧 修复配置"
echo "============================================================"
echo ""

# 生成新的 JWT_SECRET
echo -e "${BLUE}生成新的 JWT_SECRET...${NC}"
NEW_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
echo -e "${GREEN}✅ 已生成新的 JWT_SECRET${NC}"

# 更新 .env 文件
echo -e "${BLUE}更新 .env 文件...${NC}"

# 使用 Python 脚本更新配置
python3 << EOF
import re
from pathlib import Path

env_file = Path("$ENV_FILE")

# 读取文件内容
with open(env_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 更新 JWT_SECRET
content = re.sub(r'^JWT_SECRET=.*', f'JWT_SECRET={NEW_JWT_SECRET}', content, flags=re.MULTILINE)

# 更新 CORS_ORIGINS（如果包含 localhost）
if 'localhost' in content and 'aikz.usdt2026.cc' not in content:
    content = re.sub(
        r'^CORS_ORIGINS=.*',
        'CORS_ORIGINS=https://aikz.usdt2026.cc',
        content,
        flags=re.MULTILINE
    )

# 写回文件
with open(env_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已更新 JWT_SECRET 和 CORS_ORIGINS")
EOF

echo ""
echo -e "${YELLOW}⚠️  注意: ADMIN_DEFAULT_PASSWORD 需要手动设置${NC}"
echo -e "${YELLOW}   请使用强密码（至少 12 字符）${NC}"
echo ""

# 验证配置
echo "============================================================"
echo "✅ 验证配置"
echo "============================================================"

cd "$BACKEND_DIR"
source venv/bin/activate 2>/dev/null || true

if python3 scripts/check_security_config.py 2>&1 | grep -q "所有安全檢查通過"; then
    echo -e "${GREEN}✅ 所有安全检查通过！${NC}"
else
    echo -e "${YELLOW}⚠️  仍有安全问题需要修复${NC}"
    echo "请运行以下命令查看详情:"
    echo "  cd $BACKEND_DIR"
    echo "  source venv/bin/activate"
    echo "  python scripts/check_security_config.py"
fi

echo ""
echo "============================================================"
echo "🔄 重启服务"
echo "============================================================"
echo ""

# 重启后端服务
echo -e "${BLUE}重启后端服务...${NC}"
pm2 restart backend
sleep 3
pm2 status backend

echo ""
echo -e "${GREEN}✅ 安全配置修复完成！${NC}"
echo ""
echo "下一步:"
echo "1. 手动设置 ADMIN_DEFAULT_PASSWORD（编辑 .env 文件）"
echo "2. 重启服务: pm2 restart backend"
echo "3. 使用新密码登录并立即修改"

