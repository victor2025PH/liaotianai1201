# 管理后台前端部署指南

## ✅ 部署成功确认

从终端输出可以看到：
- ✅ Next.js 构建成功
- ✅ PM2 进程已启动（admin-frontend, pid: 3529）
- ✅ HTTP 服务可访问（返回 HTML 内容）

## 📋 部署步骤

### 1. 拉取最新代码

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
```

### 2. 部署管理后台

```bash
bash scripts/deploy_admin_frontend.sh
```

### 3. 验证部署

```bash
bash scripts/verify_admin_frontend.sh
```

## 🔍 验证清单

### PM2 进程检查

```bash
pm2 list | grep admin-frontend
```

应该看到：
- `status: online` (绿色)
- `pid: [数字]`
- `mem: [内存使用]`

### 端口检查

```bash
curl http://127.0.0.1:3001
```

应该返回 HTML 内容（即使显示 404 或加载中，也说明服务在运行）。

### 构建产物检查

```bash
ls -la admin-frontend/.next
```

应该看到 `.next` 目录存在且包含构建文件。

## 🌐 访问地址

- **本地访问**: `http://127.0.0.1:3001`
- **生产访问**: `https://aiadmin.usdt2026.cc/admin` (需要配置 Nginx)

## 🔧 Nginx 配置

如果需要通过域名访问，添加以下 Nginx 配置：

```nginx
# /etc/nginx/sites-available/default 或自定义配置文件

location /admin {
    proxy_pass http://127.0.0.1:3001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
}
```

然后重启 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 🐛 常见问题

### 问题 1: 进程启动但无法访问

**症状**: PM2 显示 `online`，但 `curl` 返回连接失败

**解决方案**:
```bash
# 检查端口是否被占用
lsof -i :3001

# 检查 PM2 日志
pm2 logs admin-frontend --lines 50

# 重启进程
pm2 restart admin-frontend
```

### 问题 2: 构建失败

**症状**: `npm run build` 报错

**解决方案**:
```bash
cd admin-frontend

# 清理缓存
rm -rf .next node_modules

# 重新安装依赖
npm install

# 重新构建
npm run build
```

### 问题 3: 404 错误

**症状**: 访问时显示 404

**可能原因**:
- Next.js 路由配置问题
- 构建不完整

**解决方案**:
```bash
# 检查构建产物
ls -la admin-frontend/.next

# 重新构建
cd admin-frontend
npm run build

# 重启进程
pm2 restart admin-frontend
```

## 📊 监控和维护

### 查看日志

```bash
# 实时日志
pm2 logs admin-frontend

# 最近 100 行
pm2 logs admin-frontend --lines 100 --nostream
```

### 重启服务

```bash
pm2 restart admin-frontend
```

### 停止服务

```bash
pm2 stop admin-frontend
```

### 删除服务

```bash
pm2 delete admin-frontend
```

## 🔄 更新流程

1. **拉取代码**
   ```bash
   cd /home/ubuntu/telegram-ai-system
   git pull origin main
   ```

2. **重新构建**
   ```bash
   cd admin-frontend
   npm install  # 如果需要更新依赖
   npm run build
   ```

3. **重启服务**
   ```bash
   pm2 restart admin-frontend
   ```

4. **验证**
   ```bash
   curl http://127.0.0.1:3001
   bash scripts/verify_admin_frontend.sh
   ```

## 📝 相关脚本

- `scripts/deploy_admin_frontend.sh` - 完整部署脚本
- `scripts/verify_admin_frontend.sh` - 验证部署状态
- `scripts/check_admin_frontend.sh` - 快速检查脚本

---

**最后更新**: 2025-12-24

