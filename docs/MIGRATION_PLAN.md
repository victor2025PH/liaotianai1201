# 网站迁移方案：分离到独立仓库和新服务器

## 📋 迁移概述

**目标**：将4个展示网站从当前服务器迁移到新服务器，并创建独立仓库。

**当前服务器**：165.154.242.60 (10.56.61.200)  
**目标服务器**：10.56.198.218  
**新仓库**：https://github.com/victor2025PH/web3

---

## 🎯 迁移范围

### 要迁移的网站（4个）

| 网站 | 域名 | 端口 | 目录路径 | PM2 名称 | 说明 |
|------|------|------|---------|---------|------|
| TON Mini App Studio | `tgmini.usdt2026.cc` | 3001 | `tgmini20251220/` | `tgmini-frontend` | ✅ 迁移 |
| RedEnvelope.fi | `hongbao.usdt2026.cc` | 3002 | `hbwy20251220/` | `hongbao-frontend` | ✅ 迁移 |
| Smart Control King | `aizkw.usdt2026.cc` | 3003 | `aizkw20251219/` | `aizkw-frontend` | ✅ 迁移 |
| 站点管理后台 | `aiadmin.usdt2026.cc/admin` | 3007 | `sites-admin-frontend/` | `sites-admin-frontend` | ✅ 迁移 |

### 保留在当前服务器的服务

| 服务 | 域名 | 端口 | 目录路径 | PM2 名称 | 说明 |
|------|------|------|---------|---------|------|
| 后端 API | `aiadmin.usdt2026.cc/api/` | 8000 | `admin-backend/` | `backend` | ❌ 保留 |
| 聊天 AI 后台 | `aikz.usdt2026.cc` | 3000 | `saas-demo/` | `saas-demo` | ❌ 保留 |
| 后端登录页面 | `aiadmin.usdt2026.cc/` | 8000 | `admin-backend/` | `backend` | ❌ 保留 |

---

## 📦 新仓库结构

### GitHub 仓库：https://github.com/victor2025PH/web3

```
web3/
├── README.md
├── .gitignore
├── .github/
│   └── workflows/
│       └── deploy.yml                    # 自动部署工作流
├── tgmini20251220/                      # TON Mini App Studio
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   └── dist/
├── hbwy20251220/                        # RedEnvelope.fi
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   └── dist/
├── aizkw20251219/                       # Smart Control King
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   └── dist/
├── sites-admin-frontend/                # 站点管理后台
│   ├── package.json
│   ├── vite.config.ts (或 next.config.js)
│   ├── src/
│   └── dist/ (或 .next/)
└── scripts/
    ├── deploy.sh                        # 部署脚本
    └── setup_server.sh                  # 服务器初始化脚本
```

---

## 🔄 迁移步骤

### 阶段 1：准备工作（在本地执行）

#### 1.1 创建新仓库并初始化

```bash
# 在本地创建新目录
mkdir web3-migration
cd web3-migration

# 初始化 Git 仓库
git init
git remote add origin https://github.com/victor2025PH/web3.git

# 创建基本结构
mkdir -p .github/workflows
mkdir scripts
```

#### 1.2 从当前仓库复制项目文件

```bash
# 假设当前仓库在 D:\telegram-ai-system
SOURCE_DIR="D:\telegram-ai-system"

# 复制 4 个项目目录
cp -r "$SOURCE_DIR/tgmini20251220" .
cp -r "$SOURCE_DIR/hbwy20251220" .
cp -r "$SOURCE_DIR/aizkw20251219" .
cp -r "$SOURCE_DIR/sites-admin-frontend" .
```

#### 1.3 创建必要的配置文件

**创建 `.gitignore`**：
```gitignore
# 依赖
node_modules/
.pnp
.pnp.js

# 构建输出
dist/
.next/
build/
out/

# 环境变量
.env
.env.local
.env*.local

# 日志
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# 系统文件
.DS_Store
Thumbs.db
```

**创建 `README.md`**：
```markdown
# Web3 展示网站

这个仓库包含 4 个展示网站：

1. **tgmini20251220/** - TON Mini App Studio (端口 3001)
2. **hbwy20251220/** - RedEnvelope.fi (端口 3002)
3. **aizkw20251219/** - Smart Control King (端口 3003)
4. **sites-admin-frontend/** - 站点管理后台 (端口 3007)

## 部署

部署到服务器：10.56.198.218

详见 `scripts/deploy.sh`
```

#### 1.4 创建部署脚本和 GitHub Actions

**创建 `scripts/deploy.sh`**：
- 安装依赖
- 构建项目
- 使用 PM2 启动服务
- 配置 Nginx

**创建 `.github/workflows/deploy.yml`**：
- 监听代码推送
- 在目标服务器执行部署脚本

#### 1.5 提交到新仓库

```bash
git add .
git commit -m "Initial commit: 迁移 4 个展示网站"
git branch -M main
git push -u origin main
```

