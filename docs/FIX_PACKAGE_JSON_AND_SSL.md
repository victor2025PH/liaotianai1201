# 修复 package.json 和 SSL 证书问题

> **问题**: 
> - package.json 不存在
> - SSL 证书文件不存在，Nginx 无法启动
> - 端口未监听

---

## 🔍 问题分析

从部署日志看到：

1. **package.json 不存在**
   - 所有三个网站都报告找不到 package.json
   - 可能是目录路径错误或文件确实不存在

2. **SSL 证书错误**
   - `/etc/letsencrypt/live/hongbao.usdt2026.cc/fullchain.pem` 不存在
   - 导致 Nginx 配置测试失败
   - Nginx 无法启动

3. **端口未监听**
   - 3001, 3002, 3003 都没有服务在运行
   - 因为构建失败（package.json 不存在）

---

## 🚀 修复步骤

### 步骤 1: 检查目录结构

```bash
cd /home/ubuntu/telegram-ai-system

# 检查三个网站目录是否存在
ls -la | grep -E "tgmini|hbwy|aizkw"

# 检查每个目录的内容
ls -la tgmini20251220/
ls -la hbwy20251220/
ls -la aizkw20251219/

# 检查 package.json
ls -la tgmini20251220/package.json
ls -la hbwy20251220/package.json
ls -la aizkw20251219/package.json
```

### 步骤 2: 如果 package.json 不存在

```bash
# 检查是否在子目录中
find tgmini20251220 -name "package.json"
find hbwy20251220 -name "package.json"
find aizkw20251219 -name "package.json"

# 如果确实不存在，检查 Git 仓库
cd /home/ubuntu/telegram-ai-system
git ls-files | grep -E "tgmini|hbwy|aizkw" | grep package.json

# 如果文件在 Git 中但本地不存在，恢复文件
git checkout HEAD -- tgmini20251220/package.json
git checkout HEAD -- hbwy20251220/package.json
git checkout HEAD -- aizkw20251219/package.json
```

### 步骤 3: 修复 SSL 证书问题

**选项 A: 使用修复脚本（推荐）**

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/server/fix-ssl-certificates.sh
```

**选项 B: 手动获取证书**

```bash
# 安装 Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# 为每个域名获取证书
sudo certbot certonly --nginx -d tgmini.usdt2026.cc
sudo certbot certonly --nginx -d hongbao.usdt2026.cc
sudo certbot certonly --nginx -d aikz.usdt2026.cc
```

**选项 C: 暂时使用 HTTP（如果不需要 HTTPS）**

修改 Nginx 配置，只使用 HTTP：

```bash
# 编辑 Nginx 配置
sudo nano /etc/nginx/sites-available/tgmini.usdt2026.cc

# 只保留 HTTP 配置，删除 HTTPS 部分
server {
    listen 80;
    server_name tgmini.usdt2026.cc;
    
    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 步骤 4: 重新运行部署脚本

```bash
cd /home/ubuntu/telegram-ai-system

# 拉取最新代码（包含改进的脚本）
git pull origin main

# 运行改进后的全面修复脚本
bash scripts/server/comprehensive-fix.sh
```

---

## 🔧 改进后的脚本功能

新的 `comprehensive-fix.sh` 脚本已经改进：

1. ✅ **详细的目录检查**
   - 显示当前目录和目录内容
   - 如果 package.json 不存在，尝试查找

2. ✅ **自动检测 SSL 证书**
   - 如果证书存在，配置 HTTPS
   - 如果证书不存在，只配置 HTTP

3. ✅ **改进的错误处理**
   - 更详细的错误信息
   - 即使 Nginx 配置失败，服务仍可在端口上运行

---

## 📊 验证修复

```bash
# 1. 检查 package.json
ls -la tgmini20251220/package.json
ls -la hbwy20251220/package.json
ls -la aizkw20251219/package.json

# 2. 检查 SSL 证书
sudo ls -la /etc/letsencrypt/live/tgmini.usdt2026.cc/
sudo ls -la /etc/letsencrypt/live/hongbao.usdt2026.cc/
sudo ls -la /etc/letsencrypt/live/aikz.usdt2026.cc/

# 3. 检查 PM2 进程
pm2 list

# 4. 检查端口
sudo lsof -i :3001
sudo lsof -i :3002
sudo lsof -i :3003

# 5. 测试本地访问
curl http://127.0.0.1:3001
curl http://127.0.0.1:3002
curl http://127.0.0.1:3003

# 6. 测试 Nginx
sudo nginx -t
sudo systemctl status nginx
```

---

## ⚠️ 常见问题

### 问题 1: package.json 确实不存在

**原因**: 文件可能没有提交到 Git 或目录结构不同

**解决**:
```bash
# 检查 Git 历史
git log --all --full-history -- tgmini20251220/package.json

# 如果文件在 Git 中，恢复它
git checkout HEAD -- tgmini20251220/package.json
```

### 问题 2: SSL 证书获取失败

**原因**: 
- 域名 DNS 未正确配置
- 80 端口被占用
- Certbot 配置问题

**解决**:
```bash
# 检查 DNS
nslookup tgmini.usdt2026.cc

# 检查 80 端口
sudo lsof -i :80

# 手动运行 Certbot
sudo certbot certonly --standalone -d tgmini.usdt2026.cc
```

### 问题 3: Nginx 配置测试失败

**原因**: SSL 证书路径错误或文件不存在

**解决**:
```bash
# 检查证书文件
sudo ls -la /etc/letsencrypt/live/

# 如果证书不存在，先获取证书或使用 HTTP only 配置
```

---

**最后更新**: 2025-12-21
