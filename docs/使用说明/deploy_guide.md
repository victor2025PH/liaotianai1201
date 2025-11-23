# Session Interaction Service 部署指南

## 1. 環境需求
- **系統**：Linux (Ubuntu 20.04 以上) / macOS。若使用 Windows，建議 WSL2。
- **Python**：3.11+
- **Docker**：Docker Engine 24+、Docker Compose Plugin 2.20+、Buildx（GitHub Actions `docker/setup-buildx-action` 已內建）。
- **必要服務**：
  - Redis（事件佇列 / 快取，可選）
  - PostgreSQL 或 SQLite（帳號資料庫）
  - RabbitMQ（若採 MQ 方案）
- **工具**：git、Docker (可選)、systemd 或 process supervisor。

## 2. 專案結構摘要
- `session_service/`：Session 客戶端池、紅包事件處理等核心模組。
- `tools/session_manager/`：CLI 工具（Session 生成、匯入、帳號管理）。
- `admin-backend/`：FastAPI 管理後端，提供帳號、紅包活動與告警 API。
- `admin-frontend/`：React / Vite / Ant Design 介面，呼叫管理後端 API。
- `docs/`：開發文檔、測試與部署說明。
- `deploy/`：部署腳本與配置。

## 3. 部署方式

### 3.1 Docker （推薦）
1. 建立 `.env`，內容含：
   ```
   TELEGRAM_API_ID=...
   TELEGRAM_API_HASH=...
   REDIS_URL=redis://redis:6379/0
   DATABASE_URL=postgresql://user:password@postgres:5432/sis
   JWT_SECRET=change_me
   SESSION_SERVICE_URL=http://session-service:8001
   ```
2. 本地建構映像（CI 的 `Docker Build` job 亦會檢驗建置是否成功）：
   ```bash
   docker build -t session-suite/session-service:latest -f deploy/session-service.Dockerfile .
   docker build -t session-suite/admin-backend:latest -f admin-backend/Dockerfile admin-backend
   docker build -t session-suite/admin-frontend:latest -f admin-frontend/Dockerfile admin-frontend
   ```
3. 以 Docker Compose 啟動（可放置在 `deploy/docker-compose.yaml`）：
   ```bash
   docker compose -f deploy/docker-compose.yaml up -d
   ```
4. 透過 `docker compose logs -f <service>` 追蹤服務啟動狀態，或利用 `docker exec` 進入容器執行排錯指令。

### 3.2 systemd
1. 建立虛擬環境並安裝依賴：
   ```bash
   python -m venv /opt/sis/.venv
   source /opt/sis/.venv/bin/activate
   pip install -r requirements.txt
   ```
2. 建立執行腳本 `run_sis.sh`：
   ```bash
   #!/bin/bash
   source /opt/sis/.venv/bin/activate
   export PYTHONPATH=/opt/sis
   python session_service/run.py --config configs/prod.yaml
   ```
3. 撰寫 systemd service（`/etc/systemd/system/sis.service`）：
   ```
   [Unit]
   Description=Session Interaction Service
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/opt/sis
   ExecStart=/opt/sis/run_sis.sh
   Restart=on-failure
   RestartSec=5
   StandardOutput=journal
   StandardError=journal
   EnvironmentFile=/opt/sis/.env

   [Install]
   WantedBy=multi-user.target
   ```
4. 執行：
   ```bash
   systemctl daemon-reload
   systemctl enable --now sis
   journalctl -u sis -f
   ```

### 3.3 手動啟動（開發/PoC）
```bash
source .venv/bin/activate
python session_service/run.py --config configs/stage.yaml
```

### 3.4 Admin Backend / Frontend 容器化要點
- **後端**：`admin-backend/Dockerfile` 以 Python 3.11 slim + Poetry 建置，預設啟動 `uvicorn app.main:app` 於 8000 port，環境變數由 `.env` 提供。
- **前端**：`admin-frontend/Dockerfile` 以 Node 20 建構 Vite 靜態資產，再用 `nginx:alpine` 提供 80 port 服務，可透過 `VITE_API_BASE_URL` build arg 指定 API 來源。
- **CI**：`.github/workflows/ci.yml` 新增 `Docker Build` job，於測試全數通過後使用 Buildx 分別建構兩支映像，確保 Docker 配方始終可用。

## 4. 運維 SOP
1. **啟動 / 停止**
   - systemd：`systemctl start|stop sis`
   - Docker：`docker compose up/down`
2. **重新部署**
   - 拉取最新程式碼後：
     ```
     git pull
     pip install -r requirements.txt
     systemctl restart sis
     ```
3. **Session 帳號管理**
   - 使用 `tools/session_manager/generate_session.py` 生成，並以 `account_status.py --init` 初始化資料庫。
   - `account_status.py` 可查詢上下線狀態；遇到 session 失效時執行 CLI 重登。
4. **日誌與備份**
   - 主要日誌位於 `logs/session_service.log`
   - 設備故障或資料遺失時，從 `backup/` 恢復 `session_accounts.db`
5. **緊急回滾**
   - 保留上一版容器映像與程式碼標記。
   - 透過 `git checkout <tag>` 或切換 docker tag 回滾。
   - 若資料庫變更，確保有備份或使用 migration rollback。

## 5. Docker Compose 範例
以下為結合 Session 互動服務、管理後端與前端的參考設定，可依環境調整路徑與參數：

```yaml
version: "3.9"

services:
  session-service:
    build:
      context: ..
      dockerfile: deploy/session-service.Dockerfile
    env_file:
      - ../.env
    volumes:
      - ../sessions:/app/sessions
      - ../logs:/app/logs
      - ../configs:/app/configs
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

  admin-backend:
    build:
      context: ../admin-backend
      dockerfile: Dockerfile
    env_file:
      - ../.env
    environment:
      DATABASE_URL: ${DATABASE_URL:-sqlite:///./admin.db}
      REDIS_URL: ${REDIS_URL:-redis://redis:6379/0}
      SESSION_SERVICE_URL: http://session-service:8001
    depends_on:
      - session-service
      - redis
    ports:
      - "8000:8000"
    restart: unless-stopped

  admin-frontend:
    build:
      context: ../admin-frontend
      dockerfile: Dockerfile
      args:
        VITE_API_BASE_URL: http://admin-backend:8000/api/v1
    depends_on:
      - admin-backend
    ports:
      - "4173:80"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: sis
      POSTGRES_PASSWORD: change_me
      POSTGRES_DB: sis
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 6. 注意事項
- **安全**：Session 檔必須加密（`generate_session.py --encrypt`），避免未授權存取。
- **節流參數**：依實際運營情境調整 `config.py` 中的 rate limit，避免過度觸發 Telegram 風控。
- **監控**：部署後應搭配 Prometheus/Grafana 或其他監控方案（詳見 `docs/monitoring_guide.md`）。

---

此部署指南為 Week 4 的初版，可隨著實際環境驗證結果更新。 

