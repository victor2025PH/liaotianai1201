#!/bin/bash
# 查找后端配置和服务

echo "============================================================"
echo "查找后端配置和服务"
echo "============================================================"

# 1. 查找所有可能的 .env 文件
echo ""
echo ">>> [1] 查找 .env 文件..."
find /opt /home /root -name ".env" -type f 2>/dev/null | grep -E "(admin|backend|liaotian|smart)" | head -10

# 2. 查找所有 systemd 服务
echo ""
echo ">>> [2] 查找后端相关 systemd 服务..."
systemctl list-units --type=service --all | grep -E "(backend|liaotian|admin|smart)" | head -10

# 3. 查找运行中的 Python/gunicorn 进程
echo ""
echo ">>> [3] 查找运行中的后端进程..."
ps aux | grep -E "(gunicorn|uvicorn|python.*main|admin-backend)" | grep -v grep

# 4. 查找后端代码目录
echo ""
echo ">>> [4] 查找后端代码目录..."
find /opt /home /root -type d -name "admin-backend" 2>/dev/null | head -10

# 5. 检查端口 8000 的监听进程
echo ""
echo ">>> [5] 检查端口 8000 的监听进程..."
sudo netstat -tlnp | grep :8000 || sudo ss -tlnp | grep :8000

# 6. 查找 systemd 服务文件
echo ""
echo ">>> [6] 查找 systemd 服务文件..."
find /etc/systemd/system -name "*.service" -type f | grep -E "(backend|liaotian|admin|smart)" | head -10

# 7. 检查环境变量配置
echo ""
echo ">>> [7] 检查可能的环境变量配置..."
if [ -f "/etc/systemd/system/"*backend*.service ]; then
    for service_file in /etc/systemd/system/*backend*.service; do
        echo "服务文件: $service_file"
        grep -E "EnvironmentFile|WorkingDirectory|ExecStart" "$service_file" | head -5
        echo ""
    done
fi

echo ""
echo "============================================================"
echo "查找完成"
echo "============================================================"

