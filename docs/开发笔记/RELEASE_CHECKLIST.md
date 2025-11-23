# 發布前檢查清單

本文檔提供完整的發布前檢查清單，確保系統穩定可靠。

---

## 後端檢查（admin-backend）

### 1. 單元測試

**測試文件**：`admin-backend/tests/test_api.py`

**執行命令**：
```bash
cd admin-backend
poetry run pytest tests/ -v
```

**預期結果**：
- ✅ 所有測試通過
- ✅ 測試覆蓋率 > 80%（可選）

**典型測試用例**：
- `test_health_check`：健康檢查端點
- `test_list_endpoints`：列表端點（accounts、activities、alerts）
- `test_create_command`：創建命令端點

### 2. API 測試

**執行命令**：
```bash
cd admin-backend
poetry run pytest tests/test_api.py -v
```

**檢查項目**：
- [ ] 所有 API 端點返回正確的狀態碼
- [ ] 響應數據結構符合預期
- [ ] 錯誤處理正確（4xx、5xx）

### 3. 數據庫遷移測試

**執行命令**：
```bash
# 使用測試數據庫
export DATABASE_URL="sqlite:///./test_admin.db"
python scripts/run_migrations.py
```

**檢查項目**：
- [ ] 遷移執行成功
- [ ] 遷移記錄正確寫入 `schema_migrations` 表
- [ ] 數據庫表結構正確

### 4. 環境變量檢查

**檢查命令**：
```bash
cd admin-backend
poetry run python -c "
from app.core.config import get_settings
s = get_settings()
assert s.jwt_secret != 'change_me', 'JWT_SECRET 必須修改'
assert s.admin_default_password != 'changeme123', 'ADMIN_DEFAULT_PASSWORD 必須修改'
print('✓ 環境變量檢查通過')
"
```

**檢查項目**：
- [ ] `JWT_SECRET` 已修改（生產環境）
- [ ] `ADMIN_DEFAULT_PASSWORD` 已修改（生產環境）
- [ ] `DATABASE_URL` 配置正確
- [ ] 所有必填環境變量已設置

---

## 前端檢查

### saas-demo（Next.js）

#### 1. 構建測試

**執行命令**：
```bash
cd saas-demo
npm run build
```

**檢查項目**：
- [ ] 構建成功，無錯誤
- [ ] 無 TypeScript 類型錯誤
- [ ] 無 ESLint 錯誤（或僅有可接受的警告）

#### 2. 生產構建驗證

**執行命令**：
```bash
cd saas-demo
npm run build
npm start
```

**檢查項目**：
- [ ] 生產構建正常啟動
- [ ] 所有頁面可正常訪問
- [ ] API 調用正常（或正確顯示 mock 數據提示）

#### 3. 環境變量檢查

**檢查項目**：
- [ ] `NEXT_PUBLIC_API_BASE_URL` 配置正確（生產環境）
- [ ] 無敏感信息硬編碼在代碼中

### admin-frontend（React + Vite）

#### 1. 構建測試

**執行命令**：
```bash
cd admin-frontend
npm run build
```

**檢查項目**：
- [ ] 構建成功，無錯誤
- [ ] 無 TypeScript 類型錯誤
- [ ] 無 ESLint 錯誤

#### 2. E2E 測試

**測試文件**：`admin-frontend/tests/e2e/dashboard.spec.ts`

**執行命令**：
```bash
cd admin-frontend
npm run test:e2e
```

**檢查項目**：
- [ ] 所有 E2E 測試通過
- [ ] Dashboard 頁面功能正常
- [ ] 頁面切換正常

#### 3. 環境變量檢查

**檢查項目**：
- [ ] `VITE_API_BASE_URL` 配置正確（生產環境）
- [ ] 構建時正確注入環境變量

---

## 腳本檢查

### 1. 數據庫遷移腳本

**腳本**：`scripts/run_migrations.py`

**測試命令**：
```bash
# 使用測試數據庫
export DATABASE_URL="sqlite:///./test_migration.db"
python scripts/run_migrations.py

# 驗證遷移結果
sqlite3 test_migration.db "SELECT * FROM schema_migrations;"
```

**檢查項目**：
- [ ] 遷移腳本執行成功
- [ ] 遷移記錄正確
- [ ] 數據庫備份正常

### 2. 會話管理工具

**工具**：`tools/session_manager/`

**測試命令**：
```bash
# 測試會話生成（如果可用）
python tools/session_manager/generate_session.py --help

# 測試會話導入（如果可用）
python tools/session_manager/import_sessions.py --help
```

**檢查項目**：
- [ ] 工具腳本可正常執行
- [ ] 幫助信息正確顯示
- [ ] 參數驗證正常

### 3. 對話場景編輯器

**工具**：`tools/dialogue_scene_editor.py`

**測試命令**：
```bash
python tools/dialogue_scene_editor.py --help
```

**檢查項目**：
- [ ] 工具可正常執行
- [ ] YAML 文件驗證正常

---

## 安全檢查

### 1. 環境變量安全

**檢查項目**：
- [ ] `.env` 文件已加入 `.gitignore`
- [ ] 無敏感信息提交到 Git
- [ ] 生產環境使用強密碼和隨機字符串

