# 自动化部署脚本

本目录包含自动化部署脚本，用于将系统部署到远程服务器。

## 服务器信息

### 洛杉矶服务器
- **IP**: 165.154.255.48
- **用户名**: ubuntu
- **密码**: 8iDcGrYb52Fxpzee
- **地区**: 洛杉矶

### 马尼拉服务器
- **IP**: 165.154.233.179
- **用户名**: ubuntu
- **密码**: 8iDcGrYb52Fxpzee
- **地区**: 马尼拉

## 使用方法

### PowerShell (Windows)

#### 部署到单个服务器

```powershell
# 部署到洛杉矶服务器
.\deploy_to_server.ps1 -ServerIP 165.154.255.48 -Username ubuntu -Password 8iDcGrYb52Fxpzee -ServerName "洛杉矶服务器"

# 部署到马尼拉服务器
.\deploy_to_server.ps1 -ServerIP 165.154.233.179 -Username ubuntu -Password 8iDcGrYb52Fxpzee -ServerName "马尼拉服务器"
```

#### 批量部署到所有服务器

```powershell
.\deploy_all_servers.ps1
```

#### 测试部署

```powershell
# 测试洛杉矶服务器
.\test_deployment.ps1 -ServerIP 165.154.255.48

# 测试马尼拉服务器
.\test_deployment.ps1 -ServerIP 165.154.233.179
```

### Bash (Linux/Mac)

#### 部署到单个服务器

```bash
# 部署到洛杉矶服务器
./deploy_to_server.sh 165.154.255.48 ubuntu 8iDcGrYb52Fxpzee "洛杉矶服务器"

# 部署到马尼拉服务器
./deploy_to_server.sh 165.154.233.179 ubuntu 8iDcGrYb52Fxpzee "马尼拉服务器"
```

#### 测试部署

```bash
# 测试洛杉矶服务器
./test_deployment.sh 165.154.255.48

# 测试马尼拉服务器
./test_deployment.sh 165.154.233.179
```

## 部署流程

1. **测试服务器连接** - 验证 SSH 连接
2. **检查系统环境** - 检查 Python、Node.js、Docker 等
3. **创建部署目录** - 创建 `~/telegram-ai-system` 目录
4. **打包项目文件** - 打包项目（排除 .git、node_modules 等）
5. **上传项目文件** - 上传到服务器
6. **解压并部署** - 解压项目文件
7. **安装依赖和配置** - 安装 Python 依赖、创建 .env、运行数据库迁移
8. **启动服务** - 启动后端服务并检查健康状态

## 部署后验证

部署完成后，脚本会自动进行健康检查。您也可以手动测试：

```bash
# 健康检查
curl http://165.154.255.48:8000/health

# API 文档
curl http://165.154.255.48:8000/docs

# OpenAPI Schema
curl http://165.154.255.48:8000/openapi.json

# Prometheus 指标
curl http://165.154.255.48:8000/metrics
```

## 服务管理

### 查看日志

```bash
ssh ubuntu@165.154.255.48 'tail -f ~/telegram-ai-system/logs/backend.log'
```

### 停止服务

```bash
ssh ubuntu@165.154.255.48 'kill $(cat ~/telegram-ai-system/backend.pid)'
```

### 重启服务

```bash
ssh ubuntu@165.154.255.48 << 'EOF'
cd ~/telegram-ai-system
kill $(cat backend.pid) 2>/dev/null || true
cd admin-backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid
EOF
```

## 注意事项

1. **防火墙配置**: 确保服务器防火墙允许 8000 端口访问
2. **SSH 密钥**: 建议配置 SSH 密钥认证以提高安全性
3. **环境变量**: 部署后需要手动配置生产环境的环境变量
4. **数据库**: 首次部署会自动创建数据库表
5. **依赖安装**: 确保服务器已安装 Python 3.11+ 和 pip

## 故障排查

### 连接失败

- 检查服务器 IP 和端口是否正确
- 检查防火墙设置
- 验证用户名和密码

### 服务启动失败

- 查看日志: `ssh ubuntu@<ip> 'cat ~/telegram-ai-system/logs/backend.log'`
- 检查 Python 版本: `python3 --version`
- 检查依赖安装: `pip3 list`

### 健康检查失败

- 检查服务是否运行: `ssh ubuntu@<ip> 'ps aux | grep uvicorn'`
- 检查端口是否被占用: `ssh ubuntu@<ip> 'netstat -tuln | grep 8000'`
- 检查防火墙规则
