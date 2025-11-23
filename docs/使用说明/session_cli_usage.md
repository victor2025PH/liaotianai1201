# Session CLI 使用說明與測試案例

## 1. 工具概覽
CLI 工具位於 `tools/session_manager/` 目錄，提供以下能力：

- `generate_session.py`：登入 Telegram 帳號，生成 `.session` 檔與 session string，可選擇加密儲存。
- `import_sessions.py`：批量匯入既有 `.session` 或加密 `.enc` 檔，統一整理於 `sessions/` 目錄。
- `account_status.py`：讀取帳號資料庫，顯示目前 Session 帳號狀態（上線、角色標籤、檔案路徑等）。
- `account_db.py`：內含 SQLite schema 與資料操作函式，被 CLI 工具引用。

## 2. 先決條件
- Python 3.11+ 且已安裝 `requirements.txt` 依賴，包含 `pyrogram`, `cryptography`, `tabulate` 等。
- 取得合法的 Telegram API ID/API Hash，並確保帳號可接收登入驗證碼（SMS 或應用內）。
- 建議設定虛擬環境：`python -m venv .venv && source .venv/bin/activate`（Windows 對應 `.\.venv\Scripts\activate`）。

## 3. Session 生成與加密儲存
### 3.1 基本用法
```bash
python tools/session_manager/generate_session.py \
  --api-id <API_ID> \
  --api-hash <API_HASH> \
  --phone +886912345678 \
  --session-name tg_player_01 \
  --output-dir sessions \
  --encrypt \
  --export-string
```

- 執行時會依序提示：驗證碼（SMS/Telegram App）與兩步驗證密碼（若已啟用）。
- `--encrypt` 會要求設定加密密碼（需二次確認），生成的 `.session.enc` 與 `.session_string.enc` 檔需同密碼解密。
- `--export-string` 可同時輸出 session string，方便快速登入無頭環境。

### 3.2 測試案例
1. **成功登入並加密儲存**
   - 依照上方指令登入測試帳號。
   - 驗證 `sessions/` 目錄下存在 `tg_player_01.session.enc` 與 `tg_player_01.session_string.enc`。
   - 手動或使用 `cryptography` 解密檢查檔案可用。
2. **未啟用加密流程**
   - 省略 `--encrypt`，確認輸出為純文字 `.session`，明顯較不安全（僅限開發環境）。
3. **錯誤測試：輸入錯誤驗證碼 / 密碼**
   - 確認工具能提示錯誤並中止，並不會產生不完整的 session 檔案。

## 4. Session 批量匯入
### 4.1 基本用法
```bash
python tools/session_manager/import_sessions.py \
  sessions_backup/ \
  --target-dir sessions \
  --decrypt
```

- 可同時指定多個檔案或目錄；若包含 `.enc` 檔案，會逐一詢問密碼。
- 若有共用密碼，可搭配 `--password` 參數避免重複輸入。

### 4.2 測試案例
1. **匯入單檔與目錄**
   - `import_sessions.py existing.session --target-dir sessions_test`
   - `import_sessions.py backups_dir --target-dir sessions_test`
   - 檢查 `sessions_test` 中是否拷貝完整、時間戳維持。
2. **解密匯入**
   - 先使用 `generate_session.py --encrypt` 產生 `.enc` 檔，再以 `--decrypt` 匯入並輸入密碼。
   - 驗證目標目錄出現解密後的 `.session`。
3. **錯誤處理**
   - 指定不存在的檔案：工具應輸出警告但不中斷其他檔案匯入。

## 5. 帳號資料庫與狀態看板
### 5.1 初始化資料庫
```bash
python tools/session_manager/account_status.py --init
```
- 預設使用 `data/session_accounts.db`；如需自訂路徑可加上 `--db path_to.db`。

### 5.2 註冊帳號（透過 `account_db.register_account`）
範例（可在互動式 shell 使用）：
```python
from tools.session_manager.account_db import register_account, init_db
init_db()
register_account(
    phone="+886912345678",
    session_path="sessions/tg_player_01.session.enc",
    session_string_path="sessions/tg_player_01.session_string.enc",
    display_name="玩家01",
    roles=["player", "host"]
)
```

### 5.3 查看帳號狀態
```bash
python tools/session_manager/account_status.py
```
- 會以表格展示帳號電話、名稱、角色、狀態、session 檔案路徑與最後心跳時間。

### 5.4 測試案例
1. **初始化 + 註冊 + 查詢**
   - 初始化資料庫；註冊 2~3 個帳號；執行狀態看板確認資料正確。
2. **狀態變更**
   - 透過 `update_status("+8869...", "ONLINE")` 更新狀態，再次查看。
3. **異常操作**
   - 註冊重複電話號碼：確認會覆寫 session 路徑並記錄 log。
   - 查詢空資料庫：表格顯示為空結果但程式不當掉。

## 6. 未來整合建議
- 將 CLI 納入 Makefile 或 Poetry script，簡化操作指令。
- 補充單元測試：模擬登入流程、加解密、資料庫操作。
- 與未來的 Session Interaction Service 整合：在註冊流程中同步將帳號寫入主系統配置。

---

