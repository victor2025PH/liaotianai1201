# Next.js 前端部署指南（Standalone 模式）

## 📋 概述

本文档提供在 Ubuntu 24.04 服务器上部署 Next.js 16.0.2 前端服务的完整流程，使用 standalone 模式以确保稳定运行。

## 🎯 目标

- Next.js 服务在 3000 端口正常运行
- 通过 Nginx 反向代理，访问 `http://aikz.usdt2026.cc` 能正常打开页面
- `/_next/static/chunks/*.js` 文件能返回 200

## 📦 前置要求

- Ubuntu 24.04 LTS
- Node.js v20.19.6（通过 nvm 安装）
- Nginx 已安装并配置
- 项目路径：`/home/ubuntu/telegram-ai-system/saas-demo`

## 🔧 步骤 1：检查项目配置

### 1.1 确认 next.config.ts

确保 `saas-demo/next.config.ts` 中启用了 standalone 模式：

```typescript
const nextConfig: NextConfig = {
  output: "standalone",  // 必须启用
  // ... 其他配置
};
```

### 1.2 确认 package.json

确保 `saas-demo/package.json` 中有以下脚本：

```json
{
  "scripts": {
    "build": "next build",
    "start": "next start -p 3000",
    "start:standalone": "NODE_ENV=production PORT=3000 node .next/standalone/server.js"
  }
}
```

## 🚀 步骤 2：部署服务

### 2.1 使用自动化脚本（推荐）

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/deploy-frontend-standalone.sh
```

### 2.2 手动部署

#### 2.2.1 进入项目目录

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo
```

#### 2.2.2 安装依赖

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20.19.6
npm install --production=false
```

#### 2.2.3 构建项目

```bash
npm run build
```

#### 2.2.4 检查构建结果

```bash
# 检查 standalone 文件
ls -la .next/standalone/server.js

# 检查 static 文件
ls -la .next/static/chunks | head -5

# 如果 standalone 中没有 static，需要复制
if [ ! -d ".next/standalone/.next/static" ]; then
  cp -r .next/static .next/standalone/.next/
fi
```

#### 2.2.5 安装 systemd 服务

```bash
# 复制服务文件
sudo cp deploy/systemd/liaotian-frontend.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable liaotian-frontend.service

# 启动服务
sudo systemctl start liaotian-frontend.service

# 检查状态
sudo systemctl status liaotian-frontend.service --no-pager -l
```

## 🔍 步骤 3：排查问题

### 3.1 如果服务被 Killed（status=9/KILL）

#### 检查 OOM 日志

```bash
# 查看内核日志
dmesg --ctime | grep -i -E 'killed process|out of memory' | tail -n 20

# 或使用 journalctl
journalctl -k -n 50 | grep -i -E 'killed process|out of memory'
```

#### 如果确认是 OOM

1. **检查内存使用**：
   ```bash
   free -h
   ps aux --sort=-%mem | head -10
   ```

2. **调整 NODE_OPTIONS**：
   编辑 `/etc/systemd/system/liaotian-frontend.service`，修改：
   ```ini
   Environment=NODE_OPTIONS=--max-old-space-size=1024
   ```
   然后：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart liaotian-frontend.service
   ```

3. **检查代码中的内存问题**：
   - 避免在启动时加载大量数据
   - 使用懒加载
   - 检查是否有内存泄漏

### 3.2 如果服务无法启动（status=127）

#### 检查 Node.js 路径

```bash
# 确认 Node.js 路径
which node
ls -la /home/ubuntu/.nvm/versions/node/v20.19.6/bin/node

# 如果路径不对，更新服务文件中的 ExecStart
```

#### 检查文件权限

```bash
# 确保 standalone 文件可执行
ls -la .next/standalone/server.js
chmod +x .next/standalone/server.js  # 如果需要
```

### 3.3 查看服务日志

