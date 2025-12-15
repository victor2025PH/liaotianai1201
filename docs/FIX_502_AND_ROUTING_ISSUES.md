# 502 错误和路由问题修复指南

## 问题分析

### 1. 端口冲突问题
- **症状**：端口 8000 被非 systemd 进程占用（PID 77628），导致 systemd 服务无法正常启动
- **原因**：可能有手动启动的 uvicorn 进程占用了端口
- **影响**：后端服务无法正常绑定端口，导致 502 错误

### 2. 路由配置错误
- **症状**：`/login` 路由返回 404
- **原因**：
  - 前端有 `/login` 页面（Next.js 路由），应该由前端服务（端口 3000）处理
  - 后端只有 `/api/v1/auth/login` API 端点（POST 请求）
  - 之前的 Nginx 配置错误地将 `/login` 转发到后端
- **影响**：用户无法访问登录页面

### 3. 前端服务未运行
- **症状**：Nginx 错误日志显示 `connect() failed (111: Connection refused) while connecting to upstream, upstream: "http://127.0.0.1:3000/"`
- **原因**：前端服务（Next.js）没有运行
- **影响**：所有前端页面（包括 `/login`）无法访问

## 修复方案

### 方案 1：一键修复（推荐）

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
chmod +x scripts/server/fix-all-issues-complete.sh
sudo bash scripts/server/fix-all-issues-complete.sh
```

这个脚本会自动：
1. 停止 systemd 服务
2. 清理占用端口 8000 的所有进程
3. 清理所有相关的 Python/uvicorn 进程
4. 验证端口已释放
5. 重新启动后端服务
6. 重置 Nginx 配置（已修复路由）
7. 检查前端服务状态
8. 验证所有服务

### 方案 2：分步修复

#### 步骤 1：修复端口冲突

```bash
# 停止 systemd 服务
sudo systemctl stop luckyred-api

# 查找并终止占用端口 8000 的进程
sudo lsof -ti:8000 | xargs sudo kill -9

# 查找并终止所有 uvicorn 进程
ps aux | grep "[u]vicorn.*app.main:app" | awk '{print $2}' | xargs sudo kill -9

# 验证端口已释放
sudo lsof -ti:8000  # 应该没有输出

# 重新启动服务
sudo systemctl daemon-reload
sudo systemctl start luckyred-api
sudo systemctl status luckyred-api
```

#### 步骤 2：重置 Nginx 配置

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
chmod +x scripts/server/reset-nginx-config.sh
sudo bash scripts/server/reset-nginx-config.sh
```

#### 步骤 3：启动前端服务（可选）

如果前端服务未运行，可以选择启动：

```bash
# 方式 1：使用 pm2
cd /home/ubuntu/telegram-ai-system/saas-demo
pm2 start npm --name frontend -- start

# 方式 2：直接运行（开发模式）
cd /home/ubuntu/telegram-ai-system/saas-demo
npm run start

# 方式 3：后台运行
cd /home/ubuntu/telegram-ai-system/saas-demo
nohup npm run start > frontend.log 2>&1 &
```

## 正确的 Nginx 配置

修复后的配置：

```nginx
server {
    listen 443 ssl;
    server_name aikz.usdt2026.cc;
    
    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # 后端 API - 转发到后端（优先级最高）
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 前端应用 - 转发到前端（包括 /login 页面）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# HTTP 到 HTTPS 重定向
server {
    listen 80;
    server_name aikz.usdt2026.cc;
    return 301 https://$host$request_uri;
}
```

**关键点**：
- `/api/` 路径转发到后端（端口 8000）
- 所有其他路径（包括 `/login`）转发到前端（端口 3000）
- 前端登录页面会调用 `/api/v1/auth/login` API，这个 API 会被正确转发到后端

## 验证修复

### 1. 检查后端服务

```bash
# 检查服务状态
sudo systemctl status luckyred-api

# 检查端口监听
sudo ss -tlnp | grep 8000

# 测试健康检查
curl http://127.0.0.1:8000/health
# 应该返回: {"status":"ok"}
```

### 2. 检查前端服务（如果启动）

```bash
# 检查端口监听
sudo ss -tlnp | grep 3000

# 测试前端
curl http://127.0.0.1:3000/
```

### 3. 测试 HTTPS 路由

```bash
# 测试前端登录页面（应该返回 HTML）
curl -I https://aikz.usdt2026.cc/login
# 应该返回 HTTP 200

# 测试后端 API（应该返回 JSON）
curl -I https://aikz.usdt2026.cc/api/v1/health
# 应该返回 HTTP 200 或 404（如果路由不存在）

# 测试登录 API（POST 请求）
curl -X POST https://aikz.usdt2026.cc/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123"
# 应该返回 token 或 401/422 错误（这是正常的）
```

## 常见问题

### Q1: 修复后仍然出现 502 错误

**检查清单**：
1. 后端服务是否运行：`sudo systemctl status luckyred-api`
2. 端口 8000 是否被占用：`sudo lsof -ti:8000`
3. Nginx 配置是否正确：`sudo nginx -t`
4. Nginx 错误日志：`sudo tail -50 /var/log/nginx/error.log`

### Q2: `/login` 页面仍然返回 404

**可能原因**：
1. 前端服务未运行（端口 3000）
2. Nginx 配置未正确应用

**解决方案**：
```bash
# 检查前端服务
sudo ss -tlnp | grep 3000

# 如果未运行，启动前端服务
cd /home/ubuntu/telegram-ai-system/saas-demo
pm2 start npm --name frontend -- start

# 重新加载 Nginx
sudo nginx -t && sudo systemctl reload nginx
```

### Q3: 登录 API 返回 404

**检查**：
```bash
# 测试后端登录 API
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test"
```

如果本地测试也返回 404，说明后端路由未正确注册。检查：
- `admin-backend/app/main.py` 中是否包含 `auth.router`
- `admin-backend/app/api/__init__.py` 中是否正确导入

## 总结

修复步骤：
1. ✅ 解决端口冲突（清理占用进程）
2. ✅ 修复 Nginx 路由配置（`/api/` → 后端，`/` → 前端）
3. ✅ 启动后端服务
4. ⚠️ 启动前端服务（可选，但推荐）

修复后，访问流程：
1. 用户访问 `https://aikz.usdt2026.cc/login` → Nginx → 前端（端口 3000）→ 显示登录页面
2. 用户提交登录表单 → 前端调用 `/api/v1/auth/login` → Nginx → 后端（端口 8000）→ 返回 token

