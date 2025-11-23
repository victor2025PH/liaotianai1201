# 部署指南

> **更新日期**: 2024-12-19

---

## 部署概述

本文檔說明如何將 Telegram 群組 AI 系統部署到生產環境。

---

## 環境要求

### 服務器要求

- **操作系統**: Linux (Ubuntu 20.04+ 推薦) 或 Windows Server
- **CPU**: 2+ 核心
- **內存**: 4GB+ (建議 8GB)
- **存儲**: 20GB+ 可用空間
- **網絡**: 穩定的互聯網連接

### 軟件要求

- Python 3.9+
- Node.js 18+
- PostgreSQL 12+ (或 SQLite 用於小型部署)
- Nginx (可選，用於反向代理)

---

## 部署方式

### 方式 1: Docker 部署（推薦）

#### 1. 創建 Dockerfile

**後端 Dockerfile** (`admin-backend/Dockerfile`):
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile** (`saas-demo/Dockerfile`):
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./

CMD ["npm", "start"]
```

#### 2. 創建 docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: group_ai
      POSTGRES_USER: group_ai
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./admin-backend
    environment:
      DATABASE_URL: postgresql://group_ai:${DB_PASSWORD}@db:5432/group_ai
      TELEGRAM_API_ID: ${TELEGRAM_API_ID}
      TELEGRAM_API_HASH: ${TELEGRAM_API_HASH}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./sessions:/app/sessions
      - ./ai_models:/app/ai_models
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build: ./saas-demo
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

#### 3. 啟動服務

```bash
docker-compose up -d
```

### 方式 2: 傳統部署

#### 1. 後端部署

```bash
# 1. 安裝依賴
cd admin-backend
pip install -r requirements.txt

# 2. 配置環境變量
cp .env.example .env
# 編輯 .env 文件

# 3. 初始化數據庫
alembic upgrade head

# 4. 使用 systemd 管理服務
sudo systemctl enable group-ai-backend
sudo systemctl start group-ai-backend
```

**systemd 服務文件** (`/etc/systemd/system/group-ai-backend.service`):
```ini
[Unit]
Description=Group AI Backend
After=network.target

[Service]
Type=simple
User=groupai
WorkingDirectory=/opt/group-ai/admin-backend
Environment="PATH=/opt/group-ai/venv/bin"
ExecStart=/opt/group-ai/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 2. 前端部署

```bash
# 1. 構建生產版本
cd saas-demo
npm run build

# 2. 使用 PM2 管理
pm2 start npm --name "group-ai-frontend" -- start
pm2 save
```

### 方式 3: 雲服務部署

#### AWS / Azure / GCP

1. **後端**: 使用雲服務器的容器服務（ECS, AKS, GKE）
2. **前端**: 使用靜態網站託管（S3, Blob Storage, Cloud Storage）
3. **數據庫**: 使用託管數據庫服務（RDS, Azure Database, Cloud SQL）

---

<a id="env-vars"></a>
## 配置說明

### 環境變量

**後端** (`.env`):
```env
# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# OpenAI API
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-3.5-turbo

# 數據庫
DATABASE_URL=postgresql://user:password@localhost:5432/group_ai

# 日誌
LOG_LEVEL=INFO
LOG_FILE=/var/log/group-ai/backend.log

# 安全
SECRET_KEY=your_secret_key
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

**前端** (`.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Nginx 配置（可選）

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 後端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 安全建議

1. **使用 HTTPS**
   - 配置 SSL 證書
   - 強制 HTTPS 重定向

2. **環境變量保護**
   - 不要將 `.env` 文件提交到版本控制
   - 使用密鑰管理服務

3. **數據庫安全**
   - 使用強密碼
   - 限制數據庫訪問
   - 定期備份

4. **API 安全**
   - 實現認證和授權
   - 使用 API 密鑰
   - 實現速率限制

5. **日誌管理**
   - 不要記錄敏感信息
   - 定期清理日誌
   - 監控異常活動

---

## 監控和維護

### 日誌監控

```bash
# 後端日誌
tail -f /var/log/group-ai/backend.log

# 前端日誌
pm2 logs group-ai-frontend
```

<a id="verify"></a>
### 健康檢查

```bash
# 檢查後端
curl http://localhost:8000/health

# 檢查前端
curl http://localhost:3000
```

### 驗證步驟

1. **驗證服務狀態**:
   ```bash
   # 檢查後端健康狀態
   curl http://localhost:8000/health?detailed=true
   
   # 檢查前端
   curl http://localhost:3000
   ```

2. **驗證 API 端點**:
   ```bash
   # 測試 API 文檔
   curl http://localhost:8000/docs
   
   # 測試 API 端點
   curl http://localhost:8000/api/v1/
   ```

3. **驗證數據庫連接**:
   ```bash
   # 檢查數據庫健康狀態
   curl http://localhost:8000/health?detailed=true | jq '.components.database'
   ```

4. **驗證 Session 文件**:
   ```bash
   # 使用驗證腳本
   python3 scripts/verify_session.py account1
   ```

5. **驗證監控指標**:
   ```bash
   # 檢查 Prometheus 指標
   curl http://localhost:8000/metrics
   ```

### 備份

```bash
# 數據庫備份
pg_dump group_ai > backup_$(date +%Y%m%d).sql

# Session 文件備份
tar -czf sessions_backup_$(date +%Y%m%d).tar.gz sessions/
```

---

## 故障排除

### 常見問題

1. **服務無法啟動**
   - 檢查端口是否被佔用
   - 檢查環境變量配置
   - 查看日誌文件

2. **數據庫連接失敗**
   - 檢查數據庫服務是否運行
   - 驗證連接字符串
   - 檢查防火牆設置

3. **Session 文件無效**
   - 檢查文件路徑
   - 驗證文件權限
   - 重新生成 Session

---

## 性能優化

1. **數據庫優化**
   - 添加索引
   - 定期清理舊數據
   - 使用連接池

2. **緩存**
   - 使用 Redis 緩存
   - 緩存劇本解析結果
   - 緩存賬號狀態

3. **負載均衡**
   - 使用多個後端實例
   - 配置負載均衡器

---

## 更新和升級

```bash
# 1. 備份當前版本
# 2. 拉取最新代碼
git pull

# 3. 更新依賴
pip install -r requirements.txt
npm install

# 4. 運行數據庫遷移
alembic upgrade head

# 5. 重啟服務
systemctl restart group-ai-backend
pm2 restart group-ai-frontend
```

---

**狀態**: ✅ 部署指南完成

