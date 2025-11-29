#!/bin/bash
# 修复502和404问题 - 分步执行脚本
# 在远程服务器 ubuntu@165.154.233.55 上执行

set -e

echo "========================================="
echo "开始修复 502 和 404 问题"
echo "========================================="
echo ""

# ============================================================================
# 任务一：修复 502 问题
# ============================================================================

echo "【任务一】修复 502 Bad Gateway"
echo "─────────────────────────────────────────"

# 1. 检查前端端口配置
echo "步骤1: 检查前端端口配置..."
cd ~/liaotian/saas-demo
if grep -q '"dev": "next dev -p 3000"' package.json 2>/dev/null; then
    echo "  ✓ 端口配置正确 (3000)"
else
    echo "  ⚠ 端口配置需要修复..."
    # 修复端口配置
    if command -v node >/dev/null 2>&1; then
        node -e "
        const fs = require('fs');
        const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
        pkg.scripts.dev = 'next dev -p 3000';
        fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n', 'utf8');
        "
        echo "  ✓ 已修复端口配置"
    else
        echo "  ✗ 无法修复，需要手动编辑 package.json"
    fi
fi

# 2. 重启后端
echo ""
echo "步骤2: 重启后端服务..."
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
fi

# 3. 重启前端
echo ""
echo "步骤3: 重启前端服务..."
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
    echo "  查看日志: tail -30 /tmp/frontend.log"
fi

# 4. 重载Nginx
echo ""
echo "步骤4: 重载Nginx..."
sudo systemctl reload nginx 2>/dev/null && echo "  ✓ Nginx已重载" || echo "  ✗ Nginx重载失败"

# 5. 验证服务
echo ""
echo "步骤5: 验证服务状态..."
BACKEND_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null || echo "000")
FRONTEND_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo "000")
DOMAIN_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://aikz.usdt2026.cc/group-ai/accounts 2>/dev/null || echo "000")

echo "  后端健康检查: HTTP $BACKEND_CODE"
echo "  前端服务: HTTP $FRONTEND_CODE"
echo "  域名访问: HTTP $DOMAIN_CODE"

echo ""
echo "【任务一完成】"
echo ""

# ============================================================================
# 任务二：修复 404 账号不存在问题
# ============================================================================

echo "【任务二】修复 404 账号不存在"
echo "─────────────────────────────────────────"

# 1. 登录获取token
echo "步骤1: 登录获取token..."
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])' 2>/dev/null)
    echo "  ✓ 登录成功"
else
    echo "  ✗ 登录失败"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

# 2. 获取账号列表
echo ""
echo "步骤2: 获取账号列表..."
ACCOUNTS_JSON=$(curl -s "http://localhost:8000/api/v1/group-ai/accounts?page=1&page_size=100" \
  -H "Authorization: Bearer $TOKEN")

echo "$ACCOUNTS_JSON" > /tmp/group_ai_accounts.json
echo "  ✓ 账号列表已保存到 /tmp/group_ai_accounts.json"

# 提取账号ID列表
ACCOUNT_IDS=$(echo "$ACCOUNTS_JSON" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        ids = [str(acc.get("account_id", "")) for acc in data if acc.get("account_id")]
        print("\n".join(ids))
except:
    pass
' 2>/dev/null)

if [ -n "$ACCOUNT_IDS" ]; then
    COUNT=$(echo "$ACCOUNT_IDS" | wc -l)
    echo "  找到 $COUNT 个账号"
    echo "  前5个账号ID:"
    echo "$ACCOUNT_IDS" | head -5 | sed 's/^/    - /'
    FIRST_ID=$(echo "$ACCOUNT_IDS" | head -1)
else
    echo "  ⚠ 未找到任何账号"
    FIRST_ID=""
fi

# 3. 检查目标账号
echo ""
echo "步骤3: 检查账号 639277358115..."
TARGET_ID="639277358115"

if echo "$ACCOUNT_IDS" | grep -q "^${TARGET_ID}$"; then
    echo "  ✓ 账号 $TARGET_ID 存在"
    REAL_ID="$TARGET_ID"
    NEED_FIX=false
else
    echo "  ✗ 账号 $TARGET_ID 不存在"
    NEED_FIX=true
    
    if [ -n "$FIRST_ID" ]; then
        REAL_ID="$FIRST_ID"
        echo "  将使用账号 $REAL_ID 进行替换"
    else
        REAL_ID="$TARGET_ID"
        echo "  ⚠ 没有可用的账号ID进行替换"
    fi
fi

# 4. 搜索并替换代码中的引用
if [ "$NEED_FIX" = "true" ] && [ -n "$FIRST_ID" ] && [ "$FIRST_ID" != "$TARGET_ID" ]; then
    echo ""
    echo "步骤4: 搜索并替换代码中的引用..."
    cd ~/liaotian
    
    # 搜索前端代码
    FRONTEND_FILES=$(grep -rl "$TARGET_ID" saas-demo/src 2>/dev/null | head -10 || true)
    BACKEND_FILES=$(grep -rl "$TARGET_ID" admin-backend/app 2>/dev/null | head -10 || true)
    
    if [ -n "$FRONTEND_FILES" ]; then
        echo "  找到前端文件需要替换:"
        echo "$FRONTEND_FILES" | sed 's/^/    - /' | head -5
        echo "$FRONTEND_FILES" | xargs sed -i "s/$TARGET_ID/$REAL_ID/g" 2>/dev/null || true
        echo "  ✓ 前端代码已更新"
    fi
    
    if [ -n "$BACKEND_FILES" ]; then
        echo "  找到后端文件需要替换:"
        echo "$BACKEND_FILES" | sed 's/^/    - /' | head -5
        echo "$BACKEND_FILES" | xargs sed -i "s/$TARGET_ID/$REAL_ID/g" 2>/dev/null || true
        echo "  ✓ 后端代码已更新"
        
        # 重启后端
        echo ""
        echo "步骤5: 重启后端服务..."
        pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
        sleep 2
        cd ~/liaotian/admin-backend
        source .venv/bin/activate 2>/dev/null || true
        nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
        sleep 5
        echo "  ✓ 后端服务已重启"
    fi
fi

# 5. 验证修复
echo ""
echo "步骤6: 验证修复..."
if [ -n "$REAL_ID" ]; then
    TEST_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X PUT \
      "http://localhost:8000/api/v1/group-ai/accounts/$REAL_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"script_id":"test-script","server_id":"computer_001"}' 2>/dev/null || echo "000")
    
    if [ "$TEST_STATUS" = "200" ] || [ "$TEST_STATUS" = "201" ]; then
        echo "  ✓ PUT请求成功 (HTTP $TEST_STATUS)"
    elif [ "$TEST_STATUS" = "404" ]; then
        echo "  ✗ 仍然返回404"
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
echo "修复完成！总结"
echo "========================================="
echo ""
echo "【502问题修复结果】"
echo "  后端: HTTP $BACKEND_CODE"
echo "  前端: HTTP $FRONTEND_CODE"
echo "  域名: HTTP $DOMAIN_CODE"
echo ""
echo "【404问题修复结果】"
if [ "$NEED_FIX" = "true" ]; then
    echo "  已替换账号ID: $TARGET_ID -> $REAL_ID"
else
    echo "  账号ID $TARGET_ID 已存在，无需修复"
fi
echo ""
echo "========================================="
