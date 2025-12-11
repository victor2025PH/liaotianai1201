#!/bin/bash
# ============================================================
# 修复 Next.js 静态资源 500 错误
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "◆ 修复 Next.js 静态资源 500 错误"
echo "============================================================"
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
STANDALONE_DIR="$FRONTEND_DIR/.next/standalone"

echo "[1] 检查 standalone 目录结构..."
echo "----------------------------------------"
cd "$FRONTEND_DIR" || exit 1

if [ ! -d ".next/standalone" ]; then
    echo -e "${RED}❌ .next/standalone 目录不存在${NC}"
    echo "  请先运行: npm run build"
    exit 1
fi

echo -e "${GREEN}□ standalone 目录存在${NC}"

# 检查 .next/static 是否存在
if [ ! -d ".next/static" ]; then
    echo -e "${RED}❌ .next/static 目录不存在${NC}"
    exit 1
fi

echo -e "${GREEN}□ .next/static 目录存在${NC}"
echo ""

echo "[2] 检查 standalone 目录中的 .next/static..."
echo "----------------------------------------"
cd "$STANDALONE_DIR" || exit 1

if [ ! -d ".next/static" ]; then
    echo -e "${YELLOW}▲ .next/static 不存在，正在创建并复制...${NC}"
    mkdir -p .next
    cp -r "$FRONTEND_DIR/.next/static" .next/ || {
        echo -e "${RED}❌ 复制 .next/static 失败${NC}"
        exit 1
    }
    echo -e "${GREEN}□ .next/static 已复制${NC}"
else
    echo -e "${GREEN}□ .next/static 已存在${NC}"
    # 检查是否需要更新
    if [ "$FRONTEND_DIR/.next/static" -nt ".next/static" ]; then
        echo -e "${YELLOW}▲ 检测到新的构建，更新 .next/static...${NC}"
        rm -rf .next/static
        cp -r "$FRONTEND_DIR/.next/static" .next/ || {
            echo -e "${RED}❌ 更新 .next/static 失败${NC}"
            exit 1
        }
        echo -e "${GREEN}□ .next/static 已更新${NC}"
    fi
fi
echo ""

echo "[3] 检查 public 目录..."
echo "----------------------------------------"
if [ ! -d "public" ]; then
    if [ -d "$FRONTEND_DIR/public" ]; then
        echo -e "${YELLOW}▲ public 目录不存在，正在复制...${NC}"
        cp -r "$FRONTEND_DIR/public" . || {
            echo -e "${RED}❌ 复制 public 目录失败${NC}"
            exit 1
        }
        echo -e "${GREEN}□ public 目录已复制${NC}"
    else
        echo -e "${YELLOW}▲ public 目录不存在（可能不需要）${NC}"
    fi
else
    echo -e "${GREEN}□ public 目录已存在${NC}"
fi
echo ""

echo "[4] 检查 server.js 和文件权限..."
echo "----------------------------------------"
if [ ! -f "server.js" ]; then
    echo -e "${RED}❌ server.js 文件不存在${NC}"
    exit 1
fi

echo -e "${GREEN}□ server.js 文件存在${NC}"

# 确保文件有执行权限
chmod +x server.js 2>/dev/null || true

# 检查文件所有者
OWNER=$(stat -c '%U' server.js 2>/dev/null || echo "unknown")
echo "  server.js 所有者: $OWNER"
echo ""

echo "[5] 测试静态资源路径..."
echo "----------------------------------------"
# 检查是否有静态文件
STATIC_FILES=$(find .next/static -type f 2>/dev/null | head -5 || echo "")
if [ -z "$STATIC_FILES" ]; then
    echo -e "${RED}❌ .next/static 目录中没有文件${NC}"
    exit 1
fi

echo -e "${GREEN}□ 找到静态文件${NC}"
echo "  示例文件:"
echo "$STATIC_FILES" | head -3 | while read -r file; do
    if [ -f "$file" ]; then
        echo "    ✓ $file"
    fi
done
echo ""

echo "[6] 检查 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.conf"
if [ -f "$NGINX_CONFIG" ]; then
    # 检查是否有 /_next/ 配置
    if grep -q "location /_next/" "$NGINX_CONFIG"; then
        echo -e "${GREEN}□ Nginx 配置包含 /_next/ 路径${NC}"
    else
        echo -e "${YELLOW}▲ Nginx 配置可能缺少 /_next/ 路径${NC}"
    fi
    
    # 检查是否有 /next/ 配置（错误路径）
    if grep -q "location /next/" "$NGINX_CONFIG"; then
        echo -e "${YELLOW}▲ 发现 /next/ 路径配置（可能是错误的）${NC}"
    fi
else
    echo -e "${YELLOW}▲ Nginx 配置文件不存在${NC}"
fi
echo ""

echo "[7] 重启前端服务..."
echo "----------------------------------------"
sudo systemctl restart liaotian-frontend
sleep 5

STATUS=$(sudo systemctl is-active liaotian-frontend 2>/dev/null | awk 'NR==1 {print $1}' || echo "inactive")
if [ "$STATUS" = "active" ]; then
    echo -e "${GREEN}□ 服务已重启${NC}"
else
    echo -e "${RED}❌ 服务重启失败，状态: $STATUS${NC}"
    echo "  查看日志: sudo journalctl -u liaotian-frontend -n 30 --no-pager"
    exit 1
fi
echo ""

echo "[8] 测试静态资源访问..."
echo "----------------------------------------"
sleep 3

# 尝试访问一个静态文件
TEST_FILE=$(find .next/static -type f -name "*.js" 2>/dev/null | head -1 || echo "")
if [ -n "$TEST_FILE" ]; then
    # 提取相对路径
    REL_PATH=${TEST_FILE#.next/static/}
    TEST_URL="http://localhost:3000/_next/static/$REL_PATH"
    
    echo "测试 URL: $TEST_URL"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$TEST_URL" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}□ 静态资源访问成功 (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${YELLOW}▲ 静态资源访问返回 HTTP $HTTP_CODE${NC}"
        echo "  这可能是正常的（如果文件不存在），或者需要检查 Next.js 配置"
    fi
else
    echo -e "${YELLOW}▲ 未找到测试文件${NC}"
fi
echo ""

echo "============================================================"
echo -e "${GREEN}□ 修复完成${NC}"
echo "============================================================"
echo ""
echo "如果问题仍然存在，请检查："
echo "  1. Next.js 服务器日志: sudo journalctl -u liaotian-frontend -n 50 --no-pager"
echo "  2. Nginx 错误日志: sudo tail -20 /var/log/nginx/aikz-error.log"
echo "  3. 确认请求路径是 /_next/ 而不是 /next/"

