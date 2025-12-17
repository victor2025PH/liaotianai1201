# 修复 GitHub Actions SSH 认证失败

## 问题症状

```
ssh: handshake failed: ssh: unable to authenticate, attempted methods [none publickey], no supported methods remain
```

这表明 GitHub Actions 无法通过 SSH 连接到服务器。

---

## 解决方案

### 方法一：重新配置 GitHub Secrets（推荐）

#### 步骤 1：在本地生成 SSH 密钥对（如果没有）

```bash
# 在本地 PowerShell 或 Git Bash 执行
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions_deploy -N ""
```

这会生成两个文件：
- `~/.ssh/github_actions_deploy`（私钥）
- `~/.ssh/github_actions_deploy.pub`（公钥）

#### 步骤 2：将公钥添加到服务器

```bash
# 查看公钥内容
cat ~/.ssh/github_actions_deploy.pub

# 复制公钥内容，然后登录服务器并执行：
ssh ubuntu@your-server-ip

# 在服务器上执行：
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "您的公钥内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

或者使用 `ssh-copy-id`：

```bash
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub ubuntu@your-server-ip
```

#### 步骤 3：将私钥添加到 GitHub Secrets

1. 打开 GitHub 仓库页面
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 找到 `SERVER_SSH_KEY` secret，点击 **Update**
4. 复制私钥内容（`~/.ssh/github_actions_deploy` 文件的全部内容）
5. 粘贴到 **Secret value** 字段
6. 点击 **Update secret**

**重要：** 私钥内容应该包括：
```
-----BEGIN OPENSSH PRIVATE KEY-----
...密钥内容...
-----END OPENSSH PRIVATE KEY-----
```

#### 步骤 4：验证其他 Secrets

确保以下 Secrets 都已正确配置：

- `SERVER_HOST`: 服务器 IP 地址（例如：`165.154.254.24`）
- `SERVER_USER`: SSH 用户名（通常是 `ubuntu`）
- `SERVER_SSH_KEY`: SSH 私钥（完整内容）

#### 步骤 5：测试 SSH 连接

在本地测试 SSH 密钥是否工作：

```bash
ssh -i ~/.ssh/github_actions_deploy ubuntu@your-server-ip "echo 'SSH 连接成功！'"
```

如果成功，说明密钥配置正确。

---

### 方法二：使用现有 SSH 密钥

如果您已经有可以登录服务器的 SSH 密钥：

1. **查看现有公钥**：
   ```bash
   cat ~/.ssh/id_rsa.pub
   ```

2. **确保公钥已添加到服务器**：
   ```bash
   ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@your-server-ip
   ```

3. **将私钥添加到 GitHub Secrets**：
   ```bash
   cat ~/.ssh/id_rsa
   ```
   
   复制完整的私钥内容（包括 `-----BEGIN` 和 `-----END` 行），然后更新 GitHub Secrets 中的 `SERVER_SSH_KEY`。

---

## 验证修复

1. 在 GitHub Actions 页面，点击 **Re-run jobs**
2. 查看部署日志，应该不再出现 SSH 认证错误

---

## 常见问题

### Q: 为什么会出现认证失败？

A: 可能的原因：
- GitHub Secrets 中的私钥格式不正确（缺少换行符或 `-----BEGIN`/`-----END` 标记）
- 服务器上的 `authorized_keys` 文件权限不正确
- 私钥和公钥不匹配
- 服务器上的 SSH 配置不允许密钥认证

### Q: 如何检查服务器上的 SSH 配置？

```bash
# 在服务器上执行
sudo nano /etc/ssh/sshd_config

# 确保以下设置：
# PubkeyAuthentication yes
# AuthorizedKeysFile .ssh/authorized_keys

# 检查后重启 SSH 服务
sudo systemctl restart sshd
```

### Q: 如何查看详细的 SSH 连接日志？

在 GitHub Actions 工作流中，`debug: true` 已经启用，但您也可以：

1. 在服务器上查看 SSH 日志：
   ```bash
   sudo tail -f /var/log/auth.log
   ```

2. 在本地测试时启用详细模式：
   ```bash
   ssh -v -i ~/.ssh/github_actions_deploy ubuntu@your-server-ip
   ```

---

## 下一步

SSH 认证修复后，还需要更新部署脚本以使用 PM2 而不是 systemd。请查看 `.github/workflows/deploy.yml` 的更新版本。
