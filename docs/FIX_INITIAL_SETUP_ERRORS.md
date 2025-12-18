# 修復初始化腳本錯誤指南

## 🚨 當前錯誤分析

從終端輸出中，我發現了以下錯誤：

### 錯誤 1：SSH 服務重啟失敗（已修復）
- **錯誤訊息：** `Failed to restart sshd.service: Unit sshd.service not found.`
- **狀態：** ✅ 已通過 `fix-ssh-service.sh` 修復
- **確認：** SSH 配置已正確應用

### 錯誤 2：npm 權限錯誤（目錄錯誤）
- **錯誤訊息：** `npm error code EACCES: permission denied, open '/home/package-lock.json'`
- **錯誤訊息：** `npm error enoent Could not read package.json`
- **原因：** 在錯誤的目錄（`/home`）執行了 `npm` 命令
- **解決：** 需要切換到正確的項目目錄

### 錯誤 3：Python 虛擬環境錯誤
- **錯誤訊息：** `source venv/bin/activate` 和 `requirements.txt` 找不到
- **原因：** 項目代碼尚未克隆，或不在正確的目錄

---

## ✅ 立即修復步驟

### 步驟 1：確認當前目錄並切換到正確位置

```bash
# 檢查當前目錄
pwd
# 如果顯示 /home，說明在錯誤的目錄

# 切換到項目目錄
cd /home/deployer/telegram-ai-system

# 確認目錄存在
ls -la
```

### 步驟 2：檢查項目代碼是否已克隆

```bash
# 如果在項目目錄中但沒有代碼
cd /home/deployer/telegram-ai-system

# 檢查是否有 git 倉庫
git status
# 如果顯示 "fatal: not a git repository"，說明需要克隆代碼

# 克隆項目代碼
git clone https://github.com/victor2025PH/liaotianai1201.git .
```

### 步驟 3：確認初始化腳本是否完全執行

```bash
# 檢查基礎環境
node --version
python3 --version
pm2 --version
nginx -v

# 檢查 Swap
free -h
swapon --show

# 檢查用戶
id deployer

# 檢查目錄
ls -la /home/deployer/telegram-ai-system
```

---

## 🔧 完整修復流程

### 1. 切換到 deployer 用戶

```bash
sudo su - deployer
```

### 2. 進入項目目錄

```bash
cd /home/deployer/telegram-ai-system
```

### 3. 克隆項目代碼（如果尚未克隆）

```bash
# 檢查是否已有代碼
if [ ! -d ".git" ]; then
    echo "正在克隆項目代碼..."
    git clone https://github.com/victor2025PH/liaotianai1201.git .
else
    echo "項目代碼已存在，更新中..."
    git pull origin main
fi
```

### 4. 安裝後端依賴

```bash
# 進入後端目錄
cd /home/deployer/telegram-ai-system/admin-backend

# 創建虛擬環境（如果不存在）
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虛擬環境
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 退出虛擬環境（可選）
deactivate

# 返回項目根目錄
cd ..
```

### 5. 安裝前端依賴並構建

```bash
# 進入前端目錄
cd /home/deployer/telegram-ai-system/saas-demo

# 安裝依賴
npm install

# 構建項目
npm run build

# 返回項目根目錄
cd ..
```

### 6. 啟動服務（使用 PM2）

```bash
# 確保在項目根目錄
cd /home/deployer/telegram-ai-system

# 檢查 ecosystem.config.js 是否存在
if [ ! -f "ecosystem.config.js" ]; then
    echo "⚠️  ecosystem.config.js 不存在，需要創建"
    # 參考項目文檔創建 ecosystem.config.js
else
    # 啟動服務
    pm2 start ecosystem.config.js
    
    # 保存 PM2 配置（開機自啟）
    pm2 save
    
    # 查看服務狀態
    pm2 status
    pm2 logs
fi
```

---

## 🔍 常見問題排查

### 問題 1：npm 權限錯誤

**錯誤：** `EACCES: permission denied`

**解決方法：**

