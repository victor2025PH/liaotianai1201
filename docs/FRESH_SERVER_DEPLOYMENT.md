# 全新服务器部署指南

## 📋 前置要求

- Ubuntu 20.04+ / 22.04 / 24.04
- Root 或 sudo 权限
- 域名已解析到服务器 IP
- 至少 2GB RAM，20GB 磁盘空间

## 🚀 快速部署

### 方法 1: 一键部署（推荐）

```bash
# 1. 登录服务器
ssh ubuntu@your-server-ip

# 2. 下载并执行部署脚本
cd /home/ubuntu
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
cd telegram-ai-system
chmod +x scripts/server/fresh-deploy-complete.sh
sudo bash scripts/server/fresh-deploy-complete.sh
```

### 方法 2: 分步部署

#### 步骤 1: 更新系统

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

#### 步骤 2: 安装依赖

```bash
sudo apt-get install -y \
    git curl wget build-essential \
    python3.12 python3.12-venv python3-pip \
    nodejs npm nginx sqlite3 \
    certbot python3-certbot-nginx \
    ufw fail2ban
```

#### 步骤 3: 配置防火墙

```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

#### 步骤 4: 克隆代码

```bash
cd /home/ubuntu
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
cd telegram-ai-system
```

#### 步骤 5: 安装后端依赖

```bash
cd admin-backend
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

#### 步骤 6: 安装前端依赖

```bash
cd ../saas-demo
npm install
```

#### 步骤 7: 配置环境变量

**后端环境变量** (`admin-backend/.env`):

```bash
nano admin-backend/.env
```

填入以下内容（修改密钥和密码）：

```env
APP_NAME=Smart TG Admin API
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=your-secret-key-here
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=your-secure-password
CORS_ORIGINS=https://your-domain.com
OPENAI_API_KEY=your-openai-api-key
```

**前端环境变量** (`saas-demo/.env.local`):

```bash
nano saas-demo/.env.local
```

填入以下内容：

```env
NEXT_PUBLIC_API_BASE_URL=https://your-domain.com/api/v1
NEXT_PUBLIC_GROUP_AI_API_BASE_URL=https://your-domain.com/api/v1/group-ai
NEXT_PUBLIC_WS_URL=wss://your-domain.com/api/v1/notifications/ws
NODE_ENV=production
```

#### 步骤 8: 初始化数据库

```bash
cd admin-backend
source venv/bin/activate
python3 -c "from app.db import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)"
deactivate
```

#### 步骤 9: 构建前端

```bash
cd ../saas-demo
npm run build
```

#### 步骤 10: 部署 Systemd 服务

使用项目提供的部署脚本：

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/deploy-systemd.sh
```

或手动创建服务文件（参考 `deploy/systemd/` 目录）

#### 步骤 11: 配置 Nginx

使用项目提供的 Nginx 配置脚本：

```bash
sudo bash scripts/server/reset-nginx-config.sh
```

#### 步骤 12: 配置 SSL 证书

```bash
sudo certbot --nginx -d your-domain.com
```

#### 步骤 13: 启动服务

```bash
sudo systemctl start luckyred-api
sudo systemctl start liaotian-frontend
sudo systemctl enable luckyred-api
sudo systemctl enable liaotian-frontend
```

## ✅ 验证部署

### 检查服务状态

```bash
sudo systemctl status luckyred-api
sudo systemctl status liaotian-frontend
```

### 检查端口

```bash
sudo ss -tlnp | grep -E '8000|3000'
```

### 测试 API

```bash
curl http://localhost:8000/health
```

### 测试前端

```bash
curl http://localhost:3000/login
```

### 测试 HTTPS

```bash
curl https://your-domain.com/login
```

## 🔒 安全配置

### 1. 修改默认密码

编辑 `admin-backend/.env`:

```env
ADMIN_DEFAULT_PASSWORD=your-strong-password-here
```

### 2. 配置 Fail2ban

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. 定期更新

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

## 🐛 故障排查

### 服务无法启动

```bash
# 查看服务日志
sudo journalctl -u luckyred-api -n 100 --no-pager
sudo journalctl -u liaotian-frontend -n 100 --no-pager

# 检查端口占用
sudo lsof -ti:8000
sudo lsof -ti:3000
```

### 构建失败

```bash
# 清理并重新构建
cd saas-demo
rm -rf .next node_modules
npm install
npm run build
```

### Nginx 502 错误

```bash
# 检查后端服务
sudo systemctl status luckyred-api

# 检查 Nginx 配置
sudo nginx -t

# 查看 Nginx 错误日志
sudo tail -50 /var/log/nginx/error.log
```

## 📝 重要文件位置

- 项目目录: `/home/ubuntu/telegram-ai-system`
- 后端配置: `/home/ubuntu/telegram-ai-system/admin-backend/.env`
- 前端配置: `/home/ubuntu/telegram-ai-system/saas-demo/.env.local`
- 数据库: `/home/ubuntu/telegram-ai-system/admin-backend/data/app.db`
- 后端服务: `/etc/systemd/system/luckyred-api.service`
- 前端服务: `/etc/systemd/system/liaotian-frontend.service`
- Nginx 配置: `/etc/nginx/sites-available/default`

## 🔄 更新代码

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main

# 更新后端依赖（如果需要）
cd admin-backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 更新前端依赖（如果需要）
cd ../saas-demo
npm install
npm run build

# 重启服务
sudo systemctl restart luckyred-api
sudo systemctl restart liaotian-frontend
```

## 📞 支持

如果遇到问题，请检查：
1. 服务日志: `sudo journalctl -u service-name -f`
2. Nginx 日志: `sudo tail -f /var/log/nginx/error.log`
3. 构建日志: 查看构建输出中的错误信息

