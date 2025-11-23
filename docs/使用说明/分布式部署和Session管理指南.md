# 分布式部署和 Session 管理指南

> **更新日期**: 2025-11-19  
> **适用版本**: v1.0+

---

## 概述

本指南介绍如何：
1. 检查服务器部署状态
2. 分布式上传 Session 文件
3. 设置自动运行 Session（每个服务器 3-5 个）
4. 管理分布式 Session

---

## 服务器信息

### 洛杉矶服务器
- **IP**: 165.154.255.48
- **用户名**: ubuntu
- **密码**: 8iDcGrYb52Fxpzee

### 马尼拉服务器
- **IP**: 165.154.233.179
- **用户名**: ubuntu
- **密码**: 8iDcGrYb52Fxpzee

---

## 1. 检查部署状态

### 检查单个服务器

```powershell
# 检查洛杉矶服务器
.\scripts\deployment\check_deployment.ps1 -ServerIP 165.154.255.48

# 检查马尼拉服务器
.\scripts\deployment\check_deployment.ps1 -ServerIP 165.154.233.179
```

### 检查所有服务器

```powershell
.\scripts\deployment\check_all_servers.ps1
```

### 检查内容

脚本会检查：
- ✅ 部署目录是否存在
- ✅ `main.py` 文件是否存在
- ✅ 服务运行状态
- ✅ 端口监听状态
- ✅ 健康检查
- ✅ 关键文件完整性
- ✅ Session 目录和文件
- ✅ 日志文件

---

## 2. 分布式上传 Session 文件

### 自动分配上传

```powershell
# 上传所有 Session 文件，每个服务器分配 4 个
.\scripts\deployment\distribute_sessions.ps1 -SessionDir "sessions" -SessionsPerServer 4
```

### 手动上传单个 Session

```powershell
# 上传到洛杉矶服务器
.\scripts\deployment\manage_sessions.ps1 -Action upload -ServerIP 165.154.255.48 -SessionFile "sessions/my_session.session"

# 上传到马尼拉服务器
.\scripts\deployment\manage_sessions.ps1 -Action upload -ServerIP 165.154.233.179 -SessionFile "sessions/my_session.session"
```

### 分配策略

- 脚本会自动将 Session 文件平均分配到所有服务器
- 默认每个服务器分配 4 个 Session 文件
- 可以通过 `-SessionsPerServer` 参数调整数量

---

## 3. 设置自动运行 Session

### 自动设置（推荐）

```powershell
# 每个服务器自动运行 4 个 Session
.\scripts\deployment\setup_auto_sessions.ps1 -SessionsPerServer 4

# 每个服务器自动运行 5 个 Session
.\scripts\deployment\setup_auto_sessions.ps1 -SessionsPerServer 5
```

### 设置内容

脚本会：
1. 获取每个服务器上的 Session 文件列表
2. 选择前 N 个 Session 文件（N = SessionsPerServer）
3. 创建自动运行脚本 `auto_start_sessions.sh`
4. 安装 systemd 服务（可选）
5. 启动自动运行服务

### 手动设置

如果需要手动设置，可以 SSH 到服务器：

```bash
# SSH 到服务器
ssh ubuntu@165.154.255.48

# 编辑自动运行脚本
nano ~/telegram-ai-system/auto_start_sessions.sh

# 设置执行权限
chmod +x ~/telegram-ai-system/auto_start_sessions.sh

# 手动运行
bash ~/telegram-ai-system/auto_start_sessions.sh
```

---

## 4. Session 管理

### 查看 Session 列表

```powershell
# 查看所有服务器的 Session
.\scripts\deployment\manage_sessions.ps1 -Action list

# 查看特定服务器的 Session
.\scripts\deployment\manage_sessions.ps1 -Action list -ServerIP 165.154.255.48
```

### 查看运行状态

```powershell
# 查看所有服务器的运行状态
.\scripts\deployment\manage_sessions.ps1 -Action status

# 查看特定服务器的运行状态
.\scripts\deployment\manage_sessions.ps1 -Action status -ServerIP 165.154.255.48
```

### 启动 Session

```powershell
# 启动所有服务器的 Session
.\scripts\deployment\manage_sessions.ps1 -Action start

# 启动特定服务器的 Session
.\scripts\deployment\manage_sessions.ps1 -Action start -ServerIP 165.154.255.48
```

### 停止 Session

```powershell
# 停止所有服务器的 Session
.\scripts\deployment\manage_sessions.ps1 -Action stop

# 停止特定服务器的 Session
.\scripts\deployment\manage_sessions.ps1 -Action stop -ServerIP 165.154.255.48
```

---

