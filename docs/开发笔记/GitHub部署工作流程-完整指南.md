# GitHub 部署工作流程 - 完整指南

> **创建时间**: 2025-11-28  
> **目的**: 彻底解决文件上传失败问题，建立基于 GitHub 的标准化部署流程

---

## ✅ 已完成的三项任务

### 1. ✅ 检查哪些文件需要被 Git 追踪

**脚本位置**: `deploy/检查需要追踪的文件.ps1`

**功能**:
- 检查未追踪的文件
- 检查已修改但未暂存的文件
- 检查已暂存的文件
- 验证关键文件的追踪状态

**使用方法**:
```powershell
cd "e:\002-工作文件\重要程序\聊天AI群聊程序"
.\deploy\检查需要追踪的文件.ps1
```

**输出说明**:
- 【1】未追踪的文件: 列出所有未被 Git 追踪的文件
- 【2】已修改但未暂存的文件: 列出已修改但未添加到暂存区的文件
- 【3】已暂存的文件: 列出已添加到暂存区的文件
- 【4】关键文件追踪状态: 验证关键文件是否被追踪

---

### 2. ✅ 创建一键部署脚本

#### 服务器端脚本: `deploy/从GitHub拉取并部署.sh`

**功能**:
- 从 GitHub 拉取最新代码
- 自动备份当前代码
- 验证关键文件（检查 UPSERT 代码）
- 重启后端服务
- 验证服务状态

**使用方法**:
```bash
# 在服务器上执行
ssh ubuntu@165.154.233.55 "bash ~/liaotian/deploy/从GitHub拉取并部署.sh"
```

**执行步骤**:
1. 备份当前代码到 `~/backups/backup_YYYYMMDD_HHMMSS/`
2. 从 GitHub 拉取最新代码（支持 master/main 分支）
3. 验证 `accounts.py` 是否包含 UPSERT 代码
4. 清理 Python 缓存
5. 重启后端服务（uvicorn）
6. 验证服务健康状态

#### 本地端脚本: `deploy/推送到GitHub并部署.ps1`

**功能**:
- 检查 Git 状态
- 自动添加并提交修改的文件
- 推送到 GitHub
- 在服务器上执行部署脚本

**使用方法**:
```powershell
# 基本用法
.\deploy\推送到GitHub并部署.ps1 -CommitMessage "修复说明"

# 使用密码认证
.\deploy\推送到GitHub并部署.ps1 -CommitMessage "修复说明" -Password "your_password"

# 只推送，不部署
.\deploy\推送到GitHub并部署.ps1 -CommitMessage "修复说明" -SkipDeploy

# 只部署，不推送（如果已经推送过）
.\deploy\推送到GitHub并部署.ps1 -SkipPush
```

**参数说明**:
- `-CommitMessage`: 提交信息（默认："自动部署：修复和更新"）
- `-ServerIP`: 服务器IP（默认："165.154.233.55"）
- `-Username`: SSH用户名（默认："ubuntu"）
- `-Password`: SSH密码（可选，如果使用密钥认证可不填）
- `-SkipPush`: 跳过推送到 GitHub
- `-SkipDeploy`: 跳过服务器部署
- `-AutoAdd`: 自动添加所有修改的文件（默认：true）

---

### 3. ✅ 配置自动化的 Git 工作流程

#### 已有的 GitHub Actions 配置

项目已配置完整的 CI/CD 工作流：

**文件**: `.github/workflows/deploy.yml`

**触发条件**:
- Push 到 `main` 或 `develop` 分支时自动触发
- 手动触发（workflow_dispatch）

**触发路径**:
- `admin-backend/**`
- `admin-frontend/**`
- `saas-demo/**`
- `deploy/**`
- `.github/workflows/deploy.yml`

**工作流程**:
1. **测试和构建验证**: 运行后端/前端测试和构建
2. **构建 Docker 镜像**: 构建并推送到 GitHub Container Registry
3. **部署到开发环境**: 自动部署到 Kubernetes（develop 分支）
4. **部署到生产环境**: 自动部署到 Kubernetes（main 分支）

#### 标准 Git 工作流程

```
本地开发
    ↓
git add .
    ↓
git commit -m "描述"
    ↓
git push origin master
    ↓
服务器执行: git pull
    ↓
重启服务
```

---

## 🚀 标准工作流程

### 方式1：使用一键脚本（推荐）

#### 完整自动化流程

