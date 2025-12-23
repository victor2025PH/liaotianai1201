# 系統端口與文件夾關係整理報告

**生成時間**: 2025-12-24  
**目的**: 分析並整理管理後台系統的端口、文件夾、網站之間的關係

---

## 📊 當前配置關係總覽

### 1. 文件夾與服務對應表

| 文件夾 | 服務名稱 | 端口 | PM2 進程名 | 網站路徑 | 狀態 |
|--------|---------|------|-----------|---------|------|
| `admin-backend/` | 後端 API | **8000** | `backend` / `luckyred-api` | `/api/` | ✅ 正常 |
| `admin-frontend/` | 管理後台前端 | **3006** | `admin-frontend` | - | ⚠️ **端口衝突** |
| `sites-admin-frontend/` | 三個展示網站管理後台 | **3007** | `sites-admin-frontend` | `/admin` | ✅ 正常 |
| `ai-monitor-frontend/` | AI 監控系統 | **3006** | `ai-monitor-frontend` | `/ai-monitor` | ⚠️ **端口衝突** |
| `saas-demo/` | SaaS 演示前端 | **3000** | `next-server` | `/` (aikz.usdt2026.cc) | ✅ 正常 |

### 2. 域名配置總覽

#### 主要管理後台域名: `aiadmin.usdt2026.cc`

| Nginx 路徑 | 代理到端口 | 對應服務 | 文件夾 |
|-----------|-----------|---------|--------|
| `/api/` | 8000 | 後端 API | `admin-backend/` |
| `/admin` | 3007 | 站點管理後台 | `sites-admin-frontend/` |
| `/ai-monitor` | 3006 | AI 監控系統 | `ai-monitor-frontend/` |

#### 其他展示網站域名

| 域名 | 路徑 | 端口 | 文件夾 | 服務 |
|------|------|------|--------|------|
| `aikz.usdt2026.cc` | `/` | 3000 | `saas-demo/` | SaaS 前端 |
| `tgmini.usdt2026.cc` | `/` | 3001 | `tgmini20251220/` | TON Mini App |
| `hongbao.usdt2026.cc` | `/` | 3002 | `hbwy20251220/` | RedEnvelope |
| `aizkw.usdt2026.cc` | `/` | 3003 | `aizkw20251219/` | Smart Control King |

---

## ⚠️ 發現的問題

### 問題 1: 端口衝突（嚴重）

**衝突詳情**:
- `admin-frontend/` 使用端口 **3006**
- `ai-monitor-frontend/` 也使用端口 **3006**

**影響**:
- 兩個服務無法同時運行
- 只能啟動其中一個服務
- 造成部署和運維混亂

### 問題 2: 配置不一致

**不一致點**:
1. `docs/ADMIN_FRONTEND_DEPLOYMENT.md` 文檔顯示 `admin-frontend` 使用 3006
2. 但實際 Nginx 配置中 `/admin` 指向 3007（對應 `sites-admin-frontend`）
3. `admin-frontend` 的實際用途和部署位置不明確

### 問題 3: 文件夾缺失

- 代碼庫中**未找到** `ai-monitor-frontend/` 文件夾
- 但部署腳本 `deploy_ai_monitor.sh` 引用此文件夾
- 可能導致部署失敗

---

## 🔍 詳細分析

### Nginx 配置分析

**配置文件**: `/etc/nginx/sites-available/aiadmin.usdt2026.cc`

**當前配置**:
```nginx
# 後端 API
location /api/ {
    proxy_pass http://127.0.0.1:8000;  # admin-backend
}

# AI 監控系統前端
location /ai-monitor {
    proxy_pass http://127.0.0.1:3006;  # ai-monitor-frontend
    rewrite ^/ai-monitor/?(.*) /$1 break;
}

# 站點管理後台前端
location /admin {
    proxy_pass http://127.0.0.1:3007;  # sites-admin-frontend
    rewrite ^/admin/?(.*) /$1 break;
}
```

**結論**:
- Nginx 期望 `/admin` → 3007（sites-admin-frontend）✅
- Nginx 期望 `/ai-monitor` → 3006（ai-monitor-frontend）✅
- 但 `admin-frontend` 也在使用 3006，造成衝突 ❌

### 部署腳本分析

| 腳本 | 文件夾 | 端口 | PM2 名稱 | 狀態 |
|------|--------|------|---------|------|
| `deploy_admin_frontend.sh` | `admin-frontend/` | 3006 | `admin-frontend` | ⚠️ 與 ai-monitor 衝突 |
| `deploy_sites_admin.sh` | `sites-admin-frontend/` | 3007 | `sites-admin-frontend` | ✅ 正常 |
| `deploy_ai_monitor.sh` | `ai-monitor-frontend/` | 3006 | `ai-monitor-frontend` | ⚠️ 與 admin-frontend 衝突 |

---

## 💡 推薦解決方案

