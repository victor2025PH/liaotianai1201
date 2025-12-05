# 部署紅包 SDK 更新 - 說明文檔

> 更新時間：2025-12-03

---

## 📋 部署步驟

### 步驟 1：提交代碼到 GitHub（已完成）

代碼已提交並推送到 GitHub。

---

### 步驟 2：在服務器上拉取更新

**SSH 連接到服務器後執行：**

```bash
cd ~/liaotian

# 拉取最新代碼
git pull origin main

# 重啟後端
cd admin-backend
sudo systemctl restart liaotian-backend

# 重建前端
cd ../saas-demo
npm run build

# 重啟前端
sudo systemctl restart liaotian-frontend

echo "✅ 部署完成"
```

**或使用自動部署腳本：**

```bash
cd ~/liaotian
chmod +x deploy/部署紅包SDK更新.sh
./deploy/部署紅包SDK更新.sh
```

---

### 步驟 3：配置紅包 API

1. **訪問配置頁面**
   - 打開：`https://aikz.usdt2026.cc/group-ai/redpacket`

2. **填寫配置**
   - **API 地址**: `https://api.usdt2026.cc/api/v2/ai`
   - **API Key**: `test-key-2024`
   - **啟用**: ✅ 勾選

3. **保存並測試**
   - 點擊「保存配置」
   - 點擊「測試連接」
   - 確認連接成功

---

### 步驟 4：重新下載 Worker 部署包

1. **訪問部署頁面**
   - 打開：`https://aikz.usdt2026.cc/group-ai/worker-deploy`

2. **填寫配置**
   - **節點 ID**: 輸入唯一節點名稱（如：`本地電腦001`）
   - **服務器地址**: `https://aikz.usdt2026.cc`
   - **Telegram API ID**: 你的 API ID
   - **Telegram API Hash**: 你的 API Hash

3. **下載部署包**
   - 點擊「下載全部文件」
   - 解壓到本地電腦

---

### 步驟 5：配置 Worker 環境變量

#### 方式 1：修改批處理文件（Windows）

編輯 `start_worker.bat`，在文件開頭添加：

```batch
set REDPACKET_API_URL=https://api.usdt2026.cc/api/v2/ai
set REDPACKET_API_KEY=test-key-2024
set REDPACKET_ENABLED=true
```

#### 方式 2：修改 Shell 腳本（Linux）

編輯 `start_worker.sh`，在文件開頭添加：

```bash
export REDPACKET_API_URL="https://api.usdt2026.cc/api/v2/ai"
export REDPACKET_API_KEY="test-key-2024"
export REDPACKET_ENABLED="true"
```

#### 方式 3：使用 Excel 配置（推薦）

在 Excel 配置文件中添加 `redpacket_enabled` 列：

| phone | api_id | api_hash | redpacket_enabled | ... |
|-------|--------|----------|------------------|-----|
| 639277358115 | 30390800 | 471481... | 1 | ... |

---

### 步驟 6：啟動 Worker 並驗證

1. **啟動 Worker**
   ```bash
   # Windows
   start_worker.bat
   
   # Linux
   chmod +x start_worker.sh
   ./start_worker.sh
   ```

2. **檢查日誌**
   - 應該看到：`[REDPACKET] Client initialized: https://api.usdt2026.cc/api/v2/ai`
   - 如果看到：`[REDPACKET] httpx not installed`，請手動安裝：
     ```bash
     pip install httpx
     ```

3. **驗證功能**
   - 在網頁節點管理頁面查看節點狀態
   - 確認帳號信息包含 Telegram ID

---

## 🧪 測試紅包功能

### 通過服務器下發命令測試

#### 1. 查詢餘額

```bash
curl -X POST "https://aikz.usdt2026.cc/api/v1/workers/{node_id}/commands" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "redpacket_balance",
    "params": {
      "tg_id": 5433982810
    }
  }'
```

#### 2. 發送紅包

```bash
curl -X POST "https://aikz.usdt2026.cc/api/v1/workers/{node_id}/commands" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "redpacket_send",
    "params": {
      "tg_id": 5433982810,
      "amount": 10.0,
      "count": 5,
      "message": "🤖 AI 測試紅包"
    }
  }'
```

---

## ✅ 驗證清單

- [ ] 代碼已推送到 GitHub
- [ ] 服務器已拉取最新代碼
- [ ] 後端服務已重啟
- [ ] 前端已重新構建並重啟
- [ ] 紅包 API 已在網頁上配置
- [ ] Worker 部署包已重新下載
- [ ] Worker 環境變量已配置
- [ ] Worker 已啟動並顯示紅包客戶端初始化成功
- [ ] 測試命令執行成功

---

## 🔧 故障排除

### 問題 1：Worker 顯示 "httpx not installed"

**解決方案**：
```bash
pip install httpx
# 或
pip3 install httpx
```

### 問題 2：紅包 API 連接失敗

**檢查**：
1. API 地址是否正確：`https://api.usdt2026.cc/api/v2/ai`
2. API Key 是否正確：`test-key-2024`
3. 網絡連接是否正常

### 問題 3：命令執行失敗

**檢查**：
1. Worker 是否在線
2. 節點 ID 是否正確
3. Telegram User ID 是否正確（必須是數字）

---

## 📝 更新內容摘要

### 新增功能
- ✅ Worker 客戶端紅包 SDK 集成
- ✅ 支持查詢餘額、發送紅包、領取紅包
- ✅ Excel 配置支持 `redpacket_enabled` 列
- ✅ 環境變量配置支持

### 更新的文件
- `admin-backend/app/api/workers.py` - Worker 客戶端代碼
- `docs/紅包遊戲API配置.md` - API 配置文檔
- `docs/开发笔记/紅包遊戲集成更新.md` - 更新說明

---

*部署說明生成時間：2025-12-03*
