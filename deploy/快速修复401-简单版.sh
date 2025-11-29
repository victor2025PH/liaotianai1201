#!/bin/bash
# 快速修复 401 认证问题 - 最简单版本

echo "开始修复..."

# 1. 创建文件
sudo mkdir -p /home/ubuntu/admin-backend
echo "CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc" | sudo tee /home/ubuntu/admin-backend/.env > /dev/null

# 2. 验证
echo "配置已添加："
sudo cat /home/ubuntu/admin-backend/.env

# 3. 重启服务
echo ""
echo "重启服务..."
sudo systemctl restart liaotian-backend
sleep 2

# 4. 检查状态
echo "服务状态："
sudo systemctl status liaotian-backend --no-pager | head -5

echo ""
echo "修复完成！"

