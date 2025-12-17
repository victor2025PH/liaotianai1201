# 部署后检查清单

## ✅ 已完成项目

- [x] 8GB Swap 文件创建
- [x] DNS 和软件源配置
- [x] Python 3.10 安装
- [x] Node.js LTS 安装
- [x] PM2 安装和配置
- [x] 后端服务启动（online）
- [x] 前端服务启动（online）

---

## 🔍 立即验证（请在服务器上执行）

### 1. 验证服务运行状态

```bash
# 查看 PM2 状态
pm2 status

# 查看详细进程信息
pm2 info backend
pm2 info frontend

# 查看实时日志（Ctrl+C 退出）
pm2 logs
```

### 2. 测试后端 API

```bash
# 健康检查
curl http://localhost:8000/health

# 应该返回类似：{"status": "ok"} 或类似的 JSON 响应
```

### 3. 测试前端服务

```bash
# 测试前端访问
curl http://localhost:3000

# 应该返回 HTML 内容（Next.js 应用）
```

### 4. 检查端口监听

```bash
# 检查端口 8000（后端）
sudo ss -tlnp | grep :8000

# 检查端口 3000（前端）
sudo ss -tlnp | grep :3000

# 应该看到类似输出，确认服务正在监听
```

---

## 🌐 配置 Nginx 反向代理（重要）

### 步骤 1：备份原配置

```bash
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
```

### 步骤 2：编辑 Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/default
```

### 步骤 3：使用以下配置（替换 server 块）

**注意：** 将 `your-domain.com` 替换为您的实际域名。

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名，例如：aikz.usdt2026.cc

    # 后端 API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 前端应用
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存（可选优化）
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://frontend;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 步骤 4：测试并重载 Nginx

```bash
# 测试配置语法
sudo nginx -t

# 如果测试通过，重载配置
sudo systemctl reload nginx

# 或者重启 Nginx
sudo systemctl restart nginx
```

### 步骤 5：验证 Nginx 状态

```bash
sudo systemctl status nginx
```

---

## 🔒 配置 HTTPS（推荐）

### 使用 Certbot 配置 SSL 证书

```bash
# 安装 Certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# 获取证书（替换为您的域名和邮箱）
sudo certbot --nginx -d your-domain.com -d www.your-domain.com --email your-email@example.com --agree-tos --non-interactive

# 设置自动续期
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## 📊 监控和维护

### 查看日志

```bash
# PM2 日志
pm2 logs backend --lines 100    # 后端日志（最近 100 行）
pm2 logs frontend --lines 100   # 前端日志（最近 100 行）
pm2 logs --lines 50             # 所有服务日志

# Nginx 日志
sudo tail -f /var/log/nginx/access.log  # 访问日志
sudo tail -f /var/log/nginx/error.log   # 错误日志

# 系统日志
sudo journalctl -u nginx -f
```

### 重启服务

```bash
# 重启所有 PM2 服务
pm2 restart all

# 重启单个服务
pm2 restart backend
pm2 restart frontend

# 重启 Nginx
sudo systemctl restart nginx
```

### 查看系统资源

```bash
# 内存和 Swap 使用情况
free -h

# 磁盘使用情况
df -h

# PM2 监控（实时）
pm2 monit

# 系统负载
htop  # 如果已安装
# 或
top
```

---

## 🔄 更新代码和重启服务

```bash
cd ~/telegram-ai-system

# 1. 拉取最新代码
git pull origin main

# 2. 更新后端依赖（如果需要）
cd admin-backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 3. 更新前端依赖并重新构建（如果需要）
cd saas-demo
npm install
npm run build

# 4. 复制静态资源（standalone 模式需要）
mkdir -p .next/standalone/.next/static
cp -r .next/static/* .next/standalone/.next/static/
cp -r public .next/standalone/
cd ..

# 5. 重启 PM2 服务
pm2 restart all
pm2 save

# 6. 验证服务状态
pm2 status
curl http://localhost:8000/health
```

---

## ⚠️ 常见问题排查

### 服务无法启动

```bash
# 查看 PM2 日志
pm2 logs backend --err
pm2 logs frontend --err

# 检查端口占用
sudo ss -tlnp | grep -E ':3000|:8000'

# 手动测试后端
cd ~/telegram-ai-system/admin-backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端构建失败

```bash
cd ~/telegram-ai-system/saas-demo
rm -rf .next node_modules
npm install
npm run build
```

### Nginx 502 Bad Gateway

```bash
# 检查后端和前端是否运行
pm2 status

# 检查端口监听
sudo ss -tlnp | grep -E ':3000|:8000'

# 查看 Nginx 错误日志
sudo tail -50 /var/log/nginx/error.log

# 重启服务
pm2 restart all
sudo systemctl restart nginx
```

### PM2 进程丢失（重启后）

```bash
# PM2 应该已经配置开机自启，检查启动脚本
pm2 startup

# 确保保存了进程列表
pm2 save

# 手动启动（如果需要）
cd ~/telegram-ai-system
pm2 start ecosystem.config.js
pm2 save
```

---

## 📝 下一步建议

1. ✅ **立即执行验证命令**：确认所有服务正常运行
2. ⚙️ **配置 Nginx**：设置反向代理，使外部可以访问
3. 🔒 **配置 HTTPS**：使用 Certbot 获取 SSL 证书
4. 📊 **设置监控**：考虑配置日志监控和告警
5. 🔄 **定期更新**：保持系统和依赖包更新

---

**恭喜！部署成功！** 🎉

现在您的服务器已经配置完成，后端和前端服务都在运行。接下来可以配置 Nginx 和 HTTPS，使您的应用可以通过域名访问。
