# SSH Key 配置完整指南

## 🔴 当前问题

GitHub Actions 部署失败，错误信息：
```
ssh: handshake failed: ssh: unable to authenticate, attempted methods [none publickey], no supported methods remain
```

这说明 SSH Key 认证失败。

## ✅ 解决步骤

### 步骤 1: 在服务器上生成或检查 SSH Key

**登录服务器后执行：**

```bash
# 检查是否已有 SSH Key
ls -la ~/.ssh/

# 如果没有，生成新的 SSH Key（推荐 ed25519）
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/id_ed25519 -N ""

# 或者使用 RSA（如果 ed25519 不支持）
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/id_rsa -N ""
```

**重要：生成密钥时，直接按 Enter（不设置密码）**

### 步骤 2: 将公钥添加到 authorized_keys

```bash
# 查看公钥内容
cat ~/.ssh/id_ed25519.pub
# 或
cat ~/.ssh/id_rsa.pub

# 将公钥添加到 authorized_keys（如果不存在则创建）
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 步骤 3: 获取私钥内容

```bash
# 查看私钥（完整内容，包括 BEGIN 和 END 行）
cat ~/.ssh/id_ed25519
# 或
cat ~/.ssh/id_rsa
```

**复制完整的私钥内容**（包括 `-----BEGIN` 和 `-----END` 行）

### 步骤 4: 配置 GitHub Secrets

1. 打开：https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions

2. 更新或创建以下 Secrets：

   - **SERVER_HOST**: 服务器 IP（例如：`165.154.235.170`）
   - **SERVER_USER**: SSH 用户名（例如：`ubuntu`）
   - **SERVER_SSH_KEY**: 粘贴步骤 3 中复制的**完整私钥内容**

3. **SSH Key 格式要求：**
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   [密钥内容，多行]
   -----END OPENSSH PRIVATE KEY-----
   ```
   或
   ```
   -----BEGIN RSA PRIVATE KEY-----
   [密钥内容，多行]
   -----END RSA PRIVATE KEY-----
   ```

   **重要：**
   - 必须包含 `-----BEGIN` 和 `-----END` 行
   - 每行末尾不要有多余空格
   - 必须是私钥，不是公钥

### 步骤 5: 测试 SSH 连接

**在本地 PowerShell 测试（可选）：**

```powershell
# 使用服务器上的私钥测试连接
ssh -i ~/.ssh/id_ed25519 ubuntu@165.154.235.170 "echo 'SSH 测试成功'"
```

**或在服务器上测试本地连接：**

```bash
# 测试本地 SSH 连接
ssh localhost "echo '本地 SSH 测试成功'"
```

### 步骤 6: 验证 GitHub Actions

1. 推送代码到 GitHub
2. 查看 GitHub Actions 运行日志
3. 如果仍然失败，检查日志中的具体错误信息

## 🔍 故障排除

### 问题 1: 仍然认证失败

**检查服务器 SSH 配置：**

```bash
# 检查 SSH 服务配置
sudo nano /etc/ssh/sshd_config

# 确保以下配置：
# PubkeyAuthentication yes
# AuthorizedKeysFile .ssh/authorized_keys
# PasswordAuthentication no  # 可选，禁用密码登录

# 重启 SSH 服务
sudo systemctl restart sshd
```

### 问题 2: 权限错误

**修复权限：**

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/id_ed25519  # 或 id_rsa
```

### 问题 3: 查看 SSH 日志

**在服务器上查看 SSH 认证日志：**

```bash
# 实时查看 SSH 日志
sudo tail -f /var/log/auth.log

# 或使用 journalctl
sudo journalctl -u ssh -f
```

## ✅ 验证清单

- [ ] 服务器上已生成 SSH Key
- [ ] 公钥已添加到 `~/.ssh/authorized_keys`
- [ ] `authorized_keys` 权限为 600
- [ ] `.ssh` 目录权限为 700
- [ ] GitHub Secrets 中配置了完整的私钥
- [ ] 私钥包含 `-----BEGIN` 和 `-----END` 行
- [ ] 测试 SSH 连接成功

## 📝 下一步

配置完成后：
1. 推送代码到 GitHub
2. 触发新的工作流运行
3. 查看日志确认 SSH 连接成功

