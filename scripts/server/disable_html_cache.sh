#!/bin/bash

# 禁用 HTML 缓存脚本（解决 Cloudflare CDN 缓存问题）
# 使用方法: bash scripts/server/disable_html_cache.sh

set -e

echo "=========================================="
echo "🔧 禁用 HTML 缓存（解决 CDN 缓存问题）"
echo "时间: $(date)"
echo "=========================================="
echo ""

AIKZ_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 1. 检查配置文件是否存在
echo "1. 检查配置文件..."
echo "----------------------------------------"
if [ ! -f "$AIKZ_CONFIG" ]; then
  echo "❌ 配置文件不存在: $AIKZ_CONFIG"
  echo "请先运行 quick_fix_backend_and_aikz.sh 创建配置"
  exit 1
fi

echo "✅ 找到配置文件: $AIKZ_CONFIG"
echo ""

# 2. 备份原配置
echo "2. 备份原配置..."
echo "----------------------------------------"
BACKUP_FILE="${AIKZ_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp "$AIKZ_CONFIG" "$BACKUP_FILE"
echo "✅ 配置已备份到: $BACKUP_FILE"
echo ""

# 3. 读取现有配置并添加缓存控制
echo "3. 修改配置（添加禁止缓存 headers）..."
echo "----------------------------------------"

# 使用 Python 脚本来修改配置（更可靠）
sudo python3 << 'PYTHON_SCRIPT'
import re
import sys

config_file = "/etc/nginx/sites-available/aikz.usdt2026.cc"

try:
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经添加了缓存控制
    if 'Cache-Control "no-store' in content:
        print("⚠️  配置中已存在缓存控制 headers，跳过修改")
        sys.exit(0)
    
    # 在 location / 块中添加缓存控制 headers
    # 匹配 location / { ... } 块
    pattern = r'(location\s+/\s*\{[^}]*)(proxy_cache_bypass[^;]*;)'
    
    # 检查是否有 proxy_cache_bypass
    if re.search(pattern, content, re.DOTALL):
        # 在 proxy_cache_bypass 后添加缓存控制
        replacement = r'\1\2\n        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";\n        expires off;'
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    else:
        # 如果没有 proxy_cache_bypass，在 location / 块的末尾（在 } 之前）添加
        pattern2 = r'(location\s+/\s*\{[^}]*)(\s*\})'
        replacement2 = r'\1        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";\n        expires off;\n\2'
        content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    
    # 如果还是没有匹配到，尝试更宽松的匹配
    if 'Cache-Control "no-store' not in content:
        # 在每个 location / 块中添加
        lines = content.split('\n')
        new_lines = []
        in_location = False
        location_indent = 0
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # 检测 location / 块开始
            if re.match(r'\s*location\s+/\s*\{', line):
                in_location = True
                location_indent = len(line) - len(line.lstrip())
            
            # 在 location / 块中找到合适的位置插入
            if in_location and 'proxy_set_header' in line and 'X-Forwarded-Proto' in line:
                # 在最后一个 proxy_set_header 后添加
                indent = ' ' * (location_indent + 8)
                new_lines.append(f'{indent}add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";')
                new_lines.append(f'{indent}expires off;')
            
            # 检测 location / 块结束
            if in_location and line.strip() == '}':
                in_location = False
        
        content = '\n'.join(new_lines)
    
    # 如果仍然没有添加成功，使用最简单的方法：在每个 server 块的 location / 中添加
    if 'Cache-Control "no-store' not in content:
        # 使用 sed 方式：在 location / { 后添加
        import subprocess
        result = subprocess.run(
            ['sed', '-i', 
             r's|\(location\s\+/\s\+{\)|\1\n        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";\n        expires off;|g',
             config_file],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            # 如果 sed 失败，手动添加
            lines = content.split('\n')
            new_lines = []
            for i, line in enumerate(lines):
                new_lines.append(line)
                if re.match(r'\s*location\s+/\s*\{', line):
                    indent = ' ' * (len(line) - len(line.lstrip()) + 4)
                    new_lines.append(f'{indent}add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";')
                    new_lines.append(f'{indent}expires off;')
            content = '\n'.join(new_lines)
        else:
            # sed 成功，重新读取文件
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
    
    # 写入修改后的配置
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 配置已修改，已添加禁止缓存 headers")
    
except Exception as e:
    print(f"❌ 修改配置失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

# 如果 Python 脚本失败，使用 sed 作为备用方案
if [ $? -ne 0 ]; then
  echo "⚠️  Python 脚本失败，使用 sed 作为备用方案..."
  
  # 使用 sed 在 location / { 后添加缓存控制
  sudo sed -i '/location\s\+\/\s\+{/a\        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";\n        expires off;' "$AIKZ_CONFIG"
  
  echo "✅ 使用 sed 修改配置"
fi

echo ""

# 4. 显示修改后的配置（location / 部分）
echo "4. 显示修改后的配置（location / 部分）..."
echo "----------------------------------------"
sudo grep -A 15 "location /" "$AIKZ_CONFIG" | head -20
echo ""

# 5. 测试 Nginx 配置
echo "5. 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置语法正确"
else
  echo "❌ Nginx 配置有错误"
  echo "恢复备份配置..."
  sudo cp "$BACKUP_FILE" "$AIKZ_CONFIG"
  echo "✅ 已恢复备份配置"
  exit 1
fi
echo ""

# 6. 重启 Nginx
echo "6. 重启 Nginx..."
echo "----------------------------------------"
if sudo systemctl restart nginx; then
  echo "✅ Nginx 已重启"
  
  # 等待 Nginx 启动
  sleep 2
  
  # 检查 Nginx 状态
  if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
  else
    echo "❌ Nginx 启动失败"
    sudo systemctl status nginx --no-pager | head -15
    exit 1
  fi
else
  echo "❌ Nginx 重启失败"
  sudo systemctl status nginx --no-pager | head -15
  exit 1
fi
echo ""

# 7. 验证缓存控制 headers
echo "7. 验证缓存控制 headers..."
echo "----------------------------------------"
HTTP_HEADERS=$(curl -s -I http://127.0.0.1:3003 2>/dev/null || echo "")
if echo "$HTTP_HEADERS" | grep -qi "Cache-Control.*no-store"; then
  echo "✅ 检测到 Cache-Control: no-store header"
else
  echo "⚠️  未检测到 Cache-Control header（可能需要通过 Nginx 访问）"
fi

echo ""
echo "=========================================="
echo "✅ HTML 缓存已禁用！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "配置摘要："
echo "  - 已添加 Cache-Control: no-store, no-cache, must-revalidate"
echo "  - 已添加 expires off"
echo "  - 配置文件: $AIKZ_CONFIG"
echo "  - 备份文件: $BACKUP_FILE"
echo ""
echo "重要提示："
echo "  1. 清除 Cloudflare 缓存："
echo "     - 登录 Cloudflare 控制台"
echo "     - 进入域名设置"
echo "     - 点击 'Caching' -> 'Purge Everything'"
echo "  2. 或者使用 Cloudflare API："
echo "     curl -X POST \"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache\" \\"
echo "       -H \"Authorization: Bearer {api_token}\" \\"
echo "       -H \"Content-Type: application/json\" \\"
echo "       --data '{\"purge_everything\":true}'"
echo ""
echo "如果仍有问题，请检查："
echo "  sudo nginx -T | grep -A 20 'location /'"
echo "  curl -I http://aikz.usdt2026.cc"
echo "  sudo tail -20 /var/log/nginx/error.log"
