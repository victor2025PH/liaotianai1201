#!/bin/bash
# 修复前端 500 错误脚本

echo "=========================================="
echo "修复前端 500 错误"
echo "=========================================="
echo ""

cd /home/ubuntu/telegram-ai-system || exit 1

# 1. 检查 PM2 服务状态
echo "1. 检查 PM2 服务状态"
echo "----------------------------------------"
pm2 status
echo ""

# 2. 检查前端服务日志
echo "2. 检查前端服务日志（最后50行）"
echo "----------------------------------------"
pm2 logs frontend --lines 50 --nostream 2>/dev/null | tail -n 30 || echo "无法读取日志"
echo ""

# 3. 检查前端构建文件
echo "3. 检查前端构建文件"
echo "----------------------------------------"
if [ -d "saas-demo/.next" ]; then
    echo "✓ .next 目录存在"
    ls -la saas-demo/.next/static 2>/dev/null | head -n 5 || echo "static 目录不存在或为空"
else
    echo "✗ .next 目录不存在，需要重新构建"
fi
echo ""

# 4. 检查磁盘空间
echo "4. 检查磁盘空间"
echo "----------------------------------------"
df -h / | tail -n 1
echo ""

# 5. 尝试修复步骤
echo "5. 开始修复..."
echo "----------------------------------------"

# 停止前端服务
echo "停止前端服务..."
pm2 stop frontend 2>/dev/null || true

# 清理旧的构建文件
echo "清理旧的构建文件..."
cd saas-demo
rm -rf .next
echo "✓ 已清理 .next 目录"

# 重新构建
echo "重新构建前端（这可能需要几分钟）..."
npm run build

# 检查构建是否成功
if [ -d ".next" ]; then
    echo "✓ 构建成功"
else
    echo "✗ 构建失败，请检查错误信息"
    exit 1
fi

# 重启前端服务
echo "重启前端服务..."
cd ..
pm2 restart frontend
pm2 save

# 等待服务启动
sleep 3

# 检查服务状态
echo ""
echo "6. 检查服务状态"
echo "----------------------------------------"
pm2 status frontend

# 检查端口
echo ""
echo "7. 检查端口监听"
echo "----------------------------------------"
ss -tln | grep ":3000" || echo "端口 3000 未监听"

# 测试健康状态
echo ""
echo "8. 测试前端响应"
echo "----------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✓ 前端响应正常 (HTTP $HTTP_CODE)"
else
    echo "✗ 前端响应异常 (HTTP $HTTP_CODE)"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请："
echo "1. 查看 PM2 日志: pm2 logs frontend"
echo "2. 查看构建错误: cd saas-demo && npm run build"
echo "3. 检查 Nginx 配置: sudo nginx -t"
echo ""

