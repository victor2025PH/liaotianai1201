# 服务器 Git Pull 冲突修复指南

## 问题现象

在服务器上执行 `git pull origin main` 时，出现以下错误：

```
error: The following untracked working tree files would be overwritten by merge:
aizkw20251219/...
hbwy20251220/...
tgmini20251220/...
Please move or remove them before you merge.
Aborting
```

## 问题原因

服务器上的三个前端项目目录（`aizkw20251219/`, `hbwy20251220/`, `tgmini20251220/`）中有未跟踪的文件，这些文件在远程仓库中也有同名文件，导致 Git 无法自动合并。

## 解决方案

### 方案 1: 使用强制修复脚本（推荐）

```bash
cd /home/ubuntu/telegram-ai-system

# 先拉取修复脚本
git fetch origin main

# 执行强制修复脚本
bash scripts/force_pull_fix.sh
```

这个脚本会：
1. 暂存所有本地更改
2. 删除冲突的三个目录
3. 清理所有未跟踪的文件
4. 重置到远程状态
5. 重新拉取代码

### 方案 2: 手动执行（如果脚本不存在）

```bash
cd /home/ubuntu/telegram-ai-system

# 1. 暂存所有更改
git stash

# 2. 删除冲突目录
rm -rf aizkw20251219 hbwy20251220 tgmini20251220

# 3. 清理未跟踪文件
git clean -fd

# 4. 获取远程更新
git fetch origin main

# 5. 强制重置到远程状态
git reset --hard origin/main

# 6. 验证
git status
ls -la | grep -E "aizkw|hbwy|tgmini"
```

### 方案 3: 使用 Git Clean（最直接）

```bash
cd /home/ubuntu/telegram-ai-system

# 查看会被删除的文件（预览）
git clean -n -d

# 强制删除未跟踪的文件和目录
git clean -fd

# 重新拉取
git pull origin main
```

## 执行步骤（详细）

### 步骤 1: 进入项目目录

```bash
cd /home/ubuntu/telegram-ai-system
```

### 步骤 2: 检查当前状态

```bash
git status
```

### 步骤 3: 执行修复

**选项 A - 使用脚本（如果已拉取）：**
```bash
bash scripts/force_pull_fix.sh
```

**选项 B - 手动执行：**
```bash
# 暂存更改
git stash

# 删除冲突目录
rm -rf aizkw20251219 hbwy20251220 tgmini20251220

# 清理未跟踪文件
git clean -fd

# 重置并拉取
git fetch origin main
git reset --hard origin/main
```

### 步骤 4: 验证

```bash
# 检查 Git 状态
git status

# 检查目录是否存在
ls -la aizkw20251219/
ls -la hbwy20251220/
ls -la tgmini20251220/

# 检查最新提交
git log --oneline -5
```

## 常见问题

### Q1: 执行脚本后提示 "No such file or directory"

**A:** 脚本还没有被拉取到服务器。先手动执行修复命令：

```bash
cd /home/ubuntu/telegram-ai-system
git stash
rm -rf aizkw20251219 hbwy20251220 tgmini20251220
git clean -fd
git fetch origin main
git reset --hard origin/main
```

### Q2: 删除目录后如何恢复？

**A:** 这些目录会从远程仓库重新拉取，不需要手动恢复。执行 `git reset --hard origin/main` 后会自动恢复。

### Q3: 会丢失本地更改吗？

**A:** 
- 如果使用 `git stash`，本地更改会被保存，可以用 `git stash pop` 恢复
- 如果使用 `git reset --hard`，未提交的更改会丢失
- **建议：** 如果有重要本地更改，先备份或提交

### Q4: 为什么会出现这个问题？

**A:** 通常是因为：
1. 服务器上有未提交的文件
2. 这些文件在远程仓库中也有
3. Git 无法自动决定如何处理冲突

## 预防措施

1. **定期提交和推送**
   ```bash
   git add .
   git commit -m "更新"
   git push origin main
   ```

2. **使用 .gitignore**
   - 确保不需要版本控制的文件被忽略
   - 检查各项目的 `.gitignore` 文件

3. **服务器只用于部署**
   - 避免在服务器上直接修改代码
   - 所有开发在本地完成，然后推送到远程

## 相关脚本

- `scripts/force_pull_fix.sh` - 强制修复脚本（推荐）
- `scripts/quick_fix_pull.sh` - 快速修复脚本
- `scripts/fix_git_pull_conflict.sh` - 安全修复脚本（会备份）

---

**最后更新**: 2025-12-23

