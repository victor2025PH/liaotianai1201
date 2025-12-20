# 修复 GitHub Actions SSH 部署错误

## 🚨 错误信息

```
ssh: unexpected packet in response to channel open: <nil>
```

这个错误表示 SSH 通道打开时遇到了协议问题。

---

## 🔧 解决方案

### 方案 1：检查 SSH 密钥格式（最重要）

确保 GitHub Secrets 中的 `SERVER_SSH_KEY` 格式正确：

1. **密钥必须包含完整的头部和尾部：**
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   ...密钥内容...
   -----END OPENSSH PRIVATE KEY-----
   ```

2. **检查密钥格式：**
   - 确保没有多余的空格
   - 确保每行末尾没有多余字符
   - 确保密钥是私钥，不是公钥

3. **重新生成密钥（如果需要）：**
   ```bash
   # 在本地生成新的 SSH 密钥
   ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy
   
   # 将公钥添加到服务器
   ssh-copy-id -i ~/.ssh/github_actions_deploy.pub ubuntu@your-server-ip
   
   # 复制私钥内容到 GitHub Secrets
   cat ~/.ssh/github_actions_deploy
   ```

### 方案 2：检查服务器 SSH 配置

在服务器上执行：

```bash
# 检查 SSH 服务状态
sudo systemctl status sshd

# 检查 SSH 配置
sudo nano /etc/ssh/sshd_config

# 确保以下配置正确：
# PubkeyAuthentication yes
# AuthorizedKeysFile .ssh/authorized_keys
# MaxStartups 10:30:100
# MaxSessions 10

# 重启 SSH 服务
sudo systemctl restart sshd
```

### 方案 3：检查服务器权限

```bash
# 在服务器上执行
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 方案 4：使用更新的 Action 版本

已更新 workflow 文件，添加了：
- SSH 连接测试步骤
- 备用下载方案（如果 SCP 失败，从 GitHub 直接下载脚本）
- 更详细的调试信息

---

## 📋 已实施的修复

1. ✅ **添加 SSH 连接测试步骤** - 在 SCP 之前测试连接
2. ✅ **添加备用下载方案** - 如果 SCP 失败，从 GitHub 直接下载脚本
3. ✅ **增加超时时间** - 从 300s 增加到更合理的值
4. ✅ **添加调试模式** - 启用 `debug: true` 获取更多信息

---

## 🔍 诊断步骤

### 步骤 1：本地测试 SSH 连接

```bash
# 使用相同的密钥测试
ssh -i ~/.ssh/github_actions_deploy -v ubuntu@your-server-ip "echo 'SSH 连接成功'"
```

### 步骤 2：测试 SCP 功能

```bash
# 测试文件传输
scp -i ~/.ssh/github_actions_deploy -v scripts/server/deploy.sh ubuntu@your-server-ip:/tmp/
```

### 步骤 3：检查 GitHub Secrets

在 GitHub 仓库设置中验证：
- `SERVER_HOST`: 服务器 IP 地址
- `SERVER_USER`: SSH 用户名（通常是 `ubuntu`）
- `SERVER_SSH_KEY`: 完整的私钥内容

---

## ✅ 验证修复

修复后，重新运行部署：

1. 访问 GitHub Actions 页面
2. 点击 "Deploy to Server" 工作流
3. 点击 "Run workflow" 手动触发
4. 查看日志，确认 SSH 连接测试通过
5. 确认 SCP 上传成功，或备用下载方案生效

---

## 📝 注意事项

- 如果 SCP 持续失败，备用方案会从 GitHub 直接下载脚本
- 确保 `scripts/server/deploy.sh` 文件在仓库中可访问
- 如果使用备用方案，确保服务器可以访问 GitHub（可能需要代理）

---

## 🔗 相关文档

- [SSH 连接问题排查](./SSH_CONNECTION_TROUBLESHOOTING.md)
- [GitHub Actions SSH 设置](./SETUP_GITHUB_ACTIONS_SSH.md)
- [手动触发部署](./MANUAL_TRIGGER_DEPLOYMENT.md)
