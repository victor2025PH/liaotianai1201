# 部署指南

> **最後更新**: 2025-12-09  
> **適用版本**: v0.1.0

## 快速開始

### 前置要求

- Ubuntu 20.04+ 或類似 Linux 發行版
- Python 3.9+
- Node.js 20+
- Git
- Nginx
- PM2 (用於進程管理)

### 一鍵部署腳本

```bash
# 克隆倉庫
git clone https://github.com/victor2025PH/liaotianai1201.git
cd telegram-ai-system

# 運行部署腳本
bash scripts/server/deploy.sh
```

## 詳細部署步驟

### 1. 服務器準備

#### 安裝依賴

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Python 和 pip
sudo apt install -y python3 python3-pip python3-venv

# 安裝 Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 安裝 PM2
sudo npm install -g pm2

# 安裝 Nginx
sudo apt install -y nginx

# 安裝 Git
sudo apt install -y git
```

#### 配置 Swap 內存（可選，推薦）

```bash
# 創建 4GB swap 文件
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久啟用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 驗證
free -h
```

### 2. 代碼部署

#### 克隆倉庫

```bash
cd /home/ubuntu
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
cd telegram-ai-system
```

#### 配置環境變量

```bash
# 複製環境變量模板
cp admin-backend/.env.example admin-backend/.env

# 編輯環境變量
nano admin-backend/.env
```

**必須配置的環境變量**：

```env
# 數據庫
DATABASE_URL=sqlite:///./admin-backend/data/app.db

# JWT 安全
JWT_SECRET=your_strong_random_secret_here  # 必須修改！
ADMIN_DEFAULT_PASSWORD=your_secure_password  # 必須修改！

# CORS
CORS_ORIGINS=https://aikz.usdt2026.cc,https://your-domain.com

# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

### 3. 後端部署

#### 設置 Python 虛擬環境

```bash
cd admin-backend
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install --upgrade pip
pip install -r requirements.txt
```

#### 運行數據庫遷移

```bash
# 使用 Alembic
alembic upgrade head

# 或使用腳本
python -m scripts.run_migrations
```

#### 配置 PM2

創建 `ecosystem.config.js` 在項目根目錄：

```javascript
module.exports = {
  apps: [
    {
      name: "backend",
      script: "admin-backend/app/main.py",
      interpreter: "admin-backend/venv/bin/python",
      interpreter_args: "-m uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      env: {
        PYTHONPATH: "/home/ubuntu/telegram-ai-system/admin-backend",
      },
      error_file: "./logs/backend-error.log",
      out_file: "./logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      max_memory_restart: "1G",
    },
    {
      name: "frontend",
      script: "npm",
      args: "start",
      cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
      env: {
        NODE_ENV: "production",
        PORT: 3000,
      },
      error_file: "./logs/frontend-error.log",
      out_file: "./logs/frontend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      max_memory_restart: "500M",
    },
  ],
};
```

#### 啟動服務

```bash
# 啟動所有服務
pm2 start ecosystem.config.js

# 保存 PM2 配置
pm2 save

# 設置開機自啟
pm2 startup
```

### 4. 前端部署

#### 構建前端

```bash
cd saas-demo

# 安裝依賴
npm install

# 構建生產版本
npm run build
```

#### 啟動前端（已包含在 PM2 配置中）

前端服務已配置在 `ecosystem.config.js` 中，PM2 會自動管理。

### 5. Nginx 配置

創建 Nginx 配置文件 `/etc/nginx/sites-available/aikz.usdt2026.cc`：

```nginx
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aikz.usdt2026.cc;

    # SSL 證書配置（使用 Let's Encrypt）
    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;

    # SSL 優化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 前端代理
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 後端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # FastAPI 文檔
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # 靜態資源緩存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://127.0.0.1:3000;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

啟用配置：

```bash
sudo ln -s /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL 證書（Let's Encrypt）

```bash
# 安裝 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 獲取證書
sudo certbot --nginx -d aikz.usdt2026.cc

# 自動續期測試
sudo certbot renew --dry-run
```

## 自動化部署

### GitHub Actions

項目已配置 GitHub Actions 自動部署。當代碼推送到 `main` 分支時，會自動：

