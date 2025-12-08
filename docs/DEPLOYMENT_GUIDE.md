# 部署指南

本文档提供完整的系统部署指南，包括环境准备、配置、部署步骤和故障排查。

## 目录

- [环境要求](#环境要求)
- [服务器准备](#服务器准备)
- [代码部署](#代码部署)
- [服务配置](#服务配置)
- [数据库迁移](#数据库迁移)
- [监控和日志](#监控和日志)
- [故障排查](#故障排查)

## 环境要求

### 服务器要求

- **操作系统**: Ubuntu 20.04+ / Debian 11+
- **CPU**: 2核心以上
- **内存**: 4GB以上（推荐8GB）
- **磁盘**: 20GB以上可用空间
- **网络**: 公网IP，开放80/443端口（HTTPS）和8000端口（API）

### 软件依赖

- **Python**: 3.10+
- **Node.js**: 18+
- **PostgreSQL**: 12+（可选，默认使用SQLite）
- **Nginx**: 最新稳定版
- **PM2**: 进程管理工具

## 服务器准备

### 1. 系统更新

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 安装基础软件

```bash
# 安装Python和pip
sudo apt install -y python3 python3-pip python3-venv

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 安装PM2
sudo npm install -g pm2

# 安装Nginx
sudo apt install -y nginx

# 安装Git
sudo apt install -y git
```

### 3. 创建项目目录

```bash
sudo mkdir -p /home/ubuntu/telegram-ai-system
sudo chown ubuntu:ubuntu /home/ubuntu/telegram-ai-system
cd /home/ubuntu/telegram-ai-system
```

## 代码部署

### 方法1: 从GitHub克隆（推荐）

```bash
cd /home/ubuntu/telegram-ai-system
git clone https://github.com/your-repo/telegram-ai-system.git .
```

### 方法2: 使用GitHub Actions自动部署

1. 配置GitHub Secrets:
   - `SERVER_HOST`: 服务器IP地址
   - `SERVER_USER`: SSH用户名（通常是`ubuntu`）
   - `SERVER_SSH_KEY`: SSH私钥

2. 推送到`main`分支，GitHub Actions会自动部署

### 3. 安装依赖

#### 后端依赖

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 前端依赖

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo
npm install
npm run build
```

## 服务配置

### 1. 环境变量配置

创建 `.env` 文件：

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
cp .env.example .env
nano .env
```

关键配置项：

```env
# 数据库
DATABASE_URL=sqlite:///./data/app.db
# 或 PostgreSQL: postgresql://user:password@localhost/dbname

# JWT密钥（必须修改！）
JWT_SECRET=your-strong-random-secret-key-here

# 管理员账号
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=your-secure-password

# CORS配置
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Telegram API（如果需要）
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# OpenAI API（如果需要AI功能）
OPENAI_API_KEY=your_openai_key
```

### 2. PM2配置

创建 `ecosystem.config.js`：

```javascript
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      script: "/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: { 
        PORT: 8000,
        PYTHONPATH: "/home/ubuntu/telegram-ai-system/admin-backend"
      },
      error_file: "./logs/backend-error.log",
      out_file: "./logs/backend-out.log",
      merge_logs: true
    },
    {
      name: "frontend",
      cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
      script: "npm",
      args: "start",
      env: { 
        PORT: 3000,
        NODE_ENV: "production"
      },
      error_file: "./logs/frontend-error.log",
      out_file: "./logs/frontend-out.log",
      merge_logs: true
    }
  ]
};
```

启动服务：

```bash
cd /home/ubuntu/telegram-ai-system
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # 设置开机自启
```

### 3. Nginx配置

创建配置文件 `/etc/nginx/sites-available/your-domain.com`：

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # FastAPI文档
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/your-domain.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 数据库迁移

### 运行迁移

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python -m alembic upgrade head
```

### 验证迁移

```bash
python -m alembic current
```

## 监控和日志

### PM2监控

```bash
# 查看服务状态
pm2 status

# 查看日志
pm2 logs backend
pm2 logs frontend

# 查看详细信息
pm2 describe backend
pm2 describe frontend
```

### 日志位置

- 后端日志: `/home/ubuntu/telegram-ai-system/admin-backend/logs/`
- 前端日志: `/home/ubuntu/telegram-ai-system/saas-demo/logs/`
- Nginx日志: `/var/log/nginx/`

### 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 前端健康检查
curl http://localhost:3000
```

## 故障排查

### 服务无法启动

1. 检查端口占用：
```bash
sudo lsof -i :8000
sudo lsof -i :3000
```

2. 检查日志：
```bash
pm2 logs backend --lines 50
pm2 logs frontend --lines 50
```

3. 检查环境变量：
```bash
cd admin-backend
source venv/bin/activate
python -c "from app.core.config import get_settings; print(get_settings())"
```

### 数据库连接失败

1. 检查数据库URL配置
2. 验证数据库服务是否运行
3. 检查网络连接和防火墙

### 前端502错误

1. 检查PM2服务状态
2. 检查Nginx配置
3. 查看Nginx错误日志：`sudo tail -f /var/log/nginx/error.log`

### 性能问题

1. 检查系统资源：
```bash
htop
df -h
```

2. 检查慢查询（如果使用PostgreSQL）：
```sql
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

3. 查看性能监控：
- 访问 `/performance` 页面
- 查看 `/api/v1/system/performance` API

## 安全建议

1. **修改默认密码**: 首次部署后立即修改管理员密码
2. **使用HTTPS**: 配置SSL证书
3. **防火墙配置**: 只开放必要端口
4. **定期备份**: 配置自动备份数据库和配置文件
5. **更新依赖**: 定期更新Python和Node.js依赖包

## 更新部署

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
cd admin-backend && source venv/bin/activate && pip install -r requirements.txt
cd ../saas-demo && npm install && npm run build
pm2 restart all
```

## 支持

如遇问题，请查看：
- [GitHub Issues](https://github.com/your-repo/telegram-ai-system/issues)
- [文档中心](./README.md)
- 系统日志文件