---

### 阶段 2：新服务器准备（在服务器 10.56.198.218 执行）

#### 2.1 服务器环境准备

```bash
# SSH 连接到新服务器
ssh ubuntu@10.56.198.218

# 安装基础软件
sudo apt update
sudo apt install -y nginx nodejs npm pm2 certbot python3-certbot-nginx

# 创建项目目录
sudo mkdir -p /opt/web3-sites
sudo chown ubuntu:ubuntu /opt/web3-sites
cd /opt/web3-sites

# 克隆新仓库
git clone https://github.com/victor2025PH/web3.git .
```

#### 2.2 安装依赖和构建

```bash
# 为每个项目安装依赖
cd tgmini20251220 && npm install && cd ..
cd hbwy20251220 && npm install && cd ..
cd aizkw20251219 && npm install && cd ..
cd sites-admin-frontend && npm install && cd ..
```

#### 2.3 配置 PM2

```bash
# 创建 PM2 ecosystem 配置
# 启动所有服务
pm2 start npm --name tgmini-frontend --cwd /opt/web3-sites/tgmini20251220 -- start -- --port 3001
pm2 start npm --name hongbao-frontend --cwd /opt/web3-sites/hbwy20251220 -- start -- --port 3002
pm2 start npm --name aizkw-frontend --cwd /opt/web3-sites/aizkw20251219 -- start -- --port 3003
pm2 start npm --name sites-admin-frontend --cwd /opt/web3-sites/sites-admin-frontend -- start -- --port 3007

pm2 save
pm2 startup
```

#### 2.4 配置 SSL 证书

```bash
# 为 4 个域名申请 SSL 证书
sudo certbot --nginx -d tgmini.usdt2026.cc
sudo certbot --nginx -d hongbao.usdt2026.cc
sudo certbot --nginx -d aizkw.usdt2026.cc
sudo certbot --nginx -d aiadmin.usdt2026.cc  # 只为 /admin 路径使用
```

#### 2.5 配置 Nginx

为每个域名创建 Nginx 配置文件：

**`/etc/nginx/sites-available/tgmini.usdt2026.cc`**：
- 代理到 `127.0.0.1:3001`

**`/etc/nginx/sites-available/hongbao.usdt2026.cc`**：
- 代理到 `127.0.0.1:3002`

**`/etc/nginx/sites-available/aizkw.usdt2026.cc`**：
- 代理到 `127.0.0.1:3003`

**`/etc/nginx/sites-available/aiadmin.usdt2026.cc`**：
- `/admin` → `127.0.0.1:3007`（仅此路径）
- 其他路径（如 `/api/`, `/`）需要在旧服务器配置

---

### 阶段 3：DNS 配置更新

#### 3.1 更新 DNS 记录

将以下域名的 A 记录指向新服务器 IP：`10.56.198.218`

- `tgmini.usdt2026.cc` → `10.56.198.218`
- `hongbao.usdt2026.cc` → `10.56.198.218`
- `aizkw.usdt2026.cc` → `10.56.198.218`
- `aiadmin.usdt2026.cc` → **保持不变**（仍在旧服务器，但 `/admin` 路径需要特殊配置）

**注意**：`aiadmin.usdt2026.cc` 的 DNS 应该继续指向旧服务器（165.154.242.60），因为：
- 后端 API (`/api/`) 在旧服务器
- 只有 `/admin` 路径在新服务器

#### 3.2 配置跨服务器代理（可选方案）

由于 `aiadmin.usdt2026.cc` 需要同时访问：
- `/api/` → 旧服务器 8000
- `/admin` → 新服务器 3007

有两种方案：

**方案 A：旧服务器 Nginx 代理 `/admin` 到新服务器**
- 在旧服务器配置：`location /admin { proxy_pass http://10.56.198.218:3007; }`

**方案 B：新服务器处理 `/admin`，其他路径代理到旧服务器**
- DNS 指向新服务器
- 新服务器 Nginx：`/admin` → 本地 3007，`/api/` 和 `/` → 旧服务器

**推荐方案 A**：DNS 指向旧服务器，旧服务器负责路由。

---

### 阶段 4：数据迁移（如果需要）

#### 4.1 环境变量文件

检查每个项目是否有 `.env.local` 或 `.env` 文件：

```bash
# 在旧服务器上
find tgmini20251220 hbwy20251220 aizkw20251219 sites-admin-frontend -name ".env*" -type f

# 手动复制到新服务器（不提交到 Git）
# 使用 scp 或手动创建
```

#### 4.2 静态资源

如果有静态资源需要迁移：
- 图片、文件等
- 确保路径在新服务器上正确

---

### 阶段 5：验证和测试

#### 5.1 在新服务器上测试

```bash
# 测试端口监听
curl http://127.0.0.1:3001  # tgmini
curl http://127.0.0.1:3002  # hongbao
curl http://127.0.0.1:3003  # aizkw
curl http://127.0.0.1:3007  # sites-admin-frontend
```

