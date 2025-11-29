#!/bin/bash
# 强制启动服务并诊断问题

set -e

cd ~/liaotian

echo "========================================="
echo "强制启动并诊断服务"
echo "========================================="
echo ""

# 1. 清理所有旧进程
echo "【1】清理旧进程..."
pkill -9 -f 'uvicorn.*app.main:app' 2>/dev/null || true
pkill -9 -f 'next.*dev|node.*3000' 2>/dev/null || true
sleep 3

# 2. 启动后端服务
echo ""
echo "【2】启动后端服务..."
cd admin-backend

# 确保虚拟环境存在
if [ ! -d ".venv" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 创建日志文件
touch /tmp/backend_final.log
chmod 666 /tmp/backend_final.log

# 启动后端
echo "  启动 uvicorn..."
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
BACKEND_PID=$!

echo "  后端进程已启动，PID: $BACKEND_PID"
echo "  日志文件: /tmp/backend_final.log"

# 等待后端启动
echo "  等待后端启动..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ 后端服务已就绪"
        break
    fi
    sleep 2
    echo "  ... 等待中 ($i/10)"
done

# 验证后端
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端健康检查通过"
else
    echo "  ⚠ 后端可能未完全启动，查看日志:"
    tail -30 /tmp/backend_final.log
fi

# 3. 启动前端服务
echo ""
echo "【3】启动前端服务..."
cd ../saas-demo

# 创建日志文件
touch /tmp/frontend.log
chmod 666 /tmp/frontend.log

# 启动前端
echo "  启动 Next.js..."
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "  前端进程已启动，PID: $FRONTEND_PID"
echo "  日志文件: /tmp/frontend.log"

# 等待前端启动
echo "  等待前端启动..."
sleep 15

# 验证前端
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✓ 前端服务已就绪"
else
    echo "  ⚠ 前端可能未完全启动"
fi

# 4. 显示服务状态
echo ""
echo "【4】服务状态:"
BACKEND_COUNT=$(ps aux | grep -E 'uvicorn.*app.main:app' | grep -v grep | wc -l)
FRONTEND_COUNT=$(ps aux | grep -E 'next.*dev|node.*3000' | grep -v grep | wc -l)

echo "  后端进程: $BACKEND_COUNT 个"
echo "  前端进程: $FRONTEND_COUNT 个"

# 5. 验证代码修复
echo ""
echo "【5】验证代码修复..."
cd ../admin-backend

python3 << 'VERIFY'
import os
import sys

file_path = 'app/api/group_ai/accounts.py'

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        '账号ID匹配修复': 'account_id_str = str(account_id).strip()' in content,
        '详细日志': '账号ID匹配:' in content,
        '远程扫描': 'scan_server_accounts(server_node, db)' in content,
        'UPDATE_ACCOUNT日志': '[UPDATE_ACCOUNT] 收到更新賬號請求' in content,
    }
    
    print("  后端代码修复验证:")
    all_pass = True
    for name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"    {status} {name}")
        if not result:
            all_pass = False
    
    if all_pass:
        print("  ✓ 所有代码修复已应用")
    else:
        print("  ⚠ 部分代码修复可能未应用")
else:
    print("  ✗ 文件不存在")
VERIFY

# 6. 显示日志位置和测试命令
echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "📝 日志文件:"
echo "  后端: /tmp/backend_final.log"
echo "  前端: /tmp/frontend.log"
echo ""
echo "🔍 查看后端日志:"
echo "  tail -f /tmp/backend_final.log | grep -E 'MIDDLEWARE|UPDATE_ACCOUNT|server_id|账号ID匹配|639277358115'"
echo ""
echo "🧪 测试步骤:"
echo "  1. 刷新浏览器 (Ctrl+Shift+R)"
echo "  2. 尝试分配剧本"
echo "  3. 查看日志文件"
