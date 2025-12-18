# 🚀 部署完整指南 - 修复后的详细流程

## ✅ 当前状态确认

从您的截图来看，**构建已成功完成**！

### 成功完成的项目：
- ✅ Python 依赖安装成功
- ✅ Node.js 依赖安装成功（556 packages）
- ✅ Next.js 构建成功（37/37 页面生成）
- ✅ TypeScript 编译成功

### ⚠️ 需要注意的警告（非致命）：
1. **npm 安全漏洞**：2 个漏洞（1 高危，1 严重）
   - 可以稍后修复，不影响部署
2. **npm 版本**：可更新到 11.7.0
   - 可选更新
3. **baseline-browser-mapping 模块过期**
   - 不影响功能，可稍后更新

---

## 📋 详细部署流程

### 阶段 1：验证构建结果和修复安全警告（可选）

#### 1.1 检查构建产物

```bash
# 切换到 deployer 用户
sudo su - deployer

# 进入项目目录
cd /home/deployer/telegram-ai-system

# 检查前端构建产物
ls -la saas-demo/.next/standalone/
# 应该看到 server.js 和静态文件

# 检查后端虚拟环境
ls -la admin-backend/venv/bin/
# 应该看到 python, pip, uvicorn 等
```

#### 1.2 修复 npm 安全漏洞（可选但推荐）

```bash
cd /home/deployer/telegram-ai-system/saas-demo

# 查看详细漏洞信息
npm audit

# 尝试自动修复（不破坏依赖）
npm audit fix

# 如果仍有漏洞，查看详细信息
npm audit --json | jq '.vulnerabilities'

# 强制修复（可能更新依赖版本，需测试）
# npm audit fix --force
```

#### 1.3 更新 baseline-browser-mapping（可选）

```bash
cd /home/deployer/telegram-ai-system/saas-demo
npm i baseline-browser-mapping@latest -D
```

---

### 阶段 2：配置 PM2 服务

#### 2.1 检查 ecosystem.config.js

```bash
cd /home/deployer/telegram-ai-system

# 检查配置文件是否存在
ls -la ecosystem.config.js
```

#### 2.2 如果不存在，创建 ecosystem.config.js

```bash
cd /home/deployer/telegram-ai-system

cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/deployer/telegram-ai-system/admin-backend",
      script: "/home/deployer/telegram-ai-system/admin-backend/venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        PORT: 8000,
        PYTHONPATH: "/home/deployer/telegram-ai-system/admin-backend",
        PYTHONUNBUFFERED: "1",
        NODE_ENV: "production"
      },
      error_file: "/home/deployer/telegram-ai-system/logs/backend-error.log",
      out_file: "/home/deployer/telegram-ai-system/logs/backend-out.log",
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
      cwd: "/home/deployer/telegram-ai-system/saas-demo",
      script: "/usr/bin/node",
      args: ".next/standalone/server.js",
      env: {
        PORT: 3000,
        NODE_ENV: "production",
        NODE_OPTIONS: "--max-old-space-size=1024"
      },
      error_file: "/home/deployer/telegram-ai-system/logs/frontend-error.log",
      out_file: "/home/deployer/telegram-ai-system/logs/frontend-out.log",
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

# 验证配置文件语法
node -c ecosystem.config.js && echo "✅ 配置文件语法正确" || echo "❌ 配置文件有错误"
```

---

### 阶段 3：启动 PM2 服务

#### 3.1 停止可能存在的旧服务

```bash
# 确保在项目根目录
cd /home/deployer/telegram-ai-system

# 停止所有 PM2 服务（如果存在）
pm2 stop all
pm2 delete all
```

#### 3.2 启动服务

```bash
# 启动所有服务
pm2 start ecosystem.config.js

# 查看服务状态
pm2 status

# 查看实时日志
pm2 logs

# 查看特定服务的日志
pm2 logs backend
pm2 logs frontend
```

#### 3.3 保存 PM2 配置并设置开机自启

```bash
# 保存当前进程列表
pm2 save

# 生成开机自启脚本（如果尚未配置）
pm2 startup
# 这会输出一个命令，复制并执行它（需要 sudo）

# 例如输出可能是：
# sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u deployer --hp /home/deployer
# 复制这条命令并执行
```

---

### 阶段 4：验证服务运行状态

#### 4.1 检查端口监听

