# 🚀 Worker 節點快速部署指南

> 最後更新：2025-12-04

---

## 📋 部署清單

```
✅ 步驟 1: 安裝依賴
✅ 步驟 2: 配置環境
✅ 步驟 3: 準備帳號
✅ 步驟 4: 啟動系統
✅ 步驟 5: 驗證運行
```

---

## 步驟 1️⃣ 安裝依賴

```bash
# 進入工作目錄
cd admin-backend

# 安裝 Python 依賴
pip install -r requirements.txt

# 驗證安裝
python -c "import telethon, httpx, openpyxl; print('✅ 依賴安裝成功')"
```

---

## 步驟 2️⃣ 配置環境

### 方法 A: 複製配置文件（推薦）

```bash
# 複製示例配置
copy config\worker.env.example .env.worker

# 編輯配置文件
notepad .env.worker
```

### 方法 B: 設置環境變量

```powershell
# PowerShell
$env:REDPACKET_API_URL = "http://api.usdt2026.cc"
$env:REDPACKET_API_KEY = "test-key-2024"
$env:GAME_STRATEGY = "smart"
$env:AUTO_GRAB = "true"
$env:AUTO_CHAT = "true"
```

### 配置說明

| 變量 | 說明 | 默認值 |
|------|------|--------|
| `REDPACKET_API_URL` | 紅包 API 地址 | http://api.usdt2026.cc |
| `REDPACKET_API_KEY` | API 密鑰 | test-key-2024 |
| `GAME_STRATEGY` | 遊戲策略 | smart |
| `AUTO_GRAB` | 自動搶紅包 | true |
| `AUTO_SEND` | 自動發紅包 | false |
| `AUTO_CHAT` | 智能聊天 | true |
| `LLM_ENABLED` | 啟用 LLM | false |

---

## 步驟 3️⃣ 準備帳號

### 3.1 創建帳號配置 Excel

在 `sessions/` 目錄下創建 `accounts.xlsx`：

| phone | api_id | api_hash | name | role | status |
|-------|--------|----------|------|------|--------|
| 639277358115 | 12345678 | abc123... | AI-1 | xiaoqi | active |
| 639543603735 | 12345679 | def456... | AI-2 | mimi | active |
| ... | ... | ... | ... | ... | ... |

**重要說明：**
- 每個帳號必須有獨立的 `api_id` 和 `api_hash`
- 從 https://my.telegram.org 獲取 API 憑證
- 不可共用 API 憑證

### 3.2 放入 Session 文件

將 Telegram `.session` 文件放入 `sessions/` 目錄：

```
sessions/
├── accounts.xlsx
├── 639277358115.session
├── 639543603735.session
├── 639952948692.session
├── 639454959591.session
├── 639542360349.session
└── 639950375245.session
```

### 3.3 AI 帳號列表（API 文檔提供）

| ID | Telegram User ID | 初始餘額 |
|----|------------------|----------|
| AI-1 | 639277358115 | 100 USDT |
| AI-2 | 639543603735 | 100 USDT |
| AI-3 | 639952948692 | 100 USDT |
| AI-4 | 639454959591 | 100 USDT |
| AI-5 | 639542360349 | 100 USDT |
| AI-6 | 639950375245 | 100 USDT |

---

## 步驟 4️⃣ 啟動系統

### 測試 API 連通性

```bash
python test_api.py
```

預期輸出：
```
==================================================
  紅包 API 連通性測試
==================================================

1. 測試 API 健康狀態...
   ✅ API 在線 (狀態碼: 200)

2. 測試 AI 帳號餘額查詢...
   ✅ AI-1 (ID: 639277358115) - 餘額: 100.0 USDT
   ✅ AI-2 (ID: 639543603735) - 餘額: 100.0 USDT
   ✅ AI-3 (ID: 639952948692) - 餘額: 100.0 USDT
```

### 啟動完整系統

```bash
python start_full_system.py
```

預期輸出：
```
======================================================================
  🚀 完整業務自動化系統
  功能: LLM對話 | 多群組 | 紅包遊戲 | 實時監控 | 數據分析
======================================================================

✅ 紅包 API 連接正常
✅ 實時監控已啟動
✅ 連接了 6 個帳號

🚀 系統已啟動！
   📊 6 個帳號在線
   🤖 LLM 對話: ❌
   🧧 自動搶紅包: ✅
   📤 自動發紅包: ❌
   💬 智能聊天: ✅
   📈 遊戲策略: smart

按 Ctrl+C 停止
```

---

## 步驟 5️⃣ 驗證運行

### 檢查日誌

```bash
# 查看運行日誌
type logs\app.log

# 查看錯誤日誌
type logs\error.log
```

### 查看系統狀態

系統每分鐘輸出狀態：
```
📊 狀態: 帳號=6, 紅包領取=23, 淨收益=12.30 USDT
```

### 監控端點（如果啟用了後端服務）

```bash
# 系統狀態
curl http://localhost:8000/api/v1/monitor/status

# WebSocket 監控
ws://localhost:8000/api/v1/monitor/ws
```

---

## 🎮 遊戲策略說明

| 策略 | 發紅包概率 | 搶紅包概率 | 炸彈紅包 | 適用場景 |
|------|-----------|-----------|---------|----------|
| conservative | 5% | 95% | 禁用 | 保守運營 |
| balanced | 10% | 90% | 可選 | 日常運營 |
| aggressive | 20% | 99% | 啟用 | 快速擴張 |
| smart | 動態 | 動態 | 智能 | 自適應 |

---

## ⚠️ 常見問題

### Q1: 連接超時

```
錯誤: httpx.ConnectTimeout
解決: 檢查網絡連接，確認 API 地址可訪問
```

### Q2: 認證失敗

```
錯誤: 401 API Key 無效
解決: 確認 REDPACKET_API_KEY 配置正確
```

### Q3: Session 無效

```
錯誤: 帳號未授權
解決: 重新生成 .session 文件或使用有效的 session
```

### Q4: 餘額不足

```
錯誤: 400 餘額不足
解決: 確認帳號有足夠餘額，或調整發紅包策略
```

---

## 📁 目錄結構

```
admin-backend/
├── sessions/              # Session 文件和帳號配置
│   ├── accounts.xlsx      # 帳號配置 Excel
│   └── *.session          # Telegram session 文件
├── logs/                  # 日誌文件
│   ├── app.log            # 運行日誌
│   ├── error.log          # 錯誤日誌
│   └── app.json.log       # JSON 格式日誌
├── scripts/               # 劇本文件
├── config/                # 配置文件
│   └── worker.env.example # 環境配置示例
├── start_full_system.py   # 主啟動腳本
├── test_api.py            # API 測試腳本
├── deploy_worker.py       # 部署工具
└── requirements.txt       # Python 依賴
```

---

## 📞 支持

如有問題，請查看：
- 完整文檔：`docs/完整系統功能說明.md`
- 業務指南：`docs/業務自動化系統使用指南.md`

---

*文檔版本：v1.0 | 2025-12-04*
