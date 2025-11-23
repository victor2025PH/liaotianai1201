# 在 Cursor 集成終端中啟動服務

## 問題說明

如果您發現服務都在外部終端窗口中運行，而不是在 Cursor 的集成終端中，這是因為：

1. **雙擊 `.bat` 文件**：Windows 會自動在新窗口中打開
2. **使用 `start_services.ps1`**：該腳本使用 `Start-Process` 在新窗口啟動服務

## 解決方案

### 方法 1：使用集成終端啟動腳本（推薦）

在 Cursor 的集成終端中運行：

```powershell
.\scripts\start_services_integrated.ps1
```

這個腳本會：
- 在當前終端中以後台任務（Job）方式啟動服務
- 顯示服務狀態和日誌
- 可以隨時查看和停止服務

### 方法 2：手動在集成終端中啟動

#### 啟動後端服務

打開 Cursor 的集成終端（`` Ctrl+` ``），然後：

```powershell
cd admin-backend
$env:PYTHONPATH = (Get-Location).Parent.FullName
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 啟動前端服務

打開**新的終端標籤頁**（在終端面板點擊 `+` 或使用 `Ctrl+Shift+` `），然後：

```powershell
cd saas-demo
npm run dev
```

#### 啟動管理前端（可選）

如果需要同時運行管理前端，再打開一個終端標籤頁：

```powershell
cd admin-frontend
npm run dev
```

### 方法 3：使用後台任務（PowerShell Jobs）

在單個終端中同時運行多個服務：

```powershell
# 啟動後端
$backendJob = Start-Job -ScriptBlock {
    Set-Location "E:\002-工作文件\重要程序\聊天AI群聊程序\admin-backend"
    $env:PYTHONPATH = (Get-Location).Parent.FullName
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# 啟動前端
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "E:\002-工作文件\重要程序\聊天AI群聊程序\saas-demo"
    npm run dev
}

# 查看日誌
Get-Job | Receive-Job -Keep

# 停止服務
Stop-Job -Name BackendService,FrontendService
Remove-Job -Name BackendService,FrontendService
```

## 查看服務日誌

### 使用集成終端腳本

腳本會自動顯示日誌，或使用：

```powershell
# 查看所有服務日誌
Get-Job | Receive-Job -Keep

# 查看特定服務日誌
Receive-Job -Name BackendService -Keep
Receive-Job -Name FrontendService -Keep
```

### 手動啟動時

直接在終端中查看輸出即可。

## 停止服務

### 使用集成終端腳本

按 `Ctrl+C` 或運行：

```powershell
Stop-Job -Name BackendService,FrontendService
Remove-Job -Name BackendService,FrontendService
```

### 手動啟動時

在運行服務的終端中按 `Ctrl+C`。

## 優勢

在 Cursor 集成終端中運行的優勢：

1. ✅ **統一管理**：所有服務在一個界面中
2. ✅ **方便查看日誌**：可以直接看到所有輸出
3. ✅ **快速切換**：使用終端標籤頁快速切換
4. ✅ **集成體驗**：與編輯器無縫集成
5. ✅ **快捷鍵支持**：可以使用 Cursor 的快捷鍵

## 注意事項

- 如果使用後台任務（Jobs），日誌不會實時顯示，需要手動查看
- 建議為每個服務使用單獨的終端標籤頁，這樣可以實時看到日誌
- 使用 `--reload` 參數時，後端服務會自動重載代碼變更