```bash
# 检查端口是否被监听
sudo netstat -tlnp | grep -E "3000|8000"
# 或者使用 ss 命令
sudo ss -tlnp | grep -E "3000|8000"

# 应该看到：
# 3000 (前端)
# 8000 (后端)
```

#### 4.2 测试后端健康检查

```bash
# 测试后端 API
curl http://localhost:8000/health
# 或者
curl http://localhost:8000/api/health

# 应该返回 JSON 响应或 200 状态码
```

#### 4.3 测试前端

```bash
# 测试前端
curl http://localhost:3000
# 应该返回 HTML 内容
```

#### 4.4 检查 PM2 服务状态

```bash
pm2 status

# 应该显示：
# ┌─────┬───────────┬─────────────┬─────────┬─────────┬──────────┐
# │ id  │ name      │ mode        │ ↺       │ status  │ cpu      │
# ├─────┼───────────┼─────────────┼─────────┼─────────┼──────────┤
# │ 0   │ backend   │ fork        │ 0       │ online  │ 0%       │
# │ 1   │ frontend  │ fork        │ 0       │ online  │ 0%       │
# └─────┴───────────┴─────────────┴─────────┴─────────┴──────────┘
```

---

### 阶段 5：配置 Nginx 反向代理

#### 5.1 检查 Nginx 配置

```bash
# 检查配置文件是否存在
ls -la /etc/nginx/sites-available/telegram-ai-system

# 如果不存在，创建它（初始化脚本应该已经创建了）
# 如果存在，检查内容
cat /etc/nginx/sites-available/telegram-ai-system
```

#### 5.2 更新 Nginx 配置（如果需要）

```bash
sudo nano /etc/nginx/sites-available/telegram-ai-system
```

确保配置包含：

```nginx
server {
    listen 80;
    server_name _;  # 替换为您的域名

    client_max_body_size 100M;

    # 前端代理
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket 支持
    location /api/v1/notifications/ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_buffering off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

#### 5.3 测试并重启 Nginx

```bash
# 测试配置语法
sudo nginx -t

# 如果测试通过，重启 Nginx
sudo systemctl restart nginx

# 检查 Nginx 状态
sudo systemctl status nginx
```

---

### 阶段 6：配置 GitHub Actions SSH Key

#### 6.1 查看 SSH 公钥

```bash
# 确保在 deployer 用户下
sudo su - deployer

# 查看公钥
cat ~/.ssh/id_rsa.pub
```

#### 6.2 复制私钥用于 GitHub Secrets

```bash
# 查看私钥（复制全部内容）
cat ~/.ssh/id_rsa
```

#### 6.3 添加到 GitHub Secrets

1. 访问 GitHub 仓库：
   ```
   https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions
   ```

2. 点击 "New repository secret"

3. 添加以下 Secrets：

   | Secret 名称 | 值 | 说明 |
   |------------|-----|------|
   | `SERVER_HOST` | `10.56.61.200` | 您的服务器 IP |
   | `SERVER_USER` | `deployer` | SSH 用户名 |
   | `SERVER_SSH_KEY` | 粘贴上面复制的私钥内容 | SSH 私钥（完整内容） |

#### 6.4 测试 GitHub Actions 部署

```bash
# 推送代码触发部署（如果有更改）
git push origin main

# 或者在 GitHub 网页上：
# Actions → Deploy to Server → Run workflow
```

---

### 阶段 7：验证网站访问

#### 7.1 从服务器本地测试

```bash
# 测试 HTTP
curl http://localhost
curl http://localhost/api/health

# 检查响应头
curl -I http://localhost
```

#### 7.2 从外部访问

在浏览器中访问：
- `http://10.56.61.200`（使用服务器 IP）
- 或 `http://your-domain.com`（如果已配置域名）

#### 7.3 检查服务日志

```bash
# PM2 日志
pm2 logs

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 应用日志
tail -f /home/deployer/telegram-ai-system/logs/backend-out.log
tail -f /home/deployer/telegram-ai-system/logs/frontend-out.log
```

---

### 阶段 8：安全加固（可选但推荐）

#### 8.1 关闭密码登录，仅使用 SSH Key

```bash
# 编辑 SSH 配置
sudo nano /etc/ssh/sshd_config

# 找到并修改：
PasswordAuthentication no

# 保存后重启 SSH 服务
sudo systemctl restart ssh

# 验证配置
sudo sshd -T | grep PasswordAuthentication
# 应该显示: PasswordAuthentication no
```

