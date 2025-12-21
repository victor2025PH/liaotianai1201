# PowerShell 快速修复指南

> **问题**: 在 PowerShell 中执行 `git filter-branch` 时遇到语法错误

---

## 🔍 问题原因

PowerShell 不支持多行命令的某些语法，导致 `git filter-branch` 命令执行失败。

---

## ✅ 解决方案

### 方案 1: 使用 Git Bash（推荐）

1. **打开 Git Bash**（不是 PowerShell）

2. **执行修复脚本**:
   ```bash
   cd /d/telegram-ai-system
   bash scripts/fix-openai-api-key-in-history.sh
   ```

3. **或者手动执行命令**:
   ```bash
   cd /d/telegram-ai-system
   
   # 1. 备份
   git branch backup-before-api-key-fix
   
   # 2. 重写历史（替换 <API_KEY> 为实际的 API Key）
   git filter-branch --force --tree-filter \
     "if [ -f AI_ROBOT_SETUP.md ]; then \
        sed -i 's|<API_KEY>|YOUR_OPENAI_API_KEY|g' AI_ROBOT_SETUP.md; \
      fi" \
     --prune-empty --tag-name-filter cat -- --all
   
   # 3. 清理
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   
   # 4. 强制推送
   git push origin --force --all
   ```

### 方案 2: 使用 GitHub 的允许机制（最快）

1. **访问 GitHub 提供的 unblock URL**:
   ```
   https://github.com/victor2025PH/liaotianai1201/security/secret-scanning/unblock-secret/378dhDJvqKzXReq6LSQh8Riq7BS
   ```

2. **确认并允许**:
   - 点击 "Allow this secret"
   - 确认这是你预期的密钥

3. **重新推送**:
   ```powershell
   git push origin main
   ```

⚠️ **注意**: 这不会移除敏感信息，只是允许推送。建议之后还是重写历史。

### 方案 3: 使用 BFG Repo-Cleaner（最简单）

1. **下载 BFG**:
   - 访问: https://rtyley.github.io/bfg-repo-cleaner/
   - 下载 `bfg-1.14.0.jar`

2. **创建替换文件** `passwords.txt`:
   ```
   <从 GitHub 错误信息中获取的完整 API Key>==>YOUR_OPENAI_API_KEY
   ```

3. **在 PowerShell 中执行**:
   ```powershell
   cd d:\telegram-ai-system
   
   # 克隆镜像仓库
   git clone --mirror . ..\telegram-ai-system-mirror.git
   
   # 运行 BFG
   java -jar bfg.jar --replace-text passwords.txt ..\telegram-ai-system-mirror.git
   
   # 清理并推送
   cd ..\telegram-ai-system-mirror.git
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push origin --force --all
   ```

---

## 🚀 推荐操作流程

### 快速推送（临时方案）

```powershell
# 1. 访问 GitHub unblock URL 并允许
# 2. 推送
git push origin main
```

### 彻底修复（推荐）

```bash
# 在 Git Bash 中执行
cd /d/telegram-ai-system
bash scripts/fix-openai-api-key-in-history.sh
```

---

## 📋 验证修复

```powershell
# 检查历史中是否还有 API Key
git log --all -p | Select-String -Pattern "sk-proj-kwiU8PXvsuLe1PC1DqQ2E"

# 应该没有输出（如果还有，需要继续修复）
```

---

## ⚠️ 重要提示

1. **重写历史的影响**:
   - 所有协作者需要重新克隆仓库
   - 或者执行: `git fetch origin && git reset --hard origin/main`

2. **备份**:
   - 在重写历史前，确保已创建备份分支
   - 可以使用 `git branch backup-before-api-key-fix` 创建备份

3. **PowerShell 限制**:
   - `git filter-branch` 的复杂命令在 PowerShell 中可能失败
   - 建议使用 Git Bash 或 BFG Repo-Cleaner

---

## 📚 相关文档

- [修复 Git 历史中的 OpenAI API Key](./FIX_OPENAI_API_KEY_IN_HISTORY.md)
- [GitHub Push Protection 修复指南](./FIX_GITHUB_PUSH_PROTECTION.md)