1. 拉取最新代碼
2. 更新依賴
3. 重啟服務

**配置 GitHub Secrets**：

- `SERVER_HOST`: 服務器 IP 地址
- `SERVER_USER`: SSH 用戶名（通常是 `ubuntu`）
- `SERVER_SSH_KEY`: SSH 私鑰

### 手動部署

```bash
# SSH 到服務器
ssh ubuntu@your-server-ip

# 進入項目目錄
cd /home/ubuntu/telegram-ai-system

# 拉取最新代碼
git pull origin main

# 更新後端依賴
cd admin-backend
source venv/bin/activate
pip install -r requirements.txt

# 運行數據庫遷移
alembic upgrade head

# 重啟服務
pm2 restart all
pm2 save
```

## 服務管理

### PM2 命令

```bash
# 查看服務狀態
pm2 status

# 查看日誌
pm2 logs backend
pm2 logs frontend

# 重啟服務
pm2 restart backend
pm2 restart frontend

# 停止服務
pm2 stop backend
pm2 stop frontend

# 刪除服務
pm2 delete backend
pm2 delete frontend
```

### 健康檢查

```bash
# 後端健康檢查
curl http://localhost:8000/health

# 前端健康檢查
curl http://localhost:3000

# 詳細健康檢查
curl http://localhost:8000/health?detailed=true
```

## 故障排除

### 後端服務無法啟動

1. 檢查 Python 虛擬環境是否激活
2. 檢查環境變量配置
3. 檢查數據庫連接
4. 查看 PM2 日誌：`pm2 logs backend`

### 前端服務無法啟動

1. 檢查 Node.js 版本：`node -v`（應為 20+）
2. 檢查構建是否成功：`cd saas-demo && npm run build`
3. 查看 PM2 日誌：`pm2 logs frontend`

### 502 Bad Gateway

1. 檢查後端服務是否運行：`pm2 status`
2. 檢查端口是否監聽：`ss -tlnp | grep :8000`
3. 檢查 Nginx 配置：`sudo nginx -t`
4. 查看 Nginx 錯誤日誌：`sudo tail -f /var/log/nginx/error.log`

### 數據庫問題

```bash
# 檢查數據庫文件
ls -lh admin-backend/data/app.db

# 運行數據庫遷移
cd admin-backend
source venv/bin/activate
alembic upgrade head

# 檢查數據庫版本
alembic current
```

## 性能優化

### 已實施的優化

1. **API 緩存**: 14個高頻端點已添加緩存
2. **數據庫索引**: 關鍵查詢已優化
3. **前端代碼分割**: 14個頁面已優化
4. **圖片優化**: Next.js 自動優化圖片
5. **靜態資源緩存**: Nginx 配置了30天緩存

### 監控

- **健康檢查**: `GET /health?detailed=true`
- **性能指標**: `GET /metrics` (Prometheus 格式)
- **緩存統計**: `GET /api/v1/system/performance/cache/stats`

## 安全建議

1. **修改默認密碼**: 必須修改 `ADMIN_DEFAULT_PASSWORD`
2. **使用強 JWT Secret**: 必須修改 `JWT_SECRET`
3. **配置 CORS**: 只允許信任的域名
4. **定期更新**: 保持依賴包最新
5. **備份數據**: 定期備份數據庫和配置文件

## 備份

### 自動備份

系統已配置自動備份服務，備份文件保存在 `admin-backend/backups/`。

### 手動備份

```bash
# 備份數據庫
cp admin-backend/data/app.db admin-backend/backups/app.db.$(date +%Y%m%d_%H%M%S)

# 備份配置文件
tar -czf backups/config_$(date +%Y%m%d_%H%M%S).tar.gz admin-backend/.env ecosystem.config.js
```

## 更新日誌

- **2025-12-09**: 添加 PM2 配置和自動化部署
- **2025-12-09**: 優化 Nginx 配置，添加靜態資源緩存
- **2025-12-09**: 完善健康檢查和監控功能

## 相關文檔

- [API 文檔](./API_DOCUMENTATION.md)
- [環境變量配置](./.env.example)
- [性能優化報告](./OPTIMIZATION_FINAL_STATUS.md)


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

