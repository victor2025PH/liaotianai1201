# Web SSH 部署指南

## 问题：输入密码后没响应

### 可能原因
1. **密码输入时不会显示**（这是正常的 SSH 安全特性）
2. 密码可能输入错误
3. 终端可能需要等待

### 解决方案

#### 方案1: 确认是否已登录

输入密码后，如果成功登录，您应该看到类似这样的提示符：
```
ubuntu@10-11-156-159:~$
```

如果看到这个提示符，说明已经登录成功，可以继续执行命令。

#### 方案2: 重新尝试登录

1. 如果卡住了，尝试按 `Enter` 几次
2. 或者刷新页面重新连接
3. 确保密码正确（注意大小写）

#### 方案3: 使用 SCP 直接上传（无需登录）

如果登录有问题，可以直接从本地上传文件，无需交互式登录：

**在本地 PowerShell 执行：**
```powershell
scp saas-demo/src/components/layout-wrapper.tsx ubuntu@165.154.254.99:/home/ubuntu/saas-demo/src/components/
```

然后使用 Web SSH 执行构建命令（如果能够登录的话）。

#### 方案4: 使用自动化脚本

如果 SSH 登录有问题，可以使用之前创建的 Python 脚本尝试自动部署。

## 如果成功登录后的部署步骤

一旦看到 `ubuntu@10-11-156-159:~$` 提示符，执行以下命令：

```bash
# 1. 进入前端目录
cd /home/ubuntu/saas-demo

# 2. 备份原文件
cp src/components/layout-wrapper.tsx src/components/layout-wrapper.tsx.bak

# 3. 编辑文件（需要手动粘贴修复后的代码）
nano src/components/layout-wrapper.tsx
```

在 nano 编辑器中：
- 删除所有内容（Ctrl+K 多次）
- 按 Ctrl+V 粘贴修复后的代码
- 按 Ctrl+O 保存
- 按 Enter 确认
- 按 Ctrl+X 退出

然后继续：
```bash
# 4. 确保使用 Node.js 20
source ~/.nvm/nvm.sh
nvm use 20

# 5. 重新构建
npm run build

# 6. 重启服务
sudo systemctl restart smart-tg-frontend

# 7. 检查状态
sudo systemctl status smart-tg-frontend
```

