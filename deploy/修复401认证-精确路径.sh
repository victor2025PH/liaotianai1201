#!/bin/bash
# 修复 401 认证问题 - 使用精确路径

echo "============================================================"
echo "修复 401 认证问题（精确路径版本）"
echo "============================================================"

# 根据查找结果确定的路径
BACKEND_ENV_PATH="/home/ubuntu/admin-backend/.env"
ACTUAL_BACKEND_PATH="/home/ubuntu/liaotian/admin-backend"
SERVICE_NAME="liaotian-backend"

echo ""
echo ">>> [1] 检查配置路径..."
echo "systemd 配置的 .env: $BACKEND_ENV_PATH"
echo "实际运行的后端路径: $ACTUAL_BACKEND_PATH"
echo "服务名: $SERVICE_NAME"

# 检查 .env 文件是否存在
if [ ! -f "$BACKEND_ENV_PATH" ]; then
    echo "[警告] systemd 配置的 .env 文件不存在: $BACKEND_ENV_PATH"
    echo "[信息] 检查实际后端路径的 .env 文件..."
    
    # 检查实际后端路径的 .env
    if [ -f "$ACTUAL_BACKEND_PATH/.env" ]; then
        BACKEND_ENV_PATH="$ACTUAL_BACKEND_PATH/.env"
        echo "[OK] 找到实际后端路径的 .env: $BACKEND_ENV_PATH"
    else
        echo "[信息] 实际后端路径也没有 .env 文件"
        echo "[信息] 将创建 systemd 配置的 .env 文件"
        sudo mkdir -p "$(dirname "$BACKEND_ENV_PATH")"
    fi
else
    echo "[OK] 找到 .env 文件: $BACKEND_ENV_PATH"
fi

# 2. 备份配置
echo ""
echo ">>> [2] 备份配置..."
if [ -f "$BACKEND_ENV_PATH" ]; then
    sudo cp "$BACKEND_ENV_PATH" "${BACKEND_ENV_PATH}.bak.$(date +%Y%m%d_%H%M%S)"
    echo "[OK] 已备份: ${BACKEND_ENV_PATH}.bak.$(date +%Y%m%d_%H%M%S)"
fi

# 3. 更新 CORS 配置
echo ""
echo ">>> [3] 更新 CORS 配置..."
if sudo grep -q "CORS_ORIGINS" "$BACKEND_ENV_PATH" 2>/dev/null; then
    # 如果已存在，检查是否包含生产域名
    if ! sudo grep "CORS_ORIGINS" "$BACKEND_ENV_PATH" | grep -q "aikz.usdt2026.cc"; then
        # 追加生产域名
        sudo sed -i 's|CORS_ORIGINS=\(.*\)|CORS_ORIGINS=\1,http://aikz.usdt2026.cc|' "$BACKEND_ENV_PATH"
        echo "[OK] 已添加生产域名到 CORS_ORIGINS"
    else
        echo "[OK] CORS_ORIGINS 已包含生产域名"
    fi
else
    # 如果不存在，添加新行
    echo "CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc" | sudo tee -a "$BACKEND_ENV_PATH" > /dev/null
    echo "[OK] 已添加 CORS_ORIGINS 配置"
fi

# 显示更新后的配置
echo ""
echo "当前 CORS_ORIGINS 配置:"
sudo grep CORS_ORIGINS "$BACKEND_ENV_PATH" || echo "未找到 CORS_ORIGINS"

# 4. 检查实际后端路径的 .env（如果不同）
if [ "$BACKEND_ENV_PATH" != "$ACTUAL_BACKEND_PATH/.env" ] && [ -f "$ACTUAL_BACKEND_PATH/.env" ]; then
    echo ""
    echo ">>> [4] 同步到实际后端路径的 .env..."
    if sudo grep -q "CORS_ORIGINS" "$ACTUAL_BACKEND_PATH/.env" 2>/dev/null; then
        if ! sudo grep "CORS_ORIGINS" "$ACTUAL_BACKEND_PATH/.env" | grep -q "aikz.usdt2026.cc"; then
            sudo sed -i 's|CORS_ORIGINS=\(.*\)|CORS_ORIGINS=\1,http://aikz.usdt2026.cc|' "$ACTUAL_BACKEND_PATH/.env"
            echo "[OK] 已同步到实际后端路径的 .env"
        fi
    else
        echo "CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://aikz.usdt2026.cc" | sudo tee -a "$ACTUAL_BACKEND_PATH/.env" > /dev/null
        echo "[OK] 已添加到实际后端路径的 .env"
    fi
fi

# 5. 检查 Nginx 配置
echo ""
echo ">>> [5] 检查 Nginx 配置..."
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
if [ -f "$NGINX_CONFIG" ]; then
    if ! sudo grep -q "proxy_set_header Authorization" "$NGINX_CONFIG"; then
        echo "[信息] Nginx 未显式配置 Authorization header（通常默认会传递）"
    else
        echo "[OK] Nginx 已配置 Authorization header 传递"
    fi
else
    echo "[警告] Nginx 配置文件不存在: $NGINX_CONFIG"
fi

# 6. 测试并重新加载 Nginx
echo ""
echo ">>> [6] 测试并重新加载 Nginx..."
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo "[OK] Nginx 配置测试通过"
    sudo systemctl reload nginx
    echo "[OK] Nginx 已重新加载"
else
    echo "[错误] Nginx 配置测试失败"
    sudo nginx -t
fi

# 7. 重启后端服务
echo ""
echo ">>> [7] 重启后端服务..."
if sudo systemctl restart "$SERVICE_NAME"; then
    sleep 3
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "[OK] 后端服务已重启: $SERVICE_NAME"
    else
        echo "[错误] 后端服务未运行: $SERVICE_NAME"
        sudo systemctl status "$SERVICE_NAME" --no-pager | head -15
    fi
else
    echo "[错误] 后端服务重启失败: $SERVICE_NAME"
    sudo systemctl status "$SERVICE_NAME" --no-pager | head -15
fi

# 8. 验证配置
echo ""
echo ">>> [8] 验证配置..."
echo ""
echo "CORS_ORIGINS 配置（systemd 配置的 .env）:"
sudo grep CORS_ORIGINS "$BACKEND_ENV_PATH" || echo "未找到"
if [ -f "$ACTUAL_BACKEND_PATH/.env" ] && [ "$BACKEND_ENV_PATH" != "$ACTUAL_BACKEND_PATH/.env" ]; then
    echo ""
    echo "CORS_ORIGINS 配置（实际后端路径的 .env）:"
    sudo grep CORS_ORIGINS "$ACTUAL_BACKEND_PATH/.env" || echo "未找到"
fi
echo ""
echo "后端服务状态:"
sudo systemctl status "$SERVICE_NAME" --no-pager | head -10
echo ""
echo "端口 8000 监听状态:"
sudo ss -tlnp | grep :8000 || echo "未找到监听进程"

echo ""
echo "============================================================"
echo "修复完成！"
echo "============================================================"
echo ""
echo "下一步："
echo "1. 在浏览器中访问 http://aikz.usdt2026.cc/login 重新登录"
echo "2. 登录后访问 http://aikz.usdt2026.cc/group-ai/accounts"
echo "3. 检查浏览器控制台，确认 API 请求是否成功"
echo ""
echo "如果仍有问题，检查后端日志："
echo "  sudo journalctl -u $SERVICE_NAME -n 50 | grep -i cors"

