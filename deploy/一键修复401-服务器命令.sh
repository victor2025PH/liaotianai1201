#!/bin/bash
# 一键修复 401 认证问题 - 在服务器上直接执行

echo "============================================================"
echo "修复 401 认证问题"
echo "============================================================"

# 创建目录
sudo mkdir -p /home/ubuntu/admin-backend

# 创建 .env 文件并添加 CORS 配置
echo "CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc" | sudo tee /home/ubuntu/admin-backend/.env > /dev/null

# 验证配置
echo ""
echo "配置已添加："
sudo cat /home/ubuntu/admin-backend/.env

# 重启服务
echo ""
echo "重启服务..."
sudo systemctl restart liaotian-backend
sleep 2

# 检查状态
echo ""
echo "服务状态："
sudo systemctl status liaotian-backend --no-pager | head -10

echo ""
echo "============================================================"
echo "修复完成！"
echo "============================================================"
echo ""
echo "下一步："
echo "1. 在浏览器中访问 http://aikz.usdt2026.cc/login 重新登录"
echo "2. 登录后访问 http://aikz.usdt2026.cc/group-ai/accounts"
echo "3. 检查浏览器控制台，确认 API 请求是否成功"

