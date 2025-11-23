# 健康檢查與自檢流程

本文檔說明如何檢查系統健康狀態，以及完整的自檢流程。

---

## 後端健康檢查端點

### admin-backend（端口 8000）

#### 基礎健康檢查

| 端點 | 方法 | 說明 | 預期響應 |
|------|------|------|---------|
| `/health` | GET | 基礎健康檢查 | `{"status": "ok"}` |
| `/api/v1/dashboard` | GET | Dashboard 數據（間接健康檢查） | `DashboardData` JSON |

**測試命令**：
```bash
# 基礎健康檢查
curl http://localhost:8000/health

# Dashboard 數據檢查
curl http://localhost:8000/api/v1/dashboard
```

#### API 端點健康檢查

| 端點 | 方法 | 說明 | 預期狀態碼 |
|------|------|------|-----------|
| `/api/v1/metrics` | GET | 指標數據 | 200 |
| `/api/v1/sessions` | GET | 會話列表 | 200 |
| `/api/v1/logs` | GET | 日誌列表 | 200 |
| `/api/v1/system/monitor` | GET | 系統監控數據 | 200 |
| `/api/v1/settings/alerts` | GET | 告警設置 | 200 |

---

## 前端健康檢查

### saas-demo（Next.js，端口 3000）

**健康檢查方式**：
1. 訪問 `http://localhost:3000`，檢查頁面是否正常加載
2. 檢查瀏覽器控制台是否有錯誤
3. 檢查 Network 面板，確認 API 請求是否成功

**預期行為**：
- 頁面正常渲染，顯示 Dashboard
- 如果後端不可用，會自動切換到 Mock 數據並顯示提示
- 不會出現白屏或崩潰

### admin-frontend（Vite + React，端口 5173）

**健康檢查方式**：
1. 訪問 `http://localhost:5173`，檢查頁面是否正常加載
2. 檢查瀏覽器控制台是否有錯誤
3. 檢查 Network 面板，確認 API 請求是否成功

**預期行為**：
- 頁面正常渲染，顯示 Dashboard
- API 請求返回 200 狀態碼
- 不會出現白屏或崩潰

---

## 完整自檢流程

### 階段 1：後端啟動檢查

#### 1.1 檢查後端服務是否運行

```bash
# 檢查端口 8000 是否被佔用
# Windows
netstat -ano | findstr :8000

# Linux/macOS
lsof -i :8000
```

#### 1.2 測試健康檢查端點

```bash
# 基礎健康檢查
curl http://localhost:8000/health

# 預期響應：
# {"status":"ok"}
```

#### 1.3 測試主要 API 端點

```bash
# Dashboard API
curl http://localhost:8000/api/v1/dashboard

# Metrics API
curl http://localhost:8000/api/v1/metrics

# Sessions API
curl http://localhost:8000/api/v1/sessions?page=1&page_size=10

# Logs API
curl http://localhost:8000/api/v1/logs?page=1&page_size=10

# System Monitor API
curl http://localhost:8000/api/v1/system/monitor

# Alert Settings API
curl http://localhost:8000/api/v1/settings/alerts
```

**預期結果**：
- 所有端點返回 200 狀態碼
- 返回有效的 JSON 數據
- 沒有 500 錯誤

#### 1.4 檢查數據庫連接

```bash
# 如果使用 SQLite，檢查文件是否存在
ls -la admin-backend/admin.db

# 如果使用 PostgreSQL，測試連接
psql $DATABASE_URL -c "SELECT 1;"
```

### 階段 2：前端啟動檢查

#### 2.1 檢查前端服務是否運行

```bash
# 檢查端口 3000（saas-demo）
# Windows
netstat -ano | findstr :3000

# Linux/macOS
lsof -i :3000

# 檢查端口 5173（admin-frontend）
# Windows
netstat -ano | findstr :5173

# Linux/macOS
lsof -i :5173
```

#### 2.2 測試 saas-demo 頁面

**訪問以下 URL，檢查頁面是否正常加載**：

| URL | 預期內容 |
|-----|---------|
| `http://localhost:3000/` | Dashboard 總覽頁面，顯示統計卡片、圖表、會話列表 |
| `http://localhost:3000/sessions` | 會話列表頁面，顯示表格和分頁 |
| `http://localhost:3000/logs` | 日誌中心頁面，顯示日誌列表 |
| `http://localhost:3000/monitoring` | 系統監控頁面，顯示系統健康狀態和資源使用情況 |
| `http://localhost:3000/settings/alerts` | 告警設置頁面，顯示表單和規則列表 |

**檢查點**：
- [ ] 頁面正常渲染，無白屏
- [ ] 統計卡片顯示數據（或 Skeleton 加載狀態）
- [ ] 圖表正常顯示（或顯示「暫無數據」）
- [ ] 表格正常顯示（或顯示空狀態）
- [ ] 如果後端不可用，顯示 Mock 數據提示

#### 2.3 測試 admin-frontend 頁面

**訪問以下 URL，檢查頁面是否正常加載**：

