# WebSocket 修复 - 手动执行指南

## 🔍 当前状态

由于 SSH 需要密码，自动化脚本无法自动执行。请按以下步骤手动修复。

## 📋 手动修复步骤

### 步骤 1：登录服务器

在 PowerShell 中执行：
```powershell
ssh ubuntu@165.154.233.55
```
（需要输入密码）

### 步骤 2：在服务器上执行修复命令

登录服务器后，执行以下命令：

```bash
# 备份配置
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)

# 检查是否已有 WebSocket location
if sudo grep -q "location /api/v1/notifications/ws" /etc/nginx/sites-available/aikz.usdt2026.cc; then
    echo "WebSocket location 已存在"
else
    echo "添加 WebSocket location..."
    # 在 location /api/ 之前添加
    sudo sed -i '/location \/api\/ {/i\
    # WebSocket 支持\
    location /api/v1/notifications/ws {\
        proxy_pass http://127.0.0.1:8000;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_read_timeout 86400;\
        proxy_send_timeout 86400;\
        proxy_buffering off;\
    }\
' /etc/nginx/sites-available/aikz.usdt2026.cc
fi

# 测试配置
sudo nginx -t

# 重新加载
sudo systemctl reload nginx

# 验证配置
sudo grep -A 12 "location /api/v1/notifications/ws" /etc/nginx/sites-available/aikz.usdt2026.cc
```

### 步骤 3：验证修复

执行后，应该看到 WebSocket location 配置。然后：

1. **退出服务器**：`exit`
2. **在浏览器中刷新页面**（按 F5）
3. **检查浏览器控制台**，WebSocket 错误应该消失

## 🔧 或者使用 Python 脚本（在服务器上）

如果上面的命令太复杂，可以在服务器上使用 Python 脚本：

```bash
# 在服务器上创建修复脚本
cat > /tmp/修复WS.py << 'PYEOF'
import re

config_path = "/etc/nginx/sites-available/aikz.usdt2026.cc"

with open(config_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找 location /api/ 的位置
api_idx = None
for i, line in enumerate(lines):
    if 'location /api/' in line:
        api_idx = i
        break

if api_idx is None:
    print("错误: 未找到 location /api/")
    exit(1)

# 检查是否已有 WebSocket location
has_ws = any('location /api/v1/notifications/ws' in line for line in lines[:api_idx])

if not has_ws:
    ws_block = [
        '    # WebSocket 支持\n',
        '    location /api/v1/notifications/ws {\n',
        '        proxy_pass http://127.0.0.1:8000;\n',
        '        proxy_http_version 1.1;\n',
        '        proxy_set_header Upgrade $http_upgrade;\n',
        '        proxy_set_header Connection "upgrade";\n',
        '        proxy_set_header Host $host;\n',
        '        proxy_set_header X-Real-IP $remote_addr;\n',
        '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n',
        '        proxy_set_header X-Forwarded-Proto $scheme;\n',
        '        proxy_read_timeout 86400;\n',
        '        proxy_send_timeout 86400;\n',
        '        proxy_buffering off;\n',
        '    }\n',
        '\n'
    ]
    lines[api_idx:api_idx] = ws_block
    print("已添加 WebSocket location")
else:
    print("WebSocket location 已存在")

with open(config_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("配置已更新")
PYEOF

# 执行修复
sudo python3 /tmp/修复WS.py

# 测试并重新加载
sudo nginx -t && sudo systemctl reload nginx
```

## ✅ 验证修复成功

修复后，在浏览器中：
1. 刷新页面（F5）
2. 打开开发者工具（F12）→ Console
3. WebSocket 错误应该消失
4. 不应该再看到 "WebSocket connection failed" 错误

## 🎯 推荐方案

**最简单的方法**：直接在服务器上执行修复脚本

1. 登录服务器：`ssh ubuntu@165.154.233.55`
2. 执行修复命令（见上面的步骤 2）
3. 验证修复结果

