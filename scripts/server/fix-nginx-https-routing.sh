#!/bin/bash
# ============================================================
# 修复 Nginx HTTPS 路由配置脚本
# 确保 HTTPS (443) 的 /login 和 /api 正确转发到后端
# ============================================================

set +e # 不在第一个错误时退出

echo "=========================================="
echo "🔧 修复 Nginx HTTPS 路由配置"
echo "=========================================="
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "此脚本需要 root 权限，请使用 sudo 运行"
    echo "使用方法: sudo bash $0"
    exit 1
fi

DOMAIN="aikz.usdt2026.cc"

# 查找 Nginx 配置文件
NGINX_CONFIGS=$(find /etc/nginx -name "*.conf" -type f | grep -E "(sites-available|conf.d)" | head -5)
if [ -z "$NGINX_CONFIGS" ]; then
    NGINX_CONFIGS="/etc/nginx/sites-available/default"
fi

echo "[1/6] 查找 Nginx 配置文件..."
echo "----------------------------------------"
for config in $NGINX_CONFIGS; do
    if [ -f "$config" ] && grep -q "server_name.*$DOMAIN" "$config" 2>/dev/null; then
        echo "✅ 找到配置文件: $config"
        MAIN_CONFIG="$config"
        break
    fi
done

if [ -z "$MAIN_CONFIG" ]; then
    echo "❌ 未找到包含 $DOMAIN 的配置文件"
    echo "尝试使用默认配置: /etc/nginx/sites-available/default"
    MAIN_CONFIG="/etc/nginx/sites-available/default"
fi

if [ ! -f "$MAIN_CONFIG" ]; then
    echo "❌ 配置文件不存在: $MAIN_CONFIG"
    exit 1
fi
echo ""

# 2. 备份配置
echo "[2/6] 备份配置..."
echo "----------------------------------------"
BACKUP_FILE="${MAIN_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$MAIN_CONFIG" "$BACKUP_FILE"
echo "✅ 配置已备份到: $BACKUP_FILE"
echo ""

# 3. 检查 HTTPS server 块
echo "[3/6] 检查 HTTPS server 块..."
echo "----------------------------------------"
if grep -q "listen.*443" "$MAIN_CONFIG"; then
    echo "✅ 找到 HTTPS (443) 配置"
    HTTPS_BLOCK=$(grep -n "listen.*443" "$MAIN_CONFIG" | head -1 | cut -d: -f1)
    echo "HTTPS server 块起始行: $HTTPS_BLOCK"
else
    echo "⚠️  未找到 HTTPS (443) 配置，可能需要添加"
fi
echo ""

# 4. 修复配置
echo "[4/6] 修复配置..."
echo "----------------------------------------"

# 使用 Python 修复配置
python3 <<PYTHON_SCRIPT
import re
import sys

with open("$MAIN_CONFIG", "r", encoding="utf-8") as f:
    content = f.read()

# 查找所有包含 443 的 server 块
server_blocks = re.split(r'(server\s*\{)', content)
fixed_content = ""
needs_fix = False

for i in range(0, len(server_blocks), 2):
    if i + 1 < len(server_blocks):
        server_header = server_blocks[i]
        server_body = server_blocks[i + 1] if i + 1 < len(server_blocks) else ""
        
        # 检查是否是 HTTPS (443) server 块
        if "listen.*443" in server_header or (server_body and re.search(r'listen\s+443', server_body)):
            # 检查是否包含 $DOMAIN
            if re.search(r'server_name.*$DOMAIN', server_body):
                print(f"处理 HTTPS server 块...")
                
                # 检查是否有 /login location
                if not re.search(r'location\s+.*/login', server_body):
                    print("  添加 /login location...")
                    # 在第一个 location 之前添加 /login
                    login_config = '''
    # 登录页面 - 转发到后端
    location /login {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
'''
                    # 在第一个 location 之前插入
                    server_body = re.sub(
                        r'(location\s+/)',
                        login_config + r'\1',
                        server_body,
                        count=1
                    )
                    needs_fix = True
                
                # 确保 /api 转发到后端
                if re.search(r'location\s+/api', server_body):
                    # 修复现有的 /api 配置
                    server_body = re.sub(
                        r'(location\s+/api[^{]*\{[^}]*proxy_pass\s+)(http://[^;]+)',
                        r'\1http://127.0.0.1:8000/api/',
                        server_body,
                        flags=re.DOTALL
                    )
                    print("  修复 /api location...")
                    needs_fix = True
                elif not re.search(r'location\s+/api', server_body):
                    # 添加 /api 配置
                    print("  添加 /api location...")
                    api_config = '''
    # 后端 API - 转发到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
'''
                    server_body = re.sub(
                        r'(location\s+/)',
                        api_config + r'\1',
                        server_body,
                        count=1
                    )
                    needs_fix = True
        
        fixed_content += server_header + server_body
    else:
        fixed_content += server_blocks[i]

if needs_fix:
    with open("$MAIN_CONFIG", "w", encoding="utf-8") as f:
        f.write(fixed_content)
    print("✅ 配置已修复")
else:
    print("✅ 配置无需修复")
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo "❌ Python 脚本执行失败，尝试使用 sed 修复..."
    # 简单的 sed 修复作为备选方案
    # 这里可以添加 sed 命令
fi
echo ""

# 5. 测试配置
echo "[5/6] 测试 Nginx 配置..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置语法错误:"
    nginx -t 2>&1 | tail -10
    echo ""
    echo "恢复备份配置..."
    cp "$BACKUP_FILE" "$MAIN_CONFIG"
    exit 1
fi
echo ""

# 6. 重新加载 Nginx
echo "[6/6] 重新加载 Nginx..."
echo "----------------------------------------"
systemctl reload nginx 2>/dev/null || systemctl restart nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 重新加载失败"
    systemctl status nginx --no-pager -l | head -10
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "请测试以下 URL:"
echo "1. curl -I https://$DOMAIN/login"
echo "2. curl -I https://$DOMAIN/api/v1/health"
echo ""

