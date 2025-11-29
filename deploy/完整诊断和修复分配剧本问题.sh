#!/bin/bash
# 完整诊断和修复分配剧本问题

set -e

cd ~/liaotian

echo "========================================="
echo "完整诊断和修复分配剧本问题"
echo "========================================="
echo ""

# 1. 检查并启动后端服务
echo "【步骤1】检查并启动后端服务..."
cd admin-backend

# 杀掉旧进程
echo "  清理旧进程..."
pkill -f 'uvicorn.*app.main:app' 2>/dev/null || true
sleep 2

# 激活虚拟环境
if [ ! -d ".venv" ]; then
    echo "  ⚠ 虚拟环境不存在，正在创建..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 启动后端服务
echo "  启动后端服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
BACKEND_PID=$!

echo "  后端已启动，PID: $BACKEND_PID"
sleep 8

# 检查后端是否正常
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端服务正常"
else
    echo "  ⚠ 后端服务可能未完全启动"
    echo "  查看日志: tail -50 /tmp/backend_final.log"
    tail -50 /tmp/backend_final.log
fi

# 2. 检查并启动前端服务
echo ""
echo "【步骤2】检查并启动前端服务..."
cd ../saas-demo

# 杀掉旧进程
echo "  清理旧进程..."
pkill -f 'next.*dev|node.*3000' 2>/dev/null || true
sleep 2

# 启动前端服务
echo "  启动前端服务..."
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "  前端已启动，PID: $FRONTEND_PID"
sleep 15

# 检查前端是否正常
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✓ 前端服务正常"
else
    echo "  ⚠ 前端服务可能未完全启动"
    echo "  查看日志: tail -50 /tmp/frontend.log"
    tail -50 /tmp/frontend.log
fi

# 3. 验证代码修复
echo ""
echo "【步骤3】验证代码修复..."
cd ../admin-backend

python3 << 'CHECKCODE'
import sys
import os

file_path = 'app/api/group_ai/accounts.py'
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'session_file字段': 'session_file: Optional[str] = None  # Session文件路徑' in content,
        '远程扫描逻辑': 'scan_server_accounts(server_node, db)' in content,
        '详细日志': '扫描结果: 找到' in content and '账号ID列表:' in content,
        'update_account函数': 'async def update_account(' in content,
    }
    
    print("后端代码检查:")
    for name, result in checks.items():
        print(f"  {'✓' if result else '✗'} {name}")
else:
    print("✗ 后端文件不存在")

# 检查前端
frontend_file = '../saas-demo/src/app/group-ai/accounts/page.tsx'
if os.path.exists(frontend_file):
    with open(frontend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'server_id传递': 'server_id: selectedAccountForRole.server_id || (selectedAccountForRole as any).node_id' in content,
        '调试日志': 'console.log.*分配剧本' in content or '[分配剧本]' in content,
    }
    
    print("\n前端代码检查:")
    for name, result in checks.items():
        print(f"  {'✓' if result else '✗'} {name}")
else:
    print("\n✗ 前端文件不存在")
CHECKCODE

# 4. 检查服务器配置
echo ""
echo "【步骤4】检查服务器配置..."
cd admin-backend
source .venv/bin/activate

python3 << 'CHECKSERVERS'
import sys
sys.path.insert(0, '.')

try:
    from app.api.group_ai.session_uploader import SessionUploader
    
    uploader = SessionUploader()
    servers = list(uploader.servers.keys())
    
    print(f"服务器列表: {servers}")
    
    if 'computer_001' in servers:
        print("✓ computer_001 在服务器列表中")
        server = uploader.servers['computer_001']
        print(f"  主机: {server.host}")
        print(f"  部署目录: {server.deploy_dir}")
    else:
        print("✗ computer_001 不在服务器列表中")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
CHECKSERVERS

# 5. 显示日志文件位置
echo ""
echo "【步骤5】日志文件位置:"
echo "  后端日志: /tmp/backend_final.log"
echo "  前端日志: /tmp/frontend.log"
echo ""
echo "查看实时日志:"
echo "  tail -f /tmp/backend_final.log | grep -E 'MIDDLEWARE|UPDATE_ACCOUNT|server_id|639277358115'"

echo ""
echo "========================================="
echo "诊断完成"
echo "========================================="
echo ""
echo "服务状态:"
ps aux | grep -E 'next.*dev|uvicorn.*8000' | grep -v grep | wc -l
echo "个服务运行中"
echo ""
echo "下一步:"
echo "1. 刷新浏览器 (Ctrl+Shift+R)"
echo "2. 尝试分配剧本"
echo "3. 查看日志文件"
