# 配置 SSH 密钥认证 - 手动步骤

## 📋 步骤说明

### 步骤 1：检查是否已有 SSH 密钥

在 PowerShell 中执行：
```powershell
Test-Path $env:USERPROFILE\.ssh\id_rsa
Test-Path $env:USERPROFILE\.ssh\id_rsa.pub
```

- 如果返回 `True`，说明已有密钥，跳到步骤 3
- 如果返回 `False`，需要生成新密钥，继续步骤 2

### 步骤 2：生成 SSH 密钥对（如果没有）

在 PowerShell 中执行：
```powershell
ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\id_rsa"
```

**注意：**
- 如果提示 "Enter passphrase"，可以直接按 Enter（不设置密码）
- 如果提示 "Overwrite (y/n)"，输入 `y` 覆盖现有密钥

### 步骤 3：查看公钥内容

在 PowerShell 中执行：
```powershell
Get-Content $env:USERPROFILE\.ssh\id_rsa.pub
```

**复制输出的公钥内容**（以 `ssh-rsa` 开头，以你的邮箱结尾）

### 步骤 4：将公钥复制到服务器

**方法 A：使用 ssh-copy-id（如果可用）**

在 PowerShell 中执行：
```powershell
ssh-copy-id -i "$env:USERPROFILE\.ssh\id_rsa.pub" ubuntu@165.154.233.55
```

**需要输入一次服务器密码**

**方法 B：手动复制（如果 ssh-copy-id 不可用）**

1. **登录服务器**：
   ```powershell
   ssh ubuntu@165.154.233.55
   ```
   （需要输入密码）

2. **在服务器上执行**：
   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   nano ~/.ssh/authorized_keys
   ```

3. **在编辑器中**：
   - 粘贴之前复制的公钥内容
   - 保存并退出（Ctrl+X, Y, Enter）

4. **设置权限**：
   ```bash
   chmod 600 ~/.ssh/authorized_keys
   exit
   ```

### 步骤 5：测试无密码登录

在 PowerShell 中执行：
```powershell
ssh ubuntu@165.154.233.55 "echo 'SSH 密钥认证测试成功！'"
```

**如果成功：**
- 不需要输入密码
- 直接返回 "SSH 密钥认证测试成功！"

**如果失败：**
- 检查服务器上的权限：
  ```bash
  ls -la ~/.ssh/
  # authorized_keys 应该是 600
  # .ssh 目录应该是 700
  ```

## 🔧 故障排除

### 问题 1：仍然需要密码

**检查服务器权限：**
```bash
# 在服务器上执行
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
ls -la ~/.ssh/
```

**检查 SSH 配置：**
```bash
# 在服务器上执行
sudo nano /etc/ssh/sshd_config
# 确保以下配置：
# PubkeyAuthentication yes
# AuthorizedKeysFile .ssh/authorized_keys
```

### 问题 2：权限被拒绝

**检查日志：**
```bash
# 在服务器上执行
sudo tail -f /var/log/auth.log
# 或
sudo journalctl -u ssh -f
```

### 问题 3：ssh-copy-id 命令不存在

**Windows 上可能没有 ssh-copy-id**，使用手动方法（方法 B）

## ✅ 验证配置成功

配置成功后，执行以下命令应该**不需要密码**：

```powershell
ssh ubuntu@165.154.233.55 "whoami"
ssh ubuntu@165.154.233.55 "pwd"
ssh ubuntu@165.154.233.55 "echo '测试成功'"
```

## 🎯 下一步

配置成功后，可以：
1. 运行自动化修复脚本
2. 执行远程检查命令
3. 自动化部署和修复

