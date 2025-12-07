# 🚀 Nginx 和 Systemd 配置完整指南

## 📋 概述

本指南将帮助你：
1. ✅ 配置 Nginx 反向代理（统一访问入口）
2. ✅ 设置 Systemd 服务（开机自启动）
3. ✅ 实现生产环境的稳定部署

---

## 🎯 配置前准备

### 确认服务状态

确保前端和后端服务已经在运行：

```bash
# 检查前端服务（端口 3000）
ss -tlnp | grep :3000
curl -s http://localhost:3000 | head -5

# 检查后端服务（端口 8000）
ss -tlnp | grep :8000
curl -s http://localhost:8000/health
```

如果服务未运行，先启动它们：

```bash
cd ~/liaotian

# 启动后端
cd admin-backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

# 启动前端
cd ../saas-demo
nohup npm start > /tmp/frontend.log 2>&1 &
```

---

## 🚀 一键配置（推荐）

### 方法 1: 使用自动化脚本

```bash
cd ~/liaotian

# 下载配置脚本（如果还没有）
git pull origin main

# 运行配置脚本（需要 sudo）
sudo bash scripts/setup_nginx_and_systemd.sh
```

脚本会自动完成：
- ✅ 安装 Nginx（如果没有）
- ✅ 配置 Nginx 反向代理
- ✅ 创建 Systemd 服务文件
- ✅ 启用开机自启动
- ✅ 启动所有服务
- ✅ 验证服务状态

### 方法 2: 手动配置（逐步执行）

如果自动脚本遇到问题，可以手动执行以下步骤。

---

## 📝 手动配置步骤

### 步骤 1: 安装 Nginx

```bash
sudo apt update
sudo apt install -y nginx
```

### 步骤 2: 配置 Nginx

#### 2.1 创建配置文件

```bash
sudo nano /etc/nginx/sites-available/liaotian
```

#### 2.2 复制配置内容

使用项目中的配置文件：

```bash
sudo cp ~/liaotian/deploy/nginx/liaotian.conf /etc/nginx/sites-available/liaotian
```

或者手动创建配置文件（内容见下文）。

#### 2.3 启用配置

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/liaotian /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 步骤 3: 配置 Systemd 服务

#### 3.1 创建前端服务文件

```bash
sudo nano /etc/systemd/system/liaotian-frontend.service
```

复制以下内容：

```ini
[Unit]
Description=Liaotian Frontend Service (Next.js)
After=network.target liaotian-backend.service
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/saas-demo
Environment="PATH=/usr/bin:/bin"
Environment="NODE_ENV=production"
Environment="PORT=3000"

# 智能启动：优先使用 standalone 模式
ExecStart=/bin/bash -c 'if [ -d "/home/ubuntu/liaotian/saas-demo/.next/standalone" ]; then cd /home/ubuntu/liaotian/saas-demo/.next/standalone && PORT=3000 /usr/bin/node server.js; else cd /home/ubuntu/liaotian/saas-demo && /usr/bin/npm start; fi'

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
```

#### 3.2 创建后端服务文件

```bash
sudo nano /etc/systemd/system/liaotian-backend.service
```

复制以下内容：

```ini
[Unit]
Description=Liaotian Backend API Service (FastAPI)
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/admin-backend
Environment="PATH=/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-backend

[Install]
WantedBy=multi-user.target
```

#### 3.3 启用并启动服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 停止旧服务（如果正在运行）
sudo systemctl stop liaotian-frontend 2>/dev/null || true
sudo systemctl stop liaotian-backend 2>/dev/null || true

# 启用开机自启动
sudo systemctl enable liaotian-backend
sudo systemctl enable liaotian-frontend

# 启动服务
sudo systemctl start liaotian-backend
sleep 5
sudo systemctl start liaotian-frontend

# 检查状态
sudo systemctl status liaotian-backend
sudo systemctl status liaotian-frontend
```

---

## 📊 验证配置

### 1. 检查服务状态

```bash
# 检查 systemd 服务
sudo systemctl status liaotian-frontend
sudo systemctl status liaotian-backend

# 检查端口
ss -tlnp | grep :3000
ss -tlnp | grep :8000
ss -tlnp | grep :80
```

### 2. 检查 Nginx

```bash
# 检查 Nginx 状态
sudo systemctl status nginx

# 测试配置
sudo nginx -t

# 查看日志
sudo tail -f /var/log/nginx/liaotian-access.log
sudo tail -f /var/log/nginx/liaotian-error.log
```

### 3. 测试访问

```bash
# 从服务器本地测试
curl -s http://localhost/health
curl -s http://localhost/api/health
curl -s http://localhost/ | head -10

# 从外部访问（需要开放防火墙）
# 前端: http://165.154.233.55/
# 后端: http://165.154.233.55/api
# 文档: http://165.154.233.55/docs
```

---

## 🔧 常用管理命令

### Systemd 服务管理

```bash
# 查看服务状态
sudo systemctl status liaotian-frontend
sudo systemctl status liaotian-backend

# 启动服务
sudo systemctl start liaotian-frontend
sudo systemctl start liaotian-backend

