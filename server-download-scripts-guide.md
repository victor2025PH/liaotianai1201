# 📥 服務器下載腳本指南

## ⚠️ 重要提示

如果服務器上無法下載腳本，請按照以下步驟排查和解決：

---

## 🔍 問題排查步驟

### 步驟 1: 檢查 Git 狀態

```bash
cd ~/telegram-ai-system
git status
```

**預期結果：**
- 如果顯示 "Your branch is behind 'origin/main'"，說明需要拉取更新
- 如果顯示 "Your branch is up to date"，但腳本不存在，可能是文件沒有正確上傳

### 步驟 2: 檢查遠程倉庫

```bash
# 檢查遠程倉庫地址
git remote -v

# 檢查遠程分支
git fetch origin
git branch -r
```

### 步驟 3: 強制拉取更新

```bash
# 方法 1: 正常拉取
cd ~/telegram-ai-system
git pull origin main

# 方法 2: 如果正常拉取失敗，強制重置
git fetch origin
git reset --hard origin/main

# 方法 3: 如果還是不行，清理並重新拉取
git clean -fd
git reset --hard origin/main
```

### 步驟 4: 驗證腳本是否存在

```bash
# 檢查腳本目錄
ls -la scripts/server/

# 如果目錄不存在，創建它
mkdir -p scripts/server

# 運行驗證腳本（如果已存在）
bash scripts/server/verify-scripts-on-server.sh
```

---

## 🚀 完整下載流程

### 方法 1: 標準流程（推薦）

```bash
# 1. 進入項目目錄
cd ~/telegram-ai-system

# 2. 檢查當前狀態
git status

# 3. 拉取最新代碼
git pull origin main

# 4. 設置執行權限
chmod +x scripts/server/*.sh

# 5. 驗證腳本
bash scripts/server/verify-scripts-on-server.sh

# 6. 執行腳本
bash scripts/server/quick-start.sh
```

### 方法 2: 強制同步（如果方法 1 失敗）

```bash
# 1. 進入項目目錄
cd ~/telegram-ai-system

# 2. 備份當前更改（如果有）
git stash

# 3. 強制重置到遠程版本
git fetch origin
git reset --hard origin/main

# 4. 清理未跟蹤文件
git clean -fd

# 5. 設置執行權限
chmod +x scripts/server/*.sh

# 6. 驗證腳本
ls -la scripts/server/
```

### 方法 3: 手動下載（最後手段）

如果 Git 拉取仍然失敗，可以手動下載：

```bash
# 1. 從 GitHub 直接下載腳本
cd ~/telegram-ai-system
mkdir -p scripts/server

# 2. 使用 curl 下載（替換為實際的 GitHub URL）
curl -o scripts/server/quick-start.sh \
  https://raw.githubusercontent.com/[用戶名]/[倉庫名]/main/scripts/server/quick-start.sh

# 3. 設置執行權限
chmod +x scripts/server/*.sh
```

---

## 🔧 常見問題解決

### 問題 1: `git pull` 顯示 "Already up to date" 但腳本不存在

**原因：** 腳本可能沒有正確提交到 GitHub

**解決：**
1. 在本地檢查腳本是否已提交：
   ```bash
   git log --name-only --oneline -5
   ```
2. 確認腳本在 GitHub 上存在
3. 如果不存在，重新執行上傳流程

### 問題 2: 權限被拒絕

**解決：**
```bash
chmod +x scripts/server/*.sh
```

### 問題 3: 腳本文件存在但內容為空

**原因：** 文件可能沒有正確上傳

**解決：**
```bash
# 檢查文件大小
ls -lh scripts/server/*.sh

# 如果文件為空，重新拉取
git pull origin main --force
```

### 問題 4: Git 配置問題

**檢查 Git 配置：**
```bash
git config --list
git config user.name
git config user.email
```

**如果需要設置：**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## ✅ 驗證清單

下載完成後，請確認：

- [ ] `scripts/server/` 目錄存在
- [ ] 所有 `.sh` 文件都存在
- [ ] 所有 `.sh` 文件都有執行權限（`-rwxr-xr-x`）
- [ ] 可以執行 `bash scripts/server/quick-start.sh`
- [ ] Git 狀態顯示 "Your branch is up to date"

---

## 📋 快速參考

```bash
# 一鍵驗證和修復
cd ~/telegram-ai-system
git pull origin main
chmod +x scripts/server/*.sh
bash scripts/server/verify-scripts-on-server.sh
```

---

**最後更新：** 2025-01-17

