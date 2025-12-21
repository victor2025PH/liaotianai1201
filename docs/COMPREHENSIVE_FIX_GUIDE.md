# 全面修复部署问题指南

> **问题**: 网站显示黑屏，无法正常访问

---

## 🚀 快速修复（一键解决所有问题）

### 方法 1: 使用全面修复脚本（推荐）

```bash
# SSH 到服务器
ssh ubuntu@<SERVER_HOST>

# 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 如果脚本不存在，先拉取代码
git stash
git pull origin main || git fetch origin main && git reset --hard origin/main

# 运行全面修复脚本
bash scripts/server/comprehensive-fix.sh
```

这个脚本会自动：
1. ✅ 修复 Git Pull 问题
2. ✅ 检查并安装 Node.js、PM2、serve
3. ✅ 清理、构建、部署三个网站
4. ✅ 配置 Nginx
5. ✅ 验证部署状态

---

## 📋 手动修复步骤（如果脚本失败）

### 步骤 1: 修复 Git Pull

```bash
cd /home/ubuntu/telegram-ai-system
git stash
git fetch origin main
git reset --hard origin/main
```

### 步骤 2: 检查环境

```bash
# 检查 Node.js
node -v
# 如果没有，安装: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs

# 检查 PM2
pm2 -v
# 如果没有，安装: sudo npm install -g pm2

# 检查 serve
which serve
# 如果没有，安装: sudo npm install -g serve
```

### 步骤 3: 部署单个网站（以 aizkw 为例）

```bash
cd /home/ubuntu/telegram-ai-system/aizkw20251219

# 清理
rm -rf node_modules/.cache dist

# 安装依赖
npm install --legacy-peer-deps

# 构建
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build

# 检查构建结果
ls -la dist/

# 停止旧进程
pm2 delete aizkw-frontend 2>/dev/null || true
sudo lsof -ti :3003 | xargs sudo kill -9 2>/dev/null || true

# 启动服务
pm2 start serve --name aizkw-frontend -- dist --listen 3003 --single
pm2 save

# 验证
sleep 5
curl http://127.0.0.1:3003
```

### 步骤 4: 配置 Nginx

```bash
# 创建 Nginx 配置
sudo nano /etc/nginx/sites-available/aikz.usdt2026.cc

# 内容：
server {
    listen 443 ssl http2;
    server_name aikz.usdt2026.cc;

    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

---

## 🔍 诊断问题

### 检查 PM2 进程

```bash
pm2 list
pm2 logs aizkw-frontend --lines 50
```

### 检查端口

```bash
sudo lsof -i :3001
sudo lsof -i :3002
sudo lsof -i :3003
```

### 检查构建输出

```bash
cd /home/ubuntu/telegram-ai-system/aizkw20251219
ls -la dist/
du -sh dist/
```

### 检查 Nginx 状态

```bash
sudo systemctl status nginx
sudo nginx -t
```

### 检查网站响应

```bash
# 本地测试
curl http://127.0.0.1:3001
curl http://127.0.0.1:3002
curl http://127.0.0.1:3003

# 通过域名测试
curl https://tgmini.usdt2026.cc
curl https://hongbao.usdt2026.cc
curl https://aikz.usdt2026.cc
```

---

## ⚠️ 常见问题

### 问题 1: 构建失败

**症状**: `npm run build` 失败

**解决**:
```bash
# 清理缓存
rm -rf node_modules/.cache dist

# 重新安装依赖
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps

# 增加内存限制
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### 问题 2: PM2 进程启动失败

**症状**: `pm2 start` 失败

**解决**:
```bash
# 查看日志
pm2 logs aizkw-frontend --lines 50

# 检查 dist 目录
ls -la dist/

# 手动测试 serve
cd /home/ubuntu/telegram-ai-system/aizkw20251219
serve dist -l 3003
```

### 问题 3: 端口被占用

**症状**: 端口无法监听

**解决**:
```bash
# 查找占用端口的进程
sudo lsof -i :3003

# 停止进程
sudo kill -9 <PID>

# 或强制停止所有占用端口的进程
sudo lsof -ti :3003 | xargs sudo kill -9
```

### 问题 4: Nginx 502 Bad Gateway

**症状**: 网站显示 502 错误

**解决**:
```bash
# 检查后端服务是否运行
pm2 list
curl http://127.0.0.1:3003

# 检查 Nginx 配置
sudo nginx -t
sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc

# 重启服务
pm2 restart aizkw-frontend
sudo systemctl restart nginx
```

### 问题 5: 网站显示黑屏

**症状**: 页面完全黑色，没有内容

**可能原因**:
1. 构建失败，dist 目录为空
2. PM2 服务未启动
3. Nginx 配置错误
4. 端口未监听

**解决**:
```bash
# 1. 检查构建
ls -la dist/
cat dist/index.html | head -20

# 2. 检查 PM2
pm2 list
pm2 logs aizkw-frontend

# 3. 检查端口
sudo lsof -i :3003

# 4. 检查 Nginx
sudo nginx -t
curl http://127.0.0.1:3003
```

---

## 🎯 完整修复流程

```bash
# 1. SSH 到服务器
ssh ubuntu@<SERVER_HOST>

# 2. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 3. 运行全面修复脚本
bash scripts/server/comprehensive-fix.sh

# 4. 如果脚本不存在，手动执行：
git stash
git fetch origin main
git reset --hard origin/main
bash scripts/server/comprehensive-fix.sh

# 5. 验证部署
pm2 list
curl http://127.0.0.1:3001
curl http://127.0.0.1:3002
curl http://127.0.0.1:3003
```

---

**最后更新**: 2025-12-21
