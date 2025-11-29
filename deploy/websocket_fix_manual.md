# WebSocket 连接修复指南

## 问题描述
前端 WebSocket 连接失败，无法建立实时通知连接。

## 根本原因
Nginx 反向代理缺少 WebSocket 专用配置，导致 Upgrade 和 Connection 头无法正确传递。

## 修复步骤

### 1. SSH 连接到服务器
```bash
ssh ubuntu@165.154.233.55
```

### 2. 备份当前配置
```bash
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak
```

### 3. 编辑 Nginx 配置
```bash
sudo nano /etc/nginx/sites-available/aikz.usdt2026.cc
```

### 4. 添加 WebSocket 配置
在 `location /api/` 之前添加以下配置（优先级更高）：

```nginx
# WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级更高）
location /api/v1/notifications/ws {
    proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
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
```

### 5. 完整的 Nginx 配置示例

```nginx
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务（优先级最高）
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
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

    # 前端
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

    # /api/workers/ -> /api/v1/workers（带末尾斜杠）
    location = /api/workers/ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # /api/workers/xxx -> /api/v1/workers/xxx
    location ~ ^/api/workers/(.+)$ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers/$1;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }
}
```

### 6. 测试配置
```bash
sudo nginx -t
```

### 7. 重载 Nginx
```bash
sudo systemctl reload nginx
```

### 8. 验证后端路由
检查后端服务是否正常运行：
```bash
sudo systemctl status liaotian-backend
```

检查后端日志：
```bash
sudo journalctl -u liaotian-backend -n 50 | grep -i websocket
```

### 9. 测试 WebSocket 连接
在前端浏览器控制台检查 WebSocket 连接状态，应该看到：
- 连接成功：`WebSocket connected`
- 无连接错误

## 验证要点

1. **路由路径**：`/api/v1/notifications/ws/{user_email}`
   - 后端路由：`@router.websocket("/ws/{user_email}")` 在 `notifications.py`
   - 路由前缀：`/notifications` (在 `notifications.py` 中定义)
   - API 前缀：`/api/v1` (在 `main.py` 中定义)
   - 完整路径：`/api/v1/notifications/ws/{user_email}`

2. **Nginx 配置关键点**：
   - `location /api/v1/notifications/ws` 必须在 `location /api/` 之前
   - 必须设置 `proxy_set_header Upgrade $http_upgrade`
   - 必须设置 `proxy_set_header Connection "upgrade"`
   - 建议设置长超时时间（86400 秒）

3. **前端连接**：
   - WebSocket URL: `ws://aikz.usdt2026.cc/api/v1/notifications/ws/{user_email}`
   - 或 `wss://` (如果使用 HTTPS)

## 故障排查

如果仍然无法连接：

1. **检查后端服务**：
   ```bash
   curl http://localhost:8000/api/v1/notifications/ws/test@example.com
   ```
   应该返回 WebSocket 握手错误（这是正常的，因为不是 WebSocket 客户端）

2. **检查 Nginx 日志**：
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **检查后端日志**：
   ```bash
   sudo journalctl -u liaotian-backend -f
   ```

4. **测试直接连接**（绕过 Nginx）：
   在前端临时修改 WebSocket URL 为 `ws://165.154.233.55:8000/api/v1/notifications/ws/{user_email}`
   如果直接连接成功，说明问题在 Nginx 配置