**檢查命令**：
```bash
# 檢查 .gitignore
grep -E "\.env|\.session" .gitignore

# 檢查 Git 歷史（不應包含敏感信息）
git log --all --full-history --source -- "*env*" | head -20
```

### 2. 認證與授權

**檢查項目**：
- [ ] 管理後台需要登錄（如果啟用認證）
- [ ] 管理員賬號權限與普通用戶隔離
- [ ] JWT Token 過期時間合理（建議 60 分鐘）

**測試步驟**：
```bash
# 1. 測試未認證訪問（如果啟用認證）
curl http://localhost:8000/api/v1/dashboard
# 預期：返回 401 或 403

# 2. 測試認證後訪問
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@example.com&password=changeme123" \
  | jq -r '.access_token')
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/dashboard
# 預期：返回 200 和數據
```

**注意**：當前認證已臨時禁用（`admin-backend/app/api/routes.py` 中註釋了 `dependencies=[Depends(get_current_active_user)]`），**生產環境必須啟用**！

### 3. API 安全

**檢查項目**：
- [ ] CORS 配置正確（生產環境應限制允許的域名）
- [ ] 無 SQL 注入風險（使用 ORM 參數化查詢）
- [ ] 無 XSS 風險（前端正確轉義用戶輸入）

**CORS 配置檢查**：
```python
# admin-backend/app/main.py
# 生產環境應修改為：
# allow_origins=["https://yourdomain.com"]
```

### 4. 數據安全

**檢查項目**：
- [ ] 數據庫連接使用強密碼
- [ ] 敏感數據（如會話文件）已加密
- [ ] 備份文件存儲安全

---

## 回滾策略

### 方法 1：Docker 鏡像回滾

**適用場景**：使用 Docker 部署

**回滾步驟**：

1. **停止當前容器**：
   ```bash
   docker compose -f deploy/docker-compose.yaml down
   ```

2. **切換到上一個版本標籤**：
   ```bash
   # 假設使用 Git 標籤管理版本
   git checkout v1.0.0  # 上一個穩定版本
   ```

3. **重新構建和啟動**：
   ```bash
   docker compose -f deploy/docker-compose.yaml build
   docker compose -f deploy/docker-compose.yaml up -d
   ```

4. **驗證回滾**：
   ```bash
   curl http://localhost:8000/health
   ```

### 方法 2：Git 代碼回滾

**適用場景**：直接部署代碼

**回滾步驟**：

1. **切換到上一個版本**：
   ```bash
   git checkout v1.0.0  # 或使用 commit hash
   ```

2. **恢復數據庫（如果需要）**：
   ```bash
   # 如果新版本有數據庫遷移，需要回滾
   # 使用備份恢復數據庫
   cp backup/db_bak/admin-YYYYMMDD-HHMMSS.db admin-backend/admin.db
   ```

3. **重啟服務**：
   ```bash
   # 後端
   cd admin-backend
   poetry run uvicorn app.main:app --reload
   
   # 前端
   cd saas-demo
   npm run dev
   ```

### 方法 3：數據庫遷移回滾

**適用場景**：僅數據庫結構變更有問題

**回滾步驟**：

1. **停止應用服務**

2. **恢復數據庫備份**：
   ```bash
   cp backup/db_bak/before-migrate-YYYYMMDD-HHMMSS.db admin-backend/admin.db
   ```

3. **刪除遷移記錄**：
   ```bash
   sqlite3 admin-backend/admin.db "DELETE FROM schema_migrations WHERE version = 'YYYYMMDD_description';"
   ```

4. **重啟應用服務**

---

## 發布流程

### 1. 發布前準備

- [ ] 所有檢查清單項目已完成
- [ ] 代碼已合併到主分支
- [ ] 版本號已更新
- [ ] 發布說明已準備

### 2. 構建和測試

- [ ] 後端單元測試通過
- [ ] 前端構建成功
- [ ] E2E 測試通過
- [ ] 數據庫遷移測試通過

### 3. 部署

- [ ] 備份當前版本和數據庫
- [ ] 執行數據庫遷移（如果需要）
- [ ] 部署新版本代碼
- [ ] 重啟服務

### 4. 驗證

- [ ] 健康檢查通過
- [ ] 主要功能正常
- [ ] 監控指標正常
- [ ] 無錯誤日誌

### 5. 監控

- [ ] 持續監控 30 分鐘
- [ ] 檢查錯誤率和響應時間
- [ ] 檢查系統資源使用
- [ ] 確認無異常告警

---

## 版本管理

### 版本號格式

建議使用語義化版本號：`MAJOR.MINOR.PATCH`

- `MAJOR`：不兼容的 API 變更
- `MINOR`：向後兼容的功能新增
- `PATCH`：向後兼容的問題修復

### Git 標籤

```bash
# 創建版本標籤
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

---

## 發布後檢查

### 24 小時內

- [ ] 錯誤率正常（< 5%）
- [ ] 響應時間正常（P95 < 2000ms）
- [ ] 無嚴重錯誤
- [ ] 用戶反饋正常

### 一週內

- [ ] 系統穩定性良好
- [ ] 性能指標正常
- [ ] 無安全問題
- [ ] 數據備份正常

---

**最後更新**: 2024-12-19