**⚠️ 警告：** 确保 SSH Key 可以正常使用后再执行此操作！

#### 8.2 配置防火墙（已由初始化脚本完成）

```bash
# 查看当前规则
sudo ufw status verbose

# 应该看到：
# - OpenSSH (22/tcp) - ALLOW
# - Nginx Full (80, 443/tcp) - ALLOW
```

---

## 📊 检查清单

使用以下清单确认所有步骤已完成：

### 基础环境
- [ ] Node.js 20.x 已安装
- [ ] Python 3.10+ 已安装
- [ ] PM2 已全局安装
- [ ] Nginx 已安装并运行
- [ ] Swap 文件 8GB 已创建并启用

### 项目构建
- [ ] 后端依赖已安装（venv）
- [ ] 前端依赖已安装
- [ ] 前端构建成功（.next/standalone/）
- [ ] npm 安全漏洞已修复（可选）

### 服务配置
- [ ] ecosystem.config.js 已创建
- [ ] PM2 服务已启动（backend, frontend）
- [ ] PM2 开机自启已配置
- [ ] 端口 3000 和 8000 正在监听
- [ ] 后端健康检查通过
- [ ] 前端可以访问

### Nginx 配置
- [ ] Nginx 配置文件已创建
- [ ] Nginx 配置语法正确
- [ ] Nginx 服务正在运行
- [ ] 反向代理工作正常

### GitHub Actions
- [ ] SSH 公钥已查看
- [ ] SSH 私钥已复制
- [ ] GitHub Secrets 已配置（SERVER_HOST, SERVER_USER, SERVER_SSH_KEY）
- [ ] GitHub Actions 部署测试成功

### 网站访问
- [ ] 网站可以从外部访问
- [ ] API 端点正常响应
- [ ] 前端页面正常加载
- [ ] 日志文件正常生成

---

## 🔧 故障排除

### 问题 1：PM2 服务无法启动

```bash
# 查看详细错误
pm2 logs --err

# 检查端口是否被占用
sudo lsof -i :3000
sudo lsof -i :8000

# 检查文件权限
ls -la /home/deployer/telegram-ai-system
sudo chown -R deployer:deployer /home/deployer/telegram-ai-system
```

### 问题 2：Nginx 502 Bad Gateway

```bash
# 检查后端是否运行
pm2 status backend
pm2 logs backend

# 测试后端连接
curl http://localhost:8000/health

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 问题 3：前端无法访问

```bash
# 检查前端是否运行
pm2 status frontend
pm2 logs frontend

# 检查构建产物
ls -la /home/deployer/telegram-ai-system/saas-demo/.next/standalone/

# 测试前端连接
curl http://localhost:3000
```

### 问题 4：GitHub Actions 部署失败

参考文档：
- [GitHub Actions SSH 配置指南](./SETUP_GITHUB_ACTIONS_SSH.md)
- [防火墙修复指南](./FIX_FIREWALL_FOR_GITHUB_ACTIONS.md)

---

## 📚 相关文档

- [初始化完成后的下一步操作](./NEXT_STEPS_AFTER_INITIAL_SETUP.md)
- [修复初始化脚本错误](./FIX_INITIAL_SETUP_ERRORS.md)
- [GitHub Actions SSH 配置](./SETUP_GITHUB_ACTIONS_SSH.md)
- [防火墙修复指南](./FIX_FIREWALL_FOR_GITHUB_ACTIONS.md)

---

## 🎉 完成！

恭喜！如果所有步骤都已完成，您的 Telegram AI 系统应该已经成功部署并运行了！

**快速验证命令：**

```bash
# 一键检查所有服务
echo "=== PM2 服务状态 ===" && pm2 status && \
echo "" && echo "=== 端口监听 ===" && sudo ss -tlnp | grep -E "3000|8000" && \
echo "" && echo "=== Nginx 状态 ===" && sudo systemctl status nginx --no-pager -l && \
echo "" && echo "=== 后端健康检查 ===" && curl -s http://localhost:8000/health || echo "后端未响应" && \
echo "" && echo "=== 前端响应 ===" && curl -s -I http://localhost:3000 | head -1
```

---

**如有任何问题，请查看日志文件或联系技术支持！**
