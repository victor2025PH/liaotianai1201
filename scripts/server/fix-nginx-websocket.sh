#!/bin/bash
# ============================================================
# 修复 Nginx WebSocket 配置
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
step_msg() { echo -e "${BLUE}📌 $1${NC}"; }

echo "========================================="
echo "修复 Nginx WebSocket 配置"
echo "========================================="
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    error_msg "请使用 sudo 运行此脚本"
    exit 1
fi

NGINX_CONFIG="/etc/nginx/sites-available/default"

# 检测域名
DOMAIN=$(grep -E "server_name\s+" $NGINX_CONFIG 2>/dev/null | head -1 | sed 's/.*server_name\s*\([^;]*\);.*/\1/' | awk '{print $1}' || echo "")

if [ -z "$DOMAIN" ]; then
    echo "请输入您的域名（例如：aikz.usdt2026.cc）："
    read -r DOMAIN
fi

if [ -z "$DOMAIN" ]; then
    error_msg "域名不能为空"
    exit 1
fi

info_msg "域名: $DOMAIN"
echo ""

# 备份配置
step_msg "[1/3] 备份 Nginx 配置..."
BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$NGINX_CONFIG" "$BACKUP_FILE"
success_msg "配置已备份到: $BACKUP_FILE"
echo ""

# 检查是否已有 WebSocket 配置
step_msg "[2/3] 检查现有配置..."
if grep -q "location /api/v1/notifications/ws" "$NGINX_CONFIG"; then
    info_msg "检测到已有 WebSocket 配置"
    
    # 检查配置是否正确
    if grep -A 10 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "proxy_set_header Upgrade"; then
        info_msg "WebSocket 配置看起来正确"
        
        # 测试并重载
        if nginx -t > /dev/null 2>&1; then
            systemctl reload nginx
            success_msg "Nginx 配置验证通过并已重载"
            echo ""
            echo "========================================="
            success_msg "WebSocket 配置已存在且正确！"
            echo "========================================="
            exit 0
        fi
    else
        info_msg "WebSocket 配置不完整，需要更新"
    fi
else
    info_msg "未找到 WebSocket 配置，将添加"
fi
echo ""

# 添加或更新 WebSocket 配置
step_msg "[3/3] 更新 WebSocket 配置..."

# 创建临时文件
TEMP_CONFIG=$(mktemp)

# 读取现有配置并插入 WebSocket 配置
python3 << 'PYTHON_SCRIPT'
import sys
import re

config_file = sys.argv[1]
domain = sys.argv[2]

with open(config_file, 'r') as f:
    content = f.read()

# WebSocket 配置块
websocket_config = f'''    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级更高）
    location /api/v1/notifications/ws {{
        proxy_pass http://backend/api/v1/notifications/ws;
        proxy_http_version 1.1;
        
        # WebSocket 升级头（必需）
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 标准请求头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 需要更长的超时时间
        proxy_connect_timeout 60s;
        proxy_send_timeout 86400s;
        proxy_read_timeout 86400s;
        
        # 禁用缓冲（WebSocket 必需）
        proxy_buffering off;
    }}

'''

# 如果已有 WebSocket 配置，替换它
if re.search(r'location /api/v1/notifications/ws', content):
    # 替换现有的 WebSocket 配置
    pattern = r'(\s+# WebSocket.*?location /api/v1/notifications/ws.*?^\s+})'
    content = re.sub(pattern, websocket_config.rstrip(), content, flags=re.MULTILINE | re.DOTALL)
else:
    # 在 location /api/ 之前插入 WebSocket 配置
    pattern = r'(\s+location /api/ \{)'
    replacement = websocket_config + r'\1'
    content = re.sub(pattern, replacement, content)

# 写入临时文件
with open(sys.argv[3], 'w') as f:
    f.write(content)

PYTHON_SCRIPT
"$NGINX_CONFIG" "$DOMAIN" "$TEMP_CONFIG"

# 如果 Python 脚本失败，使用 sed 方式
if [ $? -ne 0 ] || ! grep -q "location /api/v1/notifications/ws" "$TEMP_CONFIG"; then
    info_msg "使用备用方法更新配置..."
    
    # 简单的 sed 方式：在 location /api/ 之前插入
    sed -i '/location \/api\/ {/i\
    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级更高）\
    location /api/v1/notifications/ws {\
        proxy_pass http://backend/api/v1/notifications/ws;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_connect_timeout 60s;\
        proxy_send_timeout 86400s;\
        proxy_read_timeout 86400s;\
        proxy_buffering off;\
    }\
' "$NGINX_CONFIG"
    
    cp "$NGINX_CONFIG" "$TEMP_CONFIG"
fi

# 验证配置
if nginx -t; then
    # 替换原配置
    cp "$TEMP_CONFIG" "$NGINX_CONFIG"
    rm -f "$TEMP_CONFIG"
    
    # 重载 Nginx
    systemctl reload nginx
    success_msg "WebSocket 配置已更新并重载"
else
    error_msg "Nginx 配置有错误"
    nginx -t
    rm -f "$TEMP_CONFIG"
    exit 1
fi

echo ""

# 完成
echo "========================================="
success_msg "WebSocket 配置修复完成！"
echo "========================================="
echo ""
echo "📊 配置信息："
echo "  - WebSocket 路径: ws://$DOMAIN/api/v1/notifications/ws"
echo "  - 或: wss://$DOMAIN/api/v1/notifications/ws (如果已配置 HTTPS)"
echo ""
echo "🔍 验证命令："
echo "  curl -i -N -H \"Connection: Upgrade\" -H \"Upgrade: websocket\" -H \"Host: $DOMAIN\" -H \"Origin: http://$DOMAIN\" http://$DOMAIN/api/v1/notifications/ws/test"
echo ""
