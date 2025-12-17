# GitHub Actions SSH 认证故障排查

## 快速诊断

运行诊断脚本：

```powershell
cd d:\telegram-ai-system
.\scripts\local\diagnose-ssh-setup.ps1
```

---

## 常见问题和解决方案

### 问题 1：仍然显示 "ssh: handshake failed"

#### 检查清单：

1. **GitHub Secrets 中的私钥格式**
   - ✅ 私钥必须完整（包括 `-----BEGIN` 和 `-----END` 行）
   - ✅ 使用 Unix 换行符（LF），不是 Windows 换行符（CRLF）
   - ✅ 没有多余的空格或换行

2. **验证私钥格式**
   ```powershell
   # 查看私钥
   cat "$env:USERPROFILE\.ssh\github_deploy"
   
   # 应该看到类似这样的内容：
   # -----BEGIN OPENSSH PRIVATE KEY-----
   # b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAACFwAAAAdzc2gtcn
   # ...（更多行）...
   # -----END OPENSSH PRIVATE KEY-----
   ```

3. **重新复制私钥到 GitHub Secrets**
   - 打开：https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions
   - 找到 `SERVER_SSH_KEY`，点击 **Update**
   - 删除旧内容
   - 重新从文件复制并粘贴

---

### 问题 2：本地 SSH 连接成功，但 GitHub Actions 失败

#### 可能原因：

1. **换行符问题**
   - Windows 使用 CRLF（`\r\n`）
   - Linux/GitHub Actions 需要 LF（`\n`）
   
   **解决方案：** 使用诊断脚本生成的 Unix 格式私钥

2. **私钥权限问题**
   - GitHub Actions 中私钥应该作为 Secret 存储
   - 确保完整复制了私钥内容

3. **服务器配置问题**
   ```bash
   # 在服务器上检查
   ls -la ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   ```

---

### 问题 3：GitHub Secrets 配置不正确

#### 验证步骤：

1. **检查所有必需的 Secrets**
   - `SERVER_HOST`: 应该是 `165.154.254.24`
   - `SERVER_USER`: 应该是 `ubuntu`
   - `SERVER_SSH_KEY`: 完整的私钥内容

2. **验证私钥格式**
   - 必须以 `-----BEGIN` 开头
   - 必须以 `-----END` 结尾
   - 中间应该有多个字符行

---

### 问题 4：服务器拒绝连接

#### 检查服务器配置：

```bash
# SSH 登录服务器
ssh ubuntu@165.154.254.24

# 检查 SSH 配置
sudo nano /etc/ssh/sshd_config

# 确保以下设置：
# PubkeyAuthentication yes
# AuthorizedKeysFile .ssh/authorized_keys
# PasswordAuthentication yes  # 临时启用，测试后可以关闭

# 重启 SSH 服务
sudo systemctl restart sshd

# 检查日志
sudo tail -f /var/log/auth.log
```

---

## 手动修复步骤

### 步骤 1：重新生成私钥的 Unix 格式

```powershell
# 读取私钥并转换为 Unix 格式
$privateKey = Get-Content "$env:USERPROFILE\.ssh\github_deploy" -Raw
$privateKeyUnix = $privateKey -replace "`r`n", "`n" -replace "`r", "`n"

# 保存为临时文件
$tempFile = "$env:TEMP\github_deploy_unix.txt"
$privateKeyUnix.Trim() | Out-File -FilePath $tempFile -Encoding UTF8 -NoNewline

# 查看内容
cat $tempFile

# 复制到剪贴板
cat $tempFile | Set-Clipboard
```

### 步骤 2：更新 GitHub Secrets

1. 打开：https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions
2. 找到 `SERVER_SSH_KEY`
3. 点击 **Update**
4. 删除所有内容
5. 粘贴新的 Unix 格式私钥
6. 点击 **Update secret**

### 步骤 3：测试部署

1. 在 GitHub 仓库页面，点击 **Actions**
2. 找到失败的部署
3. 点击 **Re-run jobs**
4. 查看日志

---

## 验证命令

### 本地验证

```powershell
# 测试 SSH 连接
ssh -i "$env:USERPROFILE\.ssh\github_deploy" ubuntu@165.154.254.24 "echo '测试成功'"

# 应该不需要输入密码，直接返回 "测试成功"
```

### 服务器端验证

```bash
# 检查 authorized_keys
cat ~/.ssh/authorized_keys

# 检查权限
ls -la ~/.ssh/
# 应该显示：
# drwx------ 2 ubuntu ubuntu ... .ssh
# -rw------- 1 ubuntu ubuntu ... authorized_keys
```

---

## 如果仍然失败

1. **查看 GitHub Actions 日志**
   - 找到具体的错误信息
   - 检查是否还有其他问题

2. **尝试使用密码认证临时测试**
   - 确认服务器网络连接正常
   - 确认防火墙允许 SSH

3. **检查服务器日志**
   ```bash
   sudo tail -50 /var/log/auth.log | grep ssh
   ```

4. **重新生成密钥对**
   ```powershell
   # 删除旧密钥
   Remove-Item "$env:USERPROFILE\.ssh\github_deploy*"
   
   # 重新生成
   ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\github_deploy" -C "github-actions-deploy"
   
   # 重新添加到服务器
   # ...（按照之前的步骤）
   ```

---

## 联系支持

如果以上步骤都无法解决问题，请提供：
1. GitHub Actions 日志中的完整错误信息
2. 诊断脚本的输出
3. 本地 SSH 测试的结果
