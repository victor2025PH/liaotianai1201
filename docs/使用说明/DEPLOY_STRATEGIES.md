# 部署策略文檔

本文檔說明不同的部署方案和推薦策略。

---

## 部署方案對比

### 方案 1：單機部署（推薦用於開發/測試）

**適用場景**：
- 開發環境
- 測試環境
- 小規模生產環境（< 100 用戶）

**特點**：
- 所有服務運行在同一台服務器
- 使用 Docker Compose 統一管理
- 配置簡單，維護方便

**優點**：
- ✅ 部署簡單，一鍵啟動
- ✅ 資源共享，成本低
- ✅ 網絡延遲低（服務間通信快）

**缺點**：
- ❌ 單點故障風險
- ❌ 擴展性有限
- ❌ 資源競爭（CPU、內存）

### 方案 2：多服務分離部署（推薦用於生產）

**適用場景**：
- 生產環境
- 大規模部署（> 100 用戶）
- 需要高可用性

**特點**：
- 每個服務獨立容器/服務器
- 服務間通過網絡通信
- 可以獨立擴展和維護

**優點**：
- ✅ 高可用性（單個服務故障不影響整體）
- ✅ 可獨立擴展（按需增加實例）
- ✅ 資源隔離（避免相互影響）

**缺點**：
- ❌ 部署複雜（需要管理多個服務）
- ❌ 網絡配置複雜（需要服務發現）
- ❌ 成本較高（需要更多資源）

---

## 單機部署（Docker Compose）

### 配置文件

**位置**：`deploy/docker-compose.yaml`

### 啟動步驟

#### 1. 準備環境變量

創建 `.env` 文件（項目根目錄）：

```env
# 數據庫
DATABASE_URL=postgresql://sis:change_me@postgres:5432/sis
REDIS_URL=redis://redis:6379/0

# 認證
JWT_SECRET=your_strong_random_secret_here
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=your_strong_password_here

# 外部服務
SESSION_SERVICE_URL=http://session-service:8001
REDPACKET_SERVICE_URL=http://redpacket-service:8002
MONITORING_SERVICE_URL=http://monitoring-service:8003

# Telegram
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_SESSION_NAME=your_session_name

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
```

#### 2. 構建 Docker 鏡像

```bash
# 構建所有服務鏡像
docker build -t session-suite/session-service:latest -f deploy/session-service.Dockerfile .
docker build -t session-suite/admin-backend:latest -f admin-backend/Dockerfile admin-backend
docker build -t session-suite/admin-frontend:latest -f admin-frontend/Dockerfile admin-frontend
docker build -t session-suite/saas-demo:latest -f saas-demo/Dockerfile saas-demo
```

#### 3. 啟動服務

```bash
cd deploy
docker compose up -d
```

#### 4. 檢查服務狀態

```bash
# 查看所有服務狀態
docker compose ps

# 查看服務日誌
docker compose logs -f admin-backend
docker compose logs -f saas-demo
```

### 暴露端口

| 服務 | 容器端口 | 主機端口 | 說明 |
|------|---------|---------|------|
| admin-backend | 8000 | 8000 | FastAPI 後端 API |
| saas-demo | 3000 | 3000 | Next.js 前端控制台 |
| admin-frontend | 80 | 4173 | React 前端（Nginx） |
| redis | 6379 | 6379 | Redis 緩存/隊列 |
| postgres | 5432 | 5432 | PostgreSQL 數據庫 |

**訪問地址**：
- 後端 API：http://localhost:8000
- Next.js 前端：http://localhost:3000
- React 前端：http://localhost:4173
- API 文檔：http://localhost:8000/docs

---

## 多服務分離部署

### 架構圖

```
┌─────────────────┐
│   Load Balancer  │
│   (Nginx/Traefik)│
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Frontend│ │Frontend│
│(Next.js)│ │(React) │
└───┬───┘ └──┬────┘
    │        │
    └───┬────┘
        │
   ┌────▼────┐
   │  Backend │
   │ (FastAPI)│
   └────┬────┘
        │
   ┌────┴────┐
   │         │
┌──▼──┐  ┌──▼──┐
│Redis│  │Postgres│
└─────┘  └──────┘
```

### 部署步驟

#### 1. 後端服務（admin-backend）

```bash
# 構建鏡像
docker build -t session-suite/admin-backend:v1.0.0 -f admin-backend/Dockerfile admin-backend

# 推送到鏡像倉庫（可選）
docker tag session-suite/admin-backend:v1.0.0 registry.example.com/admin-backend:v1.0.0
docker push registry.example.com/admin-backend:v1.0.0

# 部署（使用 Kubernetes 或 Docker Swarm）
# 示例：Kubernetes
kubectl apply -f k8s/admin-backend-deployment.yaml
```

#### 2. 前端服務（saas-demo）

```bash
# 構建鏡像
docker build -t session-suite/saas-demo:v1.0.0 -f saas-demo/Dockerfile saas-demo

# 部署
kubectl apply -f k8s/saas-demo-deployment.yaml
```

#### 3. 數據庫服務

```bash
# 使用託管數據庫（推薦）
# 或部署 PostgreSQL 容器
kubectl apply -f k8s/postgres-deployment.yaml
```

#### 4. 負載均衡器

```bash
# 配置 Nginx 或 Traefik
# 轉發請求到對應服務
```

---

## 本地開發環境一鍵啟動

