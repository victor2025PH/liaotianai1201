#!/bin/bash
# 修复 Nginx 配置中的重复 location 块

set -e

CONFIG_FILE="/etc/nginx/sites-available/aiadmin.usdt2026.cc"

echo "🔧 修复 Nginx 配置中的重复 location 块..."

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    echo "   运行配置脚本: bash scripts/configure_admin_nginx.sh"
    exit 1
fi

# 备份原配置
BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ 已备份配置文件到: $BACKUP_FILE"

# 检查是否有重复的 location /admin
ADMIN_COUNT=$(grep -c "location /admin" "$CONFIG_FILE" || echo "0")
echo "📊 找到 $ADMIN_COUNT 个 'location /admin' 块"

if [ "$ADMIN_COUNT" -gt 1 ]; then
    echo "⚠️  发现重复的 location /admin 块，需要修复"
    
    # 使用 Python 脚本修复（更可靠）
    python3 << 'PYTHON_SCRIPT'
import re
import sys

config_file = "/etc/nginx/sites-available/aiadmin.usdt2026.cc"

try:
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有 location /admin 块
    pattern = r'location /admin \{.*?\n(?:\s+[^\}]*\n)*\s*\}'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if len(matches) > 1:
        print(f"发现 {len(matches)} 个 location /admin 块")
        
        # 保留最后一个（应该是正确的 3007 端口配置）
        # 删除前面的
        last_match = matches[-1]
        first_match = matches[0]
        
        # 检查哪个是 3007 端口的配置
        correct_match = None
        for match in matches:
            if '3007' in match.group():
                correct_match = match
                break
        
        if correct_match:
            # 删除所有 location /admin 块
            for match in reversed(matches):
                if match != correct_match:
                    content = content[:match.start()] + content[match.end():]
            
            # 确保有 /ai-monitor 配置
            if 'location /ai-monitor' not in content:
                # 在 /admin 之前插入 /ai-monitor
                admin_pos = content.find('location /admin')
                if admin_pos > 0:
                    ai_monitor_config = '''    # AI 监控系统前端代理（端口 3006）
    location /ai-monitor {
        proxy_pass http://127.0.0.1:3006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 重写路径，移除 /ai-monitor 前缀
        rewrite ^/ai-monitor/?(.*) /$1 break;
    }

'''
                    content = content[:admin_pos] + ai_monitor_config + content[admin_pos:]
            
            # 写入修复后的配置
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 已修复配置文件")
            sys.exit(0)
        else:
            print("❌ 未找到正确的 3007 端口配置")
            sys.exit(1)
    else:
        print("✅ 没有重复的 location /admin 块")
        sys.exit(0)
        
except Exception as e:
    print(f"❌ 修复失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ 配置文件已修复"
    else
        echo "❌ 自动修复失败，需要手动修复"
        echo ""
        echo "💡 手动修复步骤："
        echo "   1. 编辑配置文件: sudo nano $CONFIG_FILE"
        echo "   2. 删除重复的 'location /admin' 块"
        echo "   3. 确保只有一个 'location /admin' 块，代理到 3007"
        echo "   4. 确保有 'location /ai-monitor' 块，代理到 3006"
        exit 1
    fi
else
    echo "✅ 没有重复的 location 块"
fi

# 测试配置
echo ""
echo "🧪 测试 Nginx 配置..."
if sudo nginx -t; then
    echo "✅ Nginx 配置测试通过"
    
    # 重新加载 Nginx
    echo "🔄 重新加载 Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx 已重新加载"
    
    echo ""
    echo "=========================================="
    echo "✅ 修复完成！"
    echo "=========================================="
    echo ""
    echo "💡 现在可以访问："
    echo "   - 站点管理后台: http://aiadmin.usdt2026.cc/admin"
    echo "   - AI 监控系统: http://aiadmin.usdt2026.cc/ai-monitor"
else
    echo "❌ Nginx 配置测试失败"
    echo "请检查配置文件: $CONFIG_FILE"
    exit 1
fi

