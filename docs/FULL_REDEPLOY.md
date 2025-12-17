# 完整重新部署指南

## 🚀 一键重新部署（推荐）

在服务器上执行以下命令：

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
chmod +x scripts/server/full-redeploy.sh
sudo bash scripts/server/full-redeploy.sh
```

这个脚本会自动完成：
1. ✅ 拉取最新代码
2. ✅ 停止现有服务
3. ✅ 配置后端（创建虚拟环境、安装依赖）
4. ✅ 配置前端（安装依赖、构建）
5. ✅ 配置 systemd 服务
6. ✅ 配置 Nginx
7. ✅ 修复文件权限
8. ✅ 启动所有服务
9. ✅ 验证服务状态
10. ✅ 执行健康检查

## 📋 部署前准备

### 1. 检查服务器环境

```bash
# 检查 Python3
python3 --version  # 应该 >= 3.9

# 检查 Node.js
node --version  # 应该 >= 18

# 检查 Git
git --version

# 检查 Nginx
nginx -v
```

### 2. 确保服务器可以访问 GitHub

```bash
# 测试 GitHub 连接
curl -I https://github.com
```

## 🔧 分步部署（如果需要手动控制）

### 步骤 1: 拉取代码

```bash
cd /home/ubuntu/telegram-ai-system
git fetch origin main
git reset --hard origin/main
```

### 步骤 2: 配置后端

```bash
cd admin-backend

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 步骤 3: 配置前端

```bash
cd ../saas-demo

# 安装依赖
npm install --prefer-offline --no-audit --no-fund

# 构建前端
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build

# 复制静态资源（Next.js standalone 模式）
mkdir -p .next/standalone/.next/static
cp -r .next/static/* .next/standalone/.next/static/ 2>/dev/null || true
cp -r public .next/standalone/ 2>/dev/null || true
```

### 步骤 4: 配置 systemd 服务

```bash
cd /home/ubuntu/telegram-ai-system

# 复制服务文件
sudo cp deploy/systemd/luckyred-api.service /etc/systemd/system/
sudo cp deploy/systemd/liaotian-frontend.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable luckyred-api
sudo systemctl enable liaotian-frontend
```

### 步骤 5: 配置 Nginx

```bash
# 使用配置脚本（如果存在）
if [ -f scripts/server/create-nginx-config.sh ]; then
    chmod +x scripts/server/create-nginx-config.sh
    sudo bash scripts/server/create-nginx-config.sh
else
    # 手动配置（参考下面的配置内容）
    sudo nano /etc/nginx/sites-available/aikz.usdt2026.cc
fi

# 启用配置
sudo ln -sf /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t
```

### 步骤 6: 启动服务

```bash
# 修复文件权限
sudo chown -R ubuntu:ubuntu /home/ubuntu/telegram-ai-system

# 启动服务
sudo systemctl start luckyred-api
sleep 3
sudo systemctl start liaotian-frontend
sleep 3
sudo systemctl start nginx
```

### 步骤 7: 验证部署

```bash
# 检查服务状态
sudo systemctl status luckyred-api --no-pager | head -10
sudo systemctl status liaotian-frontend --no-pager | head -10
sudo systemctl status nginx --no-pager | head -5

# 检查端口监听
sudo ss -tlnp | grep -E ':3000|:8000|:443'

# 健康检查
curl http://localhost:8000/health
curl http://localhost:3000
```

## 📝 Nginx 配置示例

如果脚本无法自动配置 Nginx，可以使用以下配置：

```nginx
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # Workers API（专门处理，放在最前面）
    location ~ ^/api/workers(/.*)?$ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers$1;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端所有 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
    }

    # 前端应用
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # 后端健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }
}
```

保存为 `/etc/nginx/sites-available/aikz.usdt2026.cc`，然后：

```bash
sudo ln -sf /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔍 故障排查

### 服务无法启动

```bash
# 查看后端日志
sudo journalctl -u luckyred-api -n 50 --no-pager

# 查看前端日志
sudo journalctl -u liaotian-frontend -n 50 --no-pager

# 查看 Nginx 错误日志
sudo tail -50 /var/log/nginx/error.log
```

### 端口被占用

```bash
# 检查端口占用
sudo lsof -i :8000
sudo lsof -i :3000

# 杀死占用进程
sudo kill -9 <PID>
```

### 前端构建失败

```bash
# 检查内存
free -h

# 检查磁盘空间
df -h

# 清理缓存后重新构建
cd saas-demo
rm -rf .next node_modules
npm install
npm run build
```

### 后端依赖安装失败

```bash
# 检查 Python 版本
python3 --version

# 升级 pip
cd admin-backend
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# 重新安装依赖
pip install -r requirements.txt --no-cache-dir
```

## 📞 验证部署成功

部署完成后，访问：

- **前端**: http://aikz.usdt2026.cc (或 https://aikz.usdt2026.cc)
- **后端 API 文档**: http://aikz.usdt2026.cc/docs
- **健康检查**: http://aikz.usdt2026.cc/health

## ⚠️ 注意事项

1. **备份数据**：重新部署前，建议备份数据库和重要配置文件
2. **环境变量**：确保后端 `.env` 文件配置正确
3. **SSL 证书**：如果需要 HTTPS，在部署后配置 SSL 证书
4. **防火墙**：确保防火墙允许 80 和 443 端口

## 🆘 需要帮助？

如果部署遇到问题，请提供：

1. 服务状态：`sudo systemctl status luckyred-api liaotian-frontend nginx`
2. 错误日志：`sudo journalctl -u luckyred-api -n 50 --no-pager`
3. 端口监听：`sudo ss -tlnp | grep -E ':3000|:8000|:443'`
