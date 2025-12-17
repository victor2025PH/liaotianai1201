# Ubuntu 22.04 LTS 完整初始化部署指南（使用 PM2）

> 适用于全新安装的 Ubuntu 22.04 LTS 服务器
> 使用 PM2 进程管理器替代 systemd，提供更稳定的进程守护

---

## 📋 部署前准备

### 1. SSH 连接到服务器

```bash
ssh ubuntu@your-server-ip
```

### 2. 确认系统版本

```bash
lsb_release -a
```

应该显示：
```
Distributor ID: Ubuntu
Description:    Ubuntu 22.04 LTS
Release:        22.04
Codename:       jammy
```

---

## 🚀 一键部署（推荐）

### 方法一：使用自动化脚本（最简单）

```bash
# 1. 下载脚本（如果项目已克隆）
cd ~
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
cd telegram-ai-system

# 2. 赋予执行权限并运行
chmod +x scripts/server/initial-deploy-ubuntu22-pm2.sh
sudo bash scripts/server/initial-deploy-ubuntu22-pm2.sh
```

脚本会自动完成：
- ✅ 创建 8GB Swap 文件
- ✅ 检查网络配置
- ✅ 安装 Python 3.10、Node.js LTS、Nginx、PM2
- ✅ 拉取项目代码
- ✅ 安装依赖并构建
- ✅ 配置 PM2 并启动服务
- ✅ 设置 PM2 开机自启

---

## 📝 分步部署（手动执行）

如果自动脚本遇到问题，可以手动执行以下步骤：

### 第一部分：系统防死机配置（优先级最高）

#### 步骤 1：创建 8GB Swap 文件

```bash
# 创建 8GB Swap 文件（需要几分钟）
sudo fallocate -l 8G /swapfile

# 设置权限
sudo chmod 600 /swapfile

# 格式化 Swap
sudo mkswap /swapfile

# 启用 Swap
sudo swapon /swapfile

# 验证 Swap 已启用
free -h

# 添加到 /etc/fstab 实现开机自动挂载
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 验证配置
sudo swapon --show
```

**预期输出：**
```
NAME      TYPE SIZE USED PRIO
/swapfile file   8G   0B   -2
```

#### 步骤 2：检查和固化网络配置

```bash
# 检查 Netplan 配置
ls /etc/netplan/

# 查看当前网络配置
cat /etc/netplan/*.yaml

# 测试网络连接
ping -c 3 8.8.8.8

# 如果需要修改网络配置，编辑配置文件
sudo nano /etc/netplan/00-installer-config.yaml

# 应用配置（测试模式，60秒后自动回滚）
sudo netplan try

# 确认配置后应用
sudo netplan apply
```

---

### 第二部分：安装环境

#### 步骤 3：更新 apt 源

```bash
sudo apt update
sudo apt upgrade -y
```

#### 步骤 4：安装基础工具

```bash
sudo apt install -y curl wget git build-essential \
    software-properties-common ca-certificates \
    gnupg lsb-release
```

#### 步骤 5：安装 Python 3.10 和相关工具

```bash
# Ubuntu 22.04 自带 Python 3.10，验证版本
python3 --version

# 安装 pip 和 venv
sudo apt install -y python3-pip python3-venv python3-dev

# 升级 pip
python3 -m pip install --upgrade pip setuptools wheel

# 验证安装
pip3 --version
python3 -m venv --help
```

#### 步骤 6：安装 Node.js LTS

```bash
# 从 NodeSource 安装 Node.js LTS
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node --version  # 应该 >= v20.9.0
npm --version
```

#### 步骤 7：安装 Nginx

```bash
sudo apt install -y nginx

# 启动并设置开机自启
sudo systemctl enable nginx
sudo systemctl start nginx

# 验证运行状态
sudo systemctl status nginx
```

#### 步骤 8：全局安装 PM2

```bash
sudo npm install -g pm2@latest

# 验证安装
pm2 --version
```

---

### 第三部分：部署项目

#### 步骤 9：拉取项目代码

```bash
# 进入用户主目录
cd ~

# 克隆项目（如果是第一次）
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system

# 或者如果已存在，更新代码
cd telegram-ai-system
git pull origin main
```

#### 步骤 10：安装后端依赖

```bash
cd ~/telegram-ai-system/admin-backend

# 创建 Python 虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip setuptools wheel

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

#### 步骤 11：安装前端依赖并构建

```bash
cd ~/telegram-ai-system/saas-demo

# 安装依赖
npm install --prefer-offline --no-audit

# 构建前端（standalone 模式）
npm run build

# 验证构建结果
ls -la .next/standalone/server.js