| URL | 預期內容 |
|-----|---------|
| `http://localhost:5173/` | Dashboard 頁面 |
| `http://localhost:5173/accounts` | 賬戶管理頁面 |
| `http://localhost:5173/activities` | 活動記錄頁面 |
| `http://localhost:5173/alerts` | 告警管理頁面 |
| `http://localhost:5173/commands` | 命令管理頁面 |
| `http://localhost:5173/settings` | 設置頁面 |

**檢查點**：
- [ ] 頁面正常渲染，無白屏
- [ ] 側邊欄導航正常
- [ ] API 請求返回 200 狀態碼
- [ ] 數據正常顯示

### 階段 3：端到端功能檢查

#### 3.1 會話列表功能

1. 訪問 `http://localhost:3000/sessions`
2. 檢查：
   - [ ] 會話列表正常顯示
   - [ ] 分頁功能正常
   - [ ] 搜索功能正常（輸入關鍵詞）
   - [ ] 時間範圍篩選正常
   - [ ] 點擊會話詳情按鈕，Dialog 正常打開

#### 3.2 日誌中心功能

1. 訪問 `http://localhost:3000/logs`
2. 檢查：
   - [ ] 日誌列表正常顯示
   - [ ] 級別過濾正常（error/warning/info）
   - [ ] 搜索功能正常
   - [ ] 點擊日誌行，詳情 Dialog 正常打開

#### 3.3 告警設置功能

1. 訪問 `http://localhost:3000/settings/alerts`
2. 檢查：
   - [ ] 表單正常加載
   - [ ] 修改閾值後點擊「保存」，顯示成功 Toast
   - [ ] 告警規則列表正常顯示
   - [ ] 啟用/禁用規則功能正常

#### 3.4 系統監控功能

1. 訪問 `http://localhost:3000/monitoring`
2. 檢查：
   - [ ] 系統健康狀態正常顯示
   - [ ] 資源使用情況（CPU/內存/磁盤）正常顯示
   - [ ] 服務狀態正常顯示
   - [ ] 刷新按鈕功能正常

---

## 一鍵檢查命令

### Bash 腳本示例

```bash
#!/bin/bash

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== 後端健康檢查 ==="

# 檢查後端健康端點
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✓ 後端健康檢查通過${NC}"
else
    echo -e "${RED}✗ 後端健康檢查失敗${NC}"
    exit 1
fi

# 檢查 Dashboard API
if curl -s http://localhost:8000/api/v1/dashboard | grep -q "stats"; then
    echo -e "${GREEN}✓ Dashboard API 正常${NC}"
else
    echo -e "${YELLOW}⚠ Dashboard API 可能異常（檢查響應）${NC}"
fi

# 檢查 Metrics API
if curl -s http://localhost:8000/api/v1/metrics | grep -q "response_time"; then
    echo -e "${GREEN}✓ Metrics API 正常${NC}"
else
    echo -e "${YELLOW}⚠ Metrics API 可能異常（檢查響應）${NC}"
fi

# 檢查 Sessions API
if curl -s "http://localhost:8000/api/v1/sessions?page=1&page_size=10" | grep -q "items"; then
    echo -e "${GREEN}✓ Sessions API 正常${NC}"
else
    echo -e "${YELLOW}⚠ Sessions API 可能異常（檢查響應）${NC}"
fi

# 檢查 Logs API
if curl -s "http://localhost:8000/api/v1/logs?page=1&page_size=10" | grep -q "items"; then
    echo -e "${GREEN}✓ Logs API 正常${NC}"
else
    echo -e "${YELLOW}⚠ Logs API 可能異常（檢查響應）${NC}"
fi

# 檢查 System Monitor API
if curl -s http://localhost:8000/api/v1/system/monitor | grep -q "health"; then
    echo -e "${GREEN}✓ System Monitor API 正常${NC}"
else
    echo -e "${YELLOW}⚠ System Monitor API 可能異常（檢查響應）${NC}"
fi

echo ""
echo "=== 前端健康檢查 ==="

# 檢查 saas-demo（Next.js）
if curl -s http://localhost:3000 | grep -q "<!DOCTYPE html"; then
    echo -e "${GREEN}✓ saas-demo 前端正常運行${NC}"
else
    echo -e "${RED}✗ saas-demo 前端未運行或異常${NC}"
fi

# 檢查 admin-frontend（Vite）
if curl -s http://localhost:5173 | grep -q "<!DOCTYPE html"; then
    echo -e "${GREEN}✓ admin-frontend 前端正常運行${NC}"
else
    echo -e "${YELLOW}⚠ admin-frontend 前端未運行（可選）${NC}"
fi

echo ""
echo "=== 檢查完成 ==="
```

### PowerShell 腳本示例（Windows）