# 停止服务
sudo systemctl stop liaotian-frontend
sudo systemctl stop liaotian-backend

# 重启服务
sudo systemctl restart liaotian-frontend
sudo systemctl restart liaotian-backend

# 查看日志
sudo journalctl -u liaotian-frontend -f
sudo journalctl -u liaotian-backend -f

# 查看最近 100 行日志
sudo journalctl -u liaotian-frontend -n 100
sudo journalctl -u liaotian-backend -n 100

# 禁用开机自启动
sudo systemctl disable liaotian-frontend
sudo systemctl disable liaotian-backend

# 启用开机自启动
sudo systemctl enable liaotian-frontend
sudo systemctl enable liaotian-backend
```

### Nginx 管理

```bash
# 测试配置
sudo nginx -t

# 重载配置（不中断服务）
sudo systemctl reload nginx

# 重启 Nginx
sudo systemctl restart nginx

# 停止 Nginx
sudo systemctl stop nginx

# 启动 Nginx
sudo systemctl start nginx

# 查看日志
sudo tail -f /var/log/nginx/liaotian-access.log
sudo tail -f /var/log/nginx/liaotian-error.log

# 查看错误日志
sudo tail -f /var/log/nginx/error.log
```

---

## 🔥 配置防火墙

### Ubuntu UFW

```bash
# 允许 HTTP (80)
sudo ufw allow 80/tcp

# 允许 HTTPS (443) - 如果配置了 SSL
sudo ufw allow 443/tcp

# 查看防火墙状态
sudo ufw status

# 启用防火墙（如果还没有）
sudo ufw enable
```

### 其他防火墙工具

如果使用其他防火墙，确保开放：
- **端口 80** (HTTP)
- **端口 443** (HTTPS，如果配置了 SSL)

---

## 🔒 配置 SSL 证书（可选，推荐）

### 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书（替换为你的域名）
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

配置完成后，Nginx 会自动：
- ✅ 将 HTTP 重定向到 HTTPS
- ✅ 使用 SSL 证书
- ✅ 配置安全头

---

## ❌ 故障排除

### 问题 1: 服务无法启动

**检查日志：**
```bash
sudo journalctl -u liaotian-frontend -n 50
sudo journalctl -u liaotian-backend -n 50
```

**常见原因：**
- 端口被占用
- 文件权限问题
- 依赖未安装

### 问题 2: Nginx 502 Bad Gateway

**检查：**
```bash
# 检查后端服务是否运行
sudo systemctl status liaotian-backend
curl http://localhost:8000/health

# 检查前端服务是否运行
sudo systemctl status liaotian-frontend
curl http://localhost:3000
```

**解决：**
- 确保后端和前端服务都在运行
- 检查防火墙设置
- 查看 Nginx 错误日志

### 问题 3: 端口冲突

**检查端口占用：**
```bash
sudo ss -tlnp | grep :3000
sudo ss -tlnp | grep :8000
sudo ss -tlnp | grep :80
```

**解决：**
```bash
# 停止占用端口的进程
sudo kill -9 <PID>
```

### 问题 4: 权限问题

```bash
# 检查文件权限
ls -la /home/ubuntu/liaotian/saas-demo
ls -la /home/ubuntu/liaotian/admin-backend

# 修复权限（如果需要）
sudo chown -R ubuntu:ubuntu /home/ubuntu/liaotian
```

---

## 📝 配置文件位置

### Nginx

- **配置文件**: `/etc/nginx/sites-available/liaotian`
- **启用链接**: `/etc/nginx/sites-enabled/liaotian`
- **访问日志**: `/var/log/nginx/liaotian-access.log`
- **错误日志**: `/var/log/nginx/liaotian-error.log`

### Systemd

- **前端服务**: `/etc/systemd/system/liaotian-frontend.service`
- **后端服务**: `/etc/systemd/system/liaotian-backend.service`
- **服务日志**: 使用 `journalctl` 查看

### 项目文件

- **项目目录**: `/home/ubuntu/liaotian`
- **前端目录**: `/home/ubuntu/liaotian/saas-demo`
- **后端目录**: `/home/ubuntu/liaotian/admin-backend`

---

## ✅ 配置完成检查清单

- [ ] Nginx 已安装并运行
- [ ] Nginx 配置已创建并启用
- [ ] Nginx 配置测试通过
- [ ] Systemd 前端服务文件已创建
- [ ] Systemd 后端服务文件已创建
- [ ] 服务已设置为开机自启动
- [ ] 前端服务运行正常
- [ ] 后端服务运行正常
- [ ] 端口 80 可以访问
- [ ] 防火墙已配置
- [ ] SSL 证书已配置（可选）

---

## 🎯 下一步

配置完成后：

1. ✅ **测试访问**: 从浏览器访问 `http://165.154.233.55/`
2. ✅ **配置域名**: 如果有域名，更新 Nginx 配置中的 `server_name`
3. ✅ **配置 SSL**: 使用 Let's Encrypt 配置 HTTPS
4. ✅ **监控服务**: 设置监控和告警

---

**最后更新**: 2025-12-07
