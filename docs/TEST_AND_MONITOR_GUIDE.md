# 服务重启、监控和测试指南

## 🚀 快速开始

### 在服务器上执行（SSH 连接后）

#### 1. 重启所有服务并测试

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/restart-and-test.sh
```

这个脚本会：
- ✅ 停止现有服务
- ✅ 启动后端和 Bot 服务
- ✅ 执行健康检查
- ✅ 显示服务状态和最近日志

#### 2. 实时监控所有日志

在服务器上打开一个新终端（或使用 screen/tmux），执行：

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/server/monitor-all-logs.sh
```

或者分别监控：

```bash
# 监控后端日志
bash scripts/server/view-logs.sh backend -f

# 监控 Bot 日志
bash scripts/server/view-logs.sh bot -f

# 监控所有服务
bash scripts/server/view-logs.sh all -f
```

#### 3. 测试 API 端点

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/server/test-all-endpoints.sh
```

### 在本地 Windows 上执行

#### 1. 打开浏览器测试

在 PowerShell 中执行：

```powershell
cd D:\telegram-ai-system
powershell scripts/local/test-browser.ps1
```

这会自动打开以下测试页面：
- 后端 API 文档 (Swagger UI)
- 后端 API 文档 (ReDoc)
- 后端健康检查
- 前端首页

## 📋 详细测试清单

### 后端 API 测试

#### 1. 健康检查
```bash
curl http://localhost:8000/health
```

预期响应：
```json
{"status":"healthy","timestamp":"..."}
```

#### 2. API 文档
- 访问: http://localhost:8000/docs
- 检查: Swagger UI 是否正常加载
- 测试: 尝试调用一个公开的 API 端点

#### 3. 认证测试
```bash
# 测试登录端点（会返回 401，这是正常的）
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}'
```

### 前端功能测试

1. **访问首页**
   - URL: http://localhost:3000
   - 检查: 页面是否正常加载

2. **登录功能**
   - 使用管理员账号登录
   - 检查: 登录是否成功

3. **功能模块测试**
   - 账号管理
   - 剧本管理
   - 服务器管理
   - 角色分配
   - 通知配置
   - 权限管理

## 🔍 故障排查

### 服务无法启动

1. **查看服务状态**
   ```bash
   sudo systemctl status telegram-backend
   sudo systemctl status telegram-bot
   ```

2. **查看详细日志**
   ```bash
   sudo journalctl -u telegram-backend -n 100
   sudo journalctl -u telegram-bot -n 100
   ```

3. **检查端口占用**
   ```bash
   ss -tlnp | grep :8000
   ```

4. **手动测试启动**
   ```bash
   # 测试后端
   cd /home/ubuntu/telegram-ai-system/admin-backend
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   
   # 测试 Bot（在另一个终端）
   cd /home/ubuntu/telegram-ai-system
   source venv/bin/activate
   python main.py
   ```

### API 返回错误

1. **检查后端日志**
   ```bash
   bash scripts/server/view-logs.sh backend -n 50
   ```

2. **检查数据库连接**
   ```bash
   # 查看后端日志中的数据库错误
   sudo journalctl -u telegram-backend | grep -i "database\|sql"
   ```

3. **检查环境变量**
   ```bash
   # 查看服务环境变量
   sudo systemctl show telegram-backend | grep Environment
   ```

### 前端无法访问

1. **检查前端服务状态**
   ```bash
   # 如果使用 systemd
   sudo systemctl status liaotian-frontend
   
   # 或检查进程
   ps aux | grep -E "node.*next|npm.*start"
   ```

2. **检查端口**
   ```bash
   ss -tlnp | grep :3000
   ```

3. **查看前端日志**
   ```bash
   # 如果使用 systemd
   sudo journalctl -u liaotian-frontend -f
   ```

## 📊 监控命令速查

### 服务管理

```bash
# 查看所有服务状态
sudo bash scripts/server/manage-services.sh status all

# 重启所有服务
sudo bash scripts/server/manage-services.sh restart all

# 启动单个服务
sudo bash scripts/server/manage-services.sh start backend
sudo bash scripts/server/manage-services.sh start bot
```

### 日志查看

```bash
# 实时监控所有日志
bash scripts/server/monitor-all-logs.sh

# 查看后端最后 100 行
bash scripts/server/view-logs.sh backend -n 100

# 查看错误日志
bash scripts/server/view-logs.sh all -e

# 查看最近 1 小时的日志
bash scripts/server/view-logs.sh backend -s 1h
```

### 健康检查

```bash
# 快速健康检查
curl http://localhost:8000/health

# 完整 API 测试
bash scripts/server/test-all-endpoints.sh
```

## 🎯 测试流程建议

1. **重启服务**
   ```bash
   sudo bash scripts/server/restart-and-test.sh
   ```

2. **开始监控日志**（新终端）
   ```bash
   bash scripts/server/monitor-all-logs.sh
   ```

3. **测试 API**（另一个终端）
   ```bash
   bash scripts/server/test-all-endpoints.sh
   ```

4. **打开浏览器测试**（本地 Windows）
   ```powershell
   powershell scripts/local/test-browser.ps1
   ```

5. **检查功能**
   - 登录系统
   - 测试各个功能模块
   - 检查数据是否正确显示
   - 测试 CRUD 操作

6. **如果发现问题**
   - 查看监控日志中的错误信息
   - 使用故障排查步骤
   - 修复问题后重新测试

## 📝 常见问题

### Q: 服务启动后立即停止

**A:** 检查日志中的错误信息：
```bash
sudo journalctl -u telegram-backend -n 50
```

常见原因：
- 虚拟环境路径错误
- 依赖包缺失
- 端口被占用
- 环境变量配置错误

### Q: API 返回 500 错误

**A:** 查看后端日志：
```bash
bash scripts/server/view-logs.sh backend -e
```

常见原因：
- 数据库连接失败
- 代码错误
- 依赖问题

### Q: 前端页面空白或加载失败

**A:** 检查：
1. 前端服务是否运行
2. 浏览器控制台错误
3. 网络请求是否成功
4. API 地址配置是否正确

## 🔗 相关文档

- [PM2 到 Systemd 迁移指南](PM2_TO_SYSTEMD_MIGRATION.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [故障排查指南](TROUBLESHOOTING.md)

