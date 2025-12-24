#!/bin/bash
# 深度诊断 502 错误
# 检查 Nginx 错误日志、连接测试、后端绑定地址等

set -e

echo "=========================================="
echo "🔍 深度诊断 502 错误"
echo "=========================================="
echo ""

# 第一步：检查 Nginx 错误日志
echo "第一步：检查 Nginx 错误日志"
echo "----------------------------------------"
echo "最近 20 条错误日志:"
sudo tail -20 /var/log/nginx/error.log | grep -E "(502|upstream|connect|refused)" || echo "未找到相关错误"
echo ""

# 第二步：测试后端连接
echo "第二步：测试后端连接"
echo "----------------------------------------"

echo "测试 localhost:8000..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health > /dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    echo "✅ localhost:8000 可访问 (HTTP $HTTP_CODE)"
else
    echo "❌ localhost:8000 无法访问"
fi

echo ""
echo "测试 127.0.0.1:8000..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health > /dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health)
    echo "✅ 127.0.0.1:8000 可访问 (HTTP $HTTP_CODE)"
else
    echo "❌ 127.0.0.1:8000 无法访问"
fi

echo ""
echo "测试 0.0.0.0:8000..."
if curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:8000/health > /dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:8000/health)
    echo "✅ 0.0.0.0:8000 可访问 (HTTP $HTTP_CODE)"
else
    echo "⚠️  0.0.0.0:8000 无法访问（正常，0.0.0.0 是绑定地址，不能直接访问）"
fi

echo ""

# 第三步：检查后端绑定地址
echo "第三步：检查后端绑定地址"
echo "----------------------------------------"
echo "检查端口 8000 的监听地址:"
sudo netstat -tlnp | grep :8000 || sudo ss -tlnp | grep :8000 || echo "无法获取端口信息"
echo ""

# 第四步：检查 Nginx 配置中的 proxy_pass
echo "第四步：检查 Nginx 配置中的 proxy_pass"
echo "----------------------------------------"

echo "aiadmin.usdt2026.cc 配置:"
sudo grep -A 5 "proxy_pass" /etc/nginx/sites-enabled/aiadmin.usdt2026.cc 2>/dev/null || echo "配置文件不存在"
echo ""

echo "aikz.usdt2026.cc 配置:"
sudo grep -A 5 "proxy_pass" /etc/nginx/sites-enabled/aikz.usdt2026.cc 2>/dev/null || echo "配置文件不存在"
echo ""

# 第五步：测试 Nginx 能否连接到后端
echo "第五步：测试 Nginx 用户能否连接到后端"
echo "----------------------------------------"

# 检查 Nginx 用户
NGINX_USER=$(ps aux | grep nginx | grep master | awk '{print $1}' | head -1)
echo "Nginx 运行用户: $NGINX_USER"

# 尝试以 Nginx 用户身份测试连接
if sudo -u "$NGINX_USER" curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health > /dev/null 2>&1; then
    HTTP_CODE=$(sudo -u "$NGINX_USER" curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health)
    echo "✅ Nginx 用户 ($NGINX_USER) 可以连接到后端 (HTTP $HTTP_CODE)"
else
    echo "❌ Nginx 用户 ($NGINX_USER) 无法连接到后端"
    echo "   这可能是权限或网络问题"
fi

echo ""

# 第六步：检查防火墙
echo "第六步：检查防火墙"
echo "----------------------------------------"

if command -v ufw >/dev/null 2>&1; then
    echo "UFW 状态:"
    sudo ufw status | grep -E "(Status|8000)" || echo "未找到相关规则"
else
    echo "未安装 UFW"
fi

echo ""

# 第七步：检查 SELinux（如果适用）
echo "第七步：检查 SELinux（如果适用）"
echo "----------------------------------------"
if command -v getenforce >/dev/null 2>&1; then
    SELINUX_STATUS=$(getenforce 2>/dev/null || echo "Disabled")
    echo "SELinux 状态: $SELINUX_STATUS"
else
    echo "SELinux 未安装或未启用"
fi

echo ""

# 第八步：手动测试 Nginx 代理
echo "第八步：手动测试 Nginx 代理"
echo "----------------------------------------"

echo "测试 aiadmin.usdt2026.cc..."
sudo curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -H "Host: aiadmin.usdt2026.cc" http://127.0.0.1/health 2>&1 | head -5 || echo "测试失败"

echo ""
echo "测试 aikz.usdt2026.cc..."
sudo curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -H "Host: aikz.usdt2026.cc" http://127.0.0.1/api/health 2>&1 | head -5 || echo "测试失败"

echo ""
echo "=========================================="
echo "📊 诊断总结"
echo "=========================================="
echo ""
echo "根据以上诊断结果，可能的修复方案："
echo ""
echo "1. 如果 Nginx 用户无法连接后端:"
echo "   检查后端绑定地址是否为 0.0.0.0:8000"
echo ""
echo "2. 如果 proxy_pass 配置错误:"
echo "   确保使用 http://127.0.0.1:8000（不是 localhost）"
echo ""
echo "3. 如果 Nginx 错误日志显示连接被拒绝:"
echo "   检查后端是否真的在监听，重启后端服务"
echo ""
echo "4. 查看完整错误日志:"
echo "   sudo tail -50 /var/log/nginx/error.log"
echo ""

