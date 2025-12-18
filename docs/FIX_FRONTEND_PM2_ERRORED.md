# 修复前端 PM2 服务 "errored" 状态问题

## 问题描述

在 GitHub Actions 部署完成后，前端服务在 PM2 中显示为 "errored" 状态，无法正常启动。

从 PM2 状态可以看到：
```
│ 1  │ frontend    │ default     │ N/A     │ fork    │ 0        │ 0      │ 30   │ errored   │ 0%       │ 0b       │
```

- PID 为 0，说明进程启动失败
- 重启次数（↺）很高（30次），说明一直重启失败
- 状态为 "errored"

## 根本原因

前端服务启动失败的主要原因：

1. **Next.js standalone 模式构建产物问题**
   - `.next/standalone/server.js` 文件不存在或路径不正确
   - standalone 目录结构不完整（缺少必要的静态文件或配置）

2. **PM2 配置问题**
   - `ecosystem.config.js` 中的路径配置不正确
   - working directory 设置错误

3. **文件权限问题**
   - 构建产物文件权限不正确
   - 日志目录权限问题

## 解决方案

### 1. 在部署脚本中添加构建产物检查

在 PM2 重启服务之前，检查前端构建产物是否存在：

```bash
# 检查前端构建产物是否存在（Next.js standalone 模式要求）
if [ ! -f "saas-demo/.next/standalone/server.js" ]; then
    echo "❌ 错误：前端 standalone 构建产物不存在"
    exit 1
fi
```

### 2. 检查 PM2 配置

确认 `ecosystem.config.js` 中的前端服务配置正确：

```javascript
{
  name: "frontend",
  cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
  script: "/usr/bin/node",
  args: ".next/standalone/server.js",
  env: {
    PORT: 3000,
    NODE_ENV: "production",
    NODE_OPTIONS: "--max-old-space-size=1024"
  }
}
```

### 3. 查看详细错误日志

如果服务仍然失败，查看 PM2 日志：

```bash
pm2 logs frontend --lines 50
```

或查看错误日志文件：

```bash
tail -f /home/ubuntu/telegram-ai-system/logs/frontend-error.log
```

### 4. 手动测试启动

手动测试前端服务是否能正常启动：

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo
node .next/standalone/server.js
```

如果手动启动失败，查看具体的错误信息。

## 部署脚本改进

在 `.github/workflows/deploy.yml` 中已添加：

1. ✅ 构建产物检查（在重启服务前验证 `server.js` 存在）
2. ✅ 改进的 PM2 重启逻辑（如果 reload 失败则删除并重新启动）
3. ✅ 详细的错误日志输出
4. ✅ 改进的服务状态检查（显示具体状态和错误日志）
5. ✅ 正确的退出码设置

## 常见错误和解决方法

### 错误 1: `Cannot find module '/path/to/server.js'`

**原因**：standalone 目录结构不正确或文件缺失

**解决方法**：
```bash
cd saas-demo
rm -rf .next/standalone
npm run build
```

### 错误 2: `EADDRINUSE: address already in use :::3000`

**原因**：端口 3000 已被占用

**解决方法**：
```bash
# 查找占用端口的进程
sudo lsof -i :3000
# 停止占用端口的进程
pm2 delete frontend
# 或者
sudo kill -9 <PID>
```

### 错误 3: `Permission denied`

**原因**：文件权限不正确

**解决方法**：
```bash
cd /home/ubuntu/telegram-ai-system
sudo chown -R ubuntu:ubuntu saas-demo/.next
sudo chown -R ubuntu:ubuntu logs
```

### 错误 4: Next.js standalone 模式缺少静态文件

**原因**：静态文件复制不完整

**解决方法**：
检查部署脚本中的静态文件复制逻辑：
```bash
mkdir -p .next/standalone/.next/static
cp -r .next/static/* .next/standalone/.next/static/ || true
cp -r public .next/standalone/ || true
```

## 验证步骤

部署完成后，验证服务状态：

1. **检查 PM2 状态**：
   ```bash
   pm2 list
   ```
   应该看到 frontend 状态为 "online"

2. **检查端口监听**：
   ```bash
   sudo ss -tlnp | grep ':3000'
   ```

3. **检查服务健康**：
   ```bash
   curl -I http://localhost:3000
   ```

4. **查看日志**：
   ```bash
   pm2 logs frontend --lines 20
   ```

## 下次部署时的检查清单

- [ ] 前端构建成功完成
- [ ] `.next/standalone/server.js` 文件存在
- [ ] PM2 配置正确
- [ ] 文件权限正确
- [ ] 端口 3000 未被占用
- [ ] 日志目录存在且有写权限

## 相关文件

- `.github/workflows/deploy.yml` - 部署脚本
- `ecosystem.config.js` - PM2 配置文件
- `saas-demo/.next/standalone/server.js` - Next.js standalone 服务器文件
