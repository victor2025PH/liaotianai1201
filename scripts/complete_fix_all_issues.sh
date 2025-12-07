#!/bin/bash
# Complete fix for all service startup issues
# 完整修复所有服务启动问题

set -e

echo "========================================="
echo "完整修复所有服务启动问题"
echo "========================================="
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 请使用 sudo 运行此脚本"
    exit 1
fi

echo "=== 步骤 1: 彻底停止所有服务和进程 ==="
systemctl stop liaotian-frontend 2>/dev/null || true
systemctl stop liaotian-backend 2>/dev/null || true

# 查找并停止所有占用端口的进程
echo "查找占用端口 3000 的进程..."
PORT_3000_PIDS=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+')
if [ -n "$PORT_3000_PIDS" ]; then
    for PID in $PORT_3000_PIDS; do
        echo "停止占用端口 3000 的进程: $PID"
        kill -9 "$PID" 2>/dev/null || true
    done
fi

echo "查找占用端口 8000 的进程..."
PORT_8000_PIDS=$(ss -tlnp | grep :8000 | grep -oP 'pid=\K[0-9]+')
if [ -n "$PORT_8000_PIDS" ]; then
    for PID in $PORT_8000_PIDS; do
        echo "停止占用端口 8000 的进程: $PID"
        kill -9 "$PID" 2>/dev/null || true
    done
fi

# 强制停止所有相关进程
echo "强制停止所有相关进程..."
pkill -9 -f "next-server" 2>/dev/null || true
pkill -9 -f "node.*next" 2>/dev/null || true
pkill -9 -f "npm start" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "python.*uvicorn" 2>/dev/null || true
pkill -9 -f "python3.*uvicorn" 2>/dev/null || true
sleep 5

# 验证端口已释放
echo ""
echo "验证端口状态..."
if ss -tlnp | grep :3000 > /dev/null; then
    echo "⚠️  警告: 端口 3000 仍被占用"
    ss -tlnp | grep :3000
else
    echo "✅ 端口 3000 已释放"
fi

if ss -tlnp | grep :8000 > /dev/null; then
    echo "⚠️  警告: 端口 8000 仍被占用"
    ss -tlnp | grep :8000
else
    echo "✅ 端口 8000 已释放"
fi

echo ""
echo "=== 步骤 2: 检查 Python 环境 ==="
# 检查 uvicorn 是否安装
if python3 -m uvicorn --version > /dev/null 2>&1; then
    echo "✅ uvicorn 已安装"
    python3 -m uvicorn --version
else
    echo "⚠️  uvicorn 未安装，尝试安装..."
    pip3 install uvicorn fastapi --user 2>/dev/null || \
    python3 -m pip install uvicorn fastapi --user 2>/dev/null || \
    echo "❌ 无法安装 uvicorn，请手动安装: pip3 install uvicorn fastapi"
fi

echo ""
echo "=== 步骤 3: 修复 Systemd 服务文件 ==="

# 修复前端服务文件
cat > /etc/systemd/system/liaotian-frontend.service << 'EOFFRONTEND'
[Unit]
Description=Liaotian Frontend Service (Next.js)
After=network.target liaotian-backend.service
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/saas-demo
Environment="PATH=/usr/bin:/bin:/usr/local/bin"
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/bin/bash -c "if [ -d /home/ubuntu/liaotian/saas-demo/.next/standalone ]; then cd /home/ubuntu/liaotian/saas-demo/.next/standalone && PORT=3000 /usr/bin/node server.js; else cd /home/ubuntu/liaotian/saas-demo && /usr/bin/npm start; fi"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOFFRONTEND

# 修复后端服务文件（使用完整 Python 路径和确保 uvicorn 可用）
cat > /etc/systemd/system/liaotian-backend.service << 'EOFBACKEND'
[Unit]
Description=Liaotian Backend API Service (FastAPI)
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/admin-backend
Environment="PATH=/usr/bin:/bin:/usr/local/bin:/home/ubuntu/.local/bin"
ExecStart=/bin/bash -c "cd /home/ubuntu/liaotian/admin-backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120 || /usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-backend

[Install]
WantedBy=multi-user.target
EOFBACKEND

echo "✅ Systemd 服务文件已修复"

echo ""
echo "=== 步骤 4: 重新加载 systemd ==="
systemctl daemon-reload
echo "✅ Systemd 已重新加载"

echo ""
echo "=== 步骤 5: 启动后端服务 ==="
systemctl start liaotian-backend
sleep 10

if systemctl is-active --quiet liaotian-backend; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败，查看日志:"
    journalctl -u liaotian-backend -n 30 --no-pager | tail -20
    echo ""
    echo "尝试手动检查:"
    echo "  1. 检查 uvicorn 是否安装: python3 -m uvicorn --version"
    echo "  2. 检查端口 8000 是否被占用: ss -tlnp | grep :8000"
    echo "  3. 查看详细日志: sudo journalctl -u liaotian-backend -f"
fi

echo ""
echo "=== 步骤 6: 启动前端服务 ==="
systemctl start liaotian-frontend
sleep 10

if systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败，查看日志:"
    journalctl -u liaotian-frontend -n 30 --no-pager | tail -20
    echo ""
    echo "尝试手动检查:"
    echo "  1. 检查端口 3000 是否被占用: ss -tlnp | grep :3000"
    echo "  2. 检查前端构建是否完成: ls -la /home/ubuntu/liaotian/saas-demo/.next"
    echo "  3. 查看详细日志: sudo journalctl -u liaotian-frontend -f"
fi

echo ""
echo "=== 步骤 7: 最终验证 ==="
echo "服务状态:"
systemctl is-active liaotian-backend && echo "✅ 后端服务运行中" || echo "❌ 后端服务未运行"
systemctl is-active liaotian-frontend && echo "✅ 前端服务运行中" || echo "❌ 前端服务未运行"

echo ""
echo "端口状态:"
ss -tlnp | grep :3000 && echo "✅ 端口 3000 监听中" || echo "❌ 端口 3000 未监听"
ss -tlnp | grep :8000 && echo "✅ 端口 8000 监听中" || echo "❌ 端口 8000 未监听"

echo ""
echo "HTTP 测试:"
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 后端健康检查正常"
    curl -s http://localhost:8000/health
else
    echo "❌ 后端健康检查失败 (HTTP $BACKEND_HEALTH)"
fi

FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_RESPONSE" = "200" ] || [ "$FRONTEND_RESPONSE" = "301" ] || [ "$FRONTEND_RESPONSE" = "302" ]; then
    echo "✅ 前端响应正常 (HTTP $FRONTEND_RESPONSE)"
else
    echo "⚠️  前端响应异常 (HTTP $FRONTEND_RESPONSE)"
fi

echo ""
echo "========================================="
echo "修复完成！"
echo "========================================="
echo ""
echo "如果服务仍有问题，请查看日志:"
echo "  sudo journalctl -u liaotian-backend -f"
echo "  sudo journalctl -u liaotian-frontend -f"
