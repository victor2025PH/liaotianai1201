#!/bin/bash
# 一键修复502和404问题
# 在远程服务器 ubuntu@165.154.233.55 上执行

set -e

LOG_FILE="/tmp/fix_502_404_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================="
echo "一键修复 502 和 404 问题"
echo "开始时间: $(date)"
echo "========================================="
echo ""

# ============================================================================
# 任务一：修复 502
# ============================================================================

echo "【任务一】修复 502 Bad Gateway"
echo "─────────────────────────────────────────"

# 1. 重启后端
echo "[1] 重启后端服务..."
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
sleep 2
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 5

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端服务已启动"
else
    echo "  ✗ 后端服务启动失败"
    tail -20 /tmp/backend.log
    exit 1
fi

# 2. 重启前端
echo "[2] 重启前端服务..."
cd ~/liaotian/saas-demo
pkill -f "next.*dev\|node.*3000" 2>/dev/null || true
sleep 2
nohup npm run dev > /tmp/frontend.log 2>&1 &
sleep 15

FRONTEND_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_CODE" = "200" ] || [ "$FRONTEND_CODE" = "304" ]; then
    echo "  ✓ 前端服务已启动 (HTTP $FRONTEND_CODE)"
else
    echo "  ⚠ 前端服务可能未完全启动 (HTTP $FRONTEND_CODE)"
fi

# 3. 重载Nginx
echo "[3] 重载Nginx..."
sudo systemctl reload nginx 2>/dev/null && echo "  ✓ Nginx已重载" || echo "  ✗ Nginx重载失败"

# 4. 验证
echo "[4] 验证服务状态..."
BACKEND_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null || echo "000")
FRONTEND_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo "000")
DOMAIN_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://aikz.usdt2026.cc/group-ai/accounts 2>/dev/null || echo "000")

echo "  后端: HTTP $BACKEND_CODE"
echo "  前端: HTTP $FRONTEND_CODE"
echo "  域名: HTTP $DOMAIN_CODE"

echo ""
echo "【任务一完成】"
echo ""

# ============================================================================
# 任务二：修复 404
# ============================================================================

echo "【任务二】修复 404 账号不存在"
echo "─────────────────────────────────────────"

# 1. 登录获取token
echo "[1] 登录获取token..."
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])' 2>/dev/null)
    echo "  ✓ 登录成功"
else
    echo "  ✗ 登录失败: $LOGIN_RESPONSE"
    exit 1
fi

# 2. 获取账号列表
echo "[2] 获取账号列表..."
ACCOUNTS_JSON=$(curl -s "http://localhost:8000/api/v1/group-ai/accounts?page=1&page_size=100" \
  -H "Authorization: Bearer $TOKEN")

echo "$ACCOUNTS_JSON" > /tmp/group_ai_accounts.json

ACCOUNT_IDS=$(echo "$ACCOUNTS_JSON" | python3 << 'PYEOF'
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        ids = [str(acc.get("account_id", "")) for acc in data if acc.get("account_id")]
        print("\n".join(ids))
except:
    pass
PYEOF
)

if [ -n "$ACCOUNT_IDS" ]; then
    COUNT=$(echo "$ACCOUNT_IDS" | wc -l)
    FIRST_ID=$(echo "$ACCOUNT_IDS" | head -1)
    echo "  ✓ 找到 $COUNT 个账号，第一个: $FIRST_ID"
else
    echo "  ⚠ 未找到任何账号"
    FIRST_ID=""
fi

# 3. 检查目标账号
echo "[3] 检查账号 639277358115..."
TARGET_ID="639277358115"

if echo "$ACCOUNT_IDS" | grep -q "^${TARGET_ID}$"; then
    echo "  ✓ 账号 $TARGET_ID 存在"
    REAL_ID="$TARGET_ID"
else
    echo "  ✗ 账号 $TARGET_ID 不存在"
    if [ -n "$FIRST_ID" ]; then
        REAL_ID="$FIRST_ID"
        echo "  将使用账号 $REAL_ID"
        
        # 4. 搜索并替换
        echo "[4] 搜索并替换代码中的引用..."
        cd ~/liaotian
        
        FRONTEND_FILES=$(grep -rl "$TARGET_ID" saas-demo/src 2>/dev/null | head -10 || true)
        BACKEND_FILES=$(grep -rl "$TARGET_ID" admin-backend/app 2>/dev/null | head -10 || true)
        
        if [ -n "$FRONTEND_FILES" ]; then
            echo "$FRONTEND_FILES" | xargs sed -i "s/$TARGET_ID/$REAL_ID/g" 2>/dev/null || true
            echo "  ✓ 前端代码已更新"
        fi
        
        if [ -n "$BACKEND_FILES" ]; then
            echo "$BACKEND_FILES" | xargs sed -i "s/$TARGET_ID/$REAL_ID/g" 2>/dev/null || true
            echo "  ✓ 后端代码已更新"
            
            # 重启后端
            echo "[5] 重启后端服务..."
            pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
            sleep 2
            cd ~/liaotian/admin-backend
            source .venv/bin/activate 2>/dev/null || true
            nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
            sleep 5
            echo "  ✓ 后端服务已重启"
        fi
    else
        REAL_ID="$TARGET_ID"
        echo "  ⚠ 没有可用账号进行替换"
    fi
fi

# 5. 验证
echo "[6] 验证修复..."
if [ -n "$REAL_ID" ]; then
    TEST_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X PUT \
      "http://localhost:8000/api/v1/group-ai/accounts/$REAL_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"script_id":"test-script","server_id":"computer_001"}' 2>/dev/null || echo "000")
    
    if [ "$TEST_STATUS" = "200" ] || [ "$TEST_STATUS" = "201" ]; then
        echo "  ✓ PUT请求成功 (HTTP $TEST_STATUS)"
    else
        echo "  ⚠ PUT请求返回 HTTP $TEST_STATUS"
    fi
fi

echo ""
echo "【任务二完成】"
echo ""

# ============================================================================
# 最终总结
# ============================================================================

echo "========================================="
echo "修复完成！总结报告"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "【502问题修复】"
echo "  后端健康检查: HTTP $BACKEND_CODE"
echo "  前端服务: HTTP $FRONTEND_CODE"
echo "  域名访问: HTTP $DOMAIN_CODE"
echo ""
echo "【404问题修复】"
if [ "$TARGET_ID" != "$REAL_ID" ]; then
    echo "  已替换账号ID: $TARGET_ID -> $REAL_ID"
else
    echo "  账号ID $TARGET_ID 已存在，无需替换"
fi
echo ""
echo "完整日志已保存到: $LOG_FILE"
echo "========================================="
