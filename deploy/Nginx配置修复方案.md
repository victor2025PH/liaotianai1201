# Nginx 配置修复方案 - 解决 API 404 问题

## 问题分析

所有 `/api/` 请求返回前端 HTML 而不是后端 JSON，说明 Nginx 没有正确将 API 请求转发到后端。

## 修复方案

### 修复后的完整 server 配置

```nginx
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级最高）
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # 后端 API（必须在 / 之前，优先级高于前端）
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # 前端（最后，最低优先级）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
```

## 关键修复点

### 1. location 顺序（优先级从高到低）
- `/api/v1/notifications/ws` - 最具体，优先级最高
- `/api/` - 匹配所有 API 请求
- `/` - 匹配所有其他请求（前端）

### 2. proxy_pass 配置
**正确写法：**
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;  # 注意：末尾没有斜杠和路径
}
```

**错误写法：**
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;  # 错误：会导致路径重复
}
```

**原因：**
- 当 `proxy_pass` 不包含路径时，Nginx 会将完整的请求路径传递给后端
- 例如：`/api/v1/dashboard` → `http://127.0.0.1:8000/api/v1/dashboard`
- 如果写成 `proxy_pass http://127.0.0.1:8000/api/;`，会导致路径变成 `/api/api/v1/dashboard`，从而 404

### 3. WebSocket 配置
```nginx
location /api/v1/notifications/ws {
    proxy_pass http://127.0.0.1:8000;  # 不包含路径
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    # ... 其他配置
}
```

## 在服务器上执行的修复命令

### 方法 1：使用 Python 脚本自动修复（推荐）

```bash
# 1. 备份配置
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)

# 2. 执行修复脚本
sudo python3 << 'PYEOF'
import re

# 读取配置
with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找 server 块
server_pattern = r'server\s*\{[^}]*server_name\s+aikz\.usdt2026\.cc[^}]*\}'
match = re.search(server_pattern, content, re.DOTALL)

if match:
    # 替换为新的 server 配置
    new_server = """server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级最高）
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # 后端 API（必须在 / 之前，优先级高于前端）
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # 前端（最后，最低优先级）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}"""
    
    new_content = content[:match.start()] + new_server + content[match.end():]
    
    with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print('配置已修复')
else:
    print('未找到 server 块，需要手动编辑')
PYEOF

# 3. 测试配置
sudo nginx -t

# 4. 应用配置
sudo systemctl reload nginx
```

### 方法 2：手动编辑（更安全）

```bash
# 1. 备份配置
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)

# 2. 编辑配置
sudo nano /etc/nginx/sites-available/aikz.usdt2026.cc

# 3. 找到 server_name aikz.usdt2026.cc 对应的 server 块
# 4. 删除所有现有的 location 配置
# 5. 添加上面的三个 location 配置（按顺序）
# 6. 保存并退出（Ctrl+O, Enter, Ctrl+X）

# 7. 测试配置
sudo nginx -t

# 8. 应用配置
sudo systemctl reload nginx
```

## 验证修复

修复后执行以下命令验证：

```bash
# 1. 检查配置语法
sudo nginx -t

# 2. 检查 location 配置
sudo grep -A 5 'location /api/' /etc/nginx/sites-available/aikz.usdt2026.cc

# 3. 测试 API 端点
curl http://localhost/api/v1/dashboard
curl http://localhost/api/v1/users/me

# 4. 检查 Nginx 状态
sudo systemctl status nginx
```

## 预期结果

修复后：
- ✅ `/api/v1/dashboard` 返回 JSON 而不是 HTML
- ✅ `/api/v1/users/me` 返回 JSON
- ✅ `/api/v1/notifications/ws/{email}` WebSocket 连接成功
- ✅ 前端页面正常加载

## 注意事项

1. **proxy_pass 不要包含路径**：写成 `http://127.0.0.1:8000` 而不是 `http://127.0.0.1:8000/api/`
2. **location 顺序很重要**：更具体的路径必须在前面
3. **确保没有重复的 location**：特别是 `/api/v1/notifications/ws`
4. **测试后再应用**：先执行 `nginx -t` 确认语法正确