```bash
# 实时查看日志
sudo journalctl -u liaotian-frontend.service -f

# 查看最近 50 条日志
sudo journalctl -u liaotian-frontend.service -n 50 --no-pager
```

## 🌐 步骤 4：配置 Nginx

### 4.1 确认 Nginx 配置

确保 `/etc/nginx/sites-available/aikz.conf` 或相应配置文件包含：

```nginx
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # 前端应用（所有请求，包括静态资源）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
    }

    # Next.js 静态资源（可选，用于缓存优化）
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000/_next/static/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4.2 测试并重载 Nginx

```bash
# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx
```

## ✅ 步骤 5：验证部署

### 5.1 检查服务状态

```bash
# 检查服务
sudo systemctl status liaotian-frontend.service --no-pager -l

# 检查端口
ss -tlnp | grep :3000

# 检查进程
ps aux | grep -E "node.*server.js" | grep -v grep
```

### 5.2 测试 HTTP 响应

```bash
# 测试根路径
curl -I http://127.0.0.1:3000/

# 测试静态资源
one_file=$(ls .next/static/chunks 2>/dev/null | head -n 1)
curl -I "http://127.0.0.1:3000/_next/static/chunks/$one_file"

# 测试域名访问
curl -I "http://aikz.usdt2026.cc/_next/static/chunks/$one_file"
```

### 5.3 浏览器验证

1. 打开浏览器访问 `http://aikz.usdt2026.cc`
2. 打开开发者工具（F12）
3. 检查 Console 标签，确认没有 `/_next/static/chunks/*.js` 404 错误
4. 检查 Network 标签，确认静态资源返回 200

## 📝 常用命令

### 服务管理

```bash
# 启动服务
sudo systemctl start liaotian-frontend.service

# 停止服务
sudo systemctl stop liaotian-frontend.service

# 重启服务
sudo systemctl restart liaotian-frontend.service

# 查看状态
sudo systemctl status liaotian-frontend.service

# 查看日志
sudo journalctl -u liaotian-frontend.service -f
```

### 重新部署

```bash
# 停止服务
sudo systemctl stop liaotian-frontend.service

# 进入项目目录
cd /home/ubuntu/telegram-ai-system/saas-demo

# 拉取最新代码（如果使用 Git）
git pull origin main

# 重新构建
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20.19.6
npm install --production=false
npm run build

# 复制 static 文件（如果需要）
if [ ! -d ".next/standalone/.next/static" ]; then
  cp -r .next/static .next/standalone/.next/
fi

# 启动服务
sudo systemctl start liaotian-frontend.service

# 检查状态
sudo systemctl status liaotian-frontend.service --no-pager -l
```

## 🔧 故障排查清单

- [ ] 服务状态是否为 `active (running)`？
- [ ] 端口 3000 是否在监听？
- [ ] `.next/standalone/server.js` 是否存在？
- [ ] `.next/static/chunks/` 目录是否有文件？
- [ ] standalone 目录中是否有 `.next/static/`？
- [ ] Node.js 路径是否正确？
- [ ] 服务日志中是否有错误？
- [ ] Nginx 配置是否正确？
- [ ] Nginx 是否已重载？
- [ ] 防火墙是否允许 3000 端口？

## 📚 相关文件

- 服务文件：`/etc/systemd/system/liaotian-frontend.service`
- 项目目录：`/home/ubuntu/telegram-ai-system/saas-demo`
- Nginx 配置：`/etc/nginx/sites-available/aikz.conf`
- 服务日志：`sudo journalctl -u liaotian-frontend.service`

## 🆘 获取帮助

如果遇到问题，请提供以下信息：

1. 服务状态：`sudo systemctl status liaotian-frontend.service --no-pager -l`
2. 最近日志：`sudo journalctl -u liaotian-frontend.service -n 50 --no-pager`
3. 端口监听：`ss -tlnp | grep :3000`
4. OOM 日志：`dmesg --ctime | grep -i killed | tail -20`

