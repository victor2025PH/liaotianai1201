# 修复 WebSocket 连接问题

## 🔍 问题描述

浏览器控制台显示：
```
WebSocket connection to 'ws://aikz.usdt2026.cc/api/v1/notifications/ws/admin%40example.com' failed:
```

## 🔧 修复步骤

### 步骤 1：检查 Nginx WebSocket 配置

```bash
# 检查 WebSocket location 配置
sudo grep -A 15 "location /api/v1/notifications/ws" /etc/nginx/sites-available/aikz.usdt2026.cc
```

**应该看到类似配置：**
```nginx
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
```

### 步骤 2：检查后端 WebSocket 服务

```bash
# 检查后端日志
sudo journalctl -u liaotian-backend -n 100 | grep -i websocket

# 检查后端是否在运行
sudo systemctl status liaotian-backend
```

### 步骤 3：测试 WebSocket 连接

```bash
# 测试本地 WebSocket（需要先获取 token）
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" | jq -r '.access_token')

# 测试 WebSocket 连接
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/notifications/ws/admin@example.com
```

### 步骤 4：修复 Nginx 配置（如果需要）

如果 Nginx 配置不正确，修复它：

```bash
# 备份配置
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)

# 检查并修复配置（使用之前的修复脚本）
# 或者手动编辑
sudo nano /etc/nginx/sites-available/aikz.usdt2026.cc

# 测试配置
sudo nginx -t

# 重新加载
sudo systemctl reload nginx
```

## 📝 注意事项

1. **WebSocket 路径必须正确**：
   - 前端请求：`ws://aikz.usdt2026.cc/api/v1/notifications/ws/admin%40example.com`
   - Nginx 应该代理到：`http://127.0.0.1:8000/api/v1/notifications/ws/admin@example.com`

2. **WebSocket 需要特殊配置**：
   - `Upgrade` 和 `Connection` headers 必须正确
   - `proxy_pass` 不应该包含路径（让 Nginx 传递完整路径）

3. **后端必须支持 WebSocket**：
   - 检查后端代码中是否有 WebSocket 路由
   - 检查后端服务是否正常运行

## 🎯 优先级

**WebSocket 问题优先级：中等**

- 不影响主要功能（账号管理、剧本管理等）
- 只影响实时通知功能
- 可以稍后修复

如果主要功能正常，可以暂时忽略 WebSocket 错误。

