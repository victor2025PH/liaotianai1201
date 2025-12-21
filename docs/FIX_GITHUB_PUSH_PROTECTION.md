# GitHub Push Protection 修复指南

> **问题**: GitHub Push Protection 阻止推送，因为检测到敏感信息（API 密钥、密码等）

---

## 🔍 问题原因

GitHub Push Protection 会检测以下类型的敏感信息：

1. **API 密钥** (OpenAI, AWS, Google Cloud 等)
2. **密码** (数据库密码、Redis 密码等)
3. **私钥** (SSH 私钥、SSL 证书私钥等)
4. **Token** (JWT Secret, OAuth Token 等)
5. **其他敏感凭证**

### 当前问题

在以下文件中发现了硬编码的 Redis 密码：

- `docs/REDIS_PASSWORD_FIX.md` - 包含实际 Redis 密码: `GTjd0yP2uQSnHeEHTA8CnnEbu`

---

## ✅ 修复方案

### 方案 1: 移除敏感信息（推荐）

#### 步骤 1: 修改包含敏感信息的文件

将硬编码的密码替换为占位符：

```bash
# 在 docs/REDIS_PASSWORD_FIX.md 中
# 将: GTjd0yP2uQSnHeEHTA8CnnEbu
# 替换为: YOUR_REDIS_PASSWORD
```

#### 步骤 2: 提交修改

```bash
cd d:\telegram-ai-system

# 检查修改
git status

# 添加修改
git add docs/REDIS_PASSWORD_FIX.md

# 提交
git commit -m "fix: 移除硬编码的 Redis 密码"

# 推送
git push origin main
```

### 方案 2: 使用 Git 历史重写（如果密码已在历史提交中）

⚠️ **警告**: 这会重写 Git 历史，如果仓库是共享的，需要通知所有协作者。

#### 使用 git filter-branch

```bash
# 备份仓库
git clone --mirror d:\telegram-ai-system d:\telegram-ai-system-backup

# 移除敏感信息
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch docs/REDIS_PASSWORD_FIX.md" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（危险操作）
git push origin --force --all
git push origin --force --tags
```

#### 使用 BFG Repo-Cleaner（更简单，推荐）

1. 下载 BFG: https://rtyley.github.io/bfg-repo-cleaner/
2. 创建密码替换文件 `passwords.txt`:
   ```
   GTjd0yP2uQSnHeEHTA8CnnEbu==>YOUR_REDIS_PASSWORD
   ```
3. 运行 BFG:
   ```bash
   java -jar bfg.jar --replace-text passwords.txt d:\telegram-ai-system
   ```
4. 清理并推送:
   ```bash
   cd d:\telegram-ai-system
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push origin --force --all
   ```

### 方案 3: 使用 GitHub 的允许机制（临时方案）

如果 GitHub 提供了允许推送的链接：

1. 点击 GitHub 提供的链接
2. 确认这是你预期的密钥
3. 选择 "Allow this secret"
4. 重新推送

⚠️ **注意**: 这不会移除敏感信息，只是允许推送。敏感信息仍然在代码库中。

---

## 🛡️ 预防措施

### 1. 使用环境变量

**不要**在代码中硬编码密码：

```python
# ❌ 错误
REDIS_PASSWORD = "GTjd0yP2uQSnHeEHTA8CnnEbu"

# ✅ 正确
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
```

### 2. 使用 .env 文件（并添加到 .gitignore）

```bash
# .env 文件（已添加到 .gitignore）
REDIS_PASSWORD=GTjd0yP2uQSnHeEHTA8CnnEbu
```

### 3. 文档中使用占位符

在文档中使用占位符，而不是实际密码：

```markdown
# ❌ 错误
REDIS_PASSWORD=GTjd0yP2uQSnHeEHTA8CnnEbu

# ✅ 正确
REDIS_PASSWORD=YOUR_REDIS_PASSWORD
# 或
REDIS_PASSWORD=<从服务器 secure_server.sh 输出中获取>
```

### 4. 使用 GitHub Secrets（用于 CI/CD）

在 GitHub Actions 中使用 Secrets：

```yaml
# .github/workflows/deploy.yml
env:
  REDIS_PASSWORD: ${{ secrets.REDIS_PASSWORD }}
```

### 5. 使用 pre-commit 钩子

安装 `detect-secrets` 钩子：

```bash
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
```

---

## 📋 检查清单

推送前检查：

- [ ] 代码中没有硬编码的密码
- [ ] 代码中没有硬编码的 API 密钥
- [ ] 代码中没有硬编码的私钥
- [ ] 文档中使用占位符而不是实际密码
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 所有敏感信息都通过环境变量或 Secrets 管理

---

## 🔧 快速修复命令

```bash
# 1. 查找所有包含敏感信息的文件
cd d:\telegram-ai-system
grep -r "GTjd0yP2uQSnHeEHTA8CnnEbu" . --exclude-dir=.git

# 2. 替换为占位符
find . -type f -name "*.md" -exec sed -i 's/GTjd0yP2uQSnHeEHTA8CnnEbu/YOUR_REDIS_PASSWORD/g' {} \;

# 3. 检查修改
git diff

# 4. 提交并推送
git add .
git commit -m "fix: 移除硬编码的敏感信息"
git push origin main
```

---

## 📚 相关文档

- [GitHub Push Protection 文档](https://docs.github.com/en/code-security/secret-scanning/protecting-pushes-with-secret-scanning)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [detect-secrets](https://github.com/Yelp/detect-secrets)