```bash
# 確保使用正確的用戶（deployer，不是 root）
whoami
# 應該顯示: deployer

# 如果顯示 root，切換到 deployer
sudo su - deployer

# 檢查目錄權限
ls -la /home/deployer/telegram-ai-system
# 所有者應該是 deployer:deployer

# 如果權限不對，修復
sudo chown -R deployer:deployer /home/deployer/telegram-ai-system
```

### 問題 2：找不到 package.json

**錯誤：** `ENOENT: no such file or directory, open '/home/package.json'`

**解決方法：**

```bash
# 確認當前目錄
pwd
# 應該顯示: /home/deployer/telegram-ai-system/saas-demo

# 如果不是，切換到正確目錄
cd /home/deployer/telegram-ai-system/saas-demo

# 確認 package.json 存在
ls -la package.json
```

### 問題 3：找不到 requirements.txt

**錯誤：** `requirements.txt` 找不到

**解決方法：**

```bash
# 確認當前目錄
pwd
# 應該顯示: /home/deployer/telegram-ai-system/admin-backend

# 如果不是，切換到正確目錄
cd /home/deployer/telegram-ai-system/admin-backend

# 確認 requirements.txt 存在
ls -la requirements.txt
```

### 問題 4：虛擬環境不存在

**錯誤：** `source venv/bin/activate` 失敗

**解決方法：**

```bash
cd /home/deployer/telegram-ai-system/admin-backend

# 創建虛擬環境
python3 -m venv venv

# 激活虛擬環境
source venv/bin/activate

# 確認激活成功（命令提示符前應該顯示 (venv)）
which python
# 應該顯示: /home/deployer/telegram-ai-system/admin-backend/venv/bin/python
```

---

## 📋 快速修復腳本

創建一個快速修復腳本：

```bash
#!/bin/bash
# 快速修復初始化後的常見問題

set -e

echo "🔧 開始修復..."

# 1. 切換到 deployer 用戶（如果是 root）
if [ "$EUID" -eq 0 ]; then
    echo "切換到 deployer 用戶..."
    exec sudo -u deployer bash "$0"
fi

# 2. 進入項目目錄
PROJECT_DIR="/home/deployer/telegram-ai-system"
cd "$PROJECT_DIR"

# 3. 檢查並克隆代碼
if [ ! -d ".git" ]; then
    echo "正在克隆項目代碼..."
    git clone https://github.com/victor2025PH/liaotianai1201.git .
fi

# 4. 修復權限
echo "修復目錄權限..."
sudo chown -R deployer:deployer "$PROJECT_DIR"

# 5. 安裝後端依賴
echo "安裝後端依賴..."
cd admin-backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 6. 安裝前端依賴
echo "安裝前端依賴..."
cd saas-demo
npm install
npm run build
cd ..

echo "✅ 修復完成！"
```

---

## ✅ 驗證修復結果

執行以下命令驗證所有問題已解決：

```bash
# 1. 檢查目錄和權限
ls -la /home/deployer/telegram-ai-system
ls -la /home/deployer/telegram-ai-system/admin-backend
ls -la /home/deployer/telegram-ai-system/saas-demo

# 2. 檢查文件存在
test -f /home/deployer/telegram-ai-system/saas-demo/package.json && echo "✅ package.json 存在" || echo "❌ package.json 不存在"
test -f /home/deployer/telegram-ai-system/admin-backend/requirements.txt && echo "✅ requirements.txt 存在" || echo "❌ requirements.txt 不存在"
test -d /home/deployer/telegram-ai-system/admin-backend/venv && echo "✅ venv 存在" || echo "❌ venv 不存在"

# 3. 測試命令
cd /home/deployer/telegram-ai-system/admin-backend
source venv/bin/activate
python --version
deactivate

cd /home/deployer/telegram-ai-system/saas-demo
npm --version
node --version
```

---

## 🚀 下一步操作

修復所有錯誤後，按照 [下一步操作指南](./NEXT_STEPS_AFTER_INITIAL_SETUP.md) 繼續：

1. ✅ 配置 GitHub Actions SSH Key
2. ✅ 測試自動部署
3. ✅ 啟動 PM2 服務
4. ✅ 配置並重啟 Nginx
5. ✅ 訪問網站驗證

---

**如果仍有問題，請提供具體的錯誤訊息！**
