# GitHub Actions SSH 连接问题排查

## 问题：SSH Handshake Failed

如果遇到 `ssh: handshake failed: EOF` 错误，请按以下步骤排查：

### 1. 检查 GitHub Secrets 配置

确保以下 Secrets 已正确配置：
- `SERVER_HOST`: 服务器 IP 地址
- `SERVER_USER`: SSH 用户名（通常是 `ubuntu`）
- `SERVER_SSH_KEY`: SSH 私钥（完整内容，包括 `-----BEGIN OPENSSH PRIVATE KEY-----` 和 `-----END OPENSSH PRIVATE KEY-----`）

### 2. 验证 SSH 密钥格式

SSH 密钥应该是 OpenSSH 格式：
```
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

**重要**：
- 密钥必须包含完整的头部和尾部
- 密钥中不能有多余的空格或换行
- 确保密钥是私钥，不是公钥

### 3. 在服务器上验证 SSH 配置

```bash
# 检查 SSH 服务状态
sudo systemctl status sshd

# 检查 SSH 配置
sudo cat /etc/ssh/sshd_config | grep -E "PubkeyAuthentication|PasswordAuthentication|PermitRootLogin"

# 检查 authorized_keys
cat ~/.ssh/authorized_keys
```

### 4. 测试 SSH 连接

在本地测试 SSH 连接：
```bash
# 使用相同的密钥测试
ssh -i /path/to/private/key -v ubuntu@SERVER_HOST
```

### 5. 更新 GitHub Secrets

如果密钥过期或无效，需要重新生成：

```bash
# 在本地生成新的 SSH 密钥对
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions_key

# 将公钥添加到服务器
ssh-copy-id -i ~/.ssh/github_actions_key.pub ubuntu@SERVER_HOST

# 或者手动添加
cat ~/.ssh/github_actions_key.pub | ssh ubuntu@SERVER_HOST "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# 复制私钥内容到 GitHub Secrets
cat ~/.ssh/github_actions_key
```

### 6. 检查服务器防火墙

```bash
# 检查防火墙状态
sudo ufw status

# 确保 SSH 端口开放
sudo ufw allow 22/tcp
```

### 7. 检查服务器资源

```bash
# 检查磁盘空间
df -h

# 检查内存
free -h

# 检查系统负载
uptime
```

### 8. 临时解决方案

如果 SSH 连接持续失败，可以：

1. **使用密码认证（不推荐，仅用于测试）**：
   - 在 GitHub Actions 中使用 `password` 而不是 `key`
   - 确保服务器允许密码认证

2. **手动部署**：
   ```bash
   # 在服务器上手动执行
   cd /home/ubuntu/telegram-ai-system
   git pull origin main
   bash scripts/server/deploy.sh
   ```

### 9. 常见错误和解决方案

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `handshake failed: EOF` | SSH 密钥无效或格式错误 | 重新生成并配置密钥 |
| `connection refused` | 服务器 SSH 服务未运行 | 启动 SSH 服务：`sudo systemctl start sshd` |
| `permission denied` | 密钥权限问题 | 检查 `~/.ssh/authorized_keys` 权限 |
| `timeout` | 网络问题或防火墙 | 检查网络连接和防火墙设置 |

### 10. 联系支持

如果以上步骤都无法解决问题，请提供：
1. GitHub Actions 完整日志
2. 服务器 SSH 日志：`sudo tail -f /var/log/auth.log`
3. 服务器系统信息：`uname -a && cat /etc/os-release`