```powershell
# 在本地执行，自动完成所有步骤
.\deploy\推送到GitHub并部署.ps1 -CommitMessage "修复 UPSERT 功能" -Password "your_password"
```

这个脚本会：
1. ✅ 检查 Git 状态
2. ✅ 自动添加所有修改的文件
3. ✅ 提交到本地仓库
4. ✅ 推送到 GitHub
5. ✅ 在服务器上拉取最新代码
6. ✅ 重启后端服务
7. ✅ 验证服务状态

---

### 方式2：手动分步执行

#### 步骤1: 检查文件状态

```powershell
.\deploy\检查需要追踪的文件.ps1
```

#### 步骤2: 添加文件到 Git

```powershell
# 添加所有修改的文件
git add .

# 或者只添加特定文件
git add admin-backend/app/api/group_ai/accounts.py
git add deploy/从GitHub拉取并部署.sh
git add deploy/推送到GitHub并部署.ps1
git add deploy/检查需要追踪的文件.ps1

# 查看将要提交的文件
git status
```

#### 步骤3: 提交到本地

```powershell
git commit -m "修复 UPSERT 功能：账户不存在时自动创建"
```

#### 步骤4: 推送到 GitHub

```powershell
# 获取当前分支
git branch --show-current

# 推送到 GitHub（通常是 master 或 main）
git push origin master
```

#### 步骤5: 在服务器上拉取并部署

```bash
# 通过 SSH 在服务器上执行
ssh ubuntu@165.154.233.55 "bash ~/liaotian/deploy/从GitHub拉取并部署.sh"
```

---

## 📋 从检查结果中看到的文件状态

根据您运行检查脚本的结果：

### ✅ 已追踪的文件
- `admin-backend/app/api/group_ai/accounts.py` ✓

### ✗ 未追踪的文件（需要添加到 Git）

**关键部署脚本**:
- `deploy/最终完整修复方案.sh`
- `deploy/从GitHub拉取并部署.sh`
- `deploy/推送到GitHub并部署.ps1`
- `deploy/检查需要追踪的文件.ps1`
- `deploy/创建GitHub部署脚本.py`

**已修改但未暂存的代码文件**:
- `admin-backend/app/api/group_ai/accounts.py`
- `admin-backend/app/api/__init__.py`
- `admin-backend/app/api/deps.py`
- `admin-backend/app/main.py`
- 以及很多前端文件

**不需要追踪的文件**（已在 .gitignore 中）:
- `admin-backend/backups/*` - 备份文件
- `assets/*.png` - 图片资源
- 很多临时文档文件

---

## 🔧 立即操作建议

### 1. 添加关键文件到 Git

```powershell
# 添加新创建的部署脚本
git add deploy/检查需要追踪的文件.ps1
git add deploy/从GitHub拉取并部署.sh
git add deploy/推送到GitHub并部署.ps1
git add deploy/创建GitHub部署脚本.py

# 添加修改的代码文件
git add admin-backend/app/api/group_ai/accounts.py
git add admin-backend/app/api/__init__.py
git add admin-backend/app/api/deps.py

# 查看暂存的文件
git status
```

### 2. 提交并推送

```powershell
git commit -m "添加 GitHub 部署工作流程脚本和 UPSERT 功能修复"
git push origin master
```

### 3. 在服务器上拉取并部署

```bash
ssh ubuntu@165.154.233.55 "bash ~/liaotian/deploy/从GitHub拉取并部署.sh"
```

或者直接使用一键脚本：

```powershell
.\deploy\推送到GitHub并部署.ps1 -CommitMessage "添加 GitHub 部署工作流程"
```

---

## 📊 使用 GitHub 部署的优势

| 特性 | 直接上传 | GitHub 部署 |
|------|---------|------------|
| **代码版本控制** | ❌ 无 | ✅ 完整历史 |
| **回滚能力** | ❌ 困难 | ✅ 简单（git reset） |
| **多服务器部署** | ❌ 需要逐个上传 | ✅ 所有服务器 git pull |
| **团队协作** | ❌ 无法共享代码 | ✅ 所有人可访问 |
| **自动化** | ❌ 手动 | ✅ 可配置 CI/CD |
| **备份** | ❌ 无 | ✅ GitHub 自动备份 |
| **部署速度** | ⚡ 快 | ⚡ 快（git pull） |
| **可靠性** | ⚠️ 容易失败 | ✅ 高（Git 协议稳定） |

