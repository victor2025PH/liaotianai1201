#!/bin/bash
# 修复 401 认证问题 - 单行命令版本（避免复制粘贴问题）

# 1. 创建目录和文件
sudo mkdir -p /home/ubuntu/admin-backend && sudo touch /home/ubuntu/admin-backend/.env

# 2. 添加 CORS_ORIGINS 配置（如果不存在则添加，如果存在则更新）
if sudo grep -q "CORS_ORIGINS" /home/ubuntu/admin-backend/.env 2>/dev/null; then
    sudo sed -i 's|CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc|' /home/ubuntu/admin-backend/.env
else
    echo "CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc" | sudo tee -a /home/ubuntu/admin-backend/.env > /dev/null
fi

# 3. 如果实际运行路径也有 .env，也更新它
if [ -f "/home/ubuntu/liaotian/admin-backend/.env" ]; then
    if sudo grep -q "CORS_ORIGINS" /home/ubuntu/liaotian/admin-backend/.env 2>/dev/null; then
        sudo sed -i 's|CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc|' /home/ubuntu/liaotian/admin-backend/.env
    else
        echo "CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc" | sudo tee -a /home/ubuntu/liaotian/admin-backend/.env > /dev/null
    fi
fi

# 4. 验证配置
echo "=== systemd 配置的 .env ==="
sudo grep CORS_ORIGINS /home/ubuntu/admin-backend/.env || echo "未找到"
echo ""
echo "=== 实际运行路径的 .env ==="
sudo grep CORS_ORIGINS /home/ubuntu/liaotian/admin-backend/.env 2>/dev/null || echo "不存在"

# 5. 重启服务
echo ""
echo "=== 重启后端服务 ==="
sudo systemctl restart liaotian-backend
sleep 2
sudo systemctl status liaotian-backend --no-pager | head -10

echo ""
echo "=== 修复完成 ==="

