# 安全配置指南

本文档提供系统安全配置的详细说明和最佳实践。

## 立即执行的安全修复

### 1. 修复 JWT_SECRET

**问题**: JWT_SECRET使用默认值 `change_me`，存在严重安全风险。

**解决方法**:

#### 方法1: 使用快速修复脚本（推荐）

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/server/quick_fix_security.sh
pm2 restart backend
```

#### 方法2: 手动生成和配置

```bash
# 生成JWT密钥
cd admin-backend
source venv/bin/activate
python3 ../scripts/server/generate_jwt_secret.py

# 复制生成的密钥，编辑 .env 文件
nano .env
# 设置: JWT_SECRET=<生成的密钥>

# 重启服务
pm2 restart backend
```

#### 方法3: 使用交互式脚本

```bash
cd admin-backend
source venv/bin/activate
python3 ../scripts/server/update_security_config.py
```

### 2. 修改管理员密码

**问题**: ADMIN_DEFAULT_PASSWORD使用默认值 `changeme123`。

**解决方法**:

```bash
# 编辑 .env 文件
cd admin-backend
nano .env

# 设置强密码
ADMIN_DEFAULT_PASSWORD=<您的强密码>

# 重启服务
pm2 restart backend
```

**密码要求**:
- 至少8个字符
- 建议包含大小写字母、数字和特殊字符
- 不要使用常见密码或个人信息

## 通知渠道配置

### 邮件通知配置

#### 1. 使用配置脚本

```bash
cd admin-backend
source venv/bin/activate
python3 ../scripts/server/configure_notifications.py
# 选择选项 1: 邮件通知
```

#### 2. 手动配置

编辑 `.env` 文件：

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
```

**Gmail配置说明**:
1. 启用两步验证
2. 生成应用专用密码（不是Gmail密码）
3. 使用应用专用密码作为 `SMTP_PASSWORD`

**其他邮件服务商**:
- Outlook: `smtp-mail.outlook.com:587`
- QQ邮箱: `smtp.qq.com:587`
- 163邮箱: `smtp.163.com:25`

### Telegram通知配置

#### 1. 获取Bot Token

1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按照提示设置bot名称和用户名
4. BotFather会返回bot token（格式: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

#### 2. 获取Chat ID

1. 在Telegram中搜索 `@userinfobot`
2. 发送任意消息给该bot
3. 它会返回您的Chat ID（数字，例如: `123456789`）

#### 3. 配置

```bash
cd admin-backend
source venv/bin/activate
python3 ../scripts/server/configure_notifications.py
# 选择选项 2: Telegram通知
```

或手动编辑 `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### Webhook通知配置

#### 1. Slack Webhook

1. 访问 https://api.slack.com/apps
2. 创建新应用或选择现有应用
3. 启用 "Incoming Webhooks"
4. 创建Webhook URL

#### 2. 其他Webhook服务

- Discord: 创建Webhook URL
- 自定义服务: 提供接收POST请求的URL

#### 3. 配置

```bash
cd admin-backend
source venv/bin/activate
python3 ../scripts/server/configure_notifications.py
# 选择选项 3: Webhook通知
```

或手动编辑 `.env`:

```env
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 性能基准测试

### 运行基准测试

```bash
cd admin-backend
source venv/bin/activate
python3 ../scripts/server/performance_benchmark.py
```

### 设置基线

首次运行时会询问是否设置为基线，选择 `yes`。

### 对比性能

后续运行时会自动与基线对比，显示性能变化。

### 基准测试结果

结果保存在 `admin-backend/benchmarks/` 目录：
- `benchmark_YYYYMMDD_HHMMSS.json` - 每次测试的结果
- `baseline.json` - 性能基线

## 安全最佳实践

### 1. 环境变量安全

- ✅ 使用强随机字符串作为JWT_SECRET
- ✅ 定期更换敏感密钥
- ✅ 不要将 `.env` 文件提交到Git
- ✅ 使用不同的密钥用于开发和生产环境

### 2. 认证安全

- ✅ 启用认证（`disable_auth=false`）
- ✅ 使用强密码
- ✅ 定期更换密码
- ✅ 限制登录尝试次数（如需要）

### 3. CORS配置

- ✅ 限制CORS来源为特定域名
- ✅ 生产环境不要使用 `*`
- ✅ 使用HTTPS

### 4. HTTPS配置

- ✅ 配置SSL证书
- ✅ 强制HTTPS重定向
- ✅ 使用安全的TLS版本

### 5. 备份安全

- ✅ 定期备份数据库和配置文件
- ✅ 备份文件加密存储
- ✅ 测试备份恢复流程

## 验证配置

运行系统健康检查验证配置：

```bash
cd admin-backend
source venv/bin/activate
python3 ../scripts/server/system_health_check.py
```

检查项：
- ✅ JWT_SECRET已修改
- ✅ 管理员密码已修改
- ✅ 认证已启用
- ✅ CORS配置正确

## 故障排查

### JWT密钥问题

**症状**: 登录失败，token验证错误

**解决**:
1. 检查 `.env` 文件中的 `JWT_SECRET` 是否正确
2. 确认服务已重启
3. 清除浏览器缓存和Cookie

### 邮件发送失败

**症状**: 邮件通知无法发送

**检查**:
1. SMTP服务器地址和端口是否正确
2. 用户名和密码是否正确（Gmail需要使用应用专用密码）
3. 防火墙是否阻止SMTP端口
4. 查看后端日志: `pm2 logs backend`

### Telegram通知失败

**症状**: Telegram消息未收到

**检查**:
1. Bot Token是否正确
2. Chat ID是否正确
3. Bot是否已启动（发送 `/start` 给bot）
4. 查看后端日志

### Webhook通知失败

**症状**: Webhook请求失败

**检查**:
1. Webhook URL是否正确
2. 目标服务是否可访问
3. 是否需要认证头
4. 查看后端日志

## 定期维护

### 每周

- 运行系统健康检查
- 检查备份状态
- 查看告警日志

### 每月

- 运行性能基准测试
- 检查安全配置
- 更新依赖包（如需要）

### 每季度

- 更换JWT_SECRET
- 更换管理员密码
- 安全审计

---

**最后更新**: 2025-12-09

