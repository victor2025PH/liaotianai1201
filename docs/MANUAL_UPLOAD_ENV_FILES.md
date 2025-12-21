# 手动上传包含 API Key 的文件指南

> **重要**: 这些文件包含敏感信息，**不要**提交到 GitHub

---

## 📋 需要手动上传的文件列表

### 1. 项目根目录 `.env`
- **本地路径**: `d:\telegram-ai-system\.env`
- **服务器路径**: `/home/ubuntu/telegram-ai-system/.env`
- **包含**: `OPENAI_API_KEY`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` 等

### 2. 后端配置 `admin-backend/.env`
- **本地路径**: `d:\telegram-ai-system\admin-backend\.env`
- **服务器路径**: `/home/ubuntu/telegram-ai-system/admin-backend/.env`
- **包含**: `OPENAI_API_KEY`, `JWT_SECRET`, `DATABASE_URL`, `REDIS_PASSWORD` 等

### 3. 前端项目 1 `hbwy20251220/.env.local`（如果存在）
- **本地路径**: `d:\telegram-ai-system\hbwy20251220\.env.local`
- **服务器路径**: `/home/ubuntu/telegram-ai-system/hbwy20251220/.env.local`
- **包含**: `OPENAI_API_KEY`, `GEMINI_API_KEY`

### 4. 前端项目 2 `tgmini20251220/.env.local`（如果存在）
- **本地路径**: `d:\telegram-ai-system\tgmini20251220\.env.local`
- **服务器路径**: `/home/ubuntu/telegram-ai-system/tgmini20251220/.env.local`
- **包含**: `OPENAI_API_KEY`, `GEMINI_API_KEY`

---

## 🚀 上传方法

### 方法 1: 使用 PowerShell 脚本（推荐）

```powershell
# 在项目根目录执行
cd d:\telegram-ai-system

# 检查文件
.\scripts\check-env-files.ps1

# 上传文件（替换为你的服务器信息）
.\scripts\upload-env-files.ps1 -ServerUser ubuntu -ServerHost 165.154.242.60
```

### 方法 2: 使用 SCP 命令（手动）

```powershell
# 在 PowerShell 中执行（替换 user@server 为你的服务器信息）
# 服务器地址: ubuntu@165.154.242.60

# 上传项目根目录 .env
scp .env ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/.env

# 上传后端 .env
scp admin-backend\.env ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/admin-backend/.env

# 上传前端 .env.local（如果存在）
scp hbwy20251220\.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/hbwy20251220/.env.local
scp tgmini20251220\.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/tgmini20251220/.env.local
```

### 方法 3: 使用 SFTP

```powershell
# 连接到服务器
sftp ubuntu@165.154.242.60

# 在 SFTP 会话中
cd /home/ubuntu/telegram-ai-system
put .env
put admin-backend\.env admin-backend/.env

# 如果存在前端文件
put hbwy20251220\.env.local hbwy20251220/.env.local
put tgmini20251220\.env.local tgmini20251220/.env.local

# 退出
exit
```

---

## ✅ 上传后设置文件权限

SSH 到服务器并设置文件权限：

```bash
# SSH 到服务器
ssh ubuntu@165.154.242.60

# 设置文件权限（仅所有者可读）
chmod 600 /home/ubuntu/telegram-ai-system/.env
chmod 600 /home/ubuntu/telegram-ai-system/admin-backend/.env

# 如果存在前端文件
chmod 600 /home/ubuntu/telegram-ai-system/hbwy20251220/.env.local
chmod 600 /home/ubuntu/telegram-ai-system/tgmini20251220/.env.local

# 验证权限
ls -la /home/ubuntu/telegram-ai-system/.env
ls -la /home/ubuntu/telegram-ai-system/admin-backend/.env
```

---

## 🔍 检查文件是否在 Git 中

### 在 PowerShell 中：

```powershell
# 检查 .env 文件是否被 Git 跟踪
git ls-files | Select-String -Pattern "\.env$|\.env\.local$"

# 应该没有输出（如果看到文件，需要移除）
```

### 如果发现 .env 文件被跟踪：

```powershell
# 从 Git 中移除，但保留本地文件
git rm --cached .env
git rm --cached admin-backend/.env
git rm --cached hbwy20251220/.env.local
git rm --cached tgmini20251220/.env.local

# 提交更改
git commit -m "chore: 移除 .env 文件从 Git 跟踪"
```

---

## ⚠️ 重要提示

1. **永远不要提交 `.env` 文件到 Git**
   - 这些文件包含敏感信息
   - 已经在 `.gitignore` 中，但需要确认没有被跟踪

2. **检查文件是否存在**:
   ```powershell
   # 在 PowerShell 中检查
   Test-Path .env
   Test-Path admin-backend\.env
   ```

3. **服务器路径**:
   - 确保服务器上的路径正确
   - 如果目录不存在，先创建：`mkdir -p /home/ubuntu/telegram-ai-system/admin-backend`

4. **文件权限**:
   - 上传后必须设置权限为 `600`（仅所有者可读）
   - 不要将 `.env` 文件放在公开可访问的目录

---

## 📚 相关文档

- [包含 API Key 的文件清单](./FILES_WITH_API_KEYS.md)
- [环境变量配置指南](./ENV_CONFIGURATION.md)
- [API Key 配置指南](./API_KEY_SETUP_GUIDE.md)
