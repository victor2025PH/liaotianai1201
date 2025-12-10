# GitHub Actions 部署问题排查指南

## 📋 问题排查步骤

### 步骤 1: 检查 GitHub Secrets 配置

**必须配置的 Secrets：**
- `SERVER_HOST`: 服务器 IP 地址（例如：`165.154.235.170`）
- `SERVER_USER`: SSH 用户名（例如：`ubuntu`）
- `SERVER_SSH_KEY`: SSH 私钥（完整内容，包括 `-----BEGIN` 和 `-----END` 行）

**检查方法：**
1. 打开：https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions
2. 确认三个 Secrets 都已配置
3. 检查 `SERVER_SSH_KEY` 格式是否正确

### 步骤 2: 验证 SSH Key 格式

**正确的 SSH Key 格式：**
```
-----BEGIN OPENSSH PRIVATE KEY-----
[密钥内容，多行]
-----END OPENSSH PRIVATE KEY-----
```

或者：
```
-----BEGIN RSA PRIVATE KEY-----
[密钥内容，多行]
-----END RSA PRIVATE KEY-----
```

**常见错误：**
- ❌ 缺少 `-----BEGIN` 或 `-----END` 行
- ❌ 每行末尾有多余空格
- ❌ 使用了公钥而不是私钥
- ❌ 密钥被截断

### 步骤 3: 测试 SSH 连接

**在服务器上验证 SSH Key：**
```bash
# 检查 authorized_keys
cat ~/.ssh/authorized_keys

# 检查权限
ls -la ~/.ssh/
# .ssh 目录应该是 700
# authorized_keys 应该是 600
```

### 步骤 4: 查看 GitHub Actions 日志

**查看最新运行：**
1. 打开：https://github.com/victor2025PH/liaotianai1201/actions
2. 点击最新的工作流运行
3. 点击 "Deploy to Server" 步骤
4. 查看详细日志，找出错误信息

**常见错误类型：**
1. **SSH 连接失败**
   - 错误：`dial tcp: connect: connection refused`
   - 原因：服务器 IP 或端口错误，或防火墙阻止

2. **SSH 认证失败**
   - 错误：`ssh: handshake failed: ssh: unable to authenticate`
   - 原因：SSH Key 格式错误或未添加到服务器

3. **命令执行失败**
   - 错误：`command failed: exit status 1`
   - 原因：脚本中的命令执行出错

4. **超时**
   - 错误：`context deadline exceeded`
   - 原因：命令执行时间过长

## 🔧 修复方案

### 修复 1: 简化工作流（测试 SSH 连接）

创建一个简化的测试工作流，只测试 SSH 连接：

```yaml
name: Test SSH Connection

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Test SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            echo "SSH 连接测试成功！"
            whoami
            pwd
```

### 修复 2: 修复 SSH Key 格式

**获取正确的私钥（在服务器上执行）：**
```bash
# 如果使用默认密钥
cat ~/.ssh/id_rsa

# 或使用 ed25519
cat ~/.ssh/id_ed25519
```

**复制完整内容到 GitHub Secrets**

### 修复 3: 添加错误处理

在工作流中添加更详细的错误处理和日志输出。

## 📝 下一步

1. 先执行步骤 1-4 的检查
2. 如果 SSH 连接失败，修复 SSH Key
3. 如果 SSH 连接成功但部署失败，查看具体错误日志
4. 根据错误信息逐步修复

