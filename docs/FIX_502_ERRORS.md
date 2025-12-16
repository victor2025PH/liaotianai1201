# 修复 502 Bad Gateway 错误指南

## 问题描述

浏览器控制台出现多个 502 Bad Gateway 错误：
- `/api/v1/workers/502` 
- `/api/v1/workers/check/duplicates`
- `/api/v1/notifications/unread-count`
- WebSocket 连接失败：`wss://aikz.usdt2026.cc/api/v1/notifications/ws/...`

## 问题原因

502 Bad Gateway 错误通常表示：
1. **后端服务未运行** - `luckyred-api` 服务可能已停止或崩溃
2. **端口未监听** - 后端服务未在端口 8000 上监听
3. **Nginx 配置错误** - Nginx 无法正确代理到后端服务
4. **服务启动失败** - 后端服务启动时遇到错误

## 快速修复

### 方法 1: 使用自动修复脚本（推荐）

在服务器上执行：

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/fix_502_errors.sh
```

脚本会自动：
1. 重启后端服务
2. 检查端口监听
3. 测试 API 访问
4. 验证并修复 Nginx 配置
5. 提供最终验证

### 方法 2: 手动诊断和修复

#### 步骤 1: 诊断问题

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/diagnose_502_errors.sh
```

脚本会检查：
- 后端服务状态
- 端口监听情况
- 本地 API 访问
- Nginx 配置
- 后端日志

#### 步骤 2: 重启后端服务

```bash
# 重启后端服务
sudo systemctl restart luckyred-api

# 等待 5 秒
sleep 5

# 检查服务状态
sudo systemctl status luckyred-api

# 检查端口监听
ss -tlnp | grep :8000
```

#### 步骤 3: 测试本地 API

```bash
# 测试健康检查端点
curl -v http://127.0.0.1:8000/api/v1/health

# 测试 Workers API
curl -v http://127.0.0.1:8000/api/v1/workers/
```

如果本地 API 返回 200/401/404，说明后端服务正常。

#### 步骤 4: 检查 Nginx 配置

```bash
# 检查 Nginx 配置语法
sudo nginx -t

# 查看 API 代理配置
sudo grep -A 5 "location /api/" /etc/nginx/sites-available/default

# 重新加载 Nginx
sudo systemctl reload nginx
```

#### 步骤 5: 查看后端日志

如果服务启动失败，查看日志：

```bash
# 查看最近 50 行日志
sudo journalctl -u luckyred-api -n 50 --no-pager

# 实时查看日志
sudo journalctl -u luckyred-api -f
```

## 常见问题

### 问题 1: 后端服务无法启动

**症状：** `systemctl status luckyred-api` 显示 `failed` 或 `inactive`

**解决方案：**
1. 查看错误日志：`sudo journalctl -u luckyred-api -n 50 --no-pager`
2. 检查虚拟环境：确保 `/home/ubuntu/telegram-ai-system/admin-backend/venv` 存在
3. 检查依赖：`cd admin-backend && source venv/bin/activate && pip install -r requirements.txt`
4. 检查数据库：确保 `admin-backend/data/app.db` 存在且可写

### 问题 2: 端口 8000 未监听

**症状：** `ss -tlnp | grep :8000` 无输出

**解决方案：**
1. 确认服务正在运行：`systemctl is-active luckyred-api`
2. 检查服务配置：`cat /etc/systemd/system/luckyred-api.service`
3. 查看服务日志：`sudo journalctl -u luckyred-api -n 50 --no-pager`
4. 手动启动测试：`cd admin-backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000`

### 问题 3: Nginx 配置错误

**症状：** `sudo nginx -t` 显示语法错误

**解决方案：**
1. 备份当前配置：`sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup`
2. 使用修复脚本：`bash scripts/server/fix-nginx-routes-complete.sh`
3. 或手动检查配置：`sudo nano /etc/nginx/sites-available/default`

### 问题 4: WebSocket 连接失败

**症状：** 控制台显示 WebSocket 连接错误

**解决方案：**
1. 检查 Nginx WebSocket 配置：
   ```bash
   sudo grep -A 10 "location /api/v1/notifications/ws" /etc/nginx/sites-available/default
   ```
2. 确保配置包含：
   ```nginx
   location /api/v1/notifications/ws {
       proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       ...
   }
   ```
3. 重新加载 Nginx：`sudo systemctl reload nginx`

## 验证修复

修复后，验证以下内容：

1. **后端服务运行：**
   ```bash
   systemctl is-active luckyred-api
   # 应该返回: active
   ```

2. **端口监听：**
   ```bash
   ss -tlnp | grep :8000
   # 应该显示: LISTEN 0 4096 0.0.0.0:8000
   ```

3. **本地 API 访问：**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/health
   # 应该返回: 200, 401, 或 404
   ```

4. **外部 API 访问（通过 Nginx）：**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/api/v1/health
   # 应该返回: 200, 401, 或 404
   ```

5. **浏览器控制台：**
   - 刷新页面
   - 打开开发者工具（F12）
   - 检查 Network 标签
   - 应该不再有 502 错误

## 预防措施

1. **监控服务状态：**
   ```bash
   # 设置服务自动重启
   sudo systemctl enable luckyred-api
   ```

2. **定期检查日志：**
   ```bash
   # 查看最近错误
   sudo journalctl -u luckyred-api --since "1 hour ago" | grep -i error
   ```

3. **设置健康检查：**
   - 定期访问 `/api/v1/health` 端点
   - 如果返回 502，自动重启服务

## 相关脚本

- `scripts/server/diagnose_502_errors.sh` - 诊断 502 错误
- `scripts/server/fix_502_errors.sh` - 自动修复 502 错误
- `scripts/server/fix-nginx-routes-complete.sh` - 修复 Nginx 路由配置

## 联系支持

如果问题仍然存在，请提供：
1. 诊断脚本输出：`sudo bash scripts/server/diagnose_502_errors.sh`
2. 后端服务日志：`sudo journalctl -u luckyred-api -n 100 --no-pager`
3. Nginx 错误日志：`sudo tail -50 /var/log/nginx/error.log`

