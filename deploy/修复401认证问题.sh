#!/bin/bash
# 修复 401 认证问题

echo "============================================================"
echo "修复 401 认证问题"
echo "============================================================"

# 1. 备份配置
echo ">>> [1] 备份配置..."
sudo cp /home/ubuntu/liaotian/admin-backend/.env /home/ubuntu/liaotian/admin-backend/.env.bak.$(date +%Y%m%d_%H%M%S)
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)

# 2. 更新 CORS 配置
echo ">>> [2] 更新 CORS 配置..."
if sudo grep -q "CORS_ORIGINS" /home/ubuntu/liaotian/admin-backend/.env; then
    # 如果已存在，检查是否包含生产域名
    if ! sudo grep "CORS_ORIGINS" /home/ubuntu/liaotian/admin-backend/.env | grep -q "aikz.usdt2026.cc"; then
        # 追加生产域名
        sudo sed -i 's|CORS_ORIGINS=\(.*\)|CORS_ORIGINS=\1,http://aikz.usdt2026.cc|' /home/ubuntu/liaotian/admin-backend/.env
        echo "[OK] 已添加生产域名到 CORS_ORIGINS"
    else
        echo "[OK] CORS_ORIGINS 已包含生产域名"
    fi
else
    # 如果不存在，添加新行
    echo "CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc" | sudo tee -a /home/ubuntu/liaotian/admin-backend/.env
    echo "[OK] 已添加 CORS_ORIGINS 配置"
fi

# 3. 确保 Nginx 传递 Authorization header
echo ">>> [3] 检查 Nginx 配置..."
if ! sudo grep -q "proxy_set_header Authorization" /etc/nginx/sites-available/aikz.usdt2026.cc; then
    # 在 /api/ location 中添加 Authorization header
    sudo sed -i '/location \/api\/ {/,/proxy_read_timeout/ {
        /proxy_set_header X-Forwarded-Proto/a\    proxy_set_header Authorization $http_authorization;
    }' /etc/nginx/sites-available/aikz.usdt2026.cc
    echo "[OK] 已添加 Authorization header 传递"
else
    echo "[OK] Nginx 已配置 Authorization header 传递"
fi

# 4. 测试 Nginx 配置
echo ">>> [4] 测试 Nginx 配置..."
if sudo nginx -t; then
    echo "[OK] Nginx 配置测试通过"
    sudo systemctl reload nginx
    echo "[OK] Nginx 已重新加载"
else
    echo "[错误] Nginx 配置测试失败，请检查配置"
    exit 1
fi

# 5. 重启后端服务
echo ">>> [5] 重启后端服务..."
sudo systemctl restart liaotian-backend
sleep 2
if sudo systemctl is-active --quiet liaotian-backend; then
    echo "[OK] 后端服务已重启"
else
    echo "[错误] 后端服务启动失败"
    sudo systemctl status liaotian-backend --no-pager | head -20
    exit 1
fi

# 6. 验证配置
echo ">>> [6] 验证配置..."
echo "CORS_ORIGINS:"
sudo grep CORS_ORIGINS /home/ubuntu/liaotian/admin-backend/.env
echo ""
echo "Nginx Authorization header:"
sudo grep -A 2 "proxy_set_header Authorization" /etc/nginx/sites-available/aikz.usdt2026.cc || echo "未找到（可能使用默认传递）"

echo ""
echo "============================================================"
echo "修复完成！"
echo "============================================================"
echo ""
echo "下一步："
echo "1. 在浏览器中访问 http://aikz.usdt2026.cc/login 重新登录"
echo "2. 登录后访问 http://aikz.usdt2026.cc/group-ai/accounts"
echo "3. 检查浏览器控制台，确认 API 请求是否成功"

