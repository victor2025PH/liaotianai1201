# 生成 Session 文件指南

> **更新日期**: 2024-12-19

---

## 快速開始

### 方法 1: 使用項目工具生成（推薦）

**命令**:
```bash
py tools/session_manager/generate_session.py
```

**交互式流程**:
1. 輸入 Telegram API ID
2. 輸入 Telegram API Hash
3. 輸入手機號碼（含國碼，如 +86...）
4. 輸入驗證碼（從 SMS 或 Telegram App）
5. 如果需要，輸入兩步驗證密碼
6. Session 文件會自動保存到 `sessions/` 目錄

**參數選項**:
```bash
# 指定輸出目錄
py tools/session_manager/generate_session.py --output-dir sessions

# 指定 session 名稱
py tools/session_manager/generate_session.py --session-name my_account

# 啟用加密存儲
py tools/session_manager/generate_session.py --encrypt

# 同時導出 session string
py tools/session_manager/generate_session.py --export-string
```

---

## 準備測試環境

### 步驟 1: 準備現有 Session 文件

運行準備腳本，自動整理現有的 session 文件：

```bash
py scripts/prepare_sessions_for_test.py
```

這個腳本會：
- 創建 `sessions/` 目錄
- 查找項目中的 `.session` 文件
- 複製到 `sessions/` 目錄
- 顯示可用的 session 文件列表

### 步驟 2: 生成新的 Session 文件（如果需要）

如果需要更多 session 文件進行測試：

```bash
py tools/session_manager/generate_session.py
```

**注意事項**:
- 每個 Telegram 賬號只能有一個有效的 session
- 需要不同的手機號碼來生成多個 session
- 確保有有效的 Telegram API 憑證

---

## 測試需要多少 Session 文件？

### 基本測試
- **最少**: 1 個 session 文件
- **推薦**: 2-3 個 session 文件

### 完整測試
- **推薦**: 3-5 個 session 文件
- **批量測試**: 10+ 個 session 文件

### 性能測試
- **推薦**: 10-50 個 session 文件
- **壓力測試**: 50-100 個 session 文件

---

## Session 文件位置

### 標準位置
```
sessions/
├── account1.session
├── account2.session
└── account3.session
```

### 文件命名建議
- 使用有意義的名稱，如：`test_account_1.session`
- 避免使用特殊字符
- 保持文件名簡潔

---

## 驗證 Session 文件

### 檢查文件是否存在
```bash
# Windows PowerShell
Get-ChildItem sessions\*.session

# 或使用 Python
py -c "from pathlib import Path; print(list(Path('sessions').glob('*.session')))"
```

### 檢查文件大小
有效的 session 文件通常：
- 大小: 幾 KB 到幾十 KB
- 不應該為 0 字節
- 不應該損壞

---

## 常見問題

### Q1: 如何獲取 Telegram API 憑證？

1. 訪問 https://my.telegram.org/apps
2. 使用 Telegram 賬號登錄
3. 創建新應用
4. 獲取 `api_id` 和 `api_hash`

### Q2: Session 文件過期怎麼辦？

Session 文件通常不會過期，但如果：
- 賬號被登出
- 密碼被更改
- 賬號被禁用

需要重新生成 session 文件。

### Q3: 可以重複使用同一個 Session 文件嗎？

可以，但要注意：
- 同一個 session 文件不能同時在多個地方使用
- 如果一個進程正在使用，另一個進程會失敗

### Q4: 如何安全存儲 Session 文件？

1. **加密存儲**:
   ```bash
   py tools/session_manager/generate_session.py --encrypt
   ```

2. **設置權限**:
   ```bash
   # Linux/macOS
   chmod 600 sessions/*.session
   ```

3. **不要提交到 Git**:
   - 確保 `.gitignore` 包含 `*.session`
   - 不要將 session 文件上傳到公共倉庫

---

## 測試流程

### 1. 準備 Session 文件
```bash
py scripts/prepare_sessions_for_test.py
```

### 2. 運行真實測試
```bash
py scripts/test_account_manager.py
```

### 3. 檢查測試結果
- 查看測試輸出
- 檢查日誌文件
- 驗證賬號狀態

---

## 下一步

準備好 session 文件後，可以：
1. 運行完整測試: `py scripts/test_account_manager.py`
2. 測試批量加載功能
3. 測試多賬號並行運行
4. 開始階段 2 的開發

---

**文檔版本**: v1.0  
**最後更新**: 2024-12-19

