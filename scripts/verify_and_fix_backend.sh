#!/bin/bash
# 验证后端状态并修复剩余问题
# 1. 检查端口监听
# 2. 测试 API 可访问性
# 3. 检查 Nginx 配置
# 4. 修复环境变量警告

set -e

echo "=========================================="
echo "🔍 验证后端状态并修复问题"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 第一步：检查后端进程状态
echo "第一步：检查 PM2 后端状态"
echo "----------------------------------------"
pm2 list | grep backend || echo "⚠️  后端进程未找到"
echo ""

# 第二步：检查端口 8000 监听
echo "第二步：检查端口 8000 监听"
echo "----------------------------------------"
if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 端口 8000 正在监听"
    sudo lsof -i :8000 | head -3
else
    echo "❌ 端口 8000 未监听"
    echo "查看 PM2 日志:"
    pm2 logs backend --lines 10 --nostream | tail -10
    exit 1
fi
echo ""

# 第三步：测试后端 API 健康检查
echo "第三步：测试后端 API"
echo "----------------------------------------"
echo "测试健康检查端点..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1 || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ 健康检查端点正常 (HTTP $HEALTH_RESPONSE)"
    curl -s http://localhost:8000/health | head -5
else
    echo "❌ 健康检查端点失败 (HTTP $HEALTH_RESPONSE)"
    echo "尝试直接访问:"
    curl -v http://localhost:8000/health 2>&1 | head -10
fi
echo ""

# 第四步：测试登录 API
echo "第四步：测试登录 API"
echo "----------------------------------------"
echo "测试登录端点（不发送实际凭证）..."
LOGIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/login 2>&1 || echo "000")
if [ "$LOGIN_RESPONSE" = "401" ] || [ "$LOGIN_RESPONSE" = "422" ]; then
    echo "✅ 登录端点可访问 (HTTP $LOGIN_RESPONSE - 预期，因为未提供凭证)"
elif [ "$LOGIN_RESPONSE" = "200" ]; then
    echo "✅ 登录端点可访问 (HTTP $LOGIN_RESPONSE)"
else
    echo "⚠️  登录端点响应异常 (HTTP $LOGIN_RESPONSE)"
    echo "详细响应:"
    curl -s -X POST http://localhost:8000/api/v1/auth/login 2>&1 | head -5
fi
echo ""

# 第五步：检查 Nginx 配置
echo "第五步：检查 Nginx 配置"
echo "----------------------------------------"
if [ -f "/etc/nginx/sites-available/aiadmin.usdt2026.cc" ]; then
    echo "检查 aiadmin.usdt2026.cc 配置..."
    if grep -q "proxy_pass.*8000" /etc/nginx/sites-available/aiadmin.usdt2026.cc; then
        echo "✅ Nginx 配置指向端口 8000"
    else
        echo "❌ Nginx 配置未指向端口 8000"
        echo "当前配置:"
        grep -A 5 "proxy_pass" /etc/nginx/sites-available/aiadmin.usdt2026.cc || echo "未找到 proxy_pass"
    fi
else
    echo "⚠️  Nginx 配置文件不存在: /etc/nginx/sites-available/aiadmin.usdt2026.cc"
fi

if [ -f "/etc/nginx/sites-available/aikz.usdt2026.cc" ]; then
    echo "检查 aikz.usdt2026.cc 配置..."
    if grep -q "proxy_pass.*8000" /etc/nginx/sites-available/aikz.usdt2026.cc; then
        echo "✅ Nginx 配置指向端口 8000"
    else
        echo "⚠️  Nginx 配置未指向端口 8000"
        echo "当前配置:"
        grep -A 5 "proxy_pass" /etc/nginx/sites-available/aikz.usdt2026.cc || echo "未找到 proxy_pass"
    fi
fi

echo ""
echo "检查 Nginx 语法..."
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置语法错误"
fi

echo ""
echo "检查 Nginx 服务状态..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务未运行"
    echo "尝试启动 Nginx..."
    sudo systemctl start nginx || echo "启动失败"
fi
echo ""

# 第六步：测试外部访问（通过 Nginx）
echo "第六步：测试外部访问"
echo "----------------------------------------"
echo "测试 aiadmin.usdt2026.cc..."
ADMIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -k https://aiadmin.usdt2026.cc/health 2>&1 || echo "000")
if [ "$ADMIN_RESPONSE" = "200" ]; then
    echo "✅ aiadmin.usdt2026.cc 可访问 (HTTP $ADMIN_RESPONSE)"
elif [ "$ADMIN_RESPONSE" = "502" ]; then
    echo "❌ aiadmin.usdt2026.cc 返回 502 (Bad Gateway)"
    echo "   这通常意味着 Nginx 无法连接到后端"
elif [ "$ADMIN_RESPONSE" = "000" ]; then
    echo "⚠️  无法连接到 aiadmin.usdt2026.cc (可能是 DNS 或网络问题)"
else
    echo "⚠️  aiadmin.usdt2026.cc 响应异常 (HTTP $ADMIN_RESPONSE)"
fi

echo ""
echo "测试 aikz.usdt2026.cc..."
AIKZ_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -k https://aikz.usdt2026.cc/health 2>&1 || echo "000")
if [ "$AIKZ_RESPONSE" = "200" ]; then
    echo "✅ aikz.usdt2026.cc 可访问 (HTTP $AIKZ_RESPONSE)"
elif [ "$AIKZ_RESPONSE" = "502" ]; then
    echo "❌ aikz.usdt2026.cc 返回 502 (Bad Gateway)"
else
    echo "⚠️  aikz.usdt2026.cc 响应异常 (HTTP $AIKZ_RESPONSE)"
fi
echo ""

# 第七步：检查环境变量（可选）
echo "第七步：检查环境变量配置"
echo "----------------------------------------"
cd "$PROJECT_ROOT/admin-backend" || exit 1
if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
    if grep -q "OPENAI_API_KEY" .env && ! grep -q "^OPENAI_API_KEY=$" .env; then
        echo "✅ OPENAI_API_KEY 已设置"
    else
        echo "⚠️  OPENAI_API_KEY 未设置（不影响登录功能）"
    fi
else
    echo "⚠️  .env 文件不存在（不影响登录功能）"
fi
echo ""

# 总结
echo "=========================================="
echo "📊 诊断总结"
echo "=========================================="
echo ""

if [ "$HEALTH_RESPONSE" = "200" ] && sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 后端服务正常运行"
else
    echo "❌ 后端服务异常"
fi

if [ "$ADMIN_RESPONSE" = "200" ] || [ "$ADMIN_RESPONSE" = "502" ]; then
    if [ "$ADMIN_RESPONSE" = "502" ]; then
        echo "❌ Nginx 无法连接到后端 (502)"
        echo ""
        echo "修复建议:"
        echo "1. 检查后端是否在运行: pm2 status"
        echo "2. 检查端口 8000: sudo lsof -i :8000"
        echo "3. 检查后端日志: pm2 logs backend --lines 50"
        echo "4. 重启 Nginx: sudo systemctl restart nginx"
    else
        echo "✅ 外部访问正常"
    fi
else
    echo "⚠️  外部访问测试失败"
fi

echo ""
echo "如果仍有问题，请运行:"
echo "  pm2 logs backend --lines 50"
echo "  sudo tail -50 /var/log/nginx/error.log"
echo ""

