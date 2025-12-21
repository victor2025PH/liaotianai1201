# 手动上传项目文件到服务器指南

## 问题说明

服务器上的项目目录缺少 `package.json` 文件，导致无法构建和启动前端服务。

## 解决方案

需要从本地 Windows 目录上传项目文件到服务器。

## 方法 1：使用 WinSCP（推荐，图形界面）

### 步骤：

1. **下载并安装 WinSCP**
   - 访问：https://winscp.net/
   - 下载并安装

2. **连接到服务器**
   - 主机名：您的服务器 IP
   - 用户名：`ubuntu`
   - 密码：您的服务器密码
   - 协议：SFTP

3. **上传文件**
   - 左侧：本地目录 `D:\telegram-ai-system\tgmini20251220`
   - 右侧：服务器目录 `/home/ubuntu/telegram-ai-system/tgmini20251220`
   - 选择所有文件（排除 `node_modules` 和 `dist` 目录）
   - 拖拽或点击上传

4. **重复上传其他项目**
   - `D:\telegram-ai-system\hbwy20251220` → `/home/ubuntu/telegram-ai-system/hbwy20251220`
   - `D:\telegram-ai-system\aizkw20251219` → `/home/ubuntu/telegram-ai-system/aizkw20251219`

## 方法 2：使用 PowerShell scp 命令

### 前提条件：
- Windows 10/11 已启用 OpenSSH 客户端
- 或在 Windows 设置中启用 "OpenSSH 客户端"

### 步骤：

```powershell
# 1. 上传 tgmini
scp -r D:\telegram-ai-system\tgmini20251220\* ubuntu@your-server-ip:/home/ubuntu/telegram-ai-system/tgmini20251220/

# 2. 上传 hongbao
scp -r D:\telegram-ai-system\hbwy20251220\* ubuntu@your-server-ip:/home/ubuntu/telegram-ai-system/hbwy20251220/

# 3. 上传 aizkw
scp -r D:\telegram-ai-system\aizkw20251219\* ubuntu@your-server-ip:/home/ubuntu/telegram-ai-system/aizkw20251219/
```

**注意：** 排除 `node_modules` 和 `dist` 目录（这些可以在服务器上构建）

## 方法 3：使用 PowerShell 脚本（自动化）

```powershell
# 在 PowerShell 中运行
cd D:\telegram-ai-system
.\scripts\local\upload_projects_to_server.ps1 -ServerIP "your-server-ip" -ServerUser "ubuntu"
```

## 方法 4：使用 Git（如果文件在 GitHub 上）

如果项目文件已经在 GitHub 仓库中，可以在服务器上直接拉取：

```bash
# 在服务器上执行
cd /home/ubuntu/telegram-ai-system
git pull origin main

# 检查文件是否存在
ls -la tgmini20251220/package.json
ls -la hbwy20251220/package.json
ls -la aizkw20251219/package.json
```

## 上传后验证

在服务器上执行：

```bash
# 1. 检查文件是否存在
ls -la /home/ubuntu/telegram-ai-system/tgmini20251220/package.json
ls -la /home/ubuntu/telegram-ai-system/hbwy20251220/package.json
ls -la /home/ubuntu/telegram-ai-system/aizkw20251219/package.json

# 2. 构建并启动所有服务
sudo bash /home/ubuntu/telegram-ai-system/scripts/server/build_and_start_all.sh

# 3. 检查服务状态
pm2 list

# 4. 检查端口监听
sudo netstat -tlnp | grep -E ":(3001|3002|3003)"
```

## 需要上传的关键文件

对于每个项目，确保以下文件已上传：

- ✅ `package.json` （必需）
- ✅ `package-lock.json` （可选，但推荐）
- ✅ `vite.config.ts` 或 `vite.config.js` （如果使用 Vite）
- ✅ `tsconfig.json` （如果使用 TypeScript）
- ✅ `src/` 目录（源代码）
- ✅ `public/` 目录（静态资源）
- ✅ `.env` 或 `.env.production` （环境变量，如果使用）
- ❌ `node_modules/` （不需要，在服务器上运行 `npm install`）
- ❌ `dist/` （不需要，在服务器上运行 `npm run build`）

## 故障排查

### 问题 1：scp 命令未找到

**解决方案：**
1. 打开 Windows 设置
2. 应用 → 可选功能
3. 添加功能 → 选择 "OpenSSH 客户端"
4. 重启 PowerShell

### 问题 2：SSH 连接失败

**解决方案：**
- 检查服务器 IP 是否正确
- 检查防火墙是否开放 SSH 端口（22）
- 检查 SSH 密钥是否正确配置

### 问题 3：上传后文件权限问题

**解决方案：**
```bash
# 在服务器上修复权限
sudo chown -R ubuntu:ubuntu /home/ubuntu/telegram-ai-system
```
