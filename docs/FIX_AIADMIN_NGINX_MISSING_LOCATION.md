# 修复 aiadmin.usdt2026.cc Nginx 配置缺少 location / 块

## 问题

Nginx 配置文件缺少 `location /` 块，导致前端页面无法正确代理。

当前配置只有：
- `location /_next/` - Next.js 静态资源
- `location /api/` - 后端 API

缺少：
- `location /` - 前端主页面

## 解决方案

执行修复脚本：

```bash
sudo bash scripts/server/fix_aiadmin_nginx_complete.sh
```

或者手动修复：

```bash
# 备份配置
sudo cp /etc/nginx/sites-available/aiadmin.usdt2026.cc /etc/nginx/sites-available/aiadmin.usdt2026.cc.backup

# 编辑配置文件
sudo nano /etc/nginx/sites-available/aiadmin.usdt2026.cc
```

在 `location /api/` 块之后添加：

```nginx
    # 前端主页面 (3007端口，管理后台前端)
    location / {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
```

然后：

```bash
# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

## 注意

如果你通过 HTTPS 访问，还需要添加 HTTPS 配置（listen 443）。