#### 5.2 测试域名访问

```bash
# 在浏览器中访问
https://tgmini.usdt2026.cc
https://hongbao.usdt2026.cc
https://aizkw.usdt2026.cc
https://aiadmin.usdt2026.cc/admin
```

#### 5.3 测试跨服务器代理

```bash
# 测试 aiadmin.usdt2026.cc/admin（应该从旧服务器代理到新服务器）
curl -I https://aiadmin.usdt2026.cc/admin
```

---

### 阶段 6：旧服务器清理

#### 6.1 停止旧服务（在新服务器验证成功后）

```bash
# 在旧服务器上
pm2 stop tgmini-frontend
pm2 delete tgmini-frontend
pm2 stop hongbao-frontend
pm2 delete hongbao-frontend
pm2 stop aizkw-frontend
pm2 delete aizkw-frontend
pm2 stop sites-admin-frontend
pm2 delete sites-admin-frontend

pm2 save
```

#### 6.2 更新旧服务器 Nginx 配置

**`/etc/nginx/sites-available/aiadmin.usdt2026.cc`**：
```nginx
server {
    listen 443 ssl;
    server_name aiadmin.usdt2026.cc;
    
    # SSL 配置...
    
    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        # ... proxy 配置
    }
    
    # 管理后台 - 代理到新服务器
    location /admin {
        proxy_pass http://10.56.198.218:3007;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 根路径 - 后端登录页面
    location / {
        proxy_pass http://127.0.0.1:8000;
        # ... proxy 配置
    }
}
```

#### 6.3 删除旧服务器上的项目目录（可选）

```bash
# 在确认新服务器运行正常后
cd /home/ubuntu/telegram-ai-system
rm -rf tgmini20251220
rm -rf hbwy20251220
rm -rf aizkw20251219
rm -rf sites-admin-frontend
```

**注意**：建议先保留备份，确认迁移成功后再删除。

---

## ⚠️ 注意事项

### 1. DNS 传播时间

DNS 记录更新后，可能需要几分钟到几小时才能生效。在迁移期间，可以：

- 使用 `/etc/hosts` 临时测试
- 逐步迁移（先迁移一个网站测试）

### 2. SSL 证书

- 新服务器需要重新申请 SSL 证书
- 确保域名解析正确后再申请证书
- `aiadmin.usdt2026.cc` 的证书在旧服务器，`/admin` 路径需要特殊处理

### 3. 环境变量

- 检查每个项目是否有 `.env.local` 文件
- 这些文件不应该提交到 Git
- 需要手动在新服务器上创建

### 4. 端口冲突

- 确保新服务器上的端口 3001, 3002, 3003, 3007 未被占用
- 检查防火墙规则

### 5. 回滚计划

如果迁移失败，回滚步骤：

1. DNS 切回旧服务器 IP
2. 在旧服务器上恢复服务
3. 检查并修复问题后重新迁移

---

## 📝 执行清单

### 准备工作

- [ ] 创建新仓库并初始化
- [ ] 复制项目文件到新仓库
- [ ] 创建 `.gitignore` 和 `README.md`
- [ ] 创建部署脚本
- [ ] 创建 GitHub Actions 工作流
- [ ] 提交并推送到新仓库

### 新服务器配置

- [ ] SSH 连接新服务器
- [ ] 安装基础软件（Nginx, Node.js, PM2, Certbot）
- [ ] 创建项目目录并克隆仓库
- [ ] 为每个项目安装依赖
- [ ] 配置 PM2 启动服务
- [ ] 申请 SSL 证书
- [ ] 配置 Nginx
- [ ] 测试本地访问

### DNS 和网络

- [ ] 更新 DNS 记录（tgmini, hongbao, aizkw）
- [ ] 配置旧服务器的 `/admin` 代理（如果需要）
- [ ] 测试域名访问

### 验证

- [ ] 测试所有 4 个网站可访问
- [ ] 测试 SSL 证书正常
- [ ] 测试跨服务器代理（aiadmin.usdt2026.cc/admin）
- [ ] 检查日志无错误

### 清理

- [ ] 停止旧服务器上的服务
- [ ] 更新旧服务器 Nginx 配置
- [ ] （可选）删除旧服务器上的项目目录

---

## 🔗 相关链接

- 新仓库：https://github.com/victor2025PH/web3
- 旧仓库：https://github.com/victor2025PH/liaotianai1201
- 新服务器：10.56.198.218
- 旧服务器：165.154.242.60 (10.56.61.200)

---

## 📞 支持

如有问题，请检查：
1. Nginx 错误日志：`sudo tail -f /var/log/nginx/error.log`
2. PM2 日志：`pm2 logs`
3. 服务状态：`pm2 status`
4. 端口监听：`sudo lsof -i :3001`（检查各个端口）

