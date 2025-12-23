# 部署问题修复指南

## 问题 1: 数据库迁移错误 - `table users already exists`

### 问题描述

执行 `alembic upgrade head` 时出现错误：
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) table users already exists
```

### 原因

数据库表已存在，但 Alembic 迁移脚本试图重新创建它们。

### 解决方案

#### 方案 1: 使用修复脚本（推荐）

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/fix_alembic_migration.sh
```

#### 方案 2: 标记迁移为已执行

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend

# 激活虚拟环境
source .venv/bin/activate  # 或 source venv/bin/activate

# 标记初始迁移为已执行
alembic stamp 000_initial_base

# 然后运行后续迁移
alembic upgrade head
```

#### 方案 3: 手动修复（如果表结构正确）

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source .venv/bin/activate

# 检查当前版本
alembic current

# 如果显示为空，标记为最新版本
alembic stamp head
```

### 已修复

迁移脚本 `000_initial_base_tables.py` 已更新，现在会在创建表前检查表是否存在。

## 问题 2: 管理后台 404 错误

### 问题描述

访问 `http://127.0.0.1:3001` 返回 404 Not Found。

### 原因

管理后台前端未部署或未启动。

### 解决方案

#### 步骤 1: 检查状态

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/check_admin_frontend.sh
```

#### 步骤 2: 部署管理后台

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/deploy_admin_frontend.sh
```

#### 步骤 3: 验证

```bash
# 检查 PM2 进程
pm2 list | grep admin-frontend

# 检查端口
curl http://127.0.0.1:3001
```

## 问题 3: SSL 证书错误

### 问题描述

使用 `curl https://aiadmin.usdt2026.cc/...` 时出现 SSL 证书错误。

### 原因

SSL 证书配置问题或证书不匹配。

### 解决方案

#### 临时方案: 使用 HTTP（仅测试）

```bash
# 使用 HTTP 而不是 HTTPS
curl http://aiadmin.usdt2026.cc/api/v1/ai-monitoring/summary?days=7
```

#### 永久方案: 修复 SSL 证书

1. 检查 Nginx SSL 配置
2. 确保证书文件路径正确
3. 重启 Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 快速修复命令

### 一次性修复所有问题

```bash
cd /home/ubuntu/telegram-ai-system

# 1. 修复数据库迁移
cd admin-backend
source .venv/bin/activate
alembic stamp head 2>/dev/null || alembic upgrade head

# 2. 部署管理后台
cd ..
bash scripts/deploy_admin_frontend.sh

# 3. 验证
pm2 list
curl http://127.0.0.1:3001
```

## 验证清单

- [ ] 数据库迁移成功执行
- [ ] 管理后台前端进程运行中
- [ ] 端口 3001 可访问
- [ ] PM2 进程列表包含 `admin-frontend`
- [ ] 后端 API 可访问（HTTP 或 HTTPS）

## 相关脚本

- `scripts/fix_alembic_migration.sh` - 修复数据库迁移
- `scripts/check_admin_frontend.sh` - 检查管理后台状态
- `scripts/deploy_admin_frontend.sh` - 部署管理后台

---

**最后更新**: 2025-12-24

