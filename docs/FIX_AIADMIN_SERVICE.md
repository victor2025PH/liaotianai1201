# 修复 aiadmin.usdt2026.cc 服务问题

## 🔍 问题诊断结果

根据诊断脚本的输出，发现以下问题：

1. **端口 3007 未被占用**
   - 管理后台前端服务未运行
   - Nginx 配置正确指向 3007 端口，但服务不存在

2. **端口 3007 返回 aizkw 网站内容**
   - 如果端口有响应，说明可能有其他服务占用了该端口
   - 或者服务配置错误

## ✅ 修复步骤

### 方法一：使用修复脚本（推荐）

```bash
cd /opt/web3-sites
sudo bash scripts/fix_aiadmin_service.sh
```

### 方法二：手动修复

#### 步骤 1：检查并停止占用端口的进程

```bash
# 检查端口占用
sudo lsof -i :3007

# 如果被占用，停止进程
sudo lsof -ti :3007 | xargs sudo kill -9

# 停止 PM2 进程
pm2 delete sites-admin-frontend
```

#### 步骤 2：进入前端目录

```bash
cd /opt/web3-sites/sites-admin-frontend
```

#### 步骤 3：检查构建

```bash
# 检查 .next 目录是否存在
ls -la .next/

# 如果不存在，需要构建
npm install
npm run build
```

#### 步骤 4：启动服务

```bash
# 使用 PM2 启动
pm2 start npm --name sites-admin-frontend -- start -- --port 3007

# 或者如果使用 Next.js standalone 模式
cd .next/standalone
pm2 start server.js --name sites-admin-frontend

# 保存 PM2 配置
pm2 save
```

#### 步骤 5：验证服务

```bash
# 检查端口
sudo lsof -i :3007

# 检查 HTTP 响应
curl -I http://127.0.0.1:3007

# 检查内容
curl -s http://127.0.0.1:3007 | grep -i "三个展示网站管理后台\|站点概览"
```

## 🔧 常见问题

### 问题 1：端口被 aizkw 服务占用

**症状：** 端口 3007 返回 aizkw 网站内容

**解决：**
1. 检查 PM2 进程列表：
   ```bash
   pm2 list
   ```

2. 确认 aizkw 服务运行在正确的端口（应该是 3003）：
   ```bash
   pm2 describe aizkw-frontend
   ```

3. 如果 aizkw 占用了 3007，停止并重新配置：
   ```bash
   pm2 delete aizkw-frontend
   pm2 start ... --port 3003  # 使用正确端口
   ```

### 问题 2：.next 目录不存在或构建失败

**解决：**
```bash
cd /opt/web3-sites/sites-admin-frontend
rm -rf .next node_modules
npm install
npm run build
```

### 问题 3：PM2 启动失败

**解决：**
1. 检查日志：
   ```bash
   pm2 logs sites-admin-frontend --lines 50
   ```

2. 检查 package.json 中的启动脚本：
   ```bash
   cat package.json | grep -A 5 "scripts"
   ```

3. 尝试直接启动测试：
   ```bash
   npm start -- --port 3007
   ```

## 📊 验证清单

修复后，请验证：

- [ ] 端口 3007 正在监听
- [ ] HTTP 响应状态码为 200
- [ ] 返回内容包含 "三个展示网站管理后台" 或 "站点概览"
- [ ] 不包含 "智控王" 或 "aizkw" 相关内容
- [ ] PM2 进程状态为 "online"
- [ ] 域名 http://aiadmin.usdt2026.cc 可以正常访问

## 🔄 如果问题仍然存在

1. **检查 Nginx 配置**：
   ```bash
   sudo cat /etc/nginx/sites-available/aiadmin.usdt2026.cc
   ```

2. **检查 PM2 进程**：
   ```bash
   pm2 list
   pm2 describe sites-admin-frontend
   ```

3. **查看日志**：
   ```bash
   pm2 logs sites-admin-frontend --lines 100
   ```

4. **重新构建前端**：
   ```bash
   cd /opt/web3-sites/sites-admin-frontend
   rm -rf .next
   npm run build
   pm2 restart sites-admin-frontend
   ```

