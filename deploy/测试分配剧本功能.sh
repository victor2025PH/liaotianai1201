#!/bin/bash
# 分配剧本功能测试脚本

echo "=== 分配剧本功能测试 ==="
echo ""

# 1. 检查服务状态
echo "1. 检查服务状态..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)

if [ "$BACKEND_STATUS" = "200" ]; then
    echo "  ✓ 后端服务正常 (HTTP $BACKEND_STATUS)"
else
    echo "  ✗ 后端服务异常 (HTTP $BACKEND_STATUS)"
fi

if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "304" ]; then
    echo "  ✓ 前端服务正常 (HTTP $FRONTEND_STATUS)"
else
    echo "  ✗ 前端服务异常 (HTTP $FRONTEND_STATUS)"
fi

echo ""

# 2. 检查服务器配置
echo "2. 检查服务器配置..."
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
try:
    from app.api.group_ai.session_uploader import SessionUploader
    
    uploader = SessionUploader()
    servers = list(uploader.servers.keys())
    
    print(f"  找到 {len(servers)} 个服务器:")
    for server_id in servers:
        server = uploader.servers[server_id]
        print(f"    - {server_id}: {server.host} ({server.deploy_dir})")
    
    if 'computer_001' in servers:
        print("  ✓ computer_001 在服务器列表中")
    else:
        print("  ✗ computer_001 不在服务器列表中")
        print(f"  可用服务器: {servers}")
except Exception as e:
    print(f"  ✗ 检查失败: {e}")
PYEOF

echo ""

# 3. 检查后端代码修复
echo "3. 检查后端代码修复..."
cd ~/liaotian/admin-backend

python3 << 'PYEOF'
file_path = 'app/api/group_ai/accounts.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

checks = {
    '收到更新賬號請求日志': '收到更新賬號請求: account_id=' in content,
    'AccountManager检查': 'account_in_manager = account_id in manager.accounts' in content,
    'server_id检查': 'if request.server_id:' in content,
    '远程扫描逻辑': 'scan_server_accounts(server_node, db)' in content,
    'session_file字段': 'session_file: Optional[str]' in content and 'AccountUpdateRequest' in content[:2000],
}

print("  后端修复检查:")
all_passed = True
for name, result in checks.items():
    status = "✓" if result else "✗"
    print(f"    {status} {name}")
    if not result:
        all_passed = False

if all_passed:
    print("  ✓ 所有后端修复已应用")
else:
    print("  ⚠ 部分后端修复缺失")
PYEOF

echo ""

# 4. 检查前端代码修复
echo "4. 检查前端代码修复..."
cd ~/liaotian/saas-demo

python3 << 'PYEOF'
file_path = 'src/app/group-ai/accounts/page.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

checks = {
    'server_id传递': 'server_id: selectedAccountForRole.server_id || (selectedAccountForRole as any).node_id' in content,
    '调试日志': 'console.log.*分配剧本' in content,
    'session_file处理': 'session_file.*|| undefined' in content or 'session_file.*undefined' in content,
}

print("  前端修复检查:")
all_passed = True
for name, result in checks.items():
    status = "✓" if result else "✗"
    print(f"    {status} {name}")
    if not result:
        all_passed = False

if all_passed:
    print("  ✓ 所有前端修复已应用")
else:
    print("  ⚠ 部分前端修复缺失")
PYEOF

echo ""

# 5. 查看最近的日志
echo "5. 查看最近的日志（最后50行）..."
if [ -f "/tmp/backend_full_debug.log" ]; then
    echo "  后端调试日志 (/tmp/backend_full_debug.log):"
    tail -50 /tmp/backend_full_debug.log | grep -E "收到更新賬號請求|server_id|不存在|639277358115" | tail -10 || echo "    未找到相关日志"
else
    echo "  ⚠ 后端调试日志文件不存在"
fi

echo ""
echo "=== 测试完成 ==="
echo ""
echo "下一步操作："
echo "1. 刷新浏览器页面 (http://aikz.usdt2026.cc/group-ai/accounts)"
echo "2. 选择一个 Worker 节点账号（如 Eve, 639277358115）"
echo "3. 点击'分配剧本'按钮"
echo "4. 选择剧本和角色"
echo "5. 点击'分配剧本'"
echo "6. 查看浏览器控制台的日志输出"
echo "7. 查看后端日志: tail -f /tmp/backend_full_debug.log"
