#!/bin/bash
# ============================================================
# 直接修复 Nginx HTTPS /login 路由（最简版本）
# ============================================================

set +e

echo "=========================================="
echo "🔧 直接修复 Nginx HTTPS /login 路由"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

# 查找配置文件
CONFIG_FILE=$(nginx -T 2>&1 | grep "configuration file.*443" | head -1 | sed 's/# configuration file //' | sed 's/:$//')
if [ -z "$CONFIG_FILE" ]; then
    # 尝试其他方法
    CONFIG_FILE=$(find /etc/nginx/sites-available -name "*.conf" | xargs grep -l "listen.*443" 2>/dev/null | head -1)
fi
if [ -z "$CONFIG_FILE" ] || [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_FILE="/etc/nginx/sites-available/default"
fi

echo "配置文件: $CONFIG_FILE"
echo ""

# 备份
BACKUP="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_FILE" "$BACKUP"
echo "✅ 已备份到: $BACKUP"
echo ""

# 检查 HTTPS server 块中是否已有 /login
echo "[1/3] 检查当前配置..."
echo "----------------------------------------"
HTTPS_BLOCK=$(sed -n '/listen.*443/,/^[[:space:]]*}/p' "$CONFIG_FILE")
if echo "$HTTPS_BLOCK" | grep -q "location.*/login"; then
    echo "⚠️  /login 配置已存在，检查是否正确..."
    if echo "$HTTPS_BLOCK" | grep -A 5 "location.*/login" | grep -q "127.0.0.1:8000"; then
        echo "✅ /login 已正确配置为转发到后端"
        echo "但可能位置不对，需要确保在根路径之前"
    else
        echo "❌ /login 配置存在但未转发到后端，需要修复"
    fi
else
    echo "❌ /login 配置不存在"
fi
echo ""

# 修复配置
echo "[2/3] 修复配置..."
echo "----------------------------------------"

# 使用 Python 修复
python3 <<'PYTHON_SCRIPT'
import re
import sys

config_file = "$CONFIG_FILE"

with open(config_file, "r", encoding="utf-8") as f:
    content = f.read()

# 找到 HTTPS server 块
https_pattern = r'(server\s*\{[^}]*listen\s+443[^}]*\{)(.*?)(^\s*\})'
match = re.search(https_pattern, content, re.MULTILINE | re.DOTALL)

if not match:
    print("❌ 未找到 HTTPS server 块")
    sys.exit(1)

server_start = match.group(1)
server_body = match.group(2)
server_end = match.group(3)

# 检查是否已有 /login
has_login = re.search(r'location\s+.*/login', server_body)

# 准备新的 /login 配置
new_login_config = '''
    # 登录页面 - 转发到后端（必须在根路径之前）
    location /login {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
'''

if has_login:
    # 替换现有的 /login 配置
    server_body = re.sub(
        r'location\s+.*/login[^{]*\{[^}]*\}',
        new_login_config.strip(),
        server_body,
        flags=re.DOTALL
    )
    print("✅ 已替换现有的 /login 配置")
else:
    # 在第一个 location 之前添加 /login
    # 找到第一个 location
    first_location = re.search(r'(\s+)(location\s+)', server_body)
    if first_location:
        indent = first_location.group(1)
        insert_pos = first_location.start()
        server_body = server_body[:insert_pos] + new_login_config + indent + server_body[insert_pos:]
        print("✅ 已在第一个 location 之前添加 /login 配置")
    else:
        # 如果没有 location，在 server_name 之后添加
        server_name = re.search(r'server_name[^;]+;', server_body)
        if server_name:
            insert_pos = server_name.end()
            server_body = server_body[:insert_pos] + '\n' + new_login_config + server_body[insert_pos:]
            print("✅ 已在 server_name 之后添加 /login 配置")
        else:
            print("❌ 无法确定插入位置")
            sys.exit(1)

# 重新组合
new_content = content[:match.start()] + server_start + server_body + server_end + content[match.end():]

with open(config_file, "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ 配置已更新")
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo "❌ Python 脚本执行失败，恢复备份"
    cp "$BACKUP" "$CONFIG_FILE"
    exit 1
fi

# 测试配置
echo ""
echo "[3/3] 测试并重新加载..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    systemctl reload nginx 2>/dev/null || systemctl restart nginx
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重新加载"
    else
        echo "❌ Nginx 重新加载失败"
        systemctl status nginx --no-pager -l | head -10
        exit 1
    fi
else
    echo "❌ Nginx 配置语法错误:"
    nginx -t 2>&1 | tail -10
    echo ""
    echo "恢复备份配置..."
    cp "$BACKUP" "$CONFIG_FILE"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "请测试: curl -I https://aikz.usdt2026.cc/login"
echo ""

