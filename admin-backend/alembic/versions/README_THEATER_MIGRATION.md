# 智能剧场表迁移说明

## 迁移脚本
- **文件**: `007_add_theater_tables.py`
- **Revision ID**: `007_add_theater_tables`
- **依赖**: `xxxx_add_telegram_registration`

## 创建的表

### 1. `theater_scenarios` (剧场场景表)
- `id`: 主键 (String 36)
- `name`: 场景名称 (String 200, 索引)
- `description`: 场景描述 (Text)
- `roles`: 角色列表 (JSON, 默认 [])
- `timeline`: 时间轴动作列表 (JSON, 默认 [])
- `enabled`: 是否启用 (Boolean, 默认 True, 索引)
- `created_by`: 创建者用户ID (String 100)
- `created_at`: 创建时间 (DateTime)
- `updated_at`: 更新时间 (DateTime)

### 2. `theater_executions` (执行记录表)
- `id`: 主键 (String 36)
- `scenario_id`: 关联的场景ID (String 36, 索引)
- `scenario_name`: 场景名称快照 (String 200)
- `group_id`: 目标群组ID (String 100, 索引)
- `agent_mapping`: Agent 映射 (JSON, 默认 {})
- `status`: 执行状态 (String 20, 默认 'pending', 索引)
  - 可选值: `pending`, `running`, `completed`, `failed`, `cancelled`
- `started_at`: 开始时间 (DateTime)
- `completed_at`: 完成时间 (DateTime)
- `duration_seconds`: 执行时长（秒）(Integer)
- `executed_actions`: 已执行的动作列表 (JSON, 默认 [])
- `error_message`: 错误信息 (Text)
- `created_by`: 创建者用户ID (String 100)
- `created_at`: 创建时间 (DateTime, 索引)
- `updated_at`: 更新时间 (DateTime)

## 运行迁移

### 本地开发环境
```bash
cd admin-backend
alembic upgrade head
```

### 服务器环境
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate  # 或 .venv/bin/activate
alembic upgrade head
```

### 验证迁移
```bash
# 检查迁移状态
alembic current

# 查看迁移历史
alembic history

# 验证表是否创建成功（SQLite）
sqlite3 database.db ".tables" | grep theater

# 验证表是否创建成功（PostgreSQL）
psql -U username -d database -c "\dt theater*"
```

## 回滚迁移（如果需要）
```bash
alembic downgrade -1
```

## 注意事项
1. 迁移前请备份数据库
2. 确保 `alembic/env.py` 中已导入 `theater` 模型
3. 如果使用 SQLite，JSON 字段会存储为 TEXT
4. 如果使用 PostgreSQL，确保已安装 `psycopg2` 或 `psycopg2-binary`
