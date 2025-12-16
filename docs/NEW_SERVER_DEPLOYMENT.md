# 新服务器部署指南

## 概述

本指南提供完整的新服务器部署流程，包括系统初始化、软件安装、应用部署等所有步骤。

## 快速部署（推荐）

### 方法 1: 使用初始化脚本（一键部署）

1. **通过 VNC 或云控制台登录新服务器**

2. **克隆项目或上传脚本**：
   ```bash
   # 如果服务器可以访问 GitHub
   git clone https://github.com/victor2025PH/liaotianai1201.git /home/ubuntu/telegram-ai-system
   cd /home/ubuntu/telegram-ai-system
   
   # 或者手动上传 init_new_server.sh 脚本
   ```

3. **运行初始化脚本**：
   ```bash
   sudo bash scripts/server/init_new_server.sh
   ```

4. **配置 SSL 证书**（如果需要）：
   ```bash
   sudo apt-get install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d aikz.usdt2026.cc
   ```

### 方法 2: 手动部署（分步执行）

#### 步骤 1: 系统更新和基础软件

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y curl wget git vim net-tools
```

#### 步骤 2: 安装 Redis

```bash
sudo apt-get install -y redis-server
sudo sed -i 's/^#*supervised .*/supervised systemd/' /etc/redis/redis.conf
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### 步骤 3: 安装 Node.js

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get install -y nodejs
```

#### 步骤 4: 安装 Python

```bash
sudo apt-get install -y python3 python3-pip python3-venv python3-dev
```

#### 步骤 5: 安装 Nginx

```bash
sudo apt-get install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 步骤 6: 配置 SSH

```bash
sudo apt-get install -y openssh-server
sudo systemctl start ssh
sudo systemctl enable ssh
```

#### 步骤 7: 配置防火墙

```bash
sudo apt-get install -y ufw
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable
```

#### 步骤 8: 部署应用

```bash
# 克隆项目
cd /home/ubuntu
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
cd telegram-ai-system

# 设置权限
sudo chown -R ubuntu:ubuntu .

# 安装前端依赖
cd saas-demo
npm install
npm run build
cd ..

# 安装后端依赖
cd admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 部署服务
sudo cp deploy/systemd/luckyred-api.service /etc/systemd/system/
sudo cp deploy/systemd/liaotian-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable luckyred-api liaotian-frontend

# 启动服务
sudo systemctl start luckyred-api
sudo systemctl start liaotian-frontend

# 配置 Nginx
sudo bash scripts/server/fix-nginx-routes-complete.sh
```

#### 步骤 9: 配置 SSL 证书

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d aikz.usdt2026.cc
```

## 部署后验证

### 1. 检查服务状态

```bash
sudo systemctl status nginx
sudo systemctl status liaotian-frontend
sudo systemctl status luckyred-api
sudo systemctl status redis-server
sudo systemctl status ssh
```

### 2. 检查端口监听

```bash
sudo ss -tlnp | grep -E ":(22|80|443|3000|8000)"
```

### 3. 测试本地连接

```bash
# 测试前端
curl http://127.0.0.1:3000/

# 测试后端
curl http://127.0.0.1:8000/api/v1/health

# 测试 Nginx
curl http://127.0.0.1/
```

### 4. 测试外部访问

```bash
# 测试 SSH
ssh ubuntu@[服务器IP]

# 测试网站
curl https://aikz.usdt2026.cc/login
```

## 云服务商配置

### UCloud 配置检查清单

1. **防火墙规则**：
   - ✅ TCP: 22 (SSH)
   - ✅ TCP: 80 (HTTP)
   - ✅ TCP: 443 (HTTPS)
   - ✅ 确保防火墙已绑定到服务器

2. **网络配置**：
   - ✅ 确认服务器有公网 IP
   - ✅ 确认路由表配置正确
   - ✅ 确认安全组允许出站流量

3. **DNS 配置**：
   - ✅ 域名解析到服务器 IP
   - ✅ SSL 证书配置正确

## 常见问题

### Q1: 初始化脚本执行失败

**解决方法：**
- 检查网络连接：`ping -c 3 8.8.8.8`
- 检查 DNS 解析：`nslookup github.com`
- 手动执行失败的步骤

### Q2: 服务启动失败

**解决方法：**
- 查看服务日志：`sudo journalctl -u [service-name] -n 50`
- 检查配置文件：`sudo systemctl cat [service-name]`
- 检查端口占用：`sudo ss -tlnp | grep :[port]`

### Q3: 无法访问网站

**解决方法：**
- 检查防火墙规则
- 检查 Nginx 配置：`sudo nginx -t`
- 检查服务状态
- 检查 SSL 证书

## 部署时间估算

- 系统更新：5-10 分钟
- 软件安装：5-10 分钟
- 应用部署：10-20 分钟（取决于网络速度）
- SSL 配置：2-5 分钟

**总计：约 30-45 分钟**

## 后续维护

1. **定期更新**：
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **监控服务**：
   ```bash
   sudo systemctl status [service-name]
   ```

3. **查看日志**：
   ```bash
   sudo journalctl -u [service-name] -f
   ```

4. **备份数据**：
   - 数据库文件：`/home/ubuntu/telegram-ai-system/admin-backend/data/app.db`
   - 配置文件：`/etc/systemd/system/*.service`
   - Nginx 配置：`/etc/nginx/sites-available/default`

