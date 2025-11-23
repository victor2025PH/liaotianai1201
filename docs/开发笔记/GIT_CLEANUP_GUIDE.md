# Git 清理指南 - 移除大文件

> **更新时间**: 2025-01-15  
> **问题**: 部分大文件目录可能已被 Git 跟踪

---

## 问题说明

如果 `node_modules/`、`.venv/` 等大文件目录在添加 `.gitignore` 之前就已经被提交到 Git，它们会继续被跟踪，占用大量空间。

---

## 解决方案

### 方法 1: 使用提供的清理脚本（推荐）

在项目根目录执行：

```powershell
.\scripts\remove_large_files_from_git.ps1
git commit -m "Remove large directories from Git tracking"
```

### 方法 2: 手动执行命令

在项目根目录执行以下命令：

```bash
# 从 Git 中移除但保留本地文件
git rm -r --cached admin-frontend/node_modules
git rm -r --cached admin-backend/node_modules
git rm -r --cached saas-demo/node_modules
git rm -r --cached .venv
git rm -r --cached 无用文件

# 提交更改
git commit -m "Remove large directories from Git tracking"
```

### 方法 3: 如果已经推送到远程仓库

如果这些大文件已经推送到 GitHub，需要：

1. **从 Git 历史中完全移除**（需要强制推送，谨慎操作）：

```bash
# 使用 git filter-branch 或 BFG Repo-Cleaner
# 注意：这会重写 Git 历史，需要团队协作

# 选项 A: 使用 git filter-branch（较慢但安全）
git filter-branch --tree-filter "rm -rf node_modules .venv 无用文件" --prune-empty HEAD

# 选项 B: 使用 BFG Repo-Cleaner（更快，需要单独安装）
# bfg --delete-folders node_modules
# bfg --delete-folders .venv
# bfg --delete-folders 无用文件
```

2. **强制推送**（⚠️ 警告：会重写远程历史）：

```bash
git push origin --force --all
```

---

## 验证清理结果

执行以下命令验证大文件是否已被移除：

```bash
# 检查是否还有大文件被跟踪
git ls-files | findstr /i "node_modules .venv 无用文件"

# 如果没有输出，说明清理成功
```

---

## 预防措施

### 1. 确保 .gitignore 正确配置

已确认以下规则在 `.gitignore` 中：

- ✅ `.venv/`
- ✅ `node_modules/`
- ✅ `__pycache__/`
- ✅ `.pytest_cache/`
- ✅ `backup/`, `downloads/`, `voices/`, `logs/`, `sessions/`
- ✅ `无用文件/`

### 2. 提交前检查

在提交前运行：

```bash
git status
```

确保没有大文件目录出现在待提交列表中。

### 3. 使用 pre-commit 钩子

可以配置 Git pre-commit 钩子自动检查：

```bash
# .git/hooks/pre-commit
#!/bin/sh
if git diff --cached --name-only | grep -E "(node_modules|\.venv|无用文件)"; then
    echo "错误: 检测到不应提交的大文件目录！"
    exit 1
fi
```

---

## 空间节省效果

清理后预计可以节省：

- **Git 仓库大小**: 减少约 1,200+ MB
- **克隆速度**: 显著提升
- **推送/拉取速度**: 显著提升

---

## 注意事项

1. ⚠️ **备份重要数据**: 执行清理前确保重要数据已备份
2. ⚠️ **团队协作**: 如果使用 `git filter-branch` 或强制推送，需要通知团队成员
3. ✅ **本地文件保留**: 使用 `git rm --cached` 只会从 Git 中移除，本地文件不会删除
4. ✅ **依赖安装**: 其他开发者可以通过 `npm install` 和 `pip install` 重新安装依赖

---

**指南生成时间**: 2025-01-15

