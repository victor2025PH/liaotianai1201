#!/bin/bash
# 修复 401 认证问题 - 在服务器上直接执行
# 使用实际的项目路径

echo "============================================================"
echo "修复 401 认证问题"
echo "============================================================"

# 检测实际路径
BACKEND_ENV_PATHS=(
    "/opt/smart-tg/admin-backend/.env"
    "/home/ubuntu/liaotian/admin-backend/.env"
    "$(pwd)/admin-backend/.env"
)

BACKEND_ENV_PATH=""
for path in "${BACKEND_ENV_PATHS[@]}"; do
    if [ -f "$path" ]; then
        BACKEND_ENV_PATH="$path"
        echo "[OK] 找到 .env 文件: $BACKEND_ENV_PATH"
        break
    fi
done

if [ -z "$BACKEND_ENV_PATH" ]; then
    echo "[错误] 未找到 .env 文件，尝试以下路径："
    for path in "${BACKEND_ENV_PATHS[@]}"; do
        echo "  - $path"
    done
    echo ""
    echo "请手动指定 .env 文件路径："
    read -p "输入 .env 文件完整路径: " BACKEND_ENV_PATH
    if [ ! -f "$BACKEND_ENV_PATH" ]; then
        echo "[错误] 文件不存在: $BACKEND_ENV_PATH"
        exit 1
    fi
fi

# 检测服务名
SERVICE_NAMES=("smart-tg-backend" "liaotian-backend" "admin-backend")
SERVICE_NAME=""
for name in "${SERVICE_NAMES[@]}"; do
    if systemctl list-units --type=service | grep -q "$name"; then
        SERVICE_NAME="$name"
        echo "[OK] 找到后端服务: $SERVICE_NAME"
        break
    fi
done

if [ -z "$SERVICE_NAME" ]; then
    echo "[警告] 未找到后端服务，尝试使用默认名称: smart-tg-backend"
    SERVICE_NAME="smart-tg-backend"
fi

# 1. 备份配置
echo ""
echo ">>> [1] 备份配置..."
BACKEND_DIR=$(dirname "$BACKEND_ENV_PATH")
sudo cp "$BACKEND_ENV_PATH" "${BACKEND_ENV_PATH}.bak.$(date +%Y%m%d_%H%M%S)"
echo "[OK] 已备份: ${BACKEND_ENV_PATH}.bak.$(date +%Y%m%d_%H%M%S)"

# 2. 更新 CORS 配置
echo ""
echo ">>> [2] 更新 CORS 配置..."
if sudo grep -q "CORS_ORIGINS" "$BACKEND_ENV_PATH"; then
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
sudo grep CORS_ORIGINS "$BACKEND_ENV_PATH"

# 3. 确保 Nginx 传递 Authorization header
echo ""
echo ">>> [3] 检查 Nginx 配置..."
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
if [ -f "$NGINX_CONFIG" ]; then
    if ! sudo grep -q "proxy_set_header Authorization" "$NGINX_CONFIG"; then
        # 在 /api/ location 中添加 Authorization header
        sudo sed -i '/location \/api\/ {/,/proxy_read_timeout/ {
            /proxy_set_header X-Forwarded-Proto/a\    proxy_set_header Authorization $http_authorization;
        }' "$NGINX_CONFIG"
        echo "[OK] 已添加 Authorization header 传递"
    else
        echo "[OK] Nginx 已配置 Authorization header 传递"
    fi
else
    echo "[警告] Nginx 配置文件不存在: $NGINX_CONFIG"
fi

# 4. 测试 Nginx 配置
echo ""
echo ">>> [4] 测试 Nginx 配置..."
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo "[OK] Nginx 配置测试通过"
    sudo systemctl reload nginx
    echo "[OK] Nginx 已重新加载"
else
    echo "[错误] Nginx 配置测试失败"
    sudo nginx -t
    exit 1
fi

# 5. 重启后端服务
echo ""
echo ">>> [5] 重启后端服务..."
if sudo systemctl restart "$SERVICE_NAME"; then
    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "[OK] 后端服务已重启"
    else
        echo "[错误] 后端服务未运行"
        sudo systemctl status "$SERVICE_NAME" --no-pager | head -20
        exit 1
    fi
else
    echo "[错误] 后端服务重启失败"
    exit 1
fi

# 6. 验证配置
echo ""
echo ">>> [6] 验证配置..."
echo ""
echo "CORS_ORIGINS:"
sudo grep CORS_ORIGINS "$BACKEND_ENV_PATH"
echo ""
echo "后端服务状态:"
sudo systemctl status "$SERVICE_NAME" --no-pager | head -5
echo ""
echo "Nginx Authorization header:"
if [ -f "$NGINX_CONFIG" ]; then
    sudo grep -A 2 "proxy_set_header Authorization" "$NGINX_CONFIG" || echo "未找到（可能使用默认传递）"
fi

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
echo "  sudo journalctl -u $SERVICE_NAME -n 50 | grep -i auth"

