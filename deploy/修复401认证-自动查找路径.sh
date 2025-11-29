#!/bin/bash
# 修复 401 认证问题 - 自动查找路径版本

echo "============================================================"
echo "修复 401 认证问题（自动查找路径）"
echo "============================================================"

# 1. 查找 .env 文件
echo ""
echo ">>> [1] 查找 .env 文件..."
BACKEND_ENV_PATH=""
for path in $(find /opt /home /root -name ".env" -type f 2>/dev/null | grep -E "(admin|backend)" | head -5); do
    if [ -f "$path" ] && grep -q "JWT_SECRET\|DATABASE_URL" "$path" 2>/dev/null; then
        BACKEND_ENV_PATH="$path"
        echo "[OK] 找到 .env 文件: $BACKEND_ENV_PATH"
        break
    fi
done

if [ -z "$BACKEND_ENV_PATH" ]; then
    echo "[警告] 未找到 .env 文件，尝试查找 systemd 服务配置..."
    
    # 从 systemd 服务文件中查找 EnvironmentFile
    for service_file in /etc/systemd/system/*backend*.service /etc/systemd/system/*liaotian*.service; do
        if [ -f "$service_file" ]; then
            env_file=$(grep "EnvironmentFile=" "$service_file" | head -1 | sed 's/.*EnvironmentFile=//' | sed 's/-.*//' | xargs)
            if [ -f "$env_file" ]; then
                BACKEND_ENV_PATH="$env_file"
                echo "[OK] 从服务文件找到 .env: $BACKEND_ENV_PATH"
                break
            fi
        fi
    done
fi

if [ -z "$BACKEND_ENV_PATH" ]; then
    echo "[错误] 无法找到 .env 文件"
    echo "请手动指定路径，或检查后端是否使用环境变量配置"
    exit 1
fi

# 2. 查找后端服务名
echo ""
echo ">>> [2] 查找后端服务名..."
SERVICE_NAME=""
for name in $(systemctl list-units --type=service --all | grep -E "(backend|liaotian|admin)" | awk '{print $1}' | sed 's/\.service$//'); do
    if systemctl is-active --quiet "$name" 2>/dev/null || systemctl is-enabled --quiet "$name" 2>/dev/null; then
        SERVICE_NAME="$name"
        echo "[OK] 找到后端服务: $SERVICE_NAME"
        break
    fi
done

if [ -z "$SERVICE_NAME" ]; then
    echo "[警告] 未找到 systemd 服务，尝试查找运行中的进程..."
    # 查找运行中的 gunicorn/uvicorn 进程
    proc_info=$(ps aux | grep -E "gunicorn.*main|uvicorn.*main" | grep -v grep | head -1)
    if [ -n "$proc_info" ]; then
        echo "[信息] 找到运行中的后端进程:"
        echo "$proc_info"
        echo "[提示] 后端可能不是通过 systemd 管理的，需要手动重启"
    fi
fi

# 3. 备份配置
echo ""
echo ">>> [3] 备份配置..."
if [ -f "$BACKEND_ENV_PATH" ]; then
    sudo cp "$BACKEND_ENV_PATH" "${BACKEND_ENV_PATH}.bak.$(date +%Y%m%d_%H%M%S)"
    echo "[OK] 已备份: ${BACKEND_ENV_PATH}.bak.$(date +%Y%m%d_%H%M%S)"
else
    echo "[警告] .env 文件不存在，将创建新文件"
    sudo mkdir -p "$(dirname "$BACKEND_ENV_PATH")"
fi

# 4. 更新 CORS 配置
echo ""
echo ">>> [4] 更新 CORS 配置..."
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
if [ -n "$SERVICE_NAME" ]; then
    if sudo systemctl restart "$SERVICE_NAME"; then
        sleep 2
        if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
            echo "[OK] 后端服务已重启: $SERVICE_NAME"
        else
            echo "[错误] 后端服务未运行: $SERVICE_NAME"
            sudo systemctl status "$SERVICE_NAME" --no-pager | head -10
        fi
    else
        echo "[错误] 后端服务重启失败: $SERVICE_NAME"
    fi
else
    echo "[警告] 未找到 systemd 服务，需要手动重启后端"
    echo "[提示] 如果后端是通过其他方式运行的，请手动重启"
    echo "[提示] 或者查找运行中的进程并重启："
    echo "  ps aux | grep gunicorn"
    echo "  # 然后 kill 并重新启动"
fi

# 8. 验证配置
echo ""
echo ">>> [8] 验证配置..."
echo ""
echo "CORS_ORIGINS 配置:"
sudo grep CORS_ORIGINS "$BACKEND_ENV_PATH" || echo "未找到"
echo ""
if [ -n "$SERVICE_NAME" ]; then
    echo "后端服务状态:"
    sudo systemctl status "$SERVICE_NAME" --no-pager | head -5
fi
echo ""
echo "端口 8000 监听状态:"
sudo netstat -tlnp | grep :8000 || sudo ss -tlnp | grep :8000 || echo "未找到监听进程"

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
if [ -z "$SERVICE_NAME" ]; then
    echo "[重要] 如果后端不是通过 systemd 管理的，请手动重启后端服务"
    echo "查找运行中的进程："
    echo "  ps aux | grep -E 'gunicorn|uvicorn' | grep -v grep"
fi