```powershell
# 後端健康檢查
Write-Host "=== 後端健康檢查 ===" -ForegroundColor Cyan

$healthCheck = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
if ($healthCheck.StatusCode -eq 200 -and $healthCheck.Content -like '*"status":"ok"*') {
    Write-Host "✓ 後端健康檢查通過" -ForegroundColor Green
} else {
    Write-Host "✗ 後端健康檢查失敗" -ForegroundColor Red
    exit 1
}

# 檢查 Dashboard API
$dashboard = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/dashboard" -UseBasicParsing
if ($dashboard.StatusCode -eq 200) {
    Write-Host "✓ Dashboard API 正常" -ForegroundColor Green
} else {
    Write-Host "⚠ Dashboard API 異常" -ForegroundColor Yellow
}

# 檢查 Metrics API
$metrics = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/metrics" -UseBasicParsing
if ($metrics.StatusCode -eq 200) {
    Write-Host "✓ Metrics API 正常" -ForegroundColor Green
} else {
    Write-Host "⚠ Metrics API 異常" -ForegroundColor Yellow
}

# 前端健康檢查
Write-Host "`n=== 前端健康檢查 ===" -ForegroundColor Cyan

$saasDemo = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
if ($saasDemo.StatusCode -eq 200) {
    Write-Host "✓ saas-demo 前端正常運行" -ForegroundColor Green
} else {
    Write-Host "✗ saas-demo 前端未運行或異常" -ForegroundColor Red
}

Write-Host "`n=== 檢查完成 ===" -ForegroundColor Cyan
```

---

## 瀏覽器檢查清單

### saas-demo（http://localhost:3000）

#### Dashboard 頁面（/）
- [ ] 頁面正常加載，無白屏
- [ ] 6 個統計卡片正常顯示（或顯示 Skeleton）
- [ ] 響應時間趨勢圖正常顯示（或顯示「暫無數據」）
- [ ] 系統狀態卡片正常顯示（或顯示空狀態）
- [ ] 最近 10 條會話列表正常顯示（或顯示空狀態）
- [ ] 最近錯誤與警告列表正常顯示（或顯示空狀態）
- [ ] 如果後端不可用，顯示黃色 Alert 提示「當前展示的是模擬數據」

#### 會話列表頁面（/sessions）
- [ ] 會話表格正常顯示
- [ ] 分頁控件正常
- [ ] 搜索框功能正常
- [ ] 時間範圍篩選正常
- [ ] 點擊「查看詳情」按鈕，Dialog 正常打開

#### 日誌中心頁面（/logs）
- [ ] 日誌表格正常顯示
- [ ] 級別過濾正常（error/warning/info）
- [ ] 搜索功能正常
- [ ] 點擊日誌行，詳情 Dialog 正常打開

#### 系統監控頁面（/monitoring）
- [ ] 系統健康狀態正常顯示
- [ ] 資源使用情況（CPU/內存/磁盤）正常顯示
- [ ] 服務狀態正常顯示
- [ ] 刷新按鈕功能正常

#### 告警設置頁面（/settings/alerts）
- [ ] 表單正常加載
- [ ] 告警規則列表正常顯示
- [ ] 保存功能正常（顯示 Toast）
- [ ] 啟用/禁用規則功能正常

### admin-frontend（http://localhost:5173）

#### Dashboard 頁面
- [ ] 頁面正常加載
- [ ] 側邊欄導航正常
- [ ] API 請求返回 200
- [ ] 數據正常顯示

---

## 常見問題排查

### 問題 1：後端返回 500 錯誤

**排查步驟**：
1. 檢查後端日誌：`docker compose logs admin-backend` 或直接查看終端輸出
2. 檢查數據庫連接：確認 `DATABASE_URL` 正確
3. 檢查 Redis 連接：確認 `REDIS_URL` 正確
4. 檢查外部服務：確認 `SESSION_SERVICE_URL` 等配置正確

### 問題 2：前端無法連接到後端

**排查步驟**：
1. 確認後端服務正在運行（端口 8000）
2. 檢查 `NEXT_PUBLIC_API_BASE_URL` 或 `VITE_API_BASE_URL` 是否正確
3. 檢查瀏覽器控制台的 Network 面板，查看具體錯誤
4. 檢查 CORS 配置（`admin-backend/app/main.py`）

### 問題 3：前端顯示 Mock 數據

**說明**：這是正常行為，表示後端不可用時自動降級。

**排查步驟**：
1. 確認後端服務是否運行
2. 檢查 API 基礎地址配置
3. 如果後端正常，檢查網絡連接

### 問題 4：頁面白屏或崩潰

**排查步驟**：
1. 打開瀏覽器開發者工具，查看 Console 錯誤
2. 檢查是否有 JavaScript 錯誤
3. 檢查是否有 TypeScript 類型錯誤（構建時）
4. 檢查是否有組件渲染錯誤（查看 ErrorBoundary）

---

## 自動化健康檢查（CI/CD）

### GitHub Actions 示例

```yaml
- name: 後端健康檢查
  run: |
    curl -f http://localhost:8000/health || exit 1
    curl -f http://localhost:8000/api/v1/dashboard || exit 1

- name: 前端構建檢查
  run: |
    cd saas-demo
    npm run build
    cd ../admin-frontend
    npm run build
```

---

**最後更新**: 2024-12-19