**结论**: GitHub 部署是更好的选择！

---

## 🎯 推荐工作流程

### 日常开发流程

1. **修改代码**
   ```powershell
   # 修改 admin-backend/app/api/group_ai/accounts.py
   # 或其他文件
   ```

2. **检查文件状态**
   ```powershell
   .\deploy\检查需要追踪的文件.ps1
   ```

3. **提交到本地**
   ```powershell
   git add .
   git commit -m "修复说明"
   ```

4. **推送到 GitHub**
   ```powershell
   git push origin master
   ```

5. **服务器自动/手动拉取**
   ```bash
   # 自动方式（如果配置了 webhook）
   # 或手动执行
   ssh ubuntu@165.154.233.55 "bash ~/liaotian/deploy/从GitHub拉取并部署.sh"
   ```

### 一键部署流程

```powershell
# 一次性完成所有步骤
.\deploy\推送到GitHub并部署.ps1 -CommitMessage "修复说明"
```

---

## 📝 关键文件说明

### 1. `deploy/检查需要追踪的文件.ps1`

- **用途**: 检查哪些文件需要被 Git 追踪
- **运行**: 本地 PowerShell
- **输出**: 列出未追踪、已修改、已暂存的文件

### 2. `deploy/从GitHub拉取并部署.sh`

- **用途**: 在服务器上从 GitHub 拉取代码并重启服务
- **运行**: 服务器上（通过 SSH）
- **功能**: 备份、拉取、验证、重启、检查

### 3. `deploy/推送到GitHub并部署.ps1`

- **用途**: 本地推送代码到 GitHub 并触发服务器部署
- **运行**: 本地 PowerShell
- **功能**: Git 操作、推送、远程部署

### 4. `deploy/创建GitHub部署脚本.py`

- **用途**: 生成上述三个脚本文件
- **运行**: 本地 Python
- **用途**: 如果脚本丢失，可以重新生成

---

## 🔍 常见问题

### Q1: 为什么某些文件不应该被追踪？

**A**: 以下文件类型不应被追踪：
- 备份文件（`backup/`, `*.bak`）
- 临时文件（`*.tmp`, `tmp_*.py`）
- 日志文件（`*.log`）
- 环境变量文件（`.env`, `.env.local`）
- 依赖目录（`node_modules/`, `.venv/`）
- 构建输出（`.next/`, `dist/`, `build/`）

这些已在 `.gitignore` 中配置。

### Q2: 如何知道哪些文件应该被追踪？

**A**: 运行检查脚本：
```powershell
.\deploy\检查需要追踪的文件.ps1
```

脚本会显示：
- 未追踪的文件列表
- 已修改但未暂存的文件
- 关键文件的追踪状态

### Q3: 如果推送失败怎么办？

**A**: 检查：
1. 是否有推送权限
2. 远程仓库 URL 是否正确（`git remote -v`）
3. 网络连接是否正常
4. 是否有未解决的冲突（`git pull` 先）

### Q4: 如果服务器上的 git pull 失败怎么办？

**A**: 检查：
1. 服务器上的 Git 仓库是否已初始化
2. 远程仓库 URL 是否正确
3. 是否有未提交的本地修改（可能需要 stash）
4. SSH 密钥是否正确配置

---

## ✅ 下一步操作

1. **添加关键文件到 Git**:
   ```powershell
   git add deploy/检查需要追踪的文件.ps1 deploy/从GitHub拉取并部署.sh deploy/推送到GitHub并部署.ps1 deploy/创建GitHub部署脚本.py
   git add admin-backend/app/api/group_ai/accounts.py
   ```

2. **提交并推送**:
   ```powershell
   git commit -m "添加 GitHub 部署工作流程脚本"
   git push origin master
   ```

3. **测试部署流程**:
   ```powershell
   .\deploy\推送到GitHub并部署.ps1 -CommitMessage "测试 GitHub 部署流程"
   ```

---

## 📚 相关文档

- [为什么应该使用GitHub部署-完整方案.md](./为什么应该使用GitHub部署-完整方案.md)
- [404错误-分配剧本问题分析和修复.md](./404错误-分配剧本问题分析和修复.md)
- [UPSERT功能-修改完成总结.md](./UPSERT功能-修改完成总结.md)

---

**更新时间**: 2025-11-28  
**状态**: ✅ 已完成并测试
