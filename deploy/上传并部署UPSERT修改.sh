#!/bin/bash
# 通过 SSH 直接修改服务器文件并重启后端
# 在本地执行，通过 SSH 连接到服务器

SERVER="ubuntu@165.154.233.55"
REMOTE_FILE="~/liaotian/admin-backend/app/api/group_ai/accounts.py"
LOCAL_FILE="admin-backend/app/api/group_ai/accounts.py"

echo "========================================="
echo "上传并部署 UPSERT 功能修改"
echo "========================================="
echo ""

# 检查本地文件是否存在
if [ ! -f "$LOCAL_FILE" ]; then
    echo "✗ 错误: 本地文件不存在: $LOCAL_FILE"
    exit 1
fi

echo "【步骤1】备份服务器上的原始文件..."
ssh $SERVER "cd ~/liaotian/admin-backend/app/api/group_ai && cp accounts.py accounts.py.bak.\$(date +%Y%m%d_%H%M%S) && echo 'Backup created'"
echo ""

echo "【步骤2】上传修改后的文件到服务器..."
scp "$LOCAL_FILE" "$SERVER:$REMOTE_FILE"
if [ $? -eq 0 ]; then
    echo "  ✓ 文件上传成功"
else
    echo "  ✗ 文件上传失败，尝试替代方法..."
    # 使用 base64 编码传输
    cat "$LOCAL_FILE" | base64 | ssh $SERVER "base64 -d > $REMOTE_FILE && echo 'File uploaded via base64'"
fi
echo ""

echo "【步骤3】验证文件是否包含 UPSERT 代码..."
ssh $SERVER "grep -q 'UPSERT 模式' $REMOTE_FILE && echo '  ✓ UPSERT 代码已存在' || echo '  ✗ UPSERT 代码不存在'"
echo ""

echo "【步骤4】重启后端服务..."
ssh $SERVER "cd ~/liaotian/admin-backend && source .venv/bin/activate 2>/dev/null || true && pkill -f 'uvicorn.*app.main:app' || true && sleep 2 && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 & sleep 5 && curl -s http://localhost:8000/health | head -1 && echo '  ✓ 后端服务已重启'"
echo ""

echo "========================================="
echo "部署完成！"
echo "========================================="
