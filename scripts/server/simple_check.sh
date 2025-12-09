#!/bin/bash
# 最简单的验证脚本（避免内存问题）

echo "=== 快速验证 ==="
echo ""

# 1. PM2 状态（最简单）
echo "1. PM2 服务:"
pm2 list 2>/dev/null || echo "PM2 未运行或无进程"
echo ""

# 2. 端口检查（轻量）
echo "2. 端口监听:"
ss -tln 2>/dev/null | grep -E ":8000|:3000" || echo "端口未监听"
echo ""

# 3. 健康检查（最简单）
echo "3. 健康检查:"
curl -s -o /dev/null -w "后端: %{http_code}\n" http://localhost:8000/health 2>/dev/null || echo "后端: 无法连接"
curl -s -o /dev/null -w "前端: %{http_code}\n" http://localhost:3000 2>/dev/null || echo "前端: 无法连接"
echo ""

echo "=== 完成 ==="

