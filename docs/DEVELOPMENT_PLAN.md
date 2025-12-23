# AI 聊天系统开发计划

## 📋 开发优先级

按照用户要求，按以下四个优先级开始开发：

1. ✅ **优先验证生产环境部署**
2. 🔄 **逐步完善高级功能**
3. 🔄 **加强安全性（API Key 代理）**
4. 🔄 **添加管理功能（统计、监控）**

---

## ✅ 1. 优先验证生产环境部署

### 已完成
- ✅ 创建生产环境验证脚本 `scripts/verify_production_deployment.sh`
- ✅ 脚本包含 10 项检查：
  1. 项目目录检查
  2. 后端服务状态检查
  3. 端口监听检查
  4. 环境变量配置检查
  5. 本地 API 测试
  6. 远程 API 测试
  7. 路由注册检查
  8. 前端服务检查
  9. 后端日志检查
  10. Python 环境检查

### 使用方法
```bash
# 在服务器上执行
cd /home/ubuntu/telegram-ai-system
bash scripts/verify_production_deployment.sh
```

### 待执行
- ⚠️ 在服务器上运行验证脚本
- ⚠️ 根据验证结果修复问题
- ⚠️ 确认所有服务正常运行

---

## 🔄 2. 逐步完善高级功能

### 计划功能
- [ ] **流式响应** (Streaming)
  - 实现 Server-Sent Events (SSE)
  - 前端实时显示 AI 回复
  - 提升用户体验

- [ ] **消息持久化**
  - 使用 localStorage 保存消息
  - 刷新页面后恢复对话
  - 可选：后端存储（需要用户认证）

- [ ] **用户会话管理**
  - 用户识别（匿名或登录）
  - 会话隔离
  - 多设备同步（可选）

### 实施计划
1. **第一阶段**：消息持久化（localStorage）
2. **第二阶段**：流式响应
3. **第三阶段**：用户会话管理

---

## 🔄 3. 加强安全性（API Key 代理）

### 已完成
- ✅ 创建 AI 代理 API (`admin-backend/app/api/ai_proxy.py`)
- ✅ 实现后端调用 AI 服务
- ✅ 避免在前端暴露 API Keys
- ✅ 支持 Gemini 和 OpenAI
- ✅ 自动故障转移
- ✅ 使用统计记录

### API 端点
- `POST /api/v1/ai-proxy/chat` - 代理聊天请求
- `GET /api/v1/ai-proxy/stats` - 获取使用统计

### 待完成
- [ ] 更新前端代码，使用代理 API 替代直接调用
- [ ] 添加请求频率限制
- [ ] 添加用户认证（可选）
- [ ] 添加 IP 白名单（可选）

### 前端迁移步骤
1. 修改 `AIChatContext.tsx`，使用代理 API
2. 移除前端 API Key 配置
3. 更新错误处理
4. 测试验证

---

## 🔄 4. 添加管理功能（统计、监控）

### 已完成
- ✅ 创建数据库模型 (`admin-backend/app/models/ai_usage.py`)
  - `AIUsageLog` - 使用日志
  - `AIUsageStats` - 每日统计汇总
- ✅ 创建 CRUD 操作 (`admin-backend/app/crud/ai_usage.py`)
  - 使用日志记录
  - 成本计算
  - 每日统计更新
- ✅ 创建监控 API (`admin-backend/app/api/ai_monitoring.py`)
  - 使用摘要
  - 每日统计
  - 提供商统计
  - 错误日志

### API 端点
- `GET /api/v1/ai-monitoring/summary` - 使用摘要
- `GET /api/v1/ai-monitoring/daily` - 每日统计
- `GET /api/v1/ai-monitoring/providers` - 提供商统计
- `GET /api/v1/ai-monitoring/recent-errors` - 最近错误

### 待完成
- [ ] 创建数据库迁移脚本
- [ ] 创建管理后台界面（可选）
- [ ] 添加告警功能（可选）
- [ ] 成本分析和预测（可选）

### 数据库迁移
需要创建 Alembic 迁移脚本：
```bash
cd admin-backend
alembic revision --autogenerate -m "add_ai_usage_tables"
alembic upgrade head
```

---

## 📊 开发进度

### 已完成 ✅
- [x] 生产环境验证脚本
- [x] AI 代理 API（后端）
- [x] 使用统计模型
- [x] 监控 API
- [x] 成本计算功能

### 进行中 🔄
- [ ] 生产环境验证（待执行）
- [ ] 前端迁移到代理 API
- [ ] 数据库迁移

### 待开始 ⏳
- [ ] 流式响应
- [ ] 消息持久化
- [ ] 用户会话管理
- [ ] 管理后台界面

---

## 🚀 下一步行动

### 立即执行
1. **运行生产环境验证脚本**
   ```bash
   cd /home/ubuntu/telegram-ai-system
   bash scripts/verify_production_deployment.sh
   ```

2. **创建数据库迁移**
   ```bash
   cd /home/ubuntu/telegram-ai-system/admin-backend
   source venv/bin/activate
   alembic revision --autogenerate -m "add_ai_usage_tables"
   alembic upgrade head
   ```

3. **重启后端服务**
   ```bash
   pm2 restart backend
   ```

### 短期计划（1周内）
1. 完成前端迁移到代理 API
2. 测试所有功能
3. 部署到生产环境

### 中期计划（1个月内）
1. 实现消息持久化
2. 实现流式响应
3. 完善监控功能

---

## 📝 技术细节

### AI 代理 API 使用示例

**请求**:
```json
POST /api/v1/ai-proxy/chat
{
  "messages": [
    {"role": "system", "content": "你是一个AI助手"},
    {"role": "user", "content": "你好"}
  ],
  "model": "gemini-2.5-flash-latest",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**响应**:
```json
{
  "content": "你好！我是AI助手...",
  "model": "gemini-2.5-flash-latest",
  "suggestions": ["建议1", "建议2", "建议3"]
}
```

### 监控 API 使用示例

**获取使用摘要**:
```bash
GET /api/v1/ai-monitoring/summary?days=7&site_domain=aizkw.usdt2026.cc
```

**获取每日统计**:
```bash
GET /api/v1/ai-monitoring/daily?days=30
```

---

## 🔒 安全考虑

### 已实现
- ✅ API Keys 不再暴露给前端
- ✅ 后端统一管理 API Keys
- ✅ 使用统计记录（可用于审计）

### 待实现
- [ ] 请求频率限制（防止滥用）
- [ ] IP 白名单（可选）
- [ ] 用户认证（可选）
- [ ] API Key 轮换机制

---

## 📚 相关文档

- [AI 聊天系统开发进度](./AI_CHAT_SYSTEM_PROGRESS.md)
- [AI 对话功能修复方案](./AI_CHAT_FIX_PLAN.md)
- [统一后台管理系统方案](./UNIFIED_BACKEND_ADMIN_PLAN.md)

---

**最后更新**: 2025-12-23
**状态**: 开发中

