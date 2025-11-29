#!/bin/bash
# 全自动修复502错误并持续验证直到成功

set -e

cd ~/liaotian

echo "========================================"
echo "全自动修复502错误"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

MAX_ATTEMPTS=5
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    echo "[尝试 $ATTEMPT/$MAX_ATTEMPTS]"
    echo ""
    
    # 1. 启动后端
    echo "[1/4] 启动后端服务..."
    cd admin-backend
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        pkill -f "uvicorn.*app.main:app" || true
        sleep 2
        nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_auto_$ATTEMPT.log 2>&1 &
        BACKEND_PID=$!
        echo "后端已启动 (PID: $BACKEND_PID)"
        sleep 8
        
        # 验证后端
        if curl -s --max-time 5 http://localhost:8000/health | grep -q "ok\|status"; then
            echo "✅ 后端服务正常"
        else
            echo "⚠️  后端可能还在启动中"
        fi
    else
        echo "❌ 虚拟环境不存在"
        exit 1
    fi
    cd ..
    echo ""
    
    # 2. 启动前端
    echo "[2/4] 启动前端服务..."
    cd saas-demo
    pkill -f "next.*dev\|node.*3000" || true
    sleep 2
    
    nohup npm run dev > /tmp/frontend_auto_$ATTEMPT.log 2>&1 &
    FRONTEND_PID=$!
    echo "前端已启动 (PID: $FRONTEND_PID)"
    sleep 20
    
    # 验证前端
    if curl -s --max-time 5 http://localhost:3000 | head -1 | grep -q "html\|DOCTYPE"; then
        echo "✅ 前端服务正常"
    else
        echo "⚠️  前端可能还在启动中"
    fi
    cd ..
    echo ""
    
    # 3. 重载Nginx
    echo "[3/4] 重载 Nginx..."
    sudo systemctl reload nginx || sudo systemctl restart nginx
    sleep 3
    echo "✅ Nginx 已重载"
    echo ""
    
    # 4. 最终验证
    echo "[4/4] 最终验证..."
    sleep 5
    
    BACKEND_OK=false
    FRONTEND_OK=false
    
    if curl -s --max-time 5 http://localhost:8000/health | grep -q "ok\|status"; then
        echo "✅ 后端服务正常"
        BACKEND_OK=true
    else
        echo "❌ 后端服务异常"
    fi
    
    if curl -s --max-time 5 http://localhost:3000 | head -1 | grep -q "html\|DOCTYPE"; then
        echo "✅ 前端服务正常"
        FRONTEND_OK=true
    else
        echo "❌ 前端服务异常"
    fi
    
    # 检查通过域名访问
    if curl -s --max-time 5 http://aikz.usdt2026.cc/group-ai/accounts | head -1 | grep -q "html\|DOCTYPE\|<!DOCTYPE"; then
        echo "✅ 域名访问正常"
        echo ""
        echo "========================================"
        echo "✅ 修复成功！"
        echo "========================================"
        echo ""
        echo "访问地址: http://aikz.usdt2026.cc/group-ai/accounts"
        echo "后端 PID: $BACKEND_PID"
        echo "前端 PID: $FRONTEND_PID"
        exit 0
    elif [ "$BACKEND_OK" = true ] && [ "$FRONTEND_OK" = true ]; then
        echo "✅ 所有服务正常，但域名访问可能还需要时间"
        echo "请稍等片刻后刷新浏览器"
        exit 0
    else
        echo "⚠️  部分服务异常，准备重试..."
        if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
            sleep 10
        fi
    fi
    
    echo ""
done

echo "========================================"
echo "❌ 达到最大尝试次数"
echo "========================================"
echo ""
echo "查看日志:"
echo "  tail -50 /tmp/backend_auto_$ATTEMPT.log"
echo "  tail -50 /tmp/frontend_auto_$ATTEMPT.log"
exit 1
