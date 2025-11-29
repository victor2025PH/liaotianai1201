# WebSocket 连接修复报告

## 问题描述

前端 WebSocket 连接失败，无法建立实时通知连接。浏览器控制台显示多个 WebSocket 连接错误。

## 问题分析

### 1. 后端路由验证

**路由路径结构：**
- 后端 WebSocket 端点：`@router.websocket("/ws/{user_email}")` 在 `admin-backend/app/api/notifications.py:632`
- 路由前缀：`/notifications` (在 `notifications.py:35` 中定义)
- API 前缀：`/api/v1` (在 `main.py:125` 中定义)
- **完整路径：** `/api/v1/notifications/ws/{user_email}`

**路由注册验证：**
- ✅ `notifications.router` 已包含在 `api_router` 中 (`admin-backend/app/api/__init__.py:18`)
- ✅ `api_router` 已注册到主应用 (`admin-backend/app/main.py:125`)
- ✅ 路由注册正确

### 2. Nginx 配置问题

**根本原因：**
Nginx 反向代理缺少 WebSocket 专用配置，导致：
1. `Upgrade` 和 `Connection` 头无法正确传递到后端
2. WebSocket 握手失败
3. 连接被当作普通 HTTP 请求处理

**解决方案：**
需要在 Nginx 配置中添加专用的 WebSocket location 块，并设置正确的代理头。

## 修复方案

### 修复文件

1. **Nginx 配置文件：** `deploy/nginx_websocket_config.conf`
2. **手动修复指南：** `deploy/websocket_fix_manual.md`
3. **自动部署脚本：** `deploy/deploy_websocket_fix.py`

### 关键配置

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

### 配置要点

1. **优先级：** WebSocket location 必须在 `location /api/` 之前，确保优先匹配
2. **必需头：** 
   - `Upgrade: $http_upgrade` - 升级协议
   - `Connection: "upgrade"` - 保持连接
3. **超时设置：** `86400` 秒（24小时）支持长连接
4. **缓冲：** `proxy_buffering off` 禁用缓冲，确保实时性

## 部署步骤

### 方法 1：自动部署（推荐）

```bash
cd "E:\002-工作文件\重要程序\聊天AI群聊程序"
python deploy/deploy_websocket_fix.py
```

### 方法 2：手动部署

1. **SSH 连接到服务器：**
   ```bash
   ssh ubuntu@165.154.233.55
   ```

2. **备份当前配置：**
   ```bash
   sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak
   ```

3. **上传配置文件：**
   将 `deploy/nginx_websocket_config.conf` 上传到服务器，或直接编辑：
   ```bash
   sudo nano /etc/nginx/sites-available/aikz.usdt2026.cc
   ```
   添加 WebSocket location 块（在 `location /api/` 之前）

4. **测试配置：**
   ```bash
   sudo nginx -t
   ```

5. **重载 Nginx：**
   ```bash
   sudo systemctl reload nginx
   ```

详细步骤请参考：`deploy/websocket_fix_manual.md`

## 验证步骤

### 1. 检查 Nginx 配置

```bash
sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc | grep -A 12 'notifications/ws'
```

应该看到 WebSocket location 配置。

### 2. 检查后端服务

```bash
sudo systemctl status liaotian-backend
```

确保服务正常运行。

### 3. 检查后端日志

```bash
sudo journalctl -u liaotian-backend -n 50 | grep -i websocket
```

查看是否有 WebSocket 连接日志。

### 4. 前端测试

1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 筛选 WS (WebSocket) 连接
4. 刷新页面或触发通知
5. 检查连接状态：
   - ✅ 成功：状态码 101 (Switching Protocols)
   - ❌ 失败：状态码 400/404/502 等

### 5. 浏览器控制台检查

打开浏览器控制台，应该看到：
- ✅ 无 WebSocket 连接错误
- ✅ 连接成功消息（如果前端有日志）

## 故障排查

### 问题 1：仍然无法连接

**检查项：**
1. Nginx 配置是否正确应用
2. 后端服务是否正常运行
3. 防火墙是否阻止端口 8000

**测试直接连接（绕过 Nginx）：**
在前端临时修改 WebSocket URL：
```typescript
// 在 saas-demo/src/lib/api/config.ts 中临时修改
export function getWebSocketUrl(): string {
  return "ws://165.154.233.55:8000/api/v1/notifications/ws";
}
```

如果直接连接成功，说明问题在 Nginx 配置。

### 问题 2：连接建立但立即断开

**可能原因：**
1. 后端 WebSocket 端点处理错误
2. 认证失败
3. 心跳超时

**检查：**
```bash
sudo journalctl -u liaotian-backend -f
```

查看后端日志中的错误信息。

### 问题 3：Nginx 配置测试失败

**恢复备份：**
```bash
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc.bak /etc/nginx/sites-available/aikz.usdt2026.cc
sudo nginx -t
sudo systemctl reload nginx
```

## 相关文件

- **后端 WebSocket 实现：** `admin-backend/app/api/notifications.py:632-644`
- **前端 WebSocket 连接：** `saas-demo/src/components/notification-center.tsx:126-231`
- **WebSocket URL 配置：** `saas-demo/src/lib/api/config.ts:47-62`
- **Nginx 配置文件：** `deploy/nginx_websocket_config.conf`
- **手动修复指南：** `deploy/websocket_fix_manual.md`

## 完成状态

- [x] 后端路由验证
- [x] Nginx 配置创建
- [x] 部署脚本准备
- [x] 文档编写
- [ ] 配置部署到服务器（需要手动执行或运行部署脚本）
- [ ] 连接测试验证

## 下一步

1. **执行部署：** 运行 `deploy/deploy_websocket_fix.py` 或手动部署
2. **验证连接：** 按照验证步骤检查 WebSocket 连接
3. **监控日志：** 观察后端和 Nginx 日志，确保无错误
4. **前端测试：** 触发通知，验证实时推送功能

## 注意事项

1. **配置优先级：** WebSocket location 必须在 `/api/` 之前
2. **备份重要：** 部署前务必备份现有配置
3. **测试配置：** 使用 `nginx -t` 测试配置语法
4. **逐步验证：** 部署后逐步验证每个步骤
5. **回滚准备：** 保留备份文件，以便快速回滚

