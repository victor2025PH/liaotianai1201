#!/bin/bash
# 诊断 aiadmin.usdt2026.cc 跳转错误问题

echo "=========================================="
echo "诊断 aiadmin.usdt2026.cc 跳转错误"
echo "=========================================="
echo ""

NGINX_CONFIG="/etc/nginx/sites-available/aiadmin.usdt2026.cc"
NGINX_ENABLED="/etc/nginx/sites-enabled/aiadmin.usdt2026.cc"
DOMAIN="aiadmin.usdt2026.cc"

echo "1. 检查 Nginx 配置文件"
echo "----------------------------------------"
if [ -f "$NGINX_CONFIG" ]; then
    echo "✅ 配置文件存在: $NGINX_CONFIG"
    echo ""
    echo "当前配置内容："
    echo "---"
    sudo cat "$NGINX_CONFIG"
    echo "---"
    echo ""
    
    # 检查软链接
    if [ -L "$NGINX_ENABLED" ]; then
        LINK_TARGET=$(readlink "$NGINX_ENABLED")
        echo "✅ 软链接存在: $NGINX_ENABLED -> $LINK_TARGET"
        if [ "$LINK_TARGET" = "$NGINX_CONFIG" ]; then
            echo "✅ 软链接指向正确"
        else
            echo "❌ 软链接指向错误！应该指向: $NGINX_CONFIG"
        fi
    else
        echo "❌ 软链接不存在: $NGINX_ENABLED"
    fi
else
    echo "❌ 配置文件不存在: $NGINX_CONFIG"
fi

echo ""
echo "2. 检查 location / 的 proxy_pass 配置"
echo "----------------------------------------"
LOCATION_ROOT=$(sudo grep -A 10 "location / {" "$NGINX_CONFIG" 2>/dev/null | grep "proxy_pass" | head -1)
if [ -n "$LOCATION_ROOT" ]; then
    echo "当前 location / 的 proxy_pass:"
    echo "$LOCATION_ROOT"
    
    # 提取端口号
    PORT=$(echo "$LOCATION_ROOT" | grep -oP '127\.0\.0\.1:\K[0-9]+' || echo "")
    if [ -n "$PORT" ]; then
        echo "检测到的代理端口: $PORT"
        if [ "$PORT" = "3007" ]; then
            echo "✅ 端口正确 (应该是 3007)"
        else
            echo "❌ 端口错误！应该是 3007，但当前是 $PORT"
        fi
    else
        echo "⚠️  无法提取端口号"
    fi
else
    echo "❌ 未找到 location / 的 proxy_pass 配置"
fi

echo ""
echo "3. 检查 PM2 进程状态"
echo "----------------------------------------"
echo "查找 sites-admin-frontend 进程："
pm2 list | grep -E "sites-admin-frontend|id|name|status|port" || echo "未找到相关进程"

echo ""
echo "所有前端相关进程："
pm2 list | grep -E "frontend|id|name|status" | head -20

echo ""
echo "4. 检查端口占用情况"
echo "----------------------------------------"
PORTS=(3007 8000 3003 3001 3002)
for PORT in "${PORTS[@]}"; do
    echo -n "端口 $PORT: "
    if command -v lsof >/dev/null 2>&1; then
        PID=$(sudo lsof -ti:$PORT 2>/dev/null)
        if [ -n "$PID" ]; then
            PROCESS=$(ps -p $PID -o comm= 2>/dev/null)
            echo "被进程 $PID ($PROCESS) 占用"
        else
            echo "未被占用"
        fi
    elif command -v ss >/dev/null 2>&1; then
        if sudo ss -tlnp | grep -q ":$PORT "; then
            echo "被占用"
            sudo ss -tlnp | grep ":$PORT "
        else
            echo "未被占用"
        fi
    else
        echo "无法检查（需要 lsof 或 ss）"
    fi
done

echo ""
echo "5. 检查服务实际响应"
echo "----------------------------------------"
echo "测试本地端口 3007（管理后台前端）："
HTTP_3007=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3007 2>&1)
if [ "$HTTP_3007" = "200" ]; then
    echo "✅ 端口 3007 响应正常 (HTTP $HTTP_3007)"
    echo "响应内容预览（前200字符）："
    curl -s http://127.0.0.1:3007 2>&1 | head -c 200
    echo ""
else
    echo "❌ 端口 3007 响应异常 (HTTP $HTTP_3007)"
fi

echo ""
echo "测试本地端口 3003（aizkw 前端）："
HTTP_3003=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3003 2>&1)
if [ "$HTTP_3003" = "200" ]; then
    echo "✅ 端口 3003 响应正常 (HTTP $HTTP_3003)"
    echo "响应内容预览（前200字符）："
    curl -s http://127.0.0.1:3003 2>&1 | head -c 200
    echo ""
else
    echo "⚠️  端口 3003 响应异常 (HTTP $HTTP_3003)"
fi

echo ""
echo "测试本地端口 8000（管理后台后端）："
HTTP_8000=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/sites 2>&1)
if [ "$HTTP_8000" = "200" ]; then
    echo "✅ 端口 8000 响应正常 (HTTP $HTTP_8000)"
else
    echo "⚠️  端口 8000 响应异常 (HTTP $HTTP_8000)"
fi

echo ""
echo "6. 检查域名实际响应"
echo "----------------------------------------"
echo "测试 $DOMAIN："
DOMAIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN" 2>&1)
echo "HTTP 状态码: $DOMAIN_RESPONSE"

if [ "$DOMAIN_RESPONSE" = "200" ]; then
    echo "响应内容预览（前300字符）："
    curl -s "http://$DOMAIN" 2>&1 | head -c 300
    echo ""
    echo ""
    echo "检查响应中是否包含 'AI 智控王'（aizkw 网站的特征）："
    if curl -s "http://$DOMAIN" 2>&1 | grep -qi "智控王\|aizkw\|数字霸权"; then
        echo "❌ 发现 aizkw 网站内容！域名指向了错误的网站"
    else
        echo "✅ 未发现 aizkw 网站内容"
    fi
    
    echo ""
    echo "检查响应中是否包含 '三个展示网站管理后台'（管理后台的特征）："
    if curl -s "http://$DOMAIN" 2>&1 | grep -qi "三个展示网站管理后台\|sites-admin\|站点概览"; then
        echo "✅ 发现管理后台内容"
    else
        echo "❌ 未发现管理后台内容"
    fi
fi

echo ""
echo "7. 检查 Nginx 配置语法和加载状态"
echo "----------------------------------------"
echo "测试 Nginx 配置："
sudo nginx -t 2>&1

echo ""
echo "检查 Nginx 运行状态："
sudo systemctl status nginx --no-pager -l | head -10

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "根据以上信息，检查："
echo "1. Nginx location / 的 proxy_pass 是否指向 3007 端口"
echo "2. 端口 3007 是否有服务在运行"
echo "3. PM2 中 sites-admin-frontend 是否正常运行"
echo "4. 域名响应内容是否匹配管理后台"

