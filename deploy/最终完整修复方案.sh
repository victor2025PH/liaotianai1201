#!/bin/bash
# 最终完整修复方案

set -e

echo "========================================="
echo "最终完整修复 UPSERT 功能"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian/admin-backend

# 1. 检查文件
echo "【步骤1】检查文件内容..."
cd app/api/group_ai

UPSERT_COUNT=$(grep -c "UPSERT" accounts.py || echo "0")
echo "  文件中包含 'UPSERT' 的次数: $UPSERT_COUNT"

if grep -q "UPSERT 模式：账号不存在" accounts.py; then
    echo "  ✓ 找到 UPSERT 代码（第1075行附近）"
else
    echo "  ✗ 未找到 UPSERT 代码"
    echo "  请先上传修改后的文件"
    exit 1
fi

if grep -q "AccountManager 中但數據庫記錄不存在，使用 UPSERT" accounts.py; then
    echo "  ✓ 找到补充 UPSERT 代码（第1179行附近）"
else
    echo "  ⚠ 未找到补充 UPSERT 代码（可能不是最新版本）"
fi
echo ""

# 2. 完全重启后端服务
echo "【步骤2】完全重启后端服务..."

cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

echo "  强制停止所有相关进程..."
pkill -9 -f 'uvicorn.*app.main:app' || true
pkill -9 -f 'python.*uvicorn.*app.main' || true
pkill -9 -f 'python.*-m.*uvicorn.*app.main' || true
sleep 5

echo "  清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "  启动后端服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "  后端进程 PID: $BACKEND_PID"

echo "  等待服务启动（最多30秒）..."
for i in {1..15}; do
    sleep 2
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ 后端服务已启动（等待了 $((i*2)) 秒）"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "  ⚠ 服务启动较慢，查看日志..."
        tail -30 /tmp/backend.log
    fi
done

# 验证进程
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "  ✓ 后端进程正在运行"
else
    echo "  ✗ 后端进程未运行"
    echo "  查看启动日志:"
    tail -50 /tmp/backend.log
    exit 1
fi
echo ""

# 3. 测试 UPSERT
echo "【步骤3】测试 UPSERT 功能..."
LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])' 2>/dev/null)
    echo "  ✓ 登录成功"
    
    echo ""
    echo "  测试账号: 639454959591"
    echo "  节点: computer_002"
    echo ""
    
    RESPONSE=$(curl -s -w "\n\nHTTP_STATUS:%{http_code}" -X PUT \
      "http://localhost:8000/api/v1/group-ai/accounts/639454959591" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"script_id": "红包游戏陪玩剧本", "server_id": "computer_002"}' 2>&1)
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2 | tr -d ' ')
    BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS")
    
    echo "  HTTP 状态码: $HTTP_STATUS"
    echo ""
    
    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
        echo "  ✓✓✓ 成功！UPSERT 功能正常工作！"
        echo "  不再返回 404 错误！"
        echo ""
        echo "  响应内容:"
        echo "$BODY" | python3 -m json.tool 2>/dev/null | head -30 || echo "$BODY" | head -15
    else
        echo "  ✗ 仍然返回错误: $HTTP_STATUS"
        echo ""
        echo "  响应内容:"
        echo "$BODY" | head -20
        echo ""
        echo "  查看后端日志:"
        tail -100 /tmp/backend.log | grep -E "639454959591|UPDATE_ACCOUNT|UPSERT|ERROR|Exception" | tail -20
    fi
else
    echo "  ✗ 登录失败"
fi
echo ""

echo "========================================="
echo "修复完成！"
echo "完成时间: $(date)"
echo "========================================="
