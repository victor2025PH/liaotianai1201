# 一步一步修复 Git Pull 问题

> **问题**: Git pull 失败，提示 "Please commit your changes or stash them before you merge"

---

## 🔍 问题分析

从错误信息来看，有两个问题：

1. **Git Pull 失败**: 因为存在未提交的本地更改
   - `admin-backend/app/core/permissions.py`
   - `admin-backend/app/middleware/permission.py`

2. **脚本不存在**: `scripts/server/quick-fix-deployment.sh` 文件不存在

---

## 🚀 快速修复（推荐）

### 方法 1: 使用自动修复脚本

```bash
# SSH 到服务器
ssh ubuntu@<SERVER_HOST>

# 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 运行分步修复脚本
bash scripts/server/step-by-step-fix.sh
```

如果脚本不存在，先手动执行以下步骤：

---

## 📋 手动修复步骤

### 步骤 1: 处理未提交的更改

```bash
# SSH 到服务器
ssh ubuntu@<SERVER_HOST>

# 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 检查 Git 状态
git status
```

**选项 A: 暂存更改（推荐）**

```bash
# 暂存所有未提交的更改
git stash push -m "Auto stash before pull $(date +%Y%m%d_%H%M%S)"

# 验证暂存
git status
```

**选项 B: 提交更改**

```bash
# 添加所有更改
git add -A

# 提交更改
git commit -m "fix: 自动提交本地更改 $(date +%Y%m%d_%H%M%S)"

# 验证提交
git status
```

**选项 C: 放弃更改（危险，仅当确定不需要这些更改时）**

```bash
# 放弃所有未提交的更改
git reset --hard HEAD
git clean -fd
```

---

### 步骤 2: 拉取最新代码

```bash
# 获取远程更新
git fetch origin main

# 拉取最新代码
git pull origin main
```

如果 `git pull` 仍然失败，使用强制重置：

```bash
# 强制重置到远程 main 分支
git fetch origin main
git reset --hard origin/main
```

---

### 步骤 3: 检查脚本目录

```bash
# 检查脚本目录是否存在
ls -la scripts/server/

# 如果目录不存在，创建它
mkdir -p scripts/server
```

---

### 步骤 4: 获取快速修复脚本

```bash
# 方法 1: 从 Git 恢复（如果脚本在仓库中）
git checkout HEAD -- scripts/server/quick-fix-deployment.sh

# 方法 2: 如果脚本不在仓库中，需要先拉取最新代码
git pull origin main

# 验证脚本存在
ls -lh scripts/server/quick-fix-deployment.sh

# 添加执行权限
chmod +x scripts/server/quick-fix-deployment.sh
```

---

### 步骤 5: 运行快速修复脚本

```bash
# 运行快速修复脚本
bash scripts/server/quick-fix-deployment.sh
```

---

## 🔧 使用修复脚本

### 方法 1: Git Pull 修复脚本

```bash
# 运行 Git Pull 修复脚本
bash scripts/server/fix-git-pull.sh
```

这个脚本会：
1. 检查 Git 状态
2. 处理未提交的更改（提供选项：stash/commit/discard）
3. 拉取最新代码
4. 验证拉取结果

### 方法 2: 分步修复脚本

```bash
# 运行分步修复脚本
bash scripts/server/step-by-step-fix.sh
```

这个脚本会：
1. 检查项目目录
2. 修复 Git Pull 问题
3. 检查脚本目录
4. 检查并创建快速修复脚本
5. 验证脚本
6. 列出可用脚本

---

## 📊 验证修复

```bash
# 检查 Git 状态
git status

# 检查最新提交
git log --oneline -5

# 检查脚本
ls -lh scripts/server/*.sh

# 检查三个网站目录
ls -la | grep -E "tgmini|hbwy|aizkw"
```

---

## ⚠️ 常见问题

### 问题 1: "Please commit your changes or stash them before you merge"

**原因**: 有未提交的本地更改

**解决**:
```bash
# 暂存更改
git stash

# 或提交更改
git add -A
git commit -m "fix: 本地更改"
```

### 问题 2: "No such file or directory"

**原因**: 脚本文件不存在

**解决**:
```bash
# 确保已拉取最新代码
git pull origin main

# 检查脚本是否存在
ls -la scripts/server/quick-fix-deployment.sh

# 如果不存在，从 Git 恢复
git checkout HEAD -- scripts/server/quick-fix-deployment.sh
```

### 问题 3: "Permission denied"

**原因**: 脚本没有执行权限

**解决**:
```bash
# 添加执行权限
chmod +x scripts/server/quick-fix-deployment.sh
```

---

## 🎯 完整修复流程

```bash
# 1. SSH 到服务器
ssh ubuntu@<SERVER_HOST>

# 2. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 3. 运行分步修复脚本
bash scripts/server/step-by-step-fix.sh

# 4. 如果脚本不存在，手动执行：
#    a. 暂存更改: git stash
#    b. 拉取代码: git pull origin main
#    c. 创建脚本目录: mkdir -p scripts/server
#    d. 从 Git 恢复脚本: git checkout HEAD -- scripts/server/quick-fix-deployment.sh

# 5. 运行快速修复脚本
bash scripts/server/quick-fix-deployment.sh

# 6. 验证部署
pm2 list
curl http://127.0.0.1:3001
```

---

**最后更新**: 2025-12-21
