# 修复 SSH 连接超时问题

## 🚨 错误信息

```
dial tcp ***:22: connect: connection timed out
```

这表明 GitHub Actions 无法在 30 秒内建立 SSH 连接到服务器。

---

## 配置检查清单

### ✅ 当前 GitHub Actions 配置

已确认以下配置正确：

```yaml
with:
  host: ${{ secrets.SERVER_HOST }}
  username: ${{ secrets.SERVER_USER }}
  key: ${{ secrets.SERVER_SSH_KEY }}
  port: 22
  timeout: 30s
  command_timeout: 30m
  script_stop: true
  debug: true
```

**所有必需的 Secrets 都已正确引用：**
- ✅ `SERVER_HOST`
- ✅ `SERVER_USER`
- ✅ `SERVER_SSH_KEY`

---

## 可能的原因和解决方案

### 1. 服务器防火墙阻止连接

**检查：**
```bash
# 在服务器上检查防火墙
sudo ufw status
sudo iptables -L -n | grep 22
```

**修复：**
```bash
# 允许 SSH（端口 22）
sudo ufw allow 22/tcp
sudo ufw reload
```

---

### 2. 服务器网络问题或停机

**检查：**
- 从本地能否 SSH 连接？
  ```bash
  ssh -v ubuntu@your-server-ip
  ```

- 服务器是否在运行？
  - 检查云服务商控制台
  - 检查服务器状态

---

### 3. SSH 服务未运行

**检查（在服务器上）：**
```bash
sudo systemctl status sshd
```

**修复：**
```bash
sudo systemctl start sshd
sudo systemctl enable sshd
```

---

### 4. 服务器 IP 地址变更

**检查：**
- GitHub Secrets 中的 `SERVER_HOST` 是否是当前服务器 IP？
- 服务器 IP 是否已变更？

---

### 5. 30 秒超时太短

如果服务器响应慢，30 秒可能不够。可以增加超时：

```yaml
timeout: 60s  # 增加到 60 秒
```

---

## 诊断步骤

### 步骤 1：本地测试 SSH 连接

```bash
# 从本地测试
ssh -v -o ConnectTimeout=30 ubuntu@your-server-ip

# 如果成功，说明服务器可访问
# 如果失败，检查网络或防火墙
```

### 步骤 2：验证 GitHub Secrets

在 GitHub 仓库设置中检查：
1. `SERVER_HOST`: 应该是服务器 IP（例如：`165.154.254.24`）
2. `SERVER_USER`: 应该是 `ubuntu`
3. `SERVER_SSH_KEY`: 应该是完整的私钥内容

### 步骤 3：检查服务器 SSH 配置

在服务器上检查：
```bash
# 检查 SSH 监听端口
sudo ss -tlnp | grep :22

# 检查 SSH 配置
sudo nano /etc/ssh/sshd_config

# 确保：
# Port 22
# PermitRootLogin no（或 yes，取决于需要）
# PasswordAuthentication yes（临时启用用于调试）
```

---

## 临时解决方案

### 如果 30 秒超时太短

如果服务器响应慢，可以临时增加超时：

```yaml
timeout: 60s  # 或 120s
```

但这需要修改工作流文件并重新提交。

---

## 验证修复

修复后，重新运行 GitHub Actions 部署：

1. 在 GitHub Actions 页面
2. 找到失败的部署
3. 点击 **Re-run jobs**
4. 查看日志，应该不再出现连接超时

---

## 如果仍然失败

1. **检查 GitHub Actions 日志**
   - 查看详细的 SSH 连接日志（`debug: true` 已启用）
   - 查看是否有其他错误信息

2. **从本地手动测试**
   ```bash
   # 使用相同的密钥测试
   ssh -i ~/.ssh/github_deploy -v ubuntu@your-server-ip
   ```

3. **检查服务器日志**
   ```bash
   # 在服务器上
   sudo tail -f /var/log/auth.log
   ```

4. **考虑增加超时时间**
   - 如果服务器响应确实很慢，可以增加到 60s 或 120s

---

## 配置文件位置

- 工作流文件：`.github/workflows/deploy.yml`
- GitHub Secrets：`https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions`

---

当前配置看起来正确。如果仍然超时，可能是：
1. 服务器网络问题
2. 防火墙阻止
3. 服务器响应太慢（30 秒不够）

请检查服务器状态和网络连接。