# 复制静态资源（standalone 模式需要）
mkdir -p .next/standalone/.next/static
cp -r .next/static/* .next/standalone/.next/static/
cp -r public .next/standalone/
```

---

### 第四部分：配置 PM2

#### 步骤 12：生成 ecosystem.config.js

项目根目录已经有 `ecosystem.config.js` 文件，但需要确保路径正确。

**检查并确认配置文件：**

```bash
cd ~/telegram-ai-system
cat ecosystem.config.js
```

**如果需要重新生成，使用以下内容：**

```bash
cat > ~/telegram-ai-system/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      script: "/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        PORT: 8000,
        PYTHONPATH: "/home/ubuntu/telegram-ai-system/admin-backend",
        PYTHONUNBUFFERED: "1",
        NODE_ENV: "production"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/backend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      instances: 1,
      exec_mode: "fork"
    },
    {
      name: "frontend",
      cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
      script: "/usr/bin/node",
      args: ".next/standalone/server.js",
      env: {
        PORT: 3000,
        NODE_ENV: "production",
        NODE_OPTIONS: "--max-old-space-size=1024"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/frontend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/frontend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      instances: 1,
      exec_mode: "fork"
    }
  ]
};
EOF
```

#### 步骤 13：创建日志目录

```bash
mkdir -p ~/telegram-ai-system/logs
```

#### 步骤 14：启动 PM2 应用

```bash
cd ~/telegram-ai-system

# 启动应用
pm2 start ecosystem.config.js

# 查看状态
pm2 status

# 查看日志
pm2 logs

# 保存 PM2 进程列表
pm2 save
```

#### 步骤 15：设置 PM2 开机自启

```bash
# 生成 startup 脚本（会输出需要执行的命令）
pm2 startup systemd -u ubuntu --hp /home/ubuntu

# 执行输出的命令（通常类似下面这样，但需要根据实际输出执行）
# sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu

# 保存当前进程列表
pm2 save
```

---

### 第五部分：配置 Nginx（可选）

#### 步骤 16：配置 Nginx 反向代理

```bash
# 备份原配置
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# 编辑配置
sudo nano /etc/nginx/sites-available/default
```

**配置示例（替换 server 块）：**

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名

    # 后端 API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 前端应用
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**保存后测试并重载：**

```bash
# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx
```

---

## ✅ 验证部署

### 1. 检查系统资源

```bash
# 检查 Swap
free -h

# 检查磁盘空间
df -h
```

### 2. 检查服务状态

```bash
# PM2 状态
pm2 status

# PM2 详细信息
pm2 info backend
pm2 info frontend

# 查看日志
pm2 logs --lines 50
```

### 3. 测试服务

```bash
# 测试后端
curl http://localhost:8000/health

# 测试前端
curl http://localhost:3000

# 测试 Nginx（如果已配置）
curl http://localhost
```

---

## 📚 常用 PM2 命令

```bash
# 查看状态
pm2 status

# 查看日志
pm2 logs              # 所有应用
pm2 logs backend      # 仅后端
pm2 logs frontend     # 仅前端

# 重启服务
pm2 restart all       # 所有应用
pm2 restart backend   # 仅后端
pm2 restart frontend  # 仅前端

# 停止服务
pm2 stop all
pm2 stop backend

# 删除应用
pm2 delete all
pm2 delete backend

# 监控（实时）
pm2 monit

# 查看详细信息
pm2 describe backend
pm2 describe frontend

# 保存进程列表
pm2 save

# 查看启动脚本
pm2 startup
```

---

## 🔧 故障排查

### PM2 应用无法启动

```bash
# 查看详细日志
pm2 logs backend --err
pm2 logs frontend --err

# 检查端口占用
sudo ss -tlnp | grep -E ':3000|:8000'

# 手动测试后端
cd ~/telegram-ai-system/admin-backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 手动测试前端
cd ~/telegram-ai-system/saas-demo
node .next/standalone/server.js
```

### 前端构建失败

```bash
# 清理缓存重新构建
cd ~/telegram-ai-system/saas-demo
rm -rf .next node_modules
npm install
npm run build
```

### 后端依赖安装失败

```bash
# 重新创建虚拟环境
cd ~/telegram-ai-system/admin-backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Swap 未生效

```bash
# 检查 Swap 状态
sudo swapon --show
free -h

# 如果 Swap 未启用，手动启用
sudo swapon /swapfile

# 检查 /etc/fstab
cat /etc/fstab | grep swapfile
```

---

## 🔄 更新代码并重启

```bash
cd ~/telegram-ai-system

# 拉取最新代码
git pull origin main

# 更新后端依赖（如果需要）
cd admin-backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 更新前端依赖并重新构建
cd saas-demo
npm install
npm run build

# 复制静态资源
mkdir -p .next/standalone/.next/static
cp -r .next/static/* .next/standalone/.next/static/
cp -r public .next/standalone/
cd ..

# 重启 PM2 服务
pm2 restart all
pm2 save
```

---

## 📞 支持

如果遇到问题，请检查：
1. 日志文件：`~/telegram-ai-system/logs/`
2. PM2 日志：`pm2 logs`
3. Nginx 日志：`/var/log/nginx/error.log`

---

**部署完成！** 🎉
