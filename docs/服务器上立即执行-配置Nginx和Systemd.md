# ⚡ 服务器上立即执行 - 配置 Nginx 和 Systemd

## 🎯 问题

脚本文件找不到，但我们可以直接在服务器上执行配置，不需要脚本文件！

## ✅ 方案 1: 直接执行配置（最简单）

在服务器上直接复制粘贴执行以下命令：

```bash
cd ~/liaotian

# 一键配置（复制整个命令块）
sudo bash -c '
echo "开始配置 Nginx 和 Systemd..."

# 1. 安装 Nginx
if ! command -v nginx &> /dev/null; then
    apt-get update
    apt-get install -y nginx
fi

# 2. 创建 Nginx 配置
cat > /etc/nginx/sites-available/liaotian << "EOFNGINX"
upstream frontend {
    server localhost:3000;
    keepalive 64;
}

upstream backend {
    server localhost:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name 165.154.233.55;
    client_max_body_size 50M;

    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }

    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }

    location /docs {
        proxy_pass http://backend/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    access_log /var/log/nginx/liaotian-access.log;
    error_log /var/log/nginx/liaotian-error.log;
}
EOFNGINX

# 3. 启用 Nginx 配置
ln -sf /etc/nginx/sites-available/liaotian /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 4. 创建前端 Systemd 服务
cat > /etc/systemd/system/liaotian-frontend.service << "EOFFRONTEND"
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
ExecStart=/bin/bash -c "if [ -d /home/ubuntu/liaotian/saas-demo/.next/standalone ]; then cd /home/ubuntu/liaotian/saas-demo/.next/standalone && PORT=3000 /usr/bin/node server.js; else cd /home/ubuntu/liaotian/saas-demo && /usr/bin/npm start; fi"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOFFRONTEND

# 5. 创建后端 Systemd 服务
cat > /etc/systemd/system/liaotian-backend.service << "EOFBACKEND"
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
EOFBACKEND

# 6. 重新加载 systemd
systemctl daemon-reload

# 7. 停止旧服务
systemctl stop liaotian-frontend 2>/dev/null || true
systemctl stop liaotian-backend 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 3

# 8. 启用开机自启动
systemctl enable liaotian-backend
systemctl enable liaotian-frontend

# 9. 启动服务
systemctl start liaotian-backend
sleep 5
systemctl start liaotian-frontend
sleep 5

echo ""
echo "✅ 配置完成！"
echo ""
echo "服务状态："
systemctl is-active liaotian-backend && echo "✅ 后端服务运行中" || echo "❌ 后端服务未运行"
systemctl is-active liaotian-frontend && echo "✅ 前端服务运行中" || echo "❌ 前端服务未运行"
echo ""
echo "访问地址："
echo "  前端: http://165.154.233.55/"
echo "  后端: http://165.154.233.55/api"
echo "  文档: http://165.154.233.55/docs"
'
```

---

## ✅ 方案 2: 先尝试从 GitHub 拉取

如果脚本文件已经推送，可以尝试：

```bash
cd ~/liaotian

# 强制同步所有文件
git fetch origin main
git reset --hard origin/main
git clean -fd

# 检查文件是否存在
ls -lh scripts/setup_nginx_and_systemd.sh

# 如果文件存在，执行
if [ -f "scripts/setup_nginx_and_systemd.sh" ]; then
    chmod +x scripts/setup_nginx_and_systemd.sh
    sudo bash scripts/setup_nginx_and_systemd.sh
else
    echo "脚本文件不存在，请使用方案 1"
fi
```

---

## ✅ 方案 3: 分步手动配置

如果想更清晰，可以分步执行：

### 步骤 1: 安装和配置 Nginx

```bash
sudo apt update
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/liaotian
```

然后粘贴 Nginx 配置内容（见方案 1），保存后：

```bash
sudo ln -s /etc/nginx/sites-available/liaotian /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 步骤 2: 创建 Systemd 服务

```bash
# 前端服务
sudo nano /etc/systemd/system/liaotian-frontend.service
# 粘贴前端服务配置

# 后端服务
sudo nano /etc/systemd/system/liaotian-backend.service
# 粘贴后端服务配置

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable liaotian-backend
sudo systemctl enable liaotian-frontend
sudo systemctl start liaotian-backend
sudo systemctl start liaotian-frontend
```

---

## 🔍 验证配置

配置完成后，验证：

```bash
# 检查服务状态
sudo systemctl status liaotian-frontend
sudo systemctl status liaotian-backend

# 检查端口
ss -tlnp | grep :80
ss -tlnp | grep :3000
ss -tlnp | grep :8000

# 测试访问
curl http://localhost/health
curl http://localhost/api/health
```

---

## 📝 推荐

**推荐使用方案 1**，它是最简单、最可靠的方法，不需要依赖 Git 文件同步。

---

**最后更新**: 2025-12-07
