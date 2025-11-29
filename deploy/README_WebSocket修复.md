# WebSocket 连接修复 - 部署说明

## 问题
前端 WebSocket 连接失败，无法建立实时通知连接。

## 解决方案
已在 Nginx 配置中添加专用的 WebSocket location 块。

## 部署方法

### 方法 1：使用批处理文件（Windows）
双击运行：`deploy/执行WebSocket修复.bat`

### 方法 2：使用 Python 脚本
```bash
cd "E:\002-工作文件\重要程序\聊天AI群聊程序"
python deploy/deploy_ws_final.py
```

部署完成后，查看日志：`deploy/deploy_log.txt`

### 方法 3：手动部署（推荐，最可靠）

1. **SSH 连接到服务器：**
   ```bash
   ssh ubuntu@165.154.233.55
   ```

2. **备份现有配置：**
   ```bash
   sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak
   ```

3. **编辑配置文件：**
   ```bash
   sudo nano /etc/nginx/sites-available/aikz.usdt2026.cc
   ```

4. **在 `location /api/` 之前添加以下配置：**
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

5. **测试配置：**
   ```bash
   sudo nginx -t
   ```

6. **重载 Nginx：**
   ```bash
   sudo systemctl reload nginx
   ```

7. **验证配置：**
   ```bash
   sudo grep -A 12 'notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc
   ```

## 验证部署

### 检查配置
```bash
ssh ubuntu@165.154.233.55
sudo grep -A 12 'notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc
```

应该看到 WebSocket location 配置。

### 前端测试
1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 筛选 WS (WebSocket) 连接
4. 刷新页面
5. 检查连接状态：
   - ✅ 成功：状态码 101 (Switching Protocols)
   - ❌ 失败：状态码 400/404/502 等

## 相关文件

- **Nginx 配置文件：** `deploy/nginx_websocket_config.conf`
- **完整配置示例：** 见上面的手动部署步骤
- **修复报告：** `docs/开发笔记/WebSocket连接修复报告.md`
- **手动修复指南：** `deploy/websocket_fix_manual.md`

## 故障排查

如果部署后仍然无法连接：

1. **检查 Nginx 配置语法：**
   ```bash
   sudo nginx -t
   ```

2. **检查 Nginx 日志：**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **检查后端服务：**
   ```bash
   sudo systemctl status liaotian-backend
   ```

4. **检查后端日志：**
   ```bash
   sudo journalctl -u liaotian-backend -n 50 | grep -i websocket
   ```

5. **测试直接连接（绕过 Nginx）：**
   在前端临时修改 WebSocket URL 为：
   ```
   ws://165.154.233.55:8000/api/v1/notifications/ws/{user_email}
   ```
   如果直接连接成功，说明问题在 Nginx 配置。

## 回滚

如果需要回滚到之前的配置：
```bash
ssh ubuntu@165.154.233.55
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc.bak /etc/nginx/sites-available/aikz.usdt2026.cc
sudo nginx -t
sudo systemctl reload nginx
```

