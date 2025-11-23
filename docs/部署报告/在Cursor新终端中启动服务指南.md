# 在 Cursor 新终端中启动服务指南

## 方法：在 Cursor 新终端中运行

### 步骤 1: 打开第一个新终端（后端服务）

1. 在 Cursor 中按 `Ctrl+`` (反引号) 打开终端，或点击菜单 `Terminal` -> `New Terminal`
2. 在终端中运行以下命令：

```powershell
cd admin-backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. 等待看到以下消息表示启动成功：
   ```
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

### 步骤 2: 打开第二个新终端（前端服务）

1. 在 Cursor 中再次按 `Ctrl+`` 打开**另一个**新终端
2. 在第二个终端中运行以下命令：

```powershell
cd saas-demo
npm run dev
```

3. 等待看到以下消息表示启动成功：
   ```
   ✓ Ready in XXXms
   - Local:        http://localhost:3000
   ```

### 步骤 3: 验证服务

1. **后端服务**: 访问 http://localhost:8000/docs 应该能看到 API 文档
2. **前端服务**: 访问 http://localhost:3000 应该能看到登录页面

## 常见问题

### Q: 后端服务启动失败

**错误**: `SmartOptimizer.__init__() got an unexpected keyword argument 'auto_optimize_enabled'`
- **状态**: ✅ 已修复

**错误**: `AttributeError: module 'bcrypt' has no attribute '__about__'`
- **状态**: ⚠️ 警告，不影响功能

**错误**: `No module named 'psycopg2'`
- **状态**: ⚠️ 正常，会回退到 SQLite

### Q: 前端服务启动失败

**错误**: `Port 3000 is in use`
- **解决**: 停止占用端口的进程，或使用其他端口

**错误**: `Unable to acquire lock`
- **解决**: 删除 `.next/dev/lock` 文件

### Q: 服务启动后立即退出

**原因**: 可能是代码错误或依赖问题
**解决**: 查看终端中的错误信息，根据错误进行修复

## 服务管理

### 停止服务
在对应的终端中按 `Ctrl+C`

### 重启服务
1. 停止服务（Ctrl+C）
2. 重新运行启动命令

### 查看日志
服务日志会实时显示在终端中

## 验证服务运行

### 检查后端服务
```powershell
# 检查端口
Get-NetTCPConnection -LocalPort 8000

# 测试健康检查
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

### 检查前端服务
```powershell
# 检查端口
Get-NetTCPConnection -LocalPort 3000

# 在浏览器中访问
# http://localhost:3000
```

## 快速命令参考

### 后端服务
```powershell
cd admin-backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端服务
```powershell
cd saas-demo
npm run dev
```

## 注意事项

1. **保持终端打开**: 服务在终端中运行，关闭终端会停止服务
2. **查看实时日志**: 所有日志都会显示在终端中
3. **错误信息**: 如果服务启动失败，终端会显示详细的错误信息
4. **端口占用**: 确保端口 8000 和 3000 未被其他程序占用

