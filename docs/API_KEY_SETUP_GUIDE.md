# API Key 配置指南

## 📋 概述

本文檔說明如何正確配置 OpenAI API Key 和 Telegram API 憑證。

---

## 🔑 本地配置（Windows）

### 1. 檢查 .env 文件位置

`.env` 文件應該位於項目根目錄：
```
D:\telegram-ai-system\.env
```

### 2. .env 文件格式

確保 `.env` 文件格式正確，每行一個變量，沒有引號：

```env
# Telegram API 配置
TELEGRAM_API_ID=24782266
TELEGRAM_API_HASH=48ccfd1a1b2c3d4e5f6a7b8c9d0e1f2a
TELEGRAM_SESSION_NAME=639641842001

# OpenAI API 配置
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 可選配置
OPENAI_MODEL=gpt-4
OPENAI_VISION_MODEL=gpt-4o-mini
```

### 3. 驗證配置

運行配置檢查腳本：
```bash
python scripts/local/check-env.py
```

---

## 🖥️ 服務器配置（Linux）

### 1. 上傳 .env 文件

將 `.env` 文件上傳到服務器項目目錄：
```bash
# 使用 SCP 上傳
scp .env user@server:/home/ubuntu/telegram-ai-system/.env

# 或使用 SFTP
sftp user@server
put .env /home/ubuntu/telegram-ai-system/.env
```

### 2. 驗證服務器配置

SSH 到服務器並運行驗證腳本：
```bash
ssh user@server
cd /home/ubuntu/telegram-ai-system
bash scripts/server/verify-env-config.sh
```

### 3. 檢查文件權限

確保 `.env` 文件權限正確（僅所有者可讀）：
```bash
chmod 600 /home/ubuntu/telegram-ai-system/.env
```

---

## 🔍 常見問題排查

### 問題 1: API Key 無效 (401 錯誤)

**症狀**:
```
Error code: 401 - {'error': {'message': 'Incorrect API key provided'...}}
```

**解決方案**:
1. 檢查 API Key 是否完整（應該以 `sk-` 開頭）
2. 確認 API Key 沒有多餘的空格或換行符
3. 驗證 API Key 在 OpenAI 平台是否有效
4. 檢查是否有引號包裹（不應該有引號）

**檢查命令**:
```bash
# 本地檢查
python scripts/local/check-env.py

# 服務器檢查
bash scripts/server/verify-env-config.sh
```

### 問題 2: .env 文件未加載

**症狀**:
- 環境變量顯示為 `None` 或空值
- 程序無法找到配置

**解決方案**:
1. 確認 `.env` 文件在項目根目錄
2. 確認 `python-dotenv` 已安裝：
   ```bash
   pip install python-dotenv
   ```
3. 檢查 `config.py` 是否正確加載 `.env`：
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # 應該在文件開頭調用
   ```

### 問題 3: 服務器環境變量未生效

**症狀**:
- 本地測試正常，但服務器上失敗
- 服務器日誌顯示環境變量為空

**解決方案**:
1. 確認 `.env` 文件已上傳到服務器
2. 檢查服務器上的文件路徑是否正確
3. 確認 systemd 服務配置是否正確加載環境變量
4. 重啟服務：
   ```bash
   sudo systemctl restart luckyred-api
   ```

---

## ✅ 驗證清單

### 本地環境
- [ ] `.env` 文件存在於項目根目錄
- [ ] `OPENAI_API_KEY` 已設置且有效
- [ ] `TELEGRAM_API_ID` 已設置
- [ ] `TELEGRAM_API_HASH` 已設置
- [ ] `TELEGRAM_SESSION_NAME` 已設置
- [ ] 運行 `python scripts/local/check-env.py` 通過

### 服務器環境
- [ ] `.env` 文件已上傳到服務器
- [ ] 文件權限設置正確（600）
- [ ] 運行 `bash scripts/server/verify-env-config.sh` 通過
- [ ] 服務已重啟並加載新配置
- [ ] 服務日誌無環境變量相關錯誤

---

## 🧪 測試 API Key

### 本地測試
```bash
python scripts/local/test_chat.py
```

### 服務器測試
```bash
# SSH 到服務器
ssh user@server

# 進入項目目錄
cd /home/ubuntu/telegram-ai-system

# 激活虛擬環境
source venv/bin/activate

# 運行測試
python scripts/local/test_chat.py
```

---

## 📝 注意事項

1. **安全性**:
   - 永遠不要將 `.env` 文件提交到 Git
   - 確保 `.env` 在 `.gitignore` 中
   - 使用 600 權限保護服務器上的 `.env` 文件

2. **API Key 格式**:
   - OpenAI API Key 應該以 `sk-` 開頭
   - 不要包含引號或空格
   - 確保完整複製（通常很長）

3. **環境變量優先級**:
   - 系統環境變量 > `.env` 文件
   - 如果系統環境變量已設置，`.env` 中的值可能不會生效

---

## 🔗 相關文檔

- [項目驗證報告](./PROJECT_VERIFICATION_REPORT.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)
- [測試指南](./FUNCTIONAL_TEST_GUIDE.md)

---

**最後更新**: 2025-01-XX