此文件為初版操作指南與測試案例，隨著功能擴充（如 Web 後台、更多狀態欄位）將持續更新。 
# Session CLI 使用說明與測試案例

## 1. 工具概覽
CLI 工具位於 `tools/session_manager/` 目錄，提供以下能力：

- `generate_session.py`：登入 Telegram 帳號，生成 `.session` 檔與 session string，可選擇加密儲存。
- `import_sessions.py`：批量匯入既有 `.session` 或加密 `.enc` 檔，統一整理於 `sessions/` 目錄。
- `account_status.py`：讀取帳號資料庫，顯示目前 Session 帳號狀態（上線、角色標籤、檔案路徑等）。
- `account_db.py`：內含 SQLite schema 與資料操作函式，被 CLI 工具引用。

## 2. 先決條件
- Python 3.11+ 且已安裝 `requirements.txt` 依賴，包含 `pyrogram`, `cryptography`, `tabulate` 等。
- 取得合法的 Telegram API ID/API Hash，並確保帳號可接收登入驗證碼（SMS 或應用內）。
- 建議設定虛擬環境：`python -m venv .venv && source .venv/bin/activate`（Windows 對應 `.\.venv\Scripts\activate`）。

## 3. Session 生成與加密儲存
### 3.1 基本用法
```bash
python tools/session_manager/generate_session.py \
  --api-id <API_ID> \
  --api-hash <API_HASH> \
  --phone +886912345678 \
  --session-name tg_player_01 \
  --output-dir sessions \
  --encrypt \
  --export-string
```

- 執行時會依序提示：驗證碼（SMS/Telegram App）與兩步驗證密碼（若已啟用）。
- `--encrypt` 會要求設定加密密碼（需二次確認），生成的 `.session.enc` 與 `.session_string.enc` 檔需同密碼解密。
- `--export-string` 可同時輸出 session string，方便快速登入無頭環境。

### 3.2 測試案例
1. **成功登入並加密儲存**
   - 依照上方指令登入測試帳號。
   - 驗證 `sessions/` 目錄下存在 `tg_player_01.session.enc` 與 `tg_player_01.session_string.enc`。
   - 手動或使用 `cryptography` 解密檢查檔案可用。
2. **未啟用加密流程**
   - 省略 `--encrypt`，確認輸出為純文字 `.session`，明顯較不安全（僅限開發環境）。
3. **錯誤測試：輸入錯誤驗證碼 / 密碼**
   - 確認工具能提示錯誤並中止，並不會產生不完整的 session 檔案。

## 4. Session 批量匯入
### 4.1 基本用法
```bash
python tools/session_manager/import_sessions.py \
  sessions_backup/ \
  --target-dir sessions \
  --decrypt
```

- 可同時指定多個檔案或目錄；若包含 `.enc` 檔案，會逐一詢問密碼。
- 若有共用密碼，可搭配 `--password` 參數避免重複輸入。

### 4.2 測試案例
1. **匯入單檔與目錄**
   - `import_sessions.py existing.session --target-dir sessions_test`
   - `import_sessions.py backups_dir --target-dir sessions_test`
   - 檢查 `sessions_test` 中是否拷貝完整、時間戳維持。
2. **解密匯入**
   - 先使用 `generate_session.py --encrypt` 產生 `.enc` 檔，再以 `--decrypt` 匯入並輸入密碼。
   - 驗證目標目錄出現解密後的 `.session`。
3. **錯誤處理**
   - 指定不存在的檔案：工具應輸出警告但不中斷其他檔案匯入。

## 5. 帳號資料庫與狀態看板
### 5.1 初始化資料庫
```bash
python tools/session_manager/account_status.py --init
```
- 預設使用 `data/session_accounts.db`；如需自訂路徑可加上 `--db path_to.db`。

### 5.2 註冊帳號（透過 `account_db.register_account`）
範例（可在互動式 shell 使用）：
```python
from tools.session_manager.account_db import register_account, init_db
init_db()
register_account(
    phone="+886912345678",
    session_path="sessions/tg_player_01.session.enc",
    session_string_path="sessions/tg_player_01.session_string.enc",
    display_name="玩家01",
    roles=["player", "host"]
)
```

### 5.3 查看帳號狀態
```bash
python tools/session_manager/account_status.py
```
- 會以表格展示帳號電話、名稱、角色、狀態、session 檔案路徑與最後心跳時間。

### 5.4 測試案例
1. **初始化 + 註冊 + 查詢**
   - 初始化資料庫；註冊 2~3 個帳號；執行狀態看板確認資料正確。
2. **狀態變更**
   - 透過 `update_status("+8869...", "ONLINE")` 更新狀態，再次查看。
3. **異常操作**
   - 註冊重複電話號碼：確認會覆寫 session 路徑並記錄 log。
   - 查詢空資料庫：表格顯示為空結果但程式不當掉。

## 6. 未來整合建議
- 將 CLI 納入 Makefile 或 Poetry script，簡化操作指令。
- 補充單元測試：模擬登入流程、加解密、資料庫操作。
- 與未來的 Session Interaction Service 整合：在註冊流程中同步將帳號寫入主系統配置。

---

此文件為初版操作指南與測試案例，隨著功能擴充（如 Web 後台、更多狀態欄位）將持續更新。 

