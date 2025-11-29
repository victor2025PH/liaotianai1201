#!/bin/bash
# 一键启动服务并测试分配剧本功能

cd ~/liaotian

echo "========================================="
echo "一键启动服务并测试分配剧本功能"
echo "========================================="
echo ""

# 1. 启动后端服务
echo "【1/4】启动后端服务..."
cd admin-backend

# 杀掉旧进程
pkill -f 'uvicorn.*app.main:app' 2>/dev/null || true
sleep 2

# 激活虚拟环境并启动
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
BACKEND_PID=$!
echo "  后端已启动，PID: $BACKEND_PID"
sleep 8

# 验证后端
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端服务正常"
else
    echo "  ⚠ 后端服务可能未完全启动，查看日志: tail -50 /tmp/backend_final.log"
    tail -50 /tmp/backend_final.log | tail -10
fi

# 2. 启动前端服务
echo ""
echo "【2/4】启动前端服务..."
cd ../saas-demo

# 杀掉旧进程
pkill -f 'next.*dev|node.*3000' 2>/dev/null || true
sleep 2

# 启动前端
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  前端已启动，PID: $FRONTEND_PID"
sleep 15

# 验证前端
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✓ 前端服务正常"
else
    echo "  ⚠ 前端服务可能未完全启动"
fi

# 3. 验证代码修复
echo ""
echo "【3/4】验证代码修复..."
cd ../admin-backend

python3 << 'VERIFY'
import os

backend_file = 'app/api/group_ai/accounts.py'
frontend_file = '../saas-demo/src/app/group-ai/accounts/page.tsx'

checks_passed = 0
checks_total = 0

# 检查后端
if os.path.exists(backend_file):
    with open(backend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    backend_checks = {
        'session_file字段': 'session_file: Optional[str] = None' in content,
        '远程扫描逻辑': 'scan_server_accounts(server_node, db)' in content,
        '账号ID匹配修复': 'account_id_str = str(account_id).strip()' in content,
        '详细日志': '账号ID匹配:' in content,
    }
    
    print("后端修复检查:")
    for name, result in backend_checks.items():
        checks_total += 1
        if result:
            checks_passed += 1
        print(f"  {'✓' if result else '✗'} {name}")

# 检查前端
if os.path.exists(frontend_file):
    with open(frontend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    frontend_checks = {
        'server_id传递': 'server_id: selectedAccountForRole.server_id || (selectedAccountForRole as any).node_id' in content,
        '调试日志': '[分配剧本]' in content,
    }
    
    print("\n前端修复检查:")
    for name, result in frontend_checks.items():
        checks_total += 1
        if result:
            checks_passed += 1
        print(f"  {'✓' if result else '✗'} {name}")

print(f"\n检查结果: {checks_passed}/{checks_total} 通过")
VERIFY

# 4. 显示服务状态和日志位置
echo ""
echo "【4/4】服务状态:"
ps aux | grep -E 'next.*dev|uvicorn.*8000' | grep -v grep | wc -l
echo "个服务运行中"
echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "📝 日志文件:"
echo "  后端: /tmp/backend_final.log"
echo "  前端: /tmp/frontend.log"
echo ""
echo "🔍 查看实时日志:"
echo "  tail -f /tmp/backend_final.log | grep -E 'MIDDLEWARE|UPDATE_ACCOUNT|server_id|账号ID匹配'"
echo ""
echo "🧪 测试步骤:"
echo "  1. 刷新浏览器: http://aikz.usdt2026.cc/group-ai/accounts (Ctrl+Shift+R)"
echo "  2. 选择一个 Worker 节点账号（如 Eve, 639277358115）"
echo "  3. 点击'分配剧本'按钮"
echo "  4. 选择剧本和角色"
echo "  5. 点击'分配剧本'"
echo "  6. 查看浏览器控制台和后端日志"
