#!/bin/bash
# 修复502问题 - 最终方案
# 在远程服务器 ubuntu@165.154.233.55 上执行

set -e

LOG_FILE="/tmp/fix_502_final_$(date +%Y%m%d_%H%M%S).log"

{
echo "========================================="
echo "修复 502 Bad Gateway - 最终方案"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian/saas-demo || { echo "✗ 无法进入前端目录"; exit 1; }

# 步骤1: 检查配置
echo "【步骤1】检查配置"
echo "─────────────────────────────────────────"
echo "package.json dev脚本:"
grep -A 1 '"dev"' package.json
echo ""

# 步骤2: 停止旧进程
echo "【步骤2】停止旧进程"
echo "─────────────────────────────────────────"
pkill -f "next.*dev|node.*3000" 2>/dev/null || true
sleep 2
echo "  ✓ 旧进程已停止"
echo ""

# 步骤3: 确保依赖已安装
echo "【步骤3】检查依赖"
echo "─────────────────────────────────────────"
if [ ! -d node_modules ] || [ ! -f node_modules/.bin/next ]; then
    echo "  缺少依赖，正在安装..."
    npm install 2>&1 | tail -20
    echo "  ✓ 依赖安装完成"
else
    echo "  ✓ 依赖已存在"
fi
echo ""

# 步骤4: 后台启动前端
echo "【步骤4】后台启动前端服务"
echo "─────────────────────────────────────────"
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  前端进程PID: $FRONTEND_PID"
sleep 20

# 检查进程是否还在运行
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "  ✓ 前端进程正在运行"
else
    echo "  ✗ 前端进程已退出，查看日志:"
    tail -50 /tmp/frontend.log
    exit 1
fi
echo ""

# 步骤5: 验证本地连接
echo "【步骤5】验证本地连接"
echo "─────────────────────────────────────────"
FRONTEND_CODE=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://localhost:3000 2>&1 || echo "000")
echo "  前端服务: HTTP $FRONTEND_CODE"

if [ "$FRONTEND_CODE" = "200" ] || [ "$FRONTEND_CODE" = "304" ]; then
    echo "  ✓ 前端服务正常"
else
    echo "  ✗ 前端服务异常，查看日志:"
    tail -50 /tmp/frontend.log
    exit 1
fi
echo ""

# 步骤6: 重载Nginx
echo "【步骤6】重载Nginx"
echo "─────────────────────────────────────────"
sudo systemctl reload nginx 2>/dev/null && echo "  ✓ Nginx已重载" || echo "  ⚠ Nginx重载失败"
sleep 3
echo ""

# 步骤7: 验证域名访问
echo "【步骤7】验证域名访问"
echo "─────────────────────────────────────────"
DOMAIN_ACCOUNTS=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://aikz.usdt2026.cc/group-ai/accounts 2>&1 || echo "000")
DOMAIN_ROOT=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://aikz.usdt2026.cc/ 2>&1 || echo "000")

echo "  域名 /group-ai/accounts: HTTP $DOMAIN_ACCOUNTS"
echo "  域名 /: HTTP $DOMAIN_ROOT"
echo ""

if [ "$DOMAIN_ACCOUNTS" != "502" ] && [ "$DOMAIN_ROOT" != "502" ]; then
    echo "  ✅ 502问题已修复！"
    FIXED=true
else
    echo "  ⚠ 仍返回502，请检查Nginx配置"
    echo "  Nginx错误日志:"
    sudo tail -10 /var/log/nginx/error.log
    FIXED=false
fi

echo ""
echo "========================================="
echo "修复完成！"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "前端PID: $FRONTEND_PID"
echo "前端本地: HTTP $FRONTEND_CODE"
echo "域名访问: HTTP $DOMAIN_ACCOUNTS"
echo ""

if [ "$FIXED" = true ]; then
    echo "✅ 修复成功！前端服务已在3000端口运行，域名访问正常。"
else
    echo "⚠ 前端服务已启动，但域名访问仍异常，请检查Nginx配置。"
fi
echo "========================================="

} 2>&1 | tee "$LOG_FILE"

echo ""
echo "完整日志已保存到: $LOG_FILE"
