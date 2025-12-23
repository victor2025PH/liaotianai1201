# Git Pull 冲突修复指南

## 问题描述

在执行 `git pull origin main` 时，遇到以下错误：

```
error: The following untracked working tree files would be overwritten by merge:
```

这通常发生在服务器上有未跟踪的文件，而这些文件在远程仓库中也有同名文件。

## 解决方案

### 方案 1: 使用修复脚本（推荐）

#### 安全修复（会备份文件）

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/fix_git_pull_conflict.sh
```

这个脚本会：
1. 检查 Git 状态
2. 备份冲突的文件到 `backup_YYYYMMDD_HHMMSS/` 目录
3. 清理未跟踪的文件
4. 重新拉取代码

#### 快速修复（不备份，直接覆盖）

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/quick_fix_pull.sh
```

这个脚本会：
1. 使用 `git stash` 暂存所有更改
2. 清理未跟踪的文件
3. 重置到远程状态
4. 重新拉取代码

### 方案 2: 手动修复

#### 步骤 1: 备份重要文件（可选）

```bash
cd /home/ubuntu/telegram-ai-system
mkdir -p backup_$(date +%Y%m%d_%H%M%S)
cp -r aizkw20251219 backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
cp -r hbwy20251220 backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
cp -r tgmini20251220 backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
```

#### 步骤 2: 清理未跟踪的文件

```bash
# 查看哪些文件会被删除
git clean -n -d

# 删除未跟踪的文件和目录
git clean -fd
```

#### 步骤 3: 重新拉取

```bash
git pull origin main
```

### 方案 3: 使用 Git Stash（保留本地更改）

如果本地有重要更改需要保留：

```bash
# 暂存所有更改（包括未跟踪的文件）
git stash --include-untracked

# 拉取远程代码
git pull origin main

# 恢复本地更改（如果有冲突需要手动解决）
git stash pop
```

### 方案 4: 强制重置（最激进，会丢失所有本地更改）

⚠️ **警告：这会丢失所有未提交的更改！**

```bash
# 获取最新代码
git fetch origin main

# 强制重置到远程状态
git reset --hard origin/main

# 清理未跟踪的文件
git clean -fd
```

## 常见问题

### Q1: 为什么会出现这个错误？

**A:** 这通常发生在：
- 服务器上有未提交的文件
- 这些文件在远程仓库中也有同名文件
- Git 无法自动合并，需要手动处理

### Q2: 我应该使用哪个方案？

**A:** 
- **有重要本地更改**：使用方案 3（git stash）
- **没有重要更改**：使用方案 1（修复脚本）
- **确定要覆盖本地文件**：使用方案 4（强制重置）

### Q3: 如何避免这个问题？

**A:** 
1. 定期提交和推送本地更改
2. 使用 `.gitignore` 忽略不需要版本控制的文件
3. 在服务器上只进行部署，不进行开发

## 修复后的验证

修复后，验证代码是否正确：

```bash
# 检查 Git 状态
git status

# 检查文件是否存在
ls -la aizkw20251219/
ls -la hbwy20251220/
ls -la tgmini20251220/

# 检查最新提交
git log --oneline -5
```

## 相关脚本

- `scripts/fix_git_pull_conflict.sh` - 安全修复脚本（会备份）
- `scripts/quick_fix_pull.sh` - 快速修复脚本（不备份）

---

**最后更新**: 2025-12-23

