#!/bin/bash
# ============================================================
# Check 500 Internal Server Error (Server Environment - Linux)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Check backend logs for 500 errors and diagnose issues
#
# One-click execution: sudo bash scripts/server/check_500_errors.sh
# ============================================================

set -e

echo "============================================================"
echo "🔍 检查 500 Internal Server Error"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 步骤 1: 检查后端服务状态
echo "[1/4] 检查后端服务状态"
echo "----------------------------------------"
if systemctl is-active --quiet luckyred-api 2>/dev/null; then
  echo -e "${GREEN}✅ 后端服务运行中${NC}"
else
  echo -e "${RED}❌ 后端服务未运行${NC}"
  exit 1
fi

echo ""

# 步骤 2: 查看最近的错误日志
echo "[2/4] 查看最近的错误日志（最后 50 行）"
echo "----------------------------------------"
echo "查找 ERROR 和 Exception:"
sudo journalctl -u luckyred-api -n 100 --no-pager | grep -i -E "error|exception|traceback|failed" | tail -30 || echo "未找到错误日志"

echo ""

# 步骤 3: 测试 API 端点
echo "[3/4] 测试 API 端点"
echo "----------------------------------------"

# 测试 servers API
echo "测试 /api/v1/group-ai/servers/ ..."
SERVERS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --max-time 10 "http://127.0.0.1:8000/api/v1/group-ai/servers/" 2>/dev/null || echo -e "\nHTTP_CODE:000")
SERVERS_CODE=$(echo "$SERVERS_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
SERVERS_BODY=$(echo "$SERVERS_RESPONSE" | grep -v "HTTP_CODE:")

if [ "$SERVERS_CODE" = "200" ] || [ "$SERVERS_CODE" = "401" ]; then
  echo -e "${GREEN}✅ Servers API: HTTP $SERVERS_CODE${NC}"
else
  echo -e "${RED}❌ Servers API: HTTP $SERVERS_CODE${NC}"
  echo "响应内容:"
  echo "$SERVERS_BODY" | head -20
fi

echo ""

# 测试 scripts API
echo "测试 /api/v1/group-ai/scripts/ ..."
SCRIPTS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --max-time 10 "http://127.0.0.1:8000/api/v1/group-ai/scripts/" 2>/dev/null || echo -e "\nHTTP_CODE:000")
SCRIPTS_CODE=$(echo "$SCRIPTS_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
SCRIPTS_BODY=$(echo "$SCRIPTS_RESPONSE" | grep -v "HTTP_CODE:")

if [ "$SCRIPTS_CODE" = "200" ] || [ "$SCRIPTS_CODE" = "401" ]; then
  echo -e "${GREEN}✅ Scripts API: HTTP $SCRIPTS_CODE${NC}"
else
  echo -e "${RED}❌ Scripts API: HTTP $SCRIPTS_CODE${NC}"
  echo "响应内容:"
  echo "$SCRIPTS_BODY" | head -20
fi

echo ""

# 测试 accounts API
echo "测试 /api/v1/group-ai/accounts/ ..."
ACCOUNTS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --max-time 10 "http://127.0.0.1:8000/api/v1/group-ai/accounts/" 2>/dev/null || echo -e "\nHTTP_CODE:000")
ACCOUNTS_CODE=$(echo "$ACCOUNTS_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
ACCOUNTS_BODY=$(echo "$ACCOUNTS_RESPONSE" | grep -v "HTTP_CODE:")

if [ "$ACCOUNTS_CODE" = "200" ] || [ "$ACCOUNTS_CODE" = "401" ]; then
  echo -e "${GREEN}✅ Accounts API: HTTP $ACCOUNTS_CODE${NC}"
else
  echo -e "${RED}❌ Accounts API: HTTP $ACCOUNTS_CODE${NC}"
  echo "响应内容:"
  echo "$ACCOUNTS_BODY" | head -20
fi

echo ""

# 步骤 4: 检查数据库连接
echo "[4/4] 检查数据库连接"
echo "----------------------------------------"
DB_FILE="/home/ubuntu/telegram-ai-system/admin-backend/data/app.db"
if [ -f "$DB_FILE" ]; then
  echo -e "${GREEN}✅ 数据库文件存在: $DB_FILE${NC}"
  DB_SIZE=$(du -h "$DB_FILE" | cut -f1)
  echo "数据库大小: $DB_SIZE"
  
  # 检查数据库是否可读
  if sqlite3 "$DB_FILE" "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 数据库可读${NC}"
  else
    echo -e "${RED}❌ 数据库无法读取${NC}"
  fi
else
  echo -e "${RED}❌ 数据库文件不存在: $DB_FILE${NC}"
fi

echo ""

# 总结
echo "============================================================"
echo "📋 诊断摘要"
echo "============================================================"
echo ""
echo "如果看到 500 错误，请检查："
echo "1. 后端服务日志: sudo journalctl -u luckyred-api -n 100 --no-pager | grep -i error"
echo "2. 数据库文件权限: ls -la $DB_FILE"
echo "3. Python 依赖: cd admin-backend && source venv/bin/activate && pip list"
echo "4. 重启服务: sudo systemctl restart luckyred-api"
echo ""

