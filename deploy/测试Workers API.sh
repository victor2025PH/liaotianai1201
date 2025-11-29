#!/bin/bash
# 测试 Workers API 端点

echo "=========================================="
echo "测试 Workers API 端点"
echo "=========================================="
echo ""

# 1. 检查文件是否存在
echo "[1] 检查 workers.py 文件..."
if ssh ubuntu@165.154.233.55 "test -f /home/ubuntu/liaotian/admin-backend/app/api/workers.py"; then
    echo "✓ 文件存在"
else
    echo "✗ 文件不存在"
    exit 1
fi

# 2. 检查服务状态
echo ""
echo "[2] 检查后端服务状态..."
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-backend --no-pager | head -10"

# 3. 测试 Workers API 端点
echo ""
echo "[3] 测试 GET /api/v1/workers/ 端点..."
ssh ubuntu@165.154.233.55 "curl -s http://127.0.0.1:8000/api/v1/workers/ | python3 -m json.tool 2>&1 | head -30"

# 4. 测试心跳端点
echo ""
echo "[4] 测试 POST /api/v1/workers/heartbeat 端点..."
ssh ubuntu@165.154.233.55 "curl -s -X POST http://127.0.0.1:8000/api/v1/workers/heartbeat -H 'Content-Type: application/json' -d '{\"node_id\":\"computer_001\",\"status\":\"online\",\"account_count\":0,\"accounts\":[]}' | python3 -m json.tool 2>&1"

# 5. 再次测试获取 Workers 列表
echo ""
echo "[5] 再次测试 GET /api/v1/workers/ 端点（应该能看到 computer_001）..."
ssh ubuntu@165.154.233.55 "curl -s http://127.0.0.1:8000/api/v1/workers/ | python3 -m json.tool 2>&1 | head -30"

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="

