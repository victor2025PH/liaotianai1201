#!/bin/bash
# 诊断后端启动失败问题

cd ~/liaotian/admin-backend

echo "========================================="
echo "诊断后端启动失败问题"
echo "========================================="
echo ""

# 1. 检查进程
echo "【1】检查现有进程..."
ps aux | grep uvicorn | grep -v grep || echo "  无后端进程运行"
echo ""

# 2. 检查日志文件
echo "【2】查看启动日志..."
if [ -f "/tmp/backend_final.log" ]; then
    echo "  日志文件存在，最后50行:"
    tail -50 /tmp/backend_final.log
else
    echo "  ⚠ 日志文件不存在"
fi
echo ""

# 3. 检查虚拟环境
echo "【3】检查虚拟环境..."
if [ -d ".venv" ]; then
    echo "  ✓ 虚拟环境存在"
    source .venv/bin/activate
    echo "  Python版本: $(python3 --version)"
    echo "  uvicorn位置: $(which uvicorn || echo '未找到')"
else
    echo "  ✗ 虚拟环境不存在"
    exit 1
fi
echo ""

# 4. 检查模块导入
echo "【4】检查模块导入..."
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
    sys.exit(1)

try:
    import uvicorn
    print("  ✓ uvicorn 导入成功")
except Exception as e:
    print(f"  ✗ uvicorn 导入失败: {e}")
    sys.exit(1)
CHECK

if [ $? -ne 0 ]; then
    echo "  模块导入失败，请检查依赖"
    exit 1
fi
echo ""

# 5. 检查端口
echo "【5】检查端口占用..."
if sudo ss -tlnp | grep -q ":8000 "; then
    echo "  ⚠ 端口 8000 已被占用:"
    sudo ss -tlnp | grep ":8000 "
    echo "  正在杀掉占用进程..."
    sudo lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
else
    echo "  ✓ 端口 8000 空闲"
fi
echo ""

# 6. 尝试前台启动（5秒）
echo "【6】尝试前台启动（5秒测试）..."
timeout 5 uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 || echo "  启动失败或超时"
echo ""

# 7. 显示启动命令
echo "【7】建议的启动命令:"
echo "  cd ~/liaotian/admin-backend"
echo "  source .venv/bin/activate"
echo "  nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &"
echo ""
echo "========================================="
echo "诊断完成"
echo "========================================="
