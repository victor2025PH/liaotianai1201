# 设置 GitHub Actions SSH Key（Windows 详细指南）

## 🚀 快速开始

### 方法 1：使用自动化脚本（推荐）

我们提供了一个 PowerShell 脚本来自动化整个过程：

```powershell
# 在项目根目录执行
.\scripts\local\setup-github-actions-ssh-windows.ps1 -ServerIP "10.56.61.200" -ServerUser "deployer"
```

脚本会自动：
1. ✅ 生成 SSH 密钥对
2. ✅ 将公钥添加到服务器
3. ✅ 测试 SSH 连接
4. ✅ 显示私钥内容（用于 GitHub Secrets）

---

### 方法 2：手动步骤

如果脚本无法使用，可以按照以下步骤手动配置：

---

## 📋 详细步骤

### 步骤 1：生成 SSH 密钥对

在 **PowerShell** 或 **Git Bash** 中执行：

```powershell
# 检查 .ssh 目录是否存在
if (-not (Test-Path $env:USERPROFILE\.ssh)) {
    New-Item -ItemType Directory -Path $env:USERPROFILE\.ssh -Force
}

# 生成 SSH 密钥（无密码，用于自动化）
ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\github_deploy" -N ""
```

**重要提示：**
- 当提示 "Enter passphrase" 时，直接按 **Enter**（留空）
- 当提示 "Enter same passphrase again" 时，再次按 **Enter**

---

### 步骤 2：将公钥添加到服务器

#### 方法 A：使用脚本自动添加（推荐）

运行自动化脚本会自动处理这一步。

#### 方法 B：手动添加

**2.1 查看公钥内容：**

```powershell
# 在 PowerShell 中
Get-Content $env:USERPROFILE\.ssh\github_deploy.pub

# 或使用 Git Bash
cat ~/.ssh/github_deploy.pub
```

**2.2 复制输出的公钥内容**（以 `ssh-rsa` 开头，以您的邮箱或主机名结尾）

**2.3 登录服务器并添加公钥：**

```powershell
# 使用密码登录服务器（首次需要）
ssh deployer@10.56.61.200
```

**在服务器上执行：**

```bash
# 创建 .ssh 目录（如果不存在）
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 编辑 authorized_keys 文件
nano ~/.ssh/authorized_keys

# 在文件末尾粘贴公钥内容（另起一行）
# 保存退出：Ctrl+X, Y, Enter

# 设置正确的权限
chmod 600 ~/.ssh/authorized_keys

# 退出服务器
exit
```

#### 方法 C：使用单行命令（如果已配置密码登录）

```powershell
# 读取公钥内容
$publicKey = Get-Content $env:USERPROFILE\.ssh\github_deploy.pub -Raw

# 添加到服务器（需要输入密码）
ssh deployer@10.56.61.200 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$($publicKey.Trim())' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

---

### 步骤 3：测试 SSH 密钥认证

```powershell
# 使用专用密钥测试连接
ssh -i $env:USERPROFILE\.ssh\github_deploy deployer@10.56.61.200 "echo 'SSH 密钥认证成功！'"
```

**如果成功：**
- ✅ 不需要输入密码
- ✅ 直接返回 "SSH 密钥认证成功！"

**如果失败：**
- 检查服务器上的权限（见故障排查部分）
- 确认公钥是否正确添加到 `authorized_keys`

---

### 步骤 4：将私钥添加到 GitHub Secrets

**4.1 查看私钥内容：**

```powershell
# 在 PowerShell 中
Get-Content $env:USERPROFILE\.ssh\github_deploy

# 或复制到剪贴板（Windows）
Get-Content $env:USERPROFILE\.ssh\github_deploy | Set-Clipboard
```

**4.2 复制完整私钥内容**（包括以下部分）：
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAACFwAAAAdzc2gtcn
...（更多行）...
-----END OPENSSH PRIVATE KEY-----
```

**4.3 添加到 GitHub Secrets：**

1. 打开 GitHub 仓库设置：
   ```
   https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions
   ```

2. 点击 **"New repository secret"**

3. 添加以下 Secrets：

   **Secret 1: SERVER_SSH_KEY**
   - Name: `SERVER_SSH_KEY`
   - Secret: 粘贴刚才复制的**完整私钥内容**（包括 BEGIN 和 END 行）
   - 点击 **"Add secret"**

   **Secret 2: SERVER_HOST**
   - Name: `SERVER_HOST`
   - Secret: `10.56.61.200`（您的服务器 IP）
   - 点击 **"Add secret"**

   **Secret 3: SERVER_USER**
   - Name: `SERVER_USER`
   - Secret: `deployer`
   - 点击 **"Add secret"**

