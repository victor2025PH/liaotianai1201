#!/bin/bash
# 基于日志分析的自动诊断和修复

set -e

cd ~/liaotian

echo "========================================"
echo "自动诊断和修复（基于日志分析）"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 1. 清理重复的后端进程（端口 8001）
echo "[1/5] 清理重复的后端进程..."
DUPLICATE_PIDS=$(ps aux | grep "uvicorn.*app.main:app.*8001" | grep -v grep | awk '{print $2}')
if [ -n "$DUPLICATE_PIDS" ]; then
    echo "发现重复的 8001 端口进程，正在清理..."
    echo "$DUPLICATE_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 2
    echo "✅ 已清理重复进程"
else
    echo "✅ 没有重复进程"
fi
echo ""

# 2. 检查后端服务（端口 8000）
echo "[2/5] 检查后端服务（端口 8000）..."
if curl -s --max-time 5 http://localhost:8000/health | grep -q "ok\|status"; then
    echo "✅ 后端服务正常运行在端口 8000"
    BACKEND_OK=true
else
    echo "❌ 后端服务异常，正在启动..."
    cd admin-backend
    source .venv/bin/activate
    pkill -f "uvicorn.*app.main:app.*8000" || true
    sleep 2
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_$(date +%s).log 2>&1 &
    echo "后端启动中..."
    sleep 8
    if curl -s --max-time 5 http://localhost:8000/health | grep -q "ok\|status"; then
        echo "✅ 后端服务已启动"
        BACKEND_OK=true
    else
        echo "❌ 后端服务启动失败"
        BACKEND_OK=false
    fi
    cd ..
fi
echo ""

# 3. 检查并启动前端服务（端口 3000）
echo "[3/5] 检查前端服务（端口 3000）..."
if curl -s --max-time 5 http://localhost:3000 2>&1 | head -1 | grep -q "html\|DOCTYPE"; then
    echo "✅ 前端服务正常运行"
    FRONTEND_OK=true
else
    echo "❌ 前端服务未运行，正在启动..."
    cd saas-demo
    
    # 停止现有进程
    pkill -f "next.*dev\|node.*3000" || true
    sleep 2
    
    # 启动前端服务
    nohup npm run dev > /tmp/frontend_$(date +%s).log 2>&1 &
    FRONTEND_PID=$!
    echo "前端服务已启动 (PID: $FRONTEND_PID)，等待启动..."
    
    # 等待前端启动（最多等待60秒）
    FRONTEND_OK=false
    for i in {1..12}; do
        sleep 5
        if curl -s --max-time 5 http://localhost:3000 2>&1 | head -1 | grep -q "html\|DOCTYPE"; then
            echo "✅ 前端服务已就绪（等待了 $((i*5)) 秒）"
            FRONTEND_OK=true
            break
        fi
        echo "  等待中... ($i/12)"
    done
    
    if [ "$FRONTEND_OK" = false ]; then
        echo "⚠️  前端服务可能还在启动中，请稍后检查"
        echo "查看日志: tail -50 /tmp/frontend_*.log"
    fi
    
    cd ..
fi
echo ""

# 4. 检查并重载 Nginx
echo "[4/5] 检查并重载 Nginx..."
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
    sudo systemctl reload nginx
    echo "✅ Nginx 已重新加载"
else
    echo "启动 Nginx..."
    sudo systemctl start nginx
    echo "✅ Nginx 已启动"
fi
echo ""

# 5. 最终验证
echo "[5/5] 最终验证..."
sleep 3

echo ""
echo "========================================"
echo "服务状态总结"
echo "========================================"

# 后端验证
if curl -s --max-time 5 http://localhost:8000/health | grep -q "ok\|status"; then
    echo "✅ 后端服务: 正常 (http://localhost:8000/health)"
else
    echo "❌ 后端服务: 异常"
fi

# 前端验证
if curl -s --max-time 5 http://localhost:3000 2>&1 | head -1 | grep -q "html\|DOCTYPE"; then
    echo "✅ 前端服务: 正常 (http://localhost:3000)"
else
    echo "❌ 前端服务: 异常"
fi

# 进程检查
echo ""
echo "运行中的进程:"
ps aux | grep -E 'uvicorn.*8000|next.*dev|node.*3000' | grep -v grep | head -3

# 域名访问测试
echo ""
echo "域名访问测试:"
if curl -s --max-time 10 http://aikz.usdt2026.cc/group-ai/accounts 2>&1 | head -1 | grep -q "html\|DOCTYPE"; then
    echo "✅ 域名访问: 正常"
else
    echo "⚠️  域名访问: 可能需要更多时间或仍有问题"
fi

echo ""
echo "========================================"
echo "修复完成"
echo "========================================"
echo ""
echo "日志文件:"
echo "  后端: /tmp/backend_*.log"
echo "  前端: /tmp/frontend_*.log"
echo ""
echo "如果前端仍在启动，请等待1-2分钟后刷新浏览器"