### 方案: 重新分配端口（推薦）

**端口重新分配**:

| 服務 | 原端口 | 新端口 | 理由 |
|------|--------|--------|------|
| `admin-frontend/` | 3006 | **3008** | 避免衝突，保留 3006 給 ai-monitor |
| `ai-monitor-frontend/` | 3006 | **3006** | 保持不變，與 Nginx 配置一致 |
| `sites-admin-frontend/` | 3007 | **3007** | 保持不變，與 Nginx 配置一致 |

**優點**:
- 最小化對現有配置的影響
- 保持 Nginx 配置不變
- 僅調整 `admin-frontend` 一個服務

---

## 📋 修改方案執行步驟

### 步驟 1: 執行自動修復腳本

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/fix_admin_frontend_port.sh
```

此腳本會自動:
1. 備份相關文件
2. 修改 `deploy_admin_frontend.sh` 端口為 3008
3. 更新檢查和驗證腳本
4. 更新文檔

### 步驟 2: 手動驗證修改

```bash
# 檢查是否還有衝突引用
grep -r "admin-frontend.*3006\|3006.*admin-frontend" scripts/ docs/

# 應該沒有結果（除了備份文件）

# 檢查新端口引用
grep -r "admin-frontend.*3008\|3008.*admin-frontend" scripts/ docs/
```

### 步驟 3: 重新部署服務（如果需要）

```bash
# 如果 admin-frontend 正在運行，停止舊服務
pm2 delete admin-frontend 2>/dev/null || true

# 使用新端口重新部署
bash scripts/deploy_admin_frontend.sh
```

### 步驟 4: 驗證服務

```bash
# 檢查端口占用
sudo lsof -i :3008

# 測試服務
curl http://127.0.0.1:3008

# 檢查 PM2 進程
pm2 list | grep admin-frontend
```

---

## ✅ 修復後的預期配置

### 最終端口分配表

| 端口 | 服務 | 文件夾 | Nginx 路徑 | PM2 名稱 | 狀態 |
|------|------|--------|-----------|---------|------|
| 3000 | SaaS Demo | `saas-demo/` | `/` (aikz.usdt2026.cc) | `next-server` | ✅ |
| 3001 | TON Mini App | `tgmini20251220/` | `/` (tgmini.usdt2026.cc) | `tgmini-frontend` | ✅ |
| 3002 | RedEnvelope | `hbwy20251220/` | `/` (hongbao.usdt2026.cc) | `hongbao-frontend` | ✅ |
| 3003 | Smart Control King | `aizkw20251219/` | `/` (aizkw.usdt2026.cc) | `aizkw-frontend` | ✅ |
| 3006 | AI 監控系統 | `ai-monitor-frontend/` | `/ai-monitor` | `ai-monitor-frontend` | ✅ |
| 3007 | 站點管理後台 | `sites-admin-frontend/` | `/admin` | `sites-admin-frontend` | ✅ |
| 3008 | 管理後台前端 | `admin-frontend/` | (待定) | `admin-frontend` | ✅ |
| 8000 | 後端 API | `admin-backend/` | `/api/` | `backend` | ✅ |

### Nginx 配置（保持不變）

```nginx
# aiadmin.usdt2026.cc
server {
    listen 443 ssl http2;
    server_name aiadmin.usdt2026.cc;

    # 後端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }

    # AI 監控系統 (端口 3006)
    location /ai-monitor {
        proxy_pass http://127.0.0.1:3006;
        rewrite ^/ai-monitor/?(.*) /$1 break;
    }

    # 站點管理後台 (端口 3007)
    location /admin {
        proxy_pass http://127.0.0.1:3007;
        rewrite ^/admin/?(.*) /$1 break;
    }
    
    # 如果需要添加 admin-frontend 路由（可選）
    # location /admin-frontend {
    #     proxy_pass http://127.0.0.1:3008;
    #     rewrite ^/admin-frontend/?(.*) /$1 break;
    # }
}
```

---

## 📝 相關文檔

- `docs/ADMIN_SYSTEM_PORT_MAPPING_ANALYSIS.md` - 詳細技術分析（英文）
- `docs/ADMIN_SYSTEM_FIX_PLAN.md` - 修復方案詳情（英文）
- `scripts/fix_admin_frontend_port.sh` - 自動修復腳本

---

## ⚠️ 注意事項

1. **執行修復前請確認**:
   - `admin-frontend` 是否真的需要獨立部署
   - `ai-monitor-frontend` 文件夾是否存在（如果不存在需要創建）

2. **修復後需要檢查**:
   - 所有相關腳本是否正確更新
   - 文檔是否與實際配置一致
   - 服務是否可以正常啟動和訪問

3. **如果服務正在運行**:
   - 修復後需要重新部署受影響的服務
   - 建議在維護時間窗口執行

---

**最後更新**: 2025-12-24  
**狀態**: 待執行修復

