# 問題排查與解決方案

## 問題 1: Python 命令未找到

### 錯誤信息
```
The term 'python' is not recognized as a name of a cmdlet, function, script file, or executable program.
```

### 原因
Windows 系統上可能沒有將 `python` 添加到 PATH，但通常有 `py` (Python Launcher)。

### 解決方案

#### 方案 1: 使用 `py` 命令（推薦）
```powershell
# 安裝依賴
cd admin-backend
py -m pip install -r requirements.txt

# 執行數據庫遷移
py -m alembic upgrade head
```

#### 方案 2: 使用完整路徑
```powershell
# 找到 Python 路徑
where.exe py
# 輸出: C:\Users\Administrator\AppData\Local\Programs\Python\Launcher\py.exe

# 使用完整路徑
C:\Users\Administrator\AppData\Local\Programs\Python\Launcher\py.exe -m pip install -r requirements.txt
```

#### 方案 3: 添加 Python 到 PATH（永久解決）
1. 找到 Python 安裝目錄（通常在 `C:\Users\你的用戶名\AppData\Local\Programs\Python\Python3.x\`）
2. 將該目錄添加到系統 PATH 環境變量
3. 重啟終端

---

## 問題 2: 路徑重複錯誤

### 錯誤信息
```
Cannot find path '...\admin-backend\admin-backend' because it does not exist.
```

### 原因
在已經在 `admin-backend` 目錄內時，又執行了 `cd admin-backend`，導致路徑重複。

### 解決方案

#### 檢查當前目錄
```powershell
# 查看當前目錄
$PWD.Path

# 查看目錄結構
Get-ChildItem -Directory
```

#### 正確的切換目錄方式
```powershell
# 如果當前在項目根目錄
cd admin-backend

# 如果已經在 admin-backend 目錄內，不需要再 cd
# 直接執行命令即可
```

---

## 問題 3: Poetry 未安裝

### 錯誤信息
```
Poetry 未安裝，請使用 pip install -r requirements.txt
```

### 解決方案

#### 方案 1: 使用 pip 安裝（推薦，已創建 requirements.txt）
```powershell
cd admin-backend
py -m pip install -r requirements.txt
```

#### 方案 2: 安裝 Poetry（如果需要）
```powershell
# 使用 pip 安裝
py -m pip install poetry

# 或使用官方安裝腳本
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

---

## 完整安裝步驟（修正版）

### 1. 後端依賴安裝
```powershell
# 確保在項目根目錄
cd "C:\Users\Administrator\Desktop\新建文件夹\聊天AI08-继续开发"

# 進入後端目錄
cd admin-backend

# 安裝依賴（使用 py 而不是 python）
py -m pip install -r requirements.txt

# 如果 requirements.txt 不存在，可以從 pyproject.toml 生成
# py -m pip install fastapi uvicorn sqlalchemy alembic redis slowapi ...
```

### 2. 執行數據庫遷移
```powershell
# 仍在 admin-backend 目錄
py -m alembic upgrade head
```

### 3. 前端依賴安裝
```powershell
# 返回項目根目錄
cd ..

# 進入前端目錄
cd saas-demo

# 安裝依賴
npm install
```

### 4. 驗證安裝
```powershell
# 檢查後端依賴
cd admin-backend
py -c "import fastapi; print('FastAPI:', fastapi.__version__)"
py -c "import redis; print('Redis:', redis.__version__)"
py -c "import slowapi; print('SlowAPI:', slowapi.__version__)"

# 檢查前端依賴
cd ../saas-demo
npm list @tanstack/react-query
```

---

## 常見問題 FAQ

### Q: 為什麼使用 `py` 而不是 `python`？
A: Windows 上的 Python Launcher (`py.exe`) 會自動選擇已安裝的 Python 版本，更可靠。

### Q: 如何檢查 Python 是否正確安裝？
```powershell
py --version
# 應該輸出類似: Python 3.13.9
```

### Q: 如何檢查 pip 是否可用？
```powershell
py -m pip --version
```

### Q: 安裝依賴時出現權限錯誤？
```powershell
# 使用用戶安裝（不需要管理員權限）
py -m pip install --user -r requirements.txt
```

### Q: 如何創建虛擬環境？
```powershell
# 創建虛擬環境
py -m venv venv

# 激活虛擬環境（PowerShell）
.\venv\Scripts\Activate.ps1

# 在虛擬環境中安裝依賴
pip install -r requirements.txt
```

---

## 快速診斷命令

```powershell
# 1. 檢查當前目錄
$PWD.Path

# 2. 檢查 Python
py --version
where.exe py

# 3. 檢查 pip
py -m pip --version

# 4. 檢查目錄結構
Get-ChildItem -Directory | Select-Object Name

# 5. 檢查文件是否存在
Test-Path admin-backend\requirements.txt
Test-Path saas-demo\package.json
```

---

**最後更新**: 2025-01-07


