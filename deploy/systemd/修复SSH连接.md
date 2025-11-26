# 修复 SSH 主机密钥验证失败

## 问题描述

SSH 连接时出现错误：
```
WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!
Host key verification failed.
```

## 原因

这通常发生在：
1. 服务器重新安装或重置
2. SSH 服务器密钥重新生成
3. 连接到不同的服务器但使用相同的 IP

## 解决方案

### 方法1: 使用 ssh-keygen 删除旧密钥（推荐）

在 PowerShell 执行：

```powershell
ssh-keygen -R 165.154.233.55
```

这会自动从 `known_hosts` 文件中删除该主机的旧密钥。

### 方法2: 手动编辑 known_hosts 文件

1. 打开文件：`C:\Users\Administrator\.ssh\known_hosts`
2. 删除第 13 行（或包含 `165.154.233.55` 的行）
3. 保存文件

### 方法3: 使用 -o StrictHostKeyChecking=no（临时，不推荐）

```powershell
ssh -o StrictHostKeyChecking=no ubuntu@165.154.233.55
```

**注意**: 这会跳过主机密钥验证，存在安全风险，仅用于测试。

## 修复后重新连接

修复后，重新连接时会提示接受新密钥：

```powershell
ssh ubuntu@165.154.233.55
```

输入 `yes` 接受新密钥，然后输入密码：`Along2025!!!`

## 验证

连接成功后，您应该看到服务器提示符：
```
ubuntu@10-56-130-4:~$
```


