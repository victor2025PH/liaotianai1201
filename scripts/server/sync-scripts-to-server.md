# 📤 同步腳本到服務器指南

## 🎯 重要說明

**腳本在本地創建後，不會自動同步到服務器！**

每次創建或修改服務器腳本後，必須執行以下步驟：

---

## 📋 完整同步流程

### 步驟 1: 本地提交到 GitHub

**在本地項目根目錄執行：**

```bash
# 1. 添加新創建的腳本文件
git add scripts/server/

# 2. 提交更改
git commit -m "Add/Update server scripts: [腳本名稱列表]"

# 3. 推送到 GitHub
git push origin main
```

**示例：**
```bash
git add scripts/server/install-dependencies.sh scripts/server/quick-start.sh
git commit -m "Add server scripts: install-dependencies.sh, quick-start.sh"
git push origin main
```

### 步驟 2: 在服務器上下載更新

**在服務器項目根目錄執行：**

```bash
# 1. 進入項目目錄
cd ~/telegram-ai-system
# 或
cd /path/to/telegram-ai-system

# 2. 拉取最新代碼
git pull origin main

# 3. 設置執行權限（如果需要）
chmod +x scripts/server/*.sh
```

### 步驟 3: 驗證和執行

```bash
# 1. 驗證腳本是否存在
ls -la scripts/server/

# 2. 執行腳本
bash scripts/server/[腳本名稱].sh
```

---

## 🚀 當前新創建的腳本同步命令

### 需要同步的腳本列表

以下腳本需要同步到服務器：

1. `scripts/server/install-dependencies.sh`
2. `scripts/server/setup-server.sh`
3. `scripts/server/quick-start.sh`
4. `scripts/server/README.md`
5. `服務器部署快速指南.md`

### 立即執行（本地）

```bash
# 在項目根目錄執行
git add scripts/server/install-dependencies.sh
git add scripts/server/setup-server.sh
git add scripts/server/quick-start.sh
git add scripts/server/README.md
git add 服務器部署快速指南.md

git commit -m "Add server deployment scripts: install-dependencies, setup-server, quick-start"

git push origin main
```

### 立即執行（服務器）

```bash
# 在服務器項目根目錄執行
cd ~/telegram-ai-system
git pull origin main
chmod +x scripts/server/*.sh

# 驗證腳本
ls -la scripts/server/

# 執行快速啟動
bash scripts/server/quick-start.sh
```

---

## 📝 快速參考

### 單個腳本同步

**本地：**
```bash
git add scripts/server/new-script.sh
git commit -m "Add server script: new-script.sh"
git push origin main
```

**服務器：**
```bash
cd ~/telegram-ai-system
git pull origin main
chmod +x scripts/server/new-script.sh
bash scripts/server/new-script.sh
```

### 批量同步所有腳本

**本地：**
```bash
git add scripts/server/
git commit -m "Update all server scripts"
git push origin main
```

**服務器：**
```bash
cd ~/telegram-ai-system
git pull origin main
chmod +x scripts/server/*.sh
```

---

## ⚠️ 注意事項

1. **確保在正確的分支**：通常使用 `main` 或 `master` 分支
2. **檢查 Git 狀態**：執行 `git status` 確認要提交的文件
3. **設置執行權限**：服務器上執行 `chmod +x` 確保腳本可執行
4. **驗證腳本路徑**：確保在項目根目錄執行命令

---

**最後更新：** 2025-01-17

