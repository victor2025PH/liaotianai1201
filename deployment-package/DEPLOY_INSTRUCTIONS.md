# 部署说明

## 文件上传

1. 将整个 deployment-package 目录上传到服务器的以下位置：
   - 洛杉矶/马尼拉服务器: ~/telegram-ai-system/
   - worker-01: /opt/group-ai/

2. 上传方式：
   - 使用 WinSCP、FileZilla 或其他 FTP/SCP 客户端
   - 或使用 scp 命令：
     `ash
     scp -r deployment-package/* ubuntu@165.154.255.48:~/telegram-ai-system/
     `

## 部署步骤

### 1. 上传文件后，SSH 连接到服务器

`ash
ssh ubuntu@165.154.255.48
# 或
ssh ubuntu@165.154.233.179
# 或 worker-01
ssh ubuntu@165.154.254.99
`

### 2. 进入部署目录

**洛杉矶/马尼拉服务器:**
`ash
cd ~/telegram-ai-system
`

**worker-01:**
`ash
cd /opt/group-ai
`

### 3. 安装 Python 依赖

`ash
# 如果有 poetry
cd admin-backend
poetry install --no-dev

# 或使用 pip
pip3 install -r requirements.txt
`

### 4. 创建 .env 文件

`ash
cd admin-backend
cat > .env << 'EOF'
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
`

### 5. 创建必要目录

`ash
mkdir -p sessions
mkdir -p logs
chmod 700 sessions
chmod 755 logs
`

### 6. 启动服务

**洛杉矶/马尼拉服务器:**
`ash
cd admin-backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid
`

**worker-01 (使用 systemd):**
`ash
sudo systemctl start group-ai-worker
sudo systemctl enable group-ai-worker
`

### 7. 验证部署

`ash
# 检查进程
ps aux | grep uvicorn

# 检查端口
netstat -tlnp | grep 8000

# 健康检查
curl http://localhost:8000/health
`

## 服务器信息

### 洛杉矶服务器
- IP: 165.154.255.48
- 用户名: ubuntu
- 密码: 8iDcGrYb52Fxpzee
- 部署目录: ~/telegram-ai-system

### 马尼拉服务器
- IP: 165.154.233.179
- 用户名: ubuntu
- 密码: 8iDcGrYb52Fxpzee
- 部署目录: ~/telegram-ai-system

### worker-01
- IP: 165.154.254.99
- 用户名: ubuntu
- 密码: Along2025!!!
- 部署目录: /opt/group-ai

## 注意事项

1. 确保服务器已安装 Python 3.11+
2. 确保防火墙允许 8000 端口
3. 首次部署需要安装依赖，可能需要 5-10 分钟
4. 部署后需要手动配置环境变量（如 API keys）

