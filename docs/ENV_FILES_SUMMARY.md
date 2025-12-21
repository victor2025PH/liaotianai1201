# 包含 API Key 的文件总结

> **快速参考**: 需要手动上传到服务器的文件列表

---

## 📋 文件清单

根据检查，以下文件包含 API Key，需要手动上传：

### ✅ 已存在的文件

1. **`admin-backend\.env`** ✅
   - 本地路径: `d:\telegram-ai-system\admin-backend\.env`
   - 服务器路径: `/home/ubuntu/telegram-ai-system/admin-backend/.env`
   - **必须上传**

2. **`saas-demo\.env.local`** ✅
   - 本地路径: `d:\telegram-ai-system\saas-demo\.env.local`
   - 服务器路径: `/home/ubuntu/telegram-ai-system/saas-demo/.env.local`
   - **必须上传**

### ❌ 不存在的文件（可选）

- `hbwy20251220\.env.local` - 不存在
- `tgmini20251220\.env.local` - 不存在
- `.env` (项目根目录) - 不存在

---

## 🚀 快速上传命令

### 在 PowerShell 中执行：

```powershell
cd d:\telegram-ai-system

# 上传后端 .env
scp admin-backend\.env ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/admin-backend/.env

# 上传前端 .env.local
scp saas-demo\.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/saas-demo/.env.local
```

### 或者使用脚本：

```powershell
# 检查文件
.\scripts\check-env-files.ps1

# 上传文件
.\scripts\upload-env-files.ps1 -ServerUser ubuntu -ServerHost 165.154.242.60
```

---

## ✅ 上传后设置权限

```bash
ssh ubuntu@165.154.242.60

chmod 600 /home/ubuntu/telegram-ai-system/admin-backend/.env
chmod 600 /home/ubuntu/telegram-ai-system/saas-demo/.env.local
```

---

## 🔍 验证文件不在 Git 中

```powershell
# 在 PowerShell 中
git ls-files | Select-String -Pattern "\.env$|\.env\.local$"

# 应该没有输出
```

---

## 📚 详细文档

- [手动上传指南](./MANUAL_UPLOAD_ENV_FILES.md)
- [包含 API Key 的文件清单](./FILES_WITH_API_KEYS.md)
