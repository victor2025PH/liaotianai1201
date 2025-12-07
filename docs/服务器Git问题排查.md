# 服务器 Git 问题排查指南

## 📋 常见问题

### 问题 1: `fatal: not a git repository`

**错误信息:**
```bash
fatal: not a git repository (or any of the parent directories): .git
```

**原因:**
当前目录不是 Git 仓库，或者在错误的目录执行 Git 命令。

**解决方案:**

1. **检查当前目录**
   ```bash
   pwd
   # 确认是否在项目根目录
   ```

2. **切换到正确的项目目录**
   ```bash
   # 通常项目在
   cd ~/liaotian
   
   # 验证是否是 Git 仓库
   ls -la | grep .git
   ```

3. **使用检查脚本**
   ```bash
   bash scripts/server_git_check.sh
   ```

4. **如果项目目录不存在，克隆仓库**
   ```bash
   cd ~
   git clone <repository-url> liaotian
   cd liaotian
   ```

---

### 问题 2: 找不到 deploy 目录

**错误信息:**
```bash
touch: cannot touch 'deploy/my_new_script.sh': No such file or directory
```

**原因:**
`deploy` 目录不存在于当前目录。

**解决方案:**

1. **检查目录是否存在**
   ```bash
   ls -la | grep deploy
   ```

2. **确认项目结构**
   ```bash
   # 如果在项目根目录
   ls -la deploy/
   
   # 如果不存在，可能需要拉取最新代码
   git pull origin main
   ```

3. **如果目录真的不存在，创建它**
   ```bash
   mkdir -p deploy
   ```

---

### 问题 3: 文件找不到但在 GitHub 上存在

**可能原因:**
1. 未执行 `git pull`
2. 在错误的分支
3. 本地有未提交的更改导致冲突

**排查步骤:**

```bash
# 1. 确认在正确目录
cd ~/liaotian

# 2. 确认是 Git 仓库
git status

# 3. 检查当前分支
git branch

# 4. 切换到 main 分支（如果需要）
git checkout main

# 5. 拉取最新代码
git fetch origin main
git pull origin main

# 6. 验证文件是否存在
ls -la deploy/fix_and_deploy_frontend_complete.sh

# 7. 如果文件仍不存在，强制拉取
git fetch origin main
git checkout origin/main -- deploy/fix_and_deploy_frontend_complete.sh
```

---

## 🔍 完整诊断流程

### 步骤 1: 使用诊断脚本

```bash
# 运行 Git 仓库检查脚本
bash scripts/server_git_check.sh
```

### 步骤 2: 手动检查清单

```bash
# 1. 检查目录
pwd
# 应该在: /home/ubuntu/liaotian 或类似路径

# 2. 检查 Git 仓库
ls -la .git
# 应该显示 .git 目录

# 3. 检查远程配置
git remote -v
# 应该显示远程仓库地址

# 4. 检查分支
git branch
# 应该显示当前分支（通常是 main 或 master）

# 5. 检查状态
git status
# 查看是否有未提交的更改

# 6. 拉取最新代码
git fetch origin main
git pull origin main

# 7. 验证文件
ls -la deploy/fix_and_deploy_frontend_complete.sh
```

---

## ✅ 快速修复命令

### 如果不在正确目录:

```bash
# 找到项目目录
find ~ -name ".git" -type d 2>/dev/null | grep liaotian

# 或直接切换到已知位置
cd ~/liaotian
```

### 如果 Git 仓库损坏:

```bash
cd ~/liaotian

# 备份当前目录
mv ~/liaotian ~/liaotian.backup

# 重新克隆
cd ~
git clone <repository-url> liaotian

# 恢复配置文件（如果需要）
cp ~/liaotian.backup/.env ~/liaotian/.env 2>/dev/null || true
```

### 如果文件不在但应该存在:

```bash
cd ~/liaotian

# 方法1: 重置到远程状态
git fetch origin main
git reset --hard origin/main

# 方法2: 检出特定文件
git checkout origin/main -- deploy/fix_and_deploy_frontend_complete.sh

# 方法3: 清理并重新拉取
git clean -fd
git pull origin main
```

---

## 📝 预防措施

### 1. 创建快捷脚本

在 `~/.bashrc` 或 `~/.zshrc` 中添加:

```bash
# 快速跳转到项目目录
alias cdproject='cd ~/liaotian'

# 快速检查 Git 状态
alias gitcheck='cd ~/liaotian && git status'

# 快速拉取并检查
alias gitupdate='cd ~/liaotian && git pull origin main && git status'
```

然后执行:
```bash
source ~/.bashrc
```

### 2. 使用检查脚本

每次执行 Git 操作前:
```bash
bash scripts/server_git_check.sh
```

---

## 🚀 一键修复脚本

创建 `~/fix_git_repo.sh`:

```bash
#!/bin/bash
# Fix Git repository issues

set -e

PROJECT_DIR="$HOME/liaotian"

echo "Fixing Git repository..."

# Check if directory exists
if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "Project directory not found: $PROJECT_DIR"
    echo "Please clone the repository first:"
    echo "  git clone <repository-url> $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Check if it's a Git repo
if [[ ! -d ".git" ]]; then
    echo "Not a Git repository. Initializing..."
    git init
    git remote add origin <repository-url>
    git fetch origin
    git checkout -b main origin/main
else
    echo "Git repository found. Updating..."
    git fetch origin main
    git pull origin main || git reset --hard origin/main
fi

echo "Done! Repository is ready."
```

---

**最后更新**: 2025-12-07