---

### 步骤 5：验证配置

#### 本地验证

```powershell
# 测试 SSH 连接（应该不需要密码）
ssh -i $env:USERPROFILE\.ssh\github_deploy deployer@10.56.61.200 "echo '测试成功'"
```

#### GitHub Actions 验证

1. 在 GitHub 仓库页面，点击 **"Actions"** 标签
2. 找到最新的部署工作流，点击 **"Re-run jobs"**
3. 查看日志，应该不再出现 SSH 认证错误

---

## 🔧 故障排查

### 问题 1：SSH 连接仍然需要密码

**检查清单：**

```bash
# 在服务器上检查权限
ls -la ~/.ssh/
# authorized_keys 应该显示权限为 -rw------- (600)
# .ssh 目录应该显示权限为 drwx------ (700)

# 如果权限不对，修复：
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

**检查 authorized_keys 内容：**

```bash
# 在服务器上
cat ~/.ssh/authorized_keys
# 应该包含您的公钥内容
```

---

### 问题 2：GitHub Actions 仍然显示认证失败

**检查：**

1. **私钥格式是否正确**
   - ✅ 必须包含 `-----BEGIN OPENSSH PRIVATE KEY-----`
   - ✅ 必须包含 `-----END OPENSSH PRIVATE KEY-----`
   - ✅ 不能有多余的空格或换行

2. **GitHub Secrets 是否正确**
   - 检查 `SERVER_SSH_KEY` 是否包含完整私钥
   - 检查 `SERVER_HOST` 是否为 `10.56.61.200`
   - 检查 `SERVER_USER` 是否为 `deployer`

3. **服务器 SSH 配置**

```bash
# 在服务器上检查 SSH 配置
sudo nano /etc/ssh/sshd_config

# 确保以下设置：
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication yes  # 临时启用用于测试

# 重启 SSH 服务
sudo systemctl restart ssh
```

---

### 问题 3：PowerShell 脚本执行失败

**如果出现执行策略错误：**

```powershell
# 临时允许执行脚本（当前会话）
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# 然后再次运行脚本
.\scripts\local\setup-github-actions-ssh-windows.ps1
```

**如果 ssh-keygen 命令不存在：**

- Windows 10 1809+ 和 Windows 11 自带 OpenSSH
- 如果不存在，可以安装：
  - 通过 Windows 设置 > 应用 > 可选功能 > OpenSSH 客户端
  - 或使用 Git for Windows（包含 OpenSSH）

---

## 📝 完整示例（使用脚本）

```powershell
# 1. 切换到项目目录
cd D:\telegram-ai-system

# 2. 运行自动化脚本
.\scripts\local\setup-github-actions-ssh-windows.ps1 -ServerIP "10.56.61.200" -ServerUser "deployer"

# 3. 按照脚本提示操作：
#    - 脚本会自动生成密钥
#    - 自动添加公钥到服务器（可能需要输入密码）
#    - 显示私钥内容并复制到剪贴板

# 4. 将私钥粘贴到 GitHub Secrets > SERVER_SSH_KEY

# 5. 测试 GitHub Actions 部署
```

---

## ✅ 验证清单

配置完成后，确认：

- [ ] SSH 密钥已生成（`github_deploy` 和 `github_deploy.pub`）
- [ ] 公钥已添加到服务器的 `~/.ssh/authorized_keys`
- [ ] 本地 SSH 测试成功（不需要密码）
- [ ] GitHub Secrets 已配置：
  - [ ] `SERVER_SSH_KEY`（完整私钥内容）
  - [ ] `SERVER_HOST`（服务器 IP）
  - [ ] `SERVER_USER`（`deployer`）
- [ ] GitHub Actions 部署测试成功

---

## 🎯 下一步

SSH 认证配置完成后：

1. ✅ 测试 GitHub Actions 自动部署
2. ✅ 验证部署是否成功
3. ✅ 检查服务器上的服务是否正常更新

---

## 📚 相关文档

- `docs/SETUP_GITHUB_ACTIONS_SSH.md` - 通用 SSH 配置指南（Linux/Mac）
- `docs/DEPLOYMENT_COMPLETE_GUIDE.md` - 完整部署指南

---

**配置完成后，GitHub Actions 就可以自动部署到您的服务器了！** 🎉