### 使用 Docker Compose

**配置文件**：`deploy/docker-compose.yaml`

**啟動命令**：
```bash
cd deploy
docker compose up -d
```

**停止命令**：
```bash
docker compose down
```

**查看日誌**：
```bash
docker compose logs -f
```

### 手動啟動（開發模式）

#### 後端

```bash
cd admin-backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

#### 前端（Next.js）

```bash
cd saas-demo
npm install
npm run dev
```

#### 前端（React）

```bash
cd admin-frontend
npm install
npm run dev
```

---

## CI/CD 集成

### GitHub Actions 工作流示例

**文件位置**：`.github/workflows/deploy.yml`（需要創建）

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: pip install poetry
      
      - name: Install dependencies
        working-directory: admin-backend
        run: poetry install
      
      - name: Run tests
        working-directory: admin-backend
        run: poetry run pytest tests/ -v
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install frontend dependencies
        working-directory: saas-demo
        run: npm ci
      
      - name: Build frontend
        working-directory: saas-demo
        run: npm run build
      
      - name: Run E2E tests
        working-directory: admin-frontend
        run: |
          npm ci
          npm run test:e2e

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push admin-backend
        uses: docker/build-push-action@v5
        with:
          context: admin-backend
          file: admin-backend/Dockerfile
          push: true
          tags: |
            session-suite/admin-backend:latest
            session-suite/admin-backend:${{ github.sha }}
      
      - name: Build and push saas-demo
        uses: docker/build-push-action@v5
        with:
          context: saas-demo
          file: saas-demo/Dockerfile
          push: true
          tags: |
            session-suite/saas-demo:latest
            session-suite/saas-demo:${{ github.sha }}
      
      - name: Build and push admin-frontend
        uses: docker/build-push-action@v5
        with:
          context: admin-frontend
          file: admin-frontend/Dockerfile
          push: true
          tags: |
            session-suite/admin-frontend:latest
            session-suite/admin-frontend:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # TODO: 實現部署邏輯
          # 例如：SSH 到服務器執行 docker compose pull && docker compose up -d
          echo "Deploy to production server"
```

### 工作流階段

1. **測試階段**：
   - 後端單元測試
   - 前端構建測試
   - E2E 測試

2. **構建階段**：
   - 構建 Docker 鏡像
   - 推送到鏡像倉庫

3. **部署階段**：
   - 拉取最新鏡像
   - 重啟服務
   - 健康檢查

---

## 環境配置

### 開發環境

**特點**：
- 使用 SQLite 數據庫（無需額外服務）
- 熱重載啟用（`--reload`）
- 詳細日誌輸出
- Mock 數據 Fallback 啟用

**配置**：
```env
DATABASE_URL=sqlite:///./admin.db
REDIS_URL=redis://localhost:6379/0
```

### 測試環境

**特點**：
- 使用 PostgreSQL 數據庫
- 完整測試數據
- 告警規則測試

**配置**：
```env
DATABASE_URL=postgresql://test:test@test-db:5432/test_db
REDIS_URL=redis://test-redis:6379/0
```

### 生產環境

**特點**：
- 使用 PostgreSQL 數據庫（高可用）
- 強密碼和隨機字符串
- 完整監控和告警
- 備份策略

**配置**：
```env
DATABASE_URL=postgresql://prod_user:strong_password@prod-db:5432/prod_db
JWT_SECRET=strong_random_secret_32_chars_minimum
ADMIN_DEFAULT_PASSWORD=strong_password_here
```

---

## 擴展性考慮

### 水平擴展

**後端服務**：
- 可以部署多個 `admin-backend` 實例
- 使用負載均衡器分發請求
- 共享數據庫和 Redis

**前端服務**：
- 可以部署多個前端實例
- 使用 CDN 加速靜態資源

### 垂直擴展

- 增加服務器 CPU 和內存
- 優化數據庫查詢
- 使用緩存減少數據庫負載

---

## 監控和日誌

### 日誌收集

**推薦方案**：
- 使用 Docker 日誌驅動（`json-file` 或 `syslog`）
- 集成 ELK Stack（Elasticsearch、Logstash、Kibana）
- 或使用雲服務（如 AWS CloudWatch、GCP Cloud Logging）

### 監控指標

**推薦方案**：
- Prometheus + Grafana
- 或使用雲服務（如 AWS CloudWatch、GCP Cloud Monitoring）

**配置文件**：`admin-backend/prometheus.yml`

---

## 安全建議

### 1. 網絡安全

- 使用 HTTPS（生產環境）
- 配置防火牆規則
- 限制管理端口訪問（僅內網）

### 2. 容器安全

- 使用非 root 用戶運行容器
- 定期更新基礎鏡像
- 掃描鏡像漏洞

### 3. 數據安全

- 數據庫連接使用強密碼
- 敏感數據加密存儲
- 定期備份數據

---

## 故障恢復

### 1. 服務故障

**自動恢復**：
- 使用 `restart: unless-stopped`（Docker Compose）
- 或使用 Kubernetes 的 `restartPolicy: Always`

**手動恢復**：
```bash
# 重啟服務
docker compose restart admin-backend

# 或重新部署
docker compose up -d --force-recreate admin-backend
```

### 2. 數據庫故障

**恢復步驟**：
1. 停止應用服務
2. 恢復數據庫備份
3. 重啟應用服務

---

**最後更新**: 2024-12-19

