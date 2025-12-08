# 安全配置修复指南 (Security Configuration Fix Instructions)

> **重要**: 这些命令需要在 **远程 Ubuntu 服务器** 上执行，不是本地 Windows PowerShell

---

## 🚨 发现的安全问题

根据安全配置验证，发现以下安全问题：

1. ❌ **JWT_SECRET**: 已修复 ✅（已生成强随机值）
2. ❌ **ADMIN_DEFAULT_PASSWORD**: 需要手动设置
3. ❌ **CORS_ORIGINS**: 已修复 ✅（已更新为生产域名）

---

## 🔧 修复步骤

### 方法 1: 使用自动化脚本（推荐）

#### 步骤 1: SSH 连接到服务器

```bash
ssh ubuntu@165.154.233.55
```

#### 步骤 2: 运行安全配置修复脚本

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/server/fix-security-config.sh
```

这个脚本会：
- ✅ 自动生成新的 JWT_SECRET
- ✅ 更新 CORS_ORIGINS 为生产域名
- ⚠️ 提示你手动设置管理员密码

#### 步骤 3: 设置管理员密码

```bash
# 方法 A: 使用脚本（推荐）
bash scripts/server/set-admin-password.sh 'YourStrongPassword123!@#'

# 方法 B: 手动编辑
cd /home/ubuntu/telegram-ai-system/admin-backend
nano .env
# 找到 ADMIN_DEFAULT_PASSWORD=changeme123
# 修改为: ADMIN_DEFAULT_PASSWORD=YourStrongPassword123!@#
# 保存并退出 (Ctrl+X, Y, Enter)
```

#### 步骤 4: 重启服务

```bash
pm2 restart backend
```

#### 步骤 5: 验证修复

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python scripts/check_security_config.py
```

预期结果：所有检查项应显示 ✅

---

### 方法 2: 手动修复

#### 步骤 1: SSH 连接到服务器

```bash
ssh ubuntu@165.154.233.55
```

#### 步骤 2: 进入项目目录

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
```

#### 步骤 3: 创建或编辑 .env 文件

```bash
# 如果 .env 不存在，从 env.example 复制
cp env.example .env

# 编辑 .env 文件
nano .env
```

#### 步骤 4: 修改以下配置

在 `.env` 文件中找到并修改：

```bash
# 1. JWT_SECRET - 生成强随机值（至少 32 字符）
# 在服务器上运行以下命令生成：
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 然后设置到 .env 文件：
JWT_SECRET=<生成的随机值>

# 2. ADMIN_DEFAULT_PASSWORD - 设置强密码（至少 12 字符）
ADMIN_DEFAULT_PASSWORD=YourStrongPassword123!@#

# 3. CORS_ORIGINS - 配置生产域名
CORS_ORIGINS=https://aikz.usdt2026.cc
```

#### 步骤 5: 保存并退出

- 按 `Ctrl+X`
- 按 `Y` 确认保存
- 按 `Enter` 退出

#### 步骤 6: 重启服务

```bash
pm2 restart backend
```

#### 步骤 7: 验证配置

```bash
source venv/bin/activate
python scripts/check_security_config.py
```

---

## ⚠️ 重要提示

### 不要在 Windows PowerShell 中执行 Linux 命令

**错误示例**:
```powershell
# ❌ 这些命令在 Windows PowerShell 中会失败
pm2 restart backend
nano .env
cp env.example .env
cd /home/ubuntu/telegram-ai-system/admin-backend
```

**正确方法**:
```bash
# ✅ 先 SSH 连接到服务器
ssh ubuntu@165.154.233.55

# ✅ 然后在服务器上执行命令
cd /home/ubuntu/telegram-ai-system/admin-backend
pm2 restart backend
nano .env
```

---

## 📋 当前配置状态

### 已修复 ✅

- ✅ **JWT_SECRET**: 已更新为强随机值
- ✅ **CORS_ORIGINS**: 已更新为生产域名

### 待修复 ⚠️

- ⚠️ **ADMIN_DEFAULT_PASSWORD**: 需要手动设置强密码

---

## 🔐 密码要求

管理员密码必须满足：
- ✅ 至少 12 字符
- ✅ 包含大小写字母
- ✅ 包含数字
- ✅ 包含特殊字符（可选但推荐）

**示例强密码**:
- `MySecurePass123!@#`
- `Admin2025!Strong`
- `TelegramAI@2025`

---

## ✅ 验证清单

修复完成后，运行以下命令验证：

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python scripts/check_security_config.py
```

**预期输出**:
```
✅ JWT Secret: ✅ JWT_SECRET 配置正確
✅ 管理員密碼: ✅ 管理員密碼配置正確
✅ CORS 配置: ✅ CORS 配置正確
✅ 認證啟用: ✅ 認證已啟用

✅ 所有安全檢查通過！
```

---

## 🆘 故障排除

### 问题 1: 无法 SSH 连接到服务器

**解决方案**:
- 检查网络连接
- 确认服务器 IP 地址正确
- 检查 SSH 密钥配置

### 问题 2: 命令未找到（Command not found）

**原因**: 在 Windows PowerShell 中执行了 Linux 命令

**解决方案**: 先 SSH 连接到服务器，然后在服务器上执行命令

### 问题 3: 权限被拒绝（Permission denied）

**解决方案**:
```bash
# 确保文件权限正确
chmod 600 .env
chmod +x scripts/server/*.sh
```

---

## 📝 快速修复命令（复制粘贴）

```bash
# 1. SSH 连接到服务器
ssh ubuntu@165.154.233.55

# 2. 运行修复脚本
cd /home/ubuntu/telegram-ai-system
bash scripts/server/fix-security-config.sh

# 3. 设置管理员密码（替换为你的强密码）
bash scripts/server/set-admin-password.sh 'YourStrongPassword123!@#'

# 4. 验证配置
cd admin-backend
source venv/bin/activate
python scripts/check_security_config.py
```

---

**最后更新**: 2025-01-XX

