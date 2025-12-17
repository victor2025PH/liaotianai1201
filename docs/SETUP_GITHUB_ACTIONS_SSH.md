# 设置 GitHub Actions SSH 认证（快速指南）

## 🚀 快速设置（3 步）

### 步骤 1：生成专用 SSH 密钥（在本地执行）

```bash
# Windows PowerShell 或 Git Bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_deploy -N ""
```

**重要：** 当提示输入 passphrase 时，直接按 Enter（留空），这样 GitHub Actions 才能自动使用。

### 步骤 2：将公钥添加到服务器

```bash
# 方法 A：使用 ssh-copy-id（推荐）
ssh-copy-id -i ~/.ssh/github_deploy.pub ubuntu@your-server-ip

# 方法 B：手动添加
cat ~/.ssh/github_deploy.pub
# 复制输出的内容，然后：
ssh ubuntu@your-server-ip
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# 粘贴公钥内容，保存退出
chmod 600 ~/.ssh/authorized_keys
exit
```

### 步骤 3：将私钥添加到 GitHub Secrets

1. **复制私钥内容**：
   ```bash
   cat ~/.ssh/github_deploy
   ```
   
   复制**完整内容**，包括：
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   ...
   -----END OPENSSH PRIVATE KEY-----
   ```

2. **添加到 GitHub Secrets**：
   - 打开 GitHub 仓库：`https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions`
   - 点击 **New repository secret**
   - Name: `SERVER_SSH_KEY`
   - Secret: 粘贴刚才复制的私钥内容
   - 点击 **Add secret**

3. **检查其他 Secrets**：
   - `SERVER_HOST`: 服务器 IP（例如：`165.154.254.24`）
   - `SERVER_USER`: `ubuntu`

---

## ✅ 验证设置

### 本地测试

```bash
# 测试 SSH 连接
ssh -i ~/.ssh/github_deploy ubuntu@your-server-ip "echo 'SSH 连接成功！'"
```

如果成功，说明配置正确。

### GitHub Actions 测试

1. 在 GitHub 仓库页面，点击 **Actions** 标签
2. 找到失败的部署，点击 **Re-run jobs**
3. 查看日志，应该不再出现 SSH 认证错误

---

## 🔧 故障排查

### 问题 1：仍然显示认证失败

**检查清单：**
- [ ] 私钥是否完整复制（包括 `-----BEGIN` 和 `-----END` 行）
- [ ] GitHub Secrets 中的 `SERVER_SSH_KEY` 是否正确
- [ ] 服务器上的 `authorized_keys` 文件权限是否为 600
- [ ] `.ssh` 目录权限是否为 700

**修复命令（在服务器上执行）：**
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 问题 2：权限被拒绝（Permission denied）

**检查 SSH 配置（在服务器上）：**
```bash
sudo nano /etc/ssh/sshd_config
```

确保以下设置：
```
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication yes  # 临时启用，测试后可以关闭
```

重启 SSH 服务：
```bash
sudo systemctl restart sshd
```

### 问题 3：GitHub Actions 中的私钥格式错误

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
- ❌ 使用了错误的密钥类型（应该使用 RSA 或 Ed25519）

---

## 📝 完整示例

假设您的服务器 IP 是 `165.154.254.24`：

```bash
# 1. 生成密钥
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_deploy -N ""

# 2. 添加到服务器
ssh-copy-id -i ~/.ssh/github_deploy.pub ubuntu@165.154.254.24

# 3. 测试连接
ssh -i ~/.ssh/github_deploy ubuntu@165.154.254.24 "echo '成功！'"

# 4. 复制私钥到剪贴板（Windows）
cat ~/.ssh/github_deploy | clip

# 然后粘贴到 GitHub Secrets > SERVER_SSH_KEY
```

---

## 🎯 下一步

SSH 认证配置完成后，GitHub Actions 部署应该可以正常工作。如果还有问题，请检查：

1. 服务器防火墙是否允许 SSH 连接（端口 22）
2. GitHub Actions 工作流中的 `host` 和 `username` 是否正确
3. 部署脚本是否使用了正确的服务管理方式（PM2 而不是 systemd）
