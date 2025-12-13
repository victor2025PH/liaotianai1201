# Worker 节点连接问题诊断指南

## 概述

当 Worker 节点无法连接到后端服务器时，会导致账号启动失败。本文档提供完整的诊断和解决方案。

## 快速诊断

### 在服务器上运行（Linux）

```bash
# 完整诊断
bash scripts/server/diagnose-worker-complete.sh

# 或分别运行
bash scripts/server/diagnose-worker-connection.sh  # 网络连接诊断
bash scripts/server/check-backend-api.sh          # 后端 API 检查
```

### 在本地运行（Windows）

```cmd
# 双击运行或在命令行执行
scripts\local\diagnose-worker-connection.bat
```

## 诊断项目

### 1. 网络连接检查

**检查内容：**
- DNS 解析是否正常
- HTTP/HTTPS 连接是否成功
- 防火墙是否阻止连接

**常见问题：**
- DNS 解析失败：检查网络配置或 DNS 服务器
- HTTP 连接失败：检查网络连接或服务器是否运行
- 防火墙阻止：允许出站 HTTPS 连接（端口 443）

**解决方案：**
```bash
# 测试 DNS 解析
host aikz.usdt2026.cc

# 测试 HTTP 连接
curl -I https://aikz.usdt2026.cc

# 检查防火墙（UFW）
sudo ufw status
sudo ufw allow out 443/tcp

# 检查防火墙（Firewalld）
sudo firewall-cmd --list-all
sudo firewall-cmd --add-service=https --permanent
sudo firewall-cmd --reload
```

### 2. SSL 证书检查

**检查内容：**
- SSL 证书是否有效
- 证书是否过期
- 证书链是否完整

**常见问题：**
- 证书过期：联系服务器管理员更新证书
- 证书链不完整：检查服务器 SSL 配置

**解决方案：**
```bash
# 检查 SSL 证书
echo | openssl s_client -connect aikz.usdt2026.cc:443 -servername aikz.usdt2026.cc 2>/dev/null | openssl x509 -noout -dates

# 查看证书详细信息
echo | openssl s_client -connect aikz.usdt2026.cc:443 -servername aikz.usdt2026.cc 2>/dev/null | openssl x509 -noout -text
```

### 3. 后端服务检查

**检查内容：**
- 后端服务是否运行
- 端口 8000 是否监听
- 健康检查端点是否可访问
- 心跳端点是否可访问

**常见问题：**
- 后端服务未运行：启动后端服务
- 端口未监听：检查服务配置
- 健康检查失败：检查服务日志
- 心跳端点 404：检查 API 路由注册

**解决方案：**
```bash
# 检查后端服务状态
sudo systemctl status luckyred-api
# 或
sudo systemctl status telegram-backend

# 启动后端服务
sudo systemctl start luckyred-api

# 检查端口监听
sudo ss -tlnp | grep 8000

# 测试本地健康检查
curl http://localhost:8000/health

# 测试公共健康检查
curl https://aikz.usdt2026.cc/health

# 测试心跳端点
curl -X POST https://aikz.usdt2026.cc/api/v1/workers/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"node_id":"test","status":"online","account_count":0,"accounts":[]}'

# 查看后端日志
sudo journalctl -u luckyred-api -n 50 --no-pager
```

### 4. Worker 节点配置检查

**检查内容：**
- 服务器 URL 配置是否正确
- Worker 节点进程是否运行
- 配置文件是否存在

**常见问题：**
- 服务器 URL 配置错误：检查配置文件
- Worker 进程未运行：启动 Worker 节点
- 配置文件不存在：创建配置文件

**解决方案：**
```bash
# 检查 Worker 配置文件
cat worker_config.py | grep SERVER_URL
# 或
cat config.py | grep SERVER_URL

# 检查 Worker 进程
ps aux | grep worker

# 启动 Worker 节点（根据实际路径）
cd /path/to/worker
python worker.py
```

### 5. Nginx 配置检查

**检查内容：**
- Nginx 是否运行
- 反向代理配置是否正确
- API 路由是否正确配置

**常见问题：**
- Nginx 未运行：启动 Nginx
- 反向代理配置错误：检查 Nginx 配置
- API 路由未配置：添加 API 路由

**解决方案：**
```bash
# 检查 Nginx 状态
sudo systemctl status nginx

# 检查 Nginx 配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx

# 查看 Nginx 错误日志
sudo tail -n 50 /var/log/nginx/error.log

# 检查 API 路由配置
cat /etc/nginx/sites-available/aikz.conf | grep -A 10 "/api/"
```

## 常见错误和解决方案

### 错误 1: `Cannot connect to server`

**原因：**
- Worker 节点无法连接到后端服务器
- 网络连接问题
- 防火墙阻止

**解决方案：**
1. 运行诊断脚本检查网络连接
2. 检查防火墙设置
3. 检查 DNS 配置
4. 检查服务器是否运行

### 错误 2: `目标節點不在線`

**原因：**
- Worker 节点未运行
- Worker 节点无法发送心跳
- Worker 节点配置错误

**解决方案：**
1. 检查 Worker 节点进程是否运行
2. 检查 Worker 节点配置
3. 检查 Worker 节点日志
4. 确保 Worker 节点能连接到服务器

### 错误 3: `心跳端点不可访问 (404)`

**原因：**
- API 路由未注册
- Nginx 配置错误
- 后端服务未运行

**解决方案：**
1. 检查 API 路由注册：`grep -r "workers/heartbeat" admin-backend/app/api/`
2. 检查 Nginx 配置
3. 重启后端服务
4. 检查后端日志

### 错误 4: `SSL 证书无效`

**原因：**
- 证书过期
- 证书链不完整
- 证书配置错误

**解决方案：**
1. 检查证书有效期
2. 更新证书
3. 检查证书链配置
4. 联系服务器管理员

## 验证步骤

完成修复后，按以下步骤验证：

1. **验证网络连接**
   ```bash
   curl -I https://aikz.usdt2026.cc
   ```

2. **验证后端服务**
   ```bash
   curl http://localhost:8000/health
   curl https://aikz.usdt2026.cc/health
   ```

3. **验证心跳端点**
   ```bash
   curl -X POST https://aikz.usdt2026.cc/api/v1/workers/heartbeat \
     -H "Content-Type: application/json" \
     -d '{"node_id":"test","status":"online","account_count":0,"accounts":[]}'
   ```

4. **验证 Worker 节点**
   - 检查 Worker 进程是否运行
   - 检查 Worker 日志是否有错误
   - 检查 Worker 是否能发送心跳

5. **测试账号启动**
   - 在前端点击"一键启动所有账号"
   - 查看是否还有错误
   - 查看详细的错误信息

## 联系支持

如果问题仍然存在，请提供以下信息：

1. 诊断脚本的完整输出
2. Worker 节点日志
3. 后端服务日志
4. Nginx 错误日志
5. 网络配置信息

## 相关文档

- [部署指南](./DEPLOYMENT_STEPS.md)
- [故障排除指南](./QUICK_FIX_BACKEND_CONNECTION.md)
- [SSH 连接问题](./SSH_CONNECTION_TROUBLESHOOTING.md)

