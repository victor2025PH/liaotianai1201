# 📁 本地腳本說明

## 📋 腳本列表

### 同步腳本

1. **`sync-scripts-to-server.bat`** - 同步腳本到服務器（批處理）
   - 一鍵執行：`scripts\local\sync-scripts-to-server.bat`
   - 功能：將服務器腳本上傳到 GitHub

2. **`check-and-sync-scripts.ps1`** - 檢查並同步腳本（PowerShell，推薦）
   - 一鍵執行：`scripts\local\check-and-sync-scripts.ps1`
   - 功能：檢查腳本狀態並同步到 GitHub

### 啟動和測試腳本

3. **`start-all-services.bat`** - 啟動所有服務
4. **`auto-test-and-fix.bat`** - 自動測試和修復
5. **`verify-frontend.bat`** - 驗證前端
6. **`run-all-tasks.bat`** - 執行所有任務
7. **`complete-auto-test.bat`** - 完整自動測試

## 🚀 快速使用

### 同步腳本到服務器

```bash
# 方式 1: 批處理（推薦）
scripts\local\sync-scripts-to-server.bat

# 方式 2: PowerShell（更可靠）
scripts\local\check-and-sync-scripts.ps1
```

### 啟動服務

```bash
scripts\local\start-all-services.bat
```

### 自動測試

```bash
scripts\local\auto-test-and-fix.bat
```

## 📝 命名規則

**所有腳本文件名必須使用英文！**

- ✅ 正確：`sync-scripts-to-server.bat`
- ❌ 錯誤：`同步腳本到服務器.bat`

---

**最後更新：** 2025-01-17

