# 包含 API Key 的文件列表

> **注意**: 以下文件包含 API Key 或其他敏感信息，需要手动上传到服务器，**不要**提交到 GitHub

---

## 📋 需要手动上传的文件

### 1. 环境变量文件（最重要）

#### 项目根目录
- **`.env`** ⚠️ **必须手动上传**
  - 位置: `d:\telegram-ai-system\.env`
  - 包含: `OPENAI_API_KEY`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` 等
  - 状态: ✅ 已在 `.gitignore` 中

#### 后端目录
- **`admin-backend/.env`** ⚠️ **必须手动上传**
  - 位置: `d:\telegram-ai-system\admin-backend\.env`
  - 包含: `OPENAI_API_KEY`, `JWT_SECRET`, `DATABASE_URL`, `REDIS_PASSWORD` 等
  - 状态: ✅ 已在 `.gitignore` 中

#### 前端项目目录
- **`hbwy20251220/.env.local`** ⚠️ **必须手动上传**
  - 位置: `d:\telegram-ai-system\hbwy20251220\.env.local`
  - 包含: `OPENAI_API_KEY`, `GEMINI_API_KEY`
  - 状态: ✅ 已在 `.gitignore` 中（`.env.*.local`）

- **`tgmini20251220/.env.local`** ⚠️ **必须手动上传**
  - 位置: `d:\telegram-ai-system\tgmini20251220\.env.local`
  - 包含: `OPENAI_API_KEY`, `GEMINI_API_KEY`
  - 状态: ✅ 已在 `.gitignore` 中（`.env.*.local`）

### 2. 配置文件（可能包含示例，但需要检查）

- **`config.py`** ⚠️ **检查是否包含真实 API Key**
  - 位置: `d:\telegram-ai-system\config.py`
  - 说明: 从环境变量读取，但需要检查是否有硬编码
  - 状态: ⚠️ 在 Git 中，需要检查

- **`AI_ROBOT_SETUP.md`** ⚠️ **包含硬编码的 API Key（在历史中）**
  - 位置: `d:\telegram-ai-system\AI_ROBOT_SETUP.md`
  - 说明: 包含示例 API Key，已在当前版本修复为占位符
  - 状态: ⚠️ 在 Git 中，历史提交中包含真实 API Key

---

## 🔧 操作步骤

### 步骤 1: 确保文件在 .gitignore 中

以下文件**已经**在 `.gitignore` 中：
- ✅ `.env`
- ✅ `.env.local`
- ✅ `.env.*.local`
- ✅ `*.env`（部分匹配）

### 步骤 2: 从 Git 中移除已跟踪的文件（如果存在）

如果 `.env` 文件已经被 Git 跟踪，需要移除：

```bash
# 从 Git 中移除，但保留本地文件
git rm --cached .env
git rm --cached admin-backend/.env
git rm --cached hbwy20251220/.env.local
git rm --cached tgmini20251220/.env.local

# 提交更改
git commit -m "chore: 移除 .env 文件从 Git 跟踪"
```

### 步骤 3: 手动上传到服务器

使用 SCP 或 SFTP 上传：

```bash
# 上传项目根目录 .env
scp .env user@server:/home/ubuntu/telegram-ai-system/.env

# 上传后端 .env
scp admin-backend/.env user@server:/home/ubuntu/telegram-ai-system/admin-backend/.env

# 上传前端 .env.local（如果需要）
scp hbwy20251220/.env.local user@server:/home/ubuntu/telegram-ai-system/hbwy20251220/.env.local
scp tgmini20251220/.env.local user@server:/home/ubuntu/telegram-ai-system/tgmini20251220/.env.local
```

### 步骤 4: 设置服务器文件权限

```bash
# SSH 到服务器
ssh user@server

# 设置文件权限（仅所有者可读）
chmod 600 /home/ubuntu/telegram-ai-system/.env
chmod 600 /home/ubuntu/telegram-ai-system/admin-backend/.env
chmod 600 /home/ubuntu/telegram-ai-system/hbwy20251220/.env.local
chmod 600 /home/ubuntu/telegram-ai-system/tgmini20251220/.env.local
```

---

## 📝 文件清单（供手动上传参考）

### 必须上传的文件：

1. **`.env`** (项目根目录)
   - 包含: OpenAI API Key, Telegram API 配置
   - 服务器路径: `/home/ubuntu/telegram-ai-system/.env`

2. **`admin-backend/.env`** (后端配置)
   - 包含: OpenAI API Key, JWT Secret, Database URL, Redis Password
   - 服务器路径: `/home/ubuntu/telegram-ai-system/admin-backend/.env`

3. **`hbwy20251220/.env.local`** (前端项目 1，如果存在)
   - 包含: OpenAI API Key, Gemini API Key
   - 服务器路径: `/home/ubuntu/telegram-ai-system/hbwy20251220/.env.local`

4. **`tgmini20251220/.env.local`** (前端项目 2，如果存在)
   - 包含: OpenAI API Key, Gemini API Key
   - 服务器路径: `/home/ubuntu/telegram-ai-system/tgmini20251220/.env.local`

---

## ⚠️ 重要提示

1. **永远不要提交 `.env` 文件到 Git**
   - 这些文件包含敏感信息
   - 已经在 `.gitignore` 中，但需要确认没有被跟踪

2. **检查 Git 状态**:
   ```bash
   git status
   # 如果看到 .env 文件，需要移除
   ```

3. **使用环境变量示例文件**:
   - 可以提交 `.env.example` 文件作为模板
   - 示例文件不包含真实密钥

4. **服务器配置**:
   - 确保服务器上的 `.env` 文件权限正确（600）
   - 不要将 `.env` 文件放在公开可访问的目录

---

## 🔍 验证文件是否在 Git 中

```bash
# 检查 .env 文件是否被 Git 跟踪
git ls-files | grep "\.env$"

# 应该没有输出（如果看到 .env，需要移除）
```

---

## 📚 相关文档

- [环境变量配置指南](./ENV_CONFIGURATION.md)
- [API Key 配置指南](./API_KEY_SETUP_GUIDE.md)
- [GitHub Push Protection 修复指南](./FIX_GITHUB_PUSH_PROTECTION.md)
