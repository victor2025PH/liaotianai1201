# 部署检查清单

## 📋 部署前检查

### 1. 代码检查 ✅
- [x] 所有代码已提交到 Git
- [x] 代码通过 lint 检查
- [x] 所有三个前端项目已迁移到代理 API
- [x] 后端 API 已实现

### 2. 文件清单 ✅

#### 后端文件
- [x] `admin-backend/app/api/ai_proxy.py` - AI 代理 API
- [x] `admin-backend/app/api/ai_monitoring.py` - 监控 API
- [x] `admin-backend/app/models/ai_usage.py` - 数据库模型
- [x] `admin-backend/app/crud/ai_usage.py` - CRUD 操作
- [x] `admin-backend/alembic/versions/xxxx_add_ai_usage_tables.py` - 数据库迁移

#### 前端文件（每个项目）
- [x] `*/utils/aiProxy.ts` - 代理工具
- [x] `*/contexts/AIChatContext.tsx` - 更新的上下文

#### 脚本文件
- [x] `scripts/verify_production_deployment.sh` - 生产环境验证
- [x] `scripts/create_ai_usage_migration.sh` - 创建迁移脚本
- [x] `scripts/apply_ai_usage_migration.sh` - 应用迁移脚本

---

## 🚀 部署步骤

### 步骤 1: 验证生产环境

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/verify_production_deployment.sh
```

**检查项**:
- [ ] 项目目录存在
- [ ] 后端服务运行中
- [ ] 端口 8000 监听中
- [ ] 环境变量已配置
- [ ] 本地 API 可访问
- [ ] 远程 API 可访问
- [ ] 路由已注册
- [ ] 前端服务运行中
- [ ] 无错误日志
- [ ] Python 环境正常

### 步骤 2: 创建数据库迁移

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate  # 或 source .venv/bin/activate

# 方法 1: 使用自动生成（推荐）
alembic revision --autogenerate -m "add_ai_usage_tables"

# 方法 2: 使用已创建的迁移文件
# 检查并更新 revision ID
# 编辑 alembic/versions/xxxx_add_ai_usage_tables.py
# 更新 down_revision 为最新的 revision ID
```

**验证迁移文件**:
- [ ] 检查 `down_revision` 是否正确
- [ ] 检查表结构是否完整
- [ ] 检查索引是否创建

### 步骤 3: 应用数据库迁移

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate

# 查看当前版本
alembic current

# 应用迁移
alembic upgrade head

# 验证表是否创建
sqlite3 admin.db '.tables' | grep ai_usage
```

**验证**:
- [ ] `ai_usage_logs` 表已创建
- [ ] `ai_usage_stats` 表已创建
- [ ] 索引已创建

### 步骤 4: 重启后端服务

```bash
# 重启后端
pm2 restart backend

# 或使用 systemd
sudo systemctl restart luckyred-api

# 检查服务状态
pm2 list | grep backend
# 或
sudo systemctl status luckyred-api
```

**验证**:
- [ ] 服务正常运行
- [ ] 无错误日志
- [ ] API 端点可访问

### 步骤 5: 测试 API 端点

```bash
# 测试代理 API
curl -X POST http://127.0.0.1:8000/api/v1/ai-proxy/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "你是一个AI助手"},
      {"role": "user", "content": "你好"}
    ],
    "model": "gemini-2.5-flash-latest"
  }'

# 测试监控 API
curl http://127.0.0.1:8000/api/v1/ai-monitoring/summary?days=7
```

**验证**:
- [ ] 代理 API 返回正常
- [ ] 监控 API 返回正常
- [ ] 使用统计已记录

### 步骤 6: 测试前端功能

1. **访问网站**
   - https://aizkw.usdt2026.cc
   - https://hongbao.usdt2026.cc
   - https://tgmini.usdt2026.cc

2. **测试 AI 聊天**
   - [ ] 打开 AI 聊天窗口
   - [ ] 发送测试消息
   - [ ] 收到 AI 回复
   - [ ] 检查浏览器控制台无错误
   - [ ] 检查 Network 标签，确认调用代理 API

3. **验证安全性**
   - [ ] 检查浏览器控制台，确认无 API Keys 暴露
   - [ ] 检查 Network 请求，确认调用 `/api/v1/ai-proxy/chat`

---

## 🔍 故障排查

### 问题 1: 数据库迁移失败

**症状**: `alembic upgrade head` 失败

**解决方案**:
```bash
# 检查当前版本
alembic current

# 检查迁移文件
cat alembic/versions/xxxx_add_ai_usage_tables.py

# 手动修复 down_revision
# 编辑文件，更新 down_revision 为正确的 revision ID
```

### 问题 2: 代理 API 返回 404

**症状**: `POST /api/v1/ai-proxy/chat` 返回 404

**解决方案**:
```bash
# 检查路由是否注册
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python -c "
from app.main import app
for route in app.routes:
    if hasattr(route, 'path') and 'ai-proxy' in route.path:
        print(f'{route.methods} {route.path}')
"

# 检查后端日志
pm2 logs backend --lines 50
```

### 问题 3: 前端无法连接代理 API

**症状**: 浏览器控制台显示网络错误

**解决方案**:
1. 检查 API 地址配置
2. 检查 CORS 配置
3. 检查 Nginx 配置
4. 检查后端服务状态

### 问题 4: 使用统计未记录

**症状**: 监控 API 返回空数据

**解决方案**:
```bash
# 检查数据库表是否存在
sqlite3 admin.db '.tables' | grep ai_usage

# 检查是否有数据
sqlite3 admin.db 'SELECT COUNT(*) FROM ai_usage_logs;'

# 检查后端日志
pm2 logs backend --lines 100 | grep -i "ai_usage\|usage_log"
```

---

## ✅ 部署后验证

### 功能验证
- [ ] AI 聊天功能正常
- [ ] 代理 API 正常工作
- [ ] 故障转移正常（Gemini → OpenAI）
- [ ] 使用统计已记录
- [ ] 监控 API 返回数据

### 性能验证
- [ ] API 响应时间 < 3秒
- [ ] 无内存泄漏
- [ ] 无 CPU 占用过高

### 安全验证
- [ ] API Keys 未暴露给前端
- [ ] CORS 配置正确
- [ ] 无敏感信息泄露

---

## 📊 监控指标

### 关键指标
- API 调用次数
- 成功率
- 平均响应时间
- 成本统计
- 错误率

### 查看方式
```bash
# 使用监控 API
curl http://127.0.0.1:8000/api/v1/ai-monitoring/summary?days=7

# 查看数据库
sqlite3 admin.db 'SELECT * FROM ai_usage_stats ORDER BY stat_date DESC LIMIT 10;'
```

---

## 📝 回滚方案

如果出现问题，可以回滚：

### 回滚数据库迁移
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate

# 回滚到上一个版本
alembic downgrade -1
```

### 回滚前端代码
```bash
# 恢复旧的 AIChatContext.tsx
git checkout HEAD~1 -- aizkw20251219/contexts/AIChatContext.tsx
git checkout HEAD~1 -- hbwy20251220/contexts/AIChatContext.tsx
git checkout HEAD~1 -- tgmini20251220/contexts/AIChatContext.tsx

# 重新构建
cd aizkw20251219 && npm run build
cd ../hbwy20251220 && npm run build
cd ../tgmini20251220 && npm run build
```

---

**最后更新**: 2025-12-23

