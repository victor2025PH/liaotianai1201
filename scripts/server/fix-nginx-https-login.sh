#!/bin/bash
# ============================================================
# 修复 Nginx HTTPS /login 路由配置
# 确保 HTTPS (443) server 块中 /login 正确转发到后端
# ============================================================

set +e # 不在第一个错误时退出

echo "=========================================="
echo "🔧 修复 Nginx HTTPS /login 路由"
echo "=========================================="
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "此脚本需要 root 权限，请使用 sudo 运行"
    echo "使用方法: sudo bash $0"
    exit 1
fi

DOMAIN="aikz.usdt2026.cc"

# 查找配置文件
NGINX_CONFIG=$(find /etc/nginx -name "*.conf" -type f | xargs grep -l "server_name.*$DOMAIN" 2>/dev/null | head -1)
if [ -z "$NGINX_CONFIG" ]; then
    NGINX_CONFIG="/etc/nginx/sites-available/default"
fi

if [ ! -f "$NGINX_CONFIG" ]; then
    echo "❌ 配置文件不存在: $NGINX_CONFIG"
    exit 1
fi

echo "使用配置文件: $NGINX_CONFIG"
echo ""

# 备份
BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "✅ 配置已备份到: $BACKUP_FILE"
echo ""

# 检查 HTTPS server 块
echo "[1/3] 检查 HTTPS server 块..."
echo "----------------------------------------"
HTTPS_LINE=$(grep -n "listen.*443" "$NGINX_CONFIG" | head -1 | cut -d: -f1)
if [ -z "$HTTPS_LINE" ]; then
    echo "❌ 未找到 HTTPS (443) 配置"
    exit 1
fi

echo "HTTPS server 块起始行: $HTTPS_LINE"
echo ""

# 检查 /login 配置
echo "[2/3] 检查 /login 配置..."
echo "----------------------------------------"
# 从 HTTPS server 块开始查找
HTTPS_BLOCK=$(sed -n "${HTTPS_LINE},/^}$/p" "$NGINX_CONFIG" | head -100)

if echo "$HTTPS_BLOCK" | grep -q "location.*/login"; then
    echo "✅ HTTPS server 块中已有 /login 配置"
    echo "$HTTPS_BLOCK" | grep -A 10 "location.*/login" | head -15
else
    echo "❌ HTTPS server 块中缺少 /login 配置"
    echo "需要添加 /login location"
fi
echo ""

# 修复配置
echo "[3/3] 修复配置..."
echo "----------------------------------------"

# 使用 Python 修复
python3 <<PYTHON_SCRIPT
import re

with open("$NGINX_CONFIG", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 找到 HTTPS server 块的起始和结束
https_start = None
https_end = None
brace_count = 0

for i, line in enumerate(lines):
    if https_start is None and re.search(r'listen\s+443', line):
        https_start = i
        brace_count = 0
    if https_start is not None:
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0 and https_start is not None:
            https_end = i + 1
            break

if https_start is None:
    print("❌ 未找到 HTTPS server 块")
    sys.exit(1)

print(f"HTTPS server 块: 行 {https_start + 1} 到 {https_end}")

# 检查是否已有 /login
https_block = ''.join(lines[https_start:https_end])
if re.search(r'location\s+.*/login', https_block):
    print("✅ /login 配置已存在，检查是否需要修复...")
    # 检查是否转发到后端
    login_block = re.search(r'location\s+.*/login[^{]*\{[^}]*\}', https_block, re.DOTALL)
    if login_block and '127.0.0.1:8000' in login_block.group(0):
        print("✅ /login 已正确配置为转发到后端")
    else:
        print("⚠️  /login 配置存在但可能不正确，需要修复")
        # 替换 /login 配置
        new_login = '''    # 登录页面 - 转发到后端
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
        https_block = re.sub(
            r'location\s+.*/login[^{]*\{[^}]*\}',
            new_login.strip(),
            https_block,
            flags=re.DOTALL
        )
        lines[https_start:https_end] = list(https_block)
        needs_write = True
else:
    print("❌ /login 配置不存在，添加配置...")
    # 在第一个 location 之前添加 /login
    # 找到第一个 location 的位置
    first_location = None
    for i in range(https_start, https_end):
        if re.search(r'location\s+', lines[i]):
            first_location = i
            break
    
    if first_location is None:
        # 如果没有 location，在 server 块内添加（在 server_name 之后）
        for i in range(https_start, min(https_start + 10, https_end)):
            if re.search(r'server_name', lines[i]):
                first_location = i + 1
                break
        if first_location is None:
            first_location = https_start + 1
    
    new_login = '''    # 登录页面 - 转发到后端（必须在根路径之前）
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
    lines.insert(first_location, new_login)
    needs_write = True

if 'needs_write' in locals() and needs_write:
    with open("$NGINX_CONFIG", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("✅ 配置已更新")
else:
    print("✅ 配置无需修改")
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo "❌ Python 脚本执行失败"
    exit 1
fi

# 测试配置
echo ""
echo "测试 Nginx 配置..."
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    systemctl reload nginx 2>/dev/null || systemctl restart nginx
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重新加载"
    else
        echo "❌ Nginx 重新加载失败"
        exit 1
    fi
else
    echo "❌ Nginx 配置语法错误:"
    nginx -t 2>&1 | tail -10
    echo ""
    echo "恢复备份配置..."
    cp "$BACKUP_FILE" "$NGINX_CONFIG"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "请测试: curl -I https://$DOMAIN/login"
echo ""

