# Nginx 配置修复指南

## 问题描述

执行 `bash scripts/configure_admin_nginx.sh` 时出现错误：
```
cannot load certificate "/etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem": 
No such file or directory
```

## 原因

Nginx 配置脚本尝试加载 SSL 证书，但证书文件不存在。

## 解决方案

### 方案 1: 使用修复后的脚本（推荐）

修复后的脚本会自动检测 SSL 证书：
- **如果证书存在**：配置 HTTPS（HTTP 自动跳转到 HTTPS）
- **如果证书不存在**：仅配置 HTTP

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/configure_admin_nginx.sh
```

### 方案 2: 手动配置 HTTP（临时方案）

如果暂时不需要 HTTPS，可以手动编辑 Nginx 配置：

```bash
sudo nano /etc/nginx/sites-available/aiadmin.usdt2026.cc
```

使用以下配置（仅 HTTP）：

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name aiadmin.usdt2026.cc;

    # 日志
    access_log /var/log/nginx/aiadmin-access.log;
    error_log /var/log/nginx/aiadmin-error.log;

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 管理后台前端代理
    location /admin {
        proxy_pass http://127.0.0.1:3006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 重写路径，移除 /admin 前缀
        rewrite ^/admin/?(.*) /$1 break;
    }

    # 根路径跳转到 /admin
    location = / {
        return 301 /admin;
    }
}
```

然后测试并重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 方案 3: 申请 SSL 证书（推荐用于生产环境）

如果需要 HTTPS，先申请 SSL 证书：

```bash
# 使用 Certbot 申请证书
sudo certbot certonly --nginx -d aiadmin.usdt2026.cc

# 然后重新运行配置脚本
bash scripts/configure_admin_nginx.sh
```

## 访问地址

### HTTP（无 SSL 证书）
- 管理后台: `http://aiadmin.usdt2026.cc/admin`
- 后端 API: `http://aiadmin.usdt2026.cc/api/v1/...`

### HTTPS（有 SSL 证书）
- 管理后台: `https://aiadmin.usdt2026.cc/admin`
- 后端 API: `https://aiadmin.usdt2026.cc/api/v1/...`

### 直接 IP 访问（不推荐，仅测试）
- 管理后台: `http://服务器IP:3006`
- 后端 API: `http://服务器IP:8000`

## 验证配置

```bash
# 测试 Nginx 配置
sudo nginx -t

# 检查 Nginx 状态
sudo systemctl status nginx

# 测试访问
curl http://aiadmin.usdt2026.cc/admin
curl http://aiadmin.usdt2026.cc/api/v1/ai-monitoring/summary?days=7
```

## 常见问题

### Q1: 配置后仍然无法访问

**检查**:
1. DNS 是否正确指向服务器 IP
2. 防火墙是否允许 80/443 端口
3. Nginx 是否正在运行

```bash
# 检查 DNS
nslookup aiadmin.usdt2026.cc

# 检查防火墙
sudo ufw status

# 检查 Nginx
sudo systemctl status nginx
```

### Q2: 如何添加 SSL 证书

```bash
# 安装 Certbot（如果未安装）
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d aiadmin.usdt2026.cc

# 重新运行配置脚本（会自动检测到证书）
bash scripts/configure_admin_nginx.sh
```

### Q3: 如何移除 /admin 路径前缀

如果需要直接通过 `https://aiadmin.usdt2026.cc` 访问（不带 `/admin`），可以修改 Nginx 配置：

```nginx
# 将 /admin 改为 /
location / {
    proxy_pass http://127.0.0.1:3006;
    # ... 其他配置
}
```

---

**最后更新**: 2025-12-24

