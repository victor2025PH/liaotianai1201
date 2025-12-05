# 🤖 聊天 AI 群聊程序

> Telegram 群組自動化管理系統 - 支持紅包遊戲、智能對話、多群組管理

---

## 🚀 快速開始

### 1️⃣ 安裝依賴
雙擊運行：**`安裝依賴.bat`**

### 2️⃣ 測試 API
雙擊運行：**`啟動紅包API測試.bat`**

### 3️⃣ 啟動完整系統
雙擊運行：**`啟動完整系統.bat`**

---

## 📁 項目結構

```
聊天AI群聊程序/
│
├── 🚀 啟動腳本（雙擊運行）
│   ├── 安裝依賴.bat              # 安裝 Python 依賴
│   ├── 啟動紅包API測試.bat       # 測試紅包 API 連通性
│   └── 啟動完整系統.bat          # 啟動完整自動化系統
│
├── 📦 核心模組
│   ├── admin-backend/            # 後端服務 + Worker 節點
│   │   ├── worker_redpacket_client.py   # 紅包 API 客戶端
│   │   ├── worker_llm_dialogue.py       # LLM 智能對話
│   │   ├── worker_multi_group_manager.py # 多群組管理
│   │   ├── worker_realtime_monitor.py   # 實時監控
│   │   ├── worker_analytics.py          # 數據分析
│   │   ├── start_full_system.py         # 主啟動腳本
│   │   └── start_api_test.py            # API 測試腳本
│   │
│   ├── saas-demo/                # 前端管理界面 (Next.js)
│   ├── group_ai_service/         # 群組 AI 服務
│   └── session_service/          # Session 管理服務
│
├── 📚 文檔
│   └── docs/                     # 所有文檔
│       ├── 完整系統功能說明.md
│       ├── 業務自動化系統使用指南.md
│       └── ...
│
├── 🎭 AI 模型配置
│   └── ai_models/
│       └── group_scripts/        # 對話劇本
│
├── 🛠️ 工具和腳本
│   ├── tools/                    # 工具腳本
│   ├── utils/                    # 工具函數
│   └── scripts/                  # 部署腳本
│
└── 📦 其他
    ├── _archive/                 # 歸檔的舊文件
    ├── assets/                   # 圖片資源
    └── data/                     # 數據文件
```

---

## 🧧 紅包遊戲 API

### API 信息
- **地址**: http://api.usdt2026.cc
- **密鑰**: test-key-2024

### AI 帳號
| ID | Telegram User ID | 餘額 |
|----|------------------|------|
| AI-1 | 639277358115 | 100 USDT |
| AI-2 | 639543603735 | 100 USDT |
| AI-3 | 639952948692 | 100 USDT |
| AI-4 | 639454959591 | 100 USDT |
| AI-5 | 639542360349 | 100 USDT |
| AI-6 | 639950375245 | 100 USDT |

### 功能
- ✅ 發送紅包（普通/均分/手氣）
- ✅ 領取紅包
- ✅ 炸彈紅包（踩雷賠付）
- ✅ 餘額查詢
- ✅ 內部轉帳

---

## 🎮 系統功能

| 模組 | 功能 | 狀態 |
|------|------|------|
| 🧧 紅包遊戲 | 自動搶發紅包、炸彈紅包 | ✅ |
| 🤖 LLM 對話 | OpenAI/Claude 智能回復 | ✅ |
| 📊 多群組 | 群組池管理、AI 資源調度 | ✅ |
| 🖥️ 實時監控 | WebSocket 推送、告警 | ✅ |
| 📈 數據分析 | 轉化漏斗、用戶畫像 | ✅ |
| 📝 日誌系統 | 文件輸出、輪轉、JSON | ✅ |

---

## ⚙️ 配置說明

### 環境變量
```bash
# 紅包 API
REDPACKET_API_URL=http://api.usdt2026.cc
REDPACKET_API_KEY=test-key-2024

# 遊戲策略: conservative / balanced / aggressive / smart
GAME_STRATEGY=smart

# 自動化
AUTO_GRAB=true      # 自動搶紅包
AUTO_SEND=false     # 自動發紅包
AUTO_CHAT=true      # 智能聊天

# LLM（可選）
LLM_ENABLED=false
OPENAI_API_KEY=sk-xxx
```

### 帳號配置
在 `admin-backend/sessions/` 目錄下創建 `accounts.xlsx`：

| phone | api_id | api_hash | name | role |
|-------|--------|----------|------|------|
| 639277358115 | YOUR_ID | YOUR_HASH | AI-1 | xiaoqi |

---

## 📞 技術支持

- 完整文檔：`docs/完整系統功能說明.md`
- 部署指南：`admin-backend/DEPLOY_QUICKSTART.md`

---

*最後更新：2025-12-04*
