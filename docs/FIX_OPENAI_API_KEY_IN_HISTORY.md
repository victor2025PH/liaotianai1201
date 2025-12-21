# 修复 Git 历史中的 OpenAI API Key

> **问题**: GitHub Push Protection 检测到提交 `a76612b` 中包含硬编码的 OpenAI API Key

---

## 🔍 问题详情

- **提交**: `a76612b8abfd481e1a278779e1da2d3023429f0f`
- **文件**: `AI_ROBOT_SETUP.md`
- **位置**: 第 51 行和第 57 行
- **API Key**: `<已检测到的 OpenAI API Key，需要从历史中移除>`

---

## ✅ 已完成的修复

1. **修复当前文件** ✅
   - 已将 `AI_ROBOT_SETUP.md` 中的硬编码 API Key 替换为占位符
   - 添加了获取 API Key 的说明链接

2. **需要修复历史提交** ⚠️
   - 提交 `a76612b` 仍在 Git 历史中
   - 需要重写 Git 历史来移除敏感信息

---

## 🔧 修复方案

### 方案 1: 使用 BFG Repo-Cleaner（推荐）

#### 步骤 1: 下载 BFG

```bash
# 下载 BFG Repo-Cleaner
# 访问: https://rtyley.github.io/bfg-repo-cleaner/
# 或使用 wget:
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
```

#### 步骤 2: 创建密码替换文件

创建 `passwords.txt` 文件：

```
<从 GitHub 错误信息中获取的完整 API Key>==>YOUR_OPENAI_API_KEY
```

**注意**: 将 `<从 GitHub 错误信息中获取的完整 API Key>` 替换为 GitHub 错误信息中显示的完整 API Key。

#### 步骤 3: 运行 BFG

```bash
cd d:\telegram-ai-system

# 克隆一个镜像仓库（BFG 需要）
git clone --mirror . ../telegram-ai-system-mirror.git

# 运行 BFG
java -jar bfg.jar --replace-text passwords.txt ../telegram-ai-system-mirror.git

# 清理并推送
cd ../telegram-ai-system-mirror.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 推送到远程
git push origin --force --all
```

### 方案 2: 使用 git filter-branch

```bash
cd d:\telegram-ai-system

# 备份当前分支
git branch backup-before-api-key-fix

# 使用 filter-branch 替换
# 注意：在 Git Bash 中执行，不要在 PowerShell 中执行
git filter-branch --force --tree-filter "if [ -f AI_ROBOT_SETUP.md ]; then sed -i 's|<从 GitHub 错误信息中获取的完整 API Key>|YOUR_OPENAI_API_KEY|g' AI_ROBOT_SETUP.md; fi" --prune-empty --tag-name-filter cat -- --all

# 清理
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送
git push origin --force --all
```

### 方案 3: 使用 GitHub 的允许机制（临时方案）

如果 GitHub 提供了允许推送的链接：

1. 访问: `https://github.com/victor2025PH/liaotianai1201/security/secret-scanning/unblock-secret/378dhDJvqKzXReq6LSQh8Riq7BS`
2. 确认这是你预期的密钥
3. 选择 "Allow this secret"
4. 重新推送

⚠️ **注意**: 这不会移除敏感信息，只是允许推送。敏感信息仍然在代码库中。

---

## 🚀 快速修复命令（Windows PowerShell）

```powershell
cd d:\telegram-ai-system

# 1. 备份
git branch backup-before-api-key-fix

# 2. 使用 git filter-branch（需要 Git Bash 或 WSL）
# 在 Git Bash 中执行:
bash scripts/fix-openai-api-key-in-history.sh

# 3. 验证修复
git log --all -p | Select-String -Pattern "sk-proj-kwiU8PXvsuLe1PC1DqQ2E" -Context 2

# 4. 如果确认无误，强制推送
git push origin --force --all
```

---

## ⚠️ 重要注意事项

1. **重写历史的影响**:
   - 所有协作者需要重新克隆仓库
   - 或者执行: `git fetch origin && git reset --hard origin/main`

2. **备份**:
   - 在重写历史前，确保已创建备份分支
   - 可以使用 `git branch backup-before-api-key-fix` 创建备份

3. **验证**:
   - 重写历史后，验证 API Key 已被移除
   - 检查所有分支和标签

4. **推送**:
   - 重写历史后必须使用 `--force` 推送
   - 确保所有分支都已推送

---

## 📋 验证修复

```bash
# 检查历史中是否还有 API Key
git log --all -p | grep -i "sk-proj-kwiU8PXvsuLe1PC1DqQ2E"

# 应该没有输出（如果还有，需要继续修复）

# 检查当前文件
grep -r "sk-proj-kwiU8PXvsuLe1PC1DqQ2E" . --exclude-dir=.git

# 应该没有输出
```

---

## 🔄 如果修复失败

如果重写历史后仍然无法推送：

1. **检查是否还有其他敏感信息**:
   ```bash
   git log --all -p | grep -E "(password|secret|key|token).*=.*['\"][A-Za-z0-9]{20,}"
   ```

2. **使用 GitHub 的允许机制**（临时方案）

3. **联系 GitHub 支持**（如果问题持续）

---

## 📚 相关文档

- [GitHub Push Protection 修复指南](./FIX_GITHUB_PUSH_PROTECTION.md)
- [BFG Repo-Cleaner 文档](https://rtyley.github.io/bfg-repo-cleaner/)
- [Git filter-branch 文档](https://git-scm.com/docs/git-filter-branch)
