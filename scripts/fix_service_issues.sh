#!/bin/bash
# Fix service startup issues: port conflict and systemd configuration
# 修复服务启动问题：端口冲突和 systemd 配置错误

set -e

echo "========================================="
echo "修复服务启动问题"
echo "========================================="
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 请使用 sudo 运行此脚本"
    exit 1
fi

echo "=== 步骤 1: 停止所有相关服务 ==="
systemctl stop liaotian-frontend 2>/dev/null || true
systemctl stop liaotian-backend 2>/dev/null || true

echo "=== 步骤 2: 查找并停止占用端口 3000 的进程 ==="
PORT_3000_PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -n "$PORT_3000_PID" ]; then
    echo "找到占用端口 3000 的进程 PID: $PORT_3000_PID"
    ps aux | grep "$PORT_3000_PID" | grep -v grep
    kill -9 "$PORT_3000_PID" 2>/dev/null || true
    echo "✅ 已停止占用端口 3000 的进程"
    sleep 2
else
    echo "✅ 端口 3000 未被占用"
fi

# 强制停止所有可能的进程
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 3

echo ""
echo "=== 步骤 3: 修复 Systemd 服务配置文件 ==="

# 修复前端服务文件（修复 Restart 配置）
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
Environment="PATH=/usr/bin:/bin"
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

# 修复后端服务文件
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
Environment="PATH=/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120
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
echo "=== 步骤 5: 验证端口状态 ==="
echo "检查端口 3000:"
ss -tlnp | grep :3000 || echo "  端口 3000 空闲"
echo "检查端口 8000:"
ss -tlnp | grep :8000 || echo "  端口 8000 空闲"

echo ""
echo "=== 步骤 6: 启动后端服务 ==="
systemctl start liaotian-backend
sleep 5

if systemctl is-active --quiet liaotian-backend; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败，查看日志:"
    journalctl -u liaotian-backend -n 20 --no-pager
fi

echo ""
echo "=== 步骤 7: 启动前端服务 ==="
systemctl start liaotian-frontend
sleep 5

if systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败，查看日志:"
    journalctl -u liaotian-frontend -n 20 --no-pager
fi

echo ""
echo "=== 步骤 8: 最终验证 ==="
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
[ "$BACKEND_HEALTH" = "200" ] && echo "✅ 后端健康检查正常" || echo "❌ 后端健康检查失败 (HTTP $BACKEND_HEALTH)"

FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
[ "$FRONTEND_RESPONSE" = "200" ] && echo "✅ 前端响应正常" || echo "⚠️  前端响应异常 (HTTP $FRONTEND_RESPONSE)"

echo ""
echo "========================================="
echo "修复完成！"
echo "========================================="
