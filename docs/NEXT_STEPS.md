# 下一步操作指南

**当前状态**: 所有代码已部署，服务运行正常  
**更新时间**: 2025-12-09

## 立即执行（高优先级）

### 1. 修改管理员密码 ⚠️ 重要

**原因**: 当前使用默认密码 `changeme123`，存在安全风险

**执行命令**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/update_security_config.py
```

**操作步骤**:
1. 运行上述命令
2. 按照提示输入新密码（至少8个字符）
3. 确认更新
4. 重启服务: `pm2 restart backend --update-env`

### 2. 验证JWT_SECRET配置

**原因**: 确保JWT_SECRET已更新为强随机值

**执行命令**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/system_health_check.py
```

**检查项**:
- ✓ JWT_SECRET已修改（不是默认值）
- ✓ 管理员密码已修改

## 短期优化（中优先级）

### 3. 配置通知渠道

**可选渠道**:
- 邮件通知（Email）
- Telegram通知
- Webhook通知（Slack/Discord等）

**执行命令**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/configure_notifications.py
```

**配置步骤**:
1. 选择要配置的通知渠道（1-3）
2. 按照提示输入配置信息
3. 重启服务: `pm2 restart backend --update-env`

**详细指南**: 参考 `docs/NOTIFICATION_SETUP_GUIDE.md`

### 4. 运行性能基准测试

**目的**: 建立性能基线，用于后续性能对比

**执行命令**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/performance_benchmark.py
```

**操作步骤**:
1. 运行测试脚本
2. 首次运行选择 `yes` 设置为基线
3. 后续运行会自动与基线对比

**结果位置**: `admin-backend/benchmarks/`

## 定期维护（低优先级）

### 5. 系统健康检查

**频率**: 每周执行一次

**执行命令**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/system_health_check.py
```

**检查项**:
- 服务状态（后端、前端）
- 数据库连接
- 磁盘空间
- 安全配置

### 6. 数据库性能检查

**频率**: 每月执行一次

**执行命令**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/check_database_performance.py
```

### 7. 性能基准测试对比

**频率**: 每月执行一次

**执行命令**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/performance_benchmark.py
```

**目的**: 对比当前性能与基线，发现性能退化

## 功能测试

### 8. 测试前端功能

**访问地址**: `https://aikz.usdt2026.cc`

**测试项**:
- [ ] 登录功能
- [ ] 仪表板数据展示
- [ ] 账户管理
- [ ] 脚本管理
- [ ] 监控页面
- [ ] 健康检查页面 (`/health`)
- [ ] 性能监控页面 (`/performance`)
- [ ] 日志管理页面 (`/group-ai/logs`)
- [ ] 会话管理页面 (`/group-ai/sessions`)

### 9. 测试后端API

**访问地址**: `https://aikz.usdt2026.cc/docs`

**测试项**:
- [ ] 登录API (`POST /api/v1/auth/login`)
- [ ] 健康检查 (`GET /health`)
- [ ] 仪表板API (`GET /api/v1/group-ai/dashboard`)
- [ ] 性能统计API (`GET /api/v1/system/performance`)
- [ ] 告警管理API (`GET /api/v1/group-ai/alert-management/statistics`)

## 监控和告警

### 10. 配置告警规则

**配置文件**: `admin-backend/app/config/alert_rules.yaml`

**告警类型**:
- 性能告警（API响应时间、慢查询）
- 系统资源告警（CPU、内存、磁盘）
- 服务健康告警（后端、前端、数据库）
- 业务告警（账号启动失败、脚本执行错误）

### 11. 测试告警通知

**执行命令**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/test_alert_notifications.py
```

## 文档阅读

### 12. 阅读相关文档

**推荐阅读顺序**:
1. `docs/SECURITY_CONFIGURATION_GUIDE.md` - 安全配置指南
2. `docs/NOTIFICATION_SETUP_GUIDE.md` - 通知配置指南
3. `docs/DEPLOYMENT_GUIDE.md` - 部署指南
4. `docs/API_DOCUMENTATION.md` - API文档
5. `docs/USER_MANUAL.md` - 用户手册

## 快速执行清单

### 今天必须完成

- [ ] 修改管理员密码
- [ ] 验证JWT_SECRET配置
- [ ] 测试登录功能

### 本周完成

- [ ] 配置至少一个通知渠道
- [ ] 运行性能基准测试并设置基线
- [ ] 完成前端功能测试
- [ ] 阅读安全配置指南

### 本月完成

- [ ] 配置所有告警规则
- [ ] 测试告警通知功能
- [ ] 运行数据库性能检查
- [ ] 完成API功能测试

## 一键执行脚本

### 执行所有高优先级任务

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate

# 1. 更新安全配置（包括密码）
python3 ../scripts/server/update_security_config.py

# 2. 验证配置
python3 ../scripts/server/system_health_check.py

# 3. 重启服务
cd ..
pm2 restart backend --update-env

# 4. 验证服务
sleep 3
curl http://localhost:8000/health
```

### 执行所有中优先级任务

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate

# 1. 配置通知渠道
python3 ../scripts/server/configure_notifications.py

# 2. 运行性能基准测试
python3 ../scripts/server/performance_benchmark.py

# 3. 重启服务
cd ..
pm2 restart backend --update-env
```

## 故障排查

### 如果服务无法启动

```bash
# 检查PM2状态
pm2 status

# 查看日志
pm2 logs backend --lines 50
pm2 logs frontend --lines 50

# 重启服务
pm2 restart all
```

### 如果脚本无法运行

```bash
# 检查虚拟环境
cd /home/ubuntu/telegram-ai-system/admin-backend
ls -la venv/bin/activate

# 重新激活虚拟环境
source venv/bin/activate

# 检查Python路径
which python
```

### 如果文件缺失

```bash
# 强制拉取所有文件
cd /home/ubuntu/telegram-ai-system
git fetch origin
git reset --hard origin/main
bash scripts/server/deploy_all_files.sh
```

## 联系和支持

如果遇到问题：
1. 查看相关文档（`docs/` 目录）
2. 检查系统健康状态
3. 查看服务日志
4. 参考故障排查指南

---

**最后更新**: 2025-12-09  
**状态**: 系统运行正常，等待配置优化

