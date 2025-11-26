# SSH 连接问题解决方案

## 问题描述
输入 `ssh ubuntu@165.154.254.99` 后没有响应。

## 可能原因
1. SSH 服务未运行
2. 防火墙或安全组阻止
3. 网络连接问题
4. SSH 客户端配置问题

## 解决方案

### 方案1: 使用云服务器控制台的 Web SSH（推荐）

大多数云服务器提供商都提供 Web SSH 功能：

1. 登录云服务器控制台
2. 找到您的服务器实例
3. 点击"连接"或"Web SSH"
4. 在浏览器中打开终端

**优点**: 无需配置，直接可用

### 方案2: 检查并修复 SSH 连接

#### Windows PowerShell/CMD

1. **检查 SSH 是否可用**:
```powershell
ssh -V
```

2. **使用详细模式连接**（查看详细错误信息）:
```powershell
ssh -v ubuntu@165.154.254.99
```

3. **如果要求输入密码，但看不到提示**:
   - 这是正常的，SSH 为了安全不显示密码输入
   - 直接输入密码后按 Enter（输入时不会显示任何字符）

4. **如果连接超时**:
   - 检查云服务器安全组是否开放 22 端口
   - 检查服务器是否运行

#### 使用 PuTTY（Windows）

1. 下载并安装 PuTTY: https://www.putty.org/
2. 打开 PuTTY
3. 输入:
   - Host Name: `165.154.254.99`
   - Port: `22`
   - Connection type: `SSH`
4. 点击 "Open"
5. 输入用户名: `ubuntu`
6. 输入密码（输入时不会显示）

### 方案3: 使用 SCP 直接上传文件（无需 SSH 交互）

在 PowerShell 中执行：

```powershell
# 上传修复后的文件
scp saas-demo/src/components/layout-wrapper.tsx ubuntu@165.154.254.99:/home/ubuntu/saas-demo/src/components/
```

**注意**: 如果要求输入密码，直接输入（不会显示），然后按 Enter。

### 方案4: 使用自动化脚本（无需手动 SSH）

如果 SSH 无法连接，可以使用 Python 脚本自动部署：

```powershell
cd deploy/systemd
python upload_fix_file.py
```

## 部署修复后的文件

### 方法1: 使用 SCP（推荐）

```powershell
# 1. 上传文件
scp saas-demo/src/components/layout-wrapper.tsx ubuntu@165.154.254.99:/home/ubuntu/saas-demo/src/components/

# 2. 使用 Web SSH 或成功连接 SSH 后执行:
cd /home/ubuntu/saas-demo
source ~/.nvm/nvm.sh
nvm use 20
npm run build
sudo systemctl restart smart-tg-frontend
```

### 方法2: 使用 Web SSH 手动上传

1. 在云服务器控制台打开 Web SSH
2. 创建文件:
```bash
nano /home/ubuntu/saas-demo/src/components/layout-wrapper.tsx
```
3. 复制修复后的代码内容（从本地文件）
4. 粘贴到编辑器中
5. 保存（Ctrl+O, Enter, Ctrl+X）
6. 执行构建和重启命令

### 方法3: 使用 FTP/SFTP 客户端

1. 下载 FileZilla 或其他 SFTP 客户端
2. 连接到服务器:
   - 主机: `165.154.254.99`
   - 用户名: `ubuntu`
   - 密码: （服务器密码）
   - 端口: `22`
3. 上传 `layout-wrapper.tsx` 到 `/home/ubuntu/saas-demo/src/components/`
4. 使用 Web SSH 执行构建和重启命令

## 验证修复

1. 清除浏览器缓存
2. 访问: http://165.154.254.99:3000
3. 应该能正常跳转到登录页面

## 如果仍然无法连接

1. **检查云服务器状态**: 确保服务器正在运行
2. **检查安全组**: 确保 22 端口已开放
3. **检查网络**: 尝试 ping 服务器: `ping 165.154.254.99`
4. **联系云服务商**: 如果以上都正常，可能是云服务商的问题

