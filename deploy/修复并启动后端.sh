#!/bin/bash
# 修复并启动后端服务

cd ~/liaotian/admin-backend

echo "========================================="
echo "修复并启动后端服务"
echo "========================================="
echo ""

# 1. 清理旧进程
echo "【1】清理旧进程..."
pkill -9 -f 'uvicorn.*app.main:app' 2>/dev/null || true
sleep 2

# 2. 清理端口
echo "【2】清理端口 8000..."
sudo lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# 3. 检查虚拟环境
echo "【3】检查虚拟环境..."
if [ ! -d ".venv" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 4. 检查并安装依赖
echo "【4】检查依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "  ⚠ requirements.txt 不存在"
else
    echo "  检查关键依赖..."
    python3 -c "import uvicorn" 2>/dev/null || {
        echo "  安装 uvicorn..."
        pip install uvicorn[standard] > /dev/null 2>&1
    }
fi

# 5. 验证模块导入
echo "【5】验证模块导入..."
python3 << 'CHECK'
import sys
sys.path.insert(0, '.')

try:
    from app.main import app
    print("  ✓ app.main 导入成功")
except Exception as e:
    print(f"  ✗ app.main 导入失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
CHECK

if [ $? -ne 0 ]; then
    echo "  模块导入失败，无法启动"
    exit 1
fi

# 6. 创建日志文件
echo "【6】准备日志文件..."
touch /tmp/backend_final.log
chmod 666 /tmp/backend_final.log

# 7. 启动服务
echo "【7】启动后端服务..."
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
BACKEND_PID=$!

echo "  后端进程已启动，PID: $BACKEND_PID"
echo "  日志文件: /tmp/backend_final.log"

# 8. 等待启动
echo "【8】等待后端启动..."
for i in {1..10}; do
    sleep 2
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ 后端服务已就绪"
        curl -s http://localhost:8000/health
        echo ""
        exit 0
    fi
    echo "  ... 等待中 ($i/10)"
done

# 9. 如果启动失败，显示日志
echo ""
echo "  ⚠ 后端可能未完全启动，查看日志:"
tail -30 /tmp/backend_final.log

echo ""
echo "========================================="
echo "启动完成"
echo "========================================="
