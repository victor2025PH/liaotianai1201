# 部署问题诊断与解决方案

## 🔍 问题诊断

### 问题 1: 路径不匹配

**症状：**
- GitHub Actions 部署失败
- 在服务器上找不到脚本文件
- 目录 `/home/ubuntu/telegram-ai-system` 不存在

**原因：**
1. **GitHub Actions 工作流配置的路径**：`/home/ubuntu/telegram-ai-system`
2. **服务器实际项目路径**：`/opt/web3-sites`
3. **路径不一致导致**：
   - GitHub Actions 尝试访问不存在的目录
   - 脚本文件无法找到
   - Git 操作失败

**影响范围：**
- `.github/workflows/deploy-three-sites.yml` - 三个网站部署工作流
- `.github/workflows/deploy.yml` - 主部署工作流
- 所有依赖项目路径的部署脚本

### 问题 2: Git 仓库状态不明

**症状：**
- `/opt/web3-sites/` 可能是独立的 Git 仓库
- 或者不是 Git 仓库，只是文件副本
- 无法执行 `git pull` 获取最新代码

**可能的情况：**
1. `/opt/web3-sites/` 是一个独立的 Git 仓库，有自己的 `.git` 目录
2. `/opt/web3-sites/` 不是 Git 仓库，只是手动复制的文件
3. `/opt/web3-sites/` 是另一个远程仓库的克隆

### 问题 3: 文件同步问题

**症状：**
- 本地创建的脚本无法在服务器上找到
- 提交到 GitHub 的代码无法同步到服务器

**原因：**
1. 如果 `/opt/web3-sites/` 不是 Git 仓库，需要手动同步文件
2. 如果 `/opt/web3-sites/` 是独立的 Git 仓库，需要确认远程仓库地址
3. GitHub Actions 部署到错误的路径，文件无法同步到实际目录

### 问题 4: GitHub Actions 部署错误

**症状：**
- 工作流失败：`Dependencies lock file is not found`
- 工作流失败：目录不存在

**原因：**
1. 工作流可能在错误的目录执行 `npm install`
2. 工作流路径配置错误

---

## ✅ 解决方案

### 方案一：修改 GitHub Actions 工作流使用正确路径（推荐）

**优点：**
- 不需要迁移数据
- 保持现有服务器配置
- 最小改动

**步骤：**

1. **修改 `.github/workflows/deploy-three-sites.yml`**：
   ```yaml
   # 将
   PROJECT_DIR="/home/ubuntu/telegram-ai-system"
   # 改为
   PROJECT_DIR="/opt/web3-sites"
   ```

2. **修改 `.github/workflows/deploy.yml`**：
   ```yaml
   # 将
   PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
   # 改为
   PROJECT_ROOT="/opt/web3-sites"
   ```

3. **提交并推送更改**

### 方案二：确保 `/opt/web3-sites/` 是 Git 仓库

**如果 `/opt/web3-sites/` 不是 Git 仓库：**

1. **初始化 Git 仓库**：
   ```bash
   cd /opt/web3-sites
   git init
   git remote add origin https://github.com/victor2025PH/liaotianai1201.git
   git fetch origin main
   git checkout -b main origin/main
   ```

2. **如果已经是 Git 仓库，检查远程仓库**：
   ```bash
   cd /opt/web3-sites
   git remote -v
   # 如果远程仓库地址不正确，更新：
   git remote set-url origin https://github.com/victor2025PH/liaotianai1201.git
   ```

### 方案三：同步脚本到服务器

**方法 A: 通过 Git（如果 `/opt/web3-sites/` 是 Git 仓库）**

```bash
cd /opt/web3-sites
git pull origin main
```

**方法 B: 直接复制文件**

在本地执行（需要 SSH 访问）：
```bash
scp scripts/diagnose_aiadmin_redirect.py ubuntu@服务器IP:/opt/web3-sites/scripts/
scp scripts/diagnose_aiadmin_redirect.sh ubuntu@服务器IP:/opt/web3-sites/scripts/
```

**方法 C: 使用快速诊断（无需文件）**

直接在服务器上运行诊断代码，不需要文件系统上的脚本文件。

### 方案四：修复 GitHub Actions 工作流错误

**问题：`Dependencies lock file is not found`**

**原因：** 工作流可能在项目根目录执行 `npm install`，但项目根目录没有 `package.json`

**解决：**
1. 确保工作流在正确的子目录中执行 `npm install`
2. 或者移除工作流中的 `cache` 选项（如果不需要缓存）

---

## 📋 诊断检查清单

在服务器上执行以下命令进行诊断：

```bash
# 1. 检查项目目录
ls -la /opt/web3-sites/
ls -la /home/ubuntu/telegram-ai-system/ 2>&1

# 2. 检查 Git 状态
cd /opt/web3-sites
git remote -v
git status

# 3. 检查 GitHub Actions 工作流配置
grep -r "PROJECT_DIR\|PROJECT_ROOT" /opt/web3-sites/.github/workflows/ 2>/dev/null

# 4. 检查脚本是否存在
ls -la /opt/web3-sites/scripts/diagnose_aiadmin_redirect.* 2>/dev/null
```

---

## 🚀 推荐执行步骤

### 第一步：诊断问题

在服务器上运行诊断脚本（如果脚本已同步）：
```bash
cd /opt/web3-sites
bash scripts/diagnose_deployment_issues.sh
```

或者直接运行快速诊断：
```bash
# 检查路径和 Git 状态
echo "=== 检查路径 ==="
ls -d /opt/web3-sites /home/ubuntu/telegram-ai-system 2>&1

echo "=== 检查 Git 状态 ==="
cd /opt/web3-sites 2>/dev/null && git remote -v && git status || echo "不是 Git 仓库或目录不存在"
```

### 第二步：选择解决方案

根据诊断结果：
1. **如果 `/opt/web3-sites/` 是 Git 仓库**：修改 GitHub Actions 工作流路径
2. **如果 `/opt/web3-sites/` 不是 Git 仓库**：初始化 Git 仓库或选择方案三同步文件
3. **如果需要快速诊断**：使用方案三的快速方法

### 第三步：修复并验证

1. 修改 GitHub Actions 工作流文件
2. 提交并推送到 GitHub
3. 在服务器上执行 `git pull` 同步代码
4. 运行诊断脚本验证修复

---

## ⚠️ 注意事项

1. **数据安全**：修改路径前，确保备份重要数据
2. **服务中断**：修改工作流可能导致短暂的服务中断
3. **权限问题**：确保 `/opt/web3-sites/` 目录有正确的权限设置
4. **Git 冲突**：如果服务器上的代码有本地修改，`git pull` 可能会产生冲突