## 5. 服务器端管理

### 查看日志

```bash
# 查看后端服务日志
ssh ubuntu@165.154.255.48 'tail -f ~/telegram-ai-system/logs/backend.log'

# 查看 Session 运行日志
ssh ubuntu@165.154.255.48 'tail -f ~/telegram-ai-system/logs/session_*.log'
```

### 管理 Systemd 服务

```bash
# 查看服务状态
ssh ubuntu@165.154.255.48 'sudo systemctl status telegram-ai-sessions'

# 启动服务
ssh ubuntu@165.154.255.48 'sudo systemctl start telegram-ai-sessions'

# 停止服务
ssh ubuntu@165.154.255.48 'sudo systemctl stop telegram-ai-sessions'

# 重启服务
ssh ubuntu@165.154.255.48 'sudo systemctl restart telegram-ai-sessions'

# 查看服务日志
ssh ubuntu@165.154.255.48 'sudo journalctl -u telegram-ai-sessions -f'
```

### 检查进程

```bash
# 查看运行中的 Session 进程
ssh ubuntu@165.154.255.48 'ps aux | grep -E "python.*session|uvicorn.*session" | grep -v grep'

# 查看所有相关进程
ssh ubuntu@165.154.255.48 'ps aux | grep telegram-ai'
```

---

## 6. 最佳实践

### Session 分配建议

- **每个服务器 3-5 个 Session**：平衡负载和资源使用
- **均匀分配**：确保所有服务器负载均衡
- **定期检查**：定期检查 Session 运行状态

### 监控建议

1. **定期检查服务状态**
   ```powershell
   .\scripts\deployment\manage_sessions.ps1 -Action status
   ```

2. **监控日志**
   - 后端服务日志
   - Session 运行日志
   - Systemd 服务日志

3. **健康检查**
   ```powershell
   .\scripts\deployment\test_deployment.ps1 -ServerIP 165.154.255.48
   ```

### 故障处理

#### Session 启动失败

1. 检查 Session 文件是否存在
2. 检查文件权限（应该是 600）
3. 查看日志文件
4. 验证 Session 文件有效性

#### 服务无法连接

1. 检查防火墙设置
2. 验证端口是否开放
3. 检查服务是否运行
4. 查看服务日志

#### Session 运行异常

1. 检查系统资源（CPU、内存）
2. 查看 Session 日志
3. 重启相关 Session
4. 必要时重新部署

---

## 7. 完整部署流程

### 首次部署

```powershell
# 1. 部署到所有服务器
.\scripts\deployment\deploy_all_servers.ps1

# 2. 检查部署状态
.\scripts\deployment\check_all_servers.ps1

# 3. 分布式上传 Session 文件
.\scripts\deployment\distribute_sessions.ps1 -SessionsPerServer 4

# 4. 设置自动运行
.\scripts\deployment\setup_auto_sessions.ps1 -SessionsPerServer 4

# 5. 验证运行状态
.\scripts\deployment\manage_sessions.ps1 -Action status
```

### 日常管理

```powershell
# 检查所有服务器状态
.\scripts\deployment\check_all_servers.ps1

# 查看 Session 运行状态
.\scripts\deployment\manage_sessions.ps1 -Action status

# 上传新的 Session 文件
.\scripts\deployment\manage_sessions.ps1 -Action upload -ServerIP 165.154.255.48 -SessionFile "sessions/new_session.session"
```

---

## 8. 故障排查

### 常见问题

#### 1. SSH 连接失败

**原因**：
- 服务器 IP 或密码错误
- 防火墙阻止 SSH 连接
- 服务器未运行

**解决**：
- 验证服务器信息
- 检查网络连接
- 联系服务器提供商

#### 2. Session 文件上传失败

**原因**：
- 文件路径错误
- 权限不足
- 磁盘空间不足

**解决**：
- 检查文件路径
- 验证文件权限
- 检查磁盘空间

#### 3. Session 无法启动

**原因**：
- Session 文件损坏
- 配置错误
- 依赖缺失

**解决**：
- 验证 Session 文件
- 检查配置文件
- 安装缺失依赖

---

## 9. 安全建议

1. **使用 SSH 密钥**：建议配置 SSH 密钥认证
2. **文件权限**：Session 文件权限设置为 600
3. **密码管理**：使用密码管理器存储服务器密码
4. **定期更新**：定期更新系统和依赖
5. **监控访问**：监控服务器访问日志

---

## 10. 联系支持

如遇到问题，请：
1. 查看日志文件
2. 检查本文档的故障排查部分
3. 联系技术支持

---

**文档版本**: v1.0  
**最后更新**: 2025-11-19

