# 快速修复 GitHub Actions SSH 认证失败

## 🚨 错误信息

```
ssh: handshake failed: ssh: unable to authenticate, attempted methods [none publickey], no supported methods remain
```

## ✅ 快速修复（5 分钟）

### 方法一：使用 PowerShell 脚本（推荐，Windows）

1. **在本地 PowerShell 执行脚本**：
   ```powershell
   cd d:\telegram-ai-system
   .\scripts\local\setup-github-actions-ssh.ps1 -ServerIP "165.154.254.24" -ServerUser "ubuntu"
   ```

   脚本会自动：
   - ✅ 生成 SSH 密钥对
   - ✅ 将公钥添加到服务器
   - ✅ 测试连接
   - ✅ 显示私钥内容供您复制

2. **复制私钥到 GitHub Secrets**：
   - 打开：https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions
   - 找到 `SERVER_SSH_KEY`，点击 **Update**
   - 粘贴脚本输出的私钥内容（包括 `-----BEGIN` 和 `-----END` 行）
   - 点击 **Update secret**

3. **验证部署**：
   - 在 GitHub Actions 页面，点击 **Re-run jobs**

---

### 方法二：手动设置（所有平台）

#### 步骤 1：生成 SSH 密钥

```bash
# Windows PowerShell 或 Git Bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_deploy -N ""
```

**重要：** 提示输入 passphrase 时，直接按 Enter（留空）。

#### 步骤 2：查看公钥

```bash
cat ~/.ssh/github_deploy.pub
```

复制输出的内容（类似：`ssh-rsa AAAA... your-email@example.com`）

#### 步骤 3：将公钥添加到服务器

**方法 A：使用 ssh-copy-id**
```bash
ssh-copy-id -i ~/.ssh/github_deploy.pub ubuntu@165.154.254.24
```

**方法 B：手动添加**
```bash
# 1. 登录服务器
ssh ubuntu@165.154.254.24

# 2. 在服务器上执行
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# 粘贴公钥内容，保存退出（Ctrl+X, Y, Enter）
chmod 600 ~/.ssh/authorized_keys
exit
```

#### 步骤 4：测试连接

```bash
ssh -i ~/.ssh/github_deploy ubuntu@165.154.254.24 "echo '成功！'"
```

如果成功，说明密钥配置正确。

#### 步骤 5：复制私钥到 GitHub Secrets

```bash
# 查看私钥
cat ~/.ssh/github_deploy
```

**复制完整内容**（包括 `-----BEGIN` 和 `-----END` 行），然后：

1. 打开：https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions
2. 找到 `SERVER_SSH_KEY`，点击 **Update**
3. 粘贴私钥内容
4. 点击 **Update secret**

#### 步骤 6：检查其他 Secrets

确保以下 Secrets 都已正确配置：

- `SERVER_HOST`: `165.154.254.24`（您的服务器 IP）
- `SERVER_USER`: `ubuntu`
- `SERVER_SSH_KEY`: （刚才添加的私钥）

---

## 🔍 验证修复

### 本地测试

```bash
ssh -i ~/.ssh/github_deploy ubuntu@165.154.254.24 "echo 'SSH 连接成功！'"
```

### GitHub Actions 测试

1. 在 GitHub 仓库页面，点击 **Actions**
2. 找到失败的部署
3. 点击 **Re-run jobs**
4. 查看日志，应该不再出现 SSH 认证错误

---

## ❓ 常见问题

### Q: 仍然显示认证失败？

**检查清单：**
- [ ] 私钥是否完整复制（包括 `-----BEGIN` 和 `-----END` 行）
- [ ] GitHub Secrets 中的 `SERVER_SSH_KEY` 是否正确
- [ ] 服务器上的 `authorized_keys` 文件权限是否为 600
- [ ] `.ssh` 目录权限是否为 700

**修复权限（在服务器上执行）：**
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Q: 权限被拒绝（Permission denied）？

**检查服务器 SSH 配置：**
```bash
sudo nano /etc/ssh/sshd_config
```

确保：
```
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
```

重启 SSH 服务：
```bash
sudo systemctl restart sshd
```

### Q: 私钥格式错误？

**正确格式：**
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAACFwAAAAdzc2gtcn
...（更多行）...
-----END OPENSSH PRIVATE KEY-----
```

**常见错误：**
- ❌ 缺少 `-----BEGIN` 或 `-----END` 行
- ❌ 有额外的空格或换行
- ❌ 使用了错误的密钥类型

---

## 🎯 完成后的验证

执行以下命令验证所有配置：

```bash
# 1. 本地 SSH 测试
ssh -i ~/.ssh/github_deploy ubuntu@165.154.254.24 "echo '本地测试成功'"

# 2. 检查 GitHub Secrets（在 GitHub 网页上）
# - SERVER_HOST: 165.154.254.24
# - SERVER_USER: ubuntu
# - SERVER_SSH_KEY: （完整私钥）

# 3. 触发 GitHub Actions 部署
# - 在 GitHub 仓库页面
# - 点击 Actions
# - 找到失败的部署，点击 Re-run jobs
```

---

**修复完成后，GitHub Actions 部署应该可以正常工作！** 🎉
