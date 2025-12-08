# 通知渠道配置指南

本文档提供邮件、Telegram、Webhook通知的详细配置说明。

## 快速配置

使用交互式配置脚本：

```bash
cd admin-backend
source venv/bin/activate
python3 ../scripts/server/configure_notifications.py
```

## 邮件通知配置

### Gmail配置

1. **启用两步验证**
   - 访问 https://myaccount.google.com/security
   - 启用"两步验证"

2. **生成应用专用密码**
   - 访问 https://myaccount.google.com/apppasswords
   - 选择"邮件"和"其他设备"
   - 生成16位应用专用密码

3. **配置.env文件**

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-digit-app-password
EMAIL_FROM=your-email@gmail.com
```

### 其他邮件服务商

#### Outlook/Hotmail

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
EMAIL_FROM=your-email@outlook.com
```

#### QQ邮箱

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your-qq@qq.com
SMTP_PASSWORD=your-authorization-code
EMAIL_FROM=your-qq@qq.com
```

**注意**: QQ邮箱需要使用授权码，不是QQ密码。在QQ邮箱设置中生成授权码。

#### 163邮箱

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.163.com
SMTP_PORT=25
SMTP_USER=your-email@163.com
SMTP_PASSWORD=your-authorization-code
EMAIL_FROM=your-email@163.com
```

### 测试邮件通知

配置完成后，重启服务：

```bash
pm2 restart backend
```

告警触发时会自动发送邮件通知。

## Telegram通知配置

### 步骤1: 创建Telegram Bot

1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按照提示：
   - 输入bot名称（例如: "My Alert Bot"）
   - 输入bot用户名（必须以`bot`结尾，例如: "my_alert_bot"）
4. BotFather会返回bot token，格式类似：
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
5. **保存这个token**，稍后需要用到

### 步骤2: 获取Chat ID

#### 方法1: 使用@userinfobot

1. 在Telegram中搜索 `@userinfobot`
2. 发送任意消息给该bot
3. 它会返回您的Chat ID（数字，例如: `123456789`）

#### 方法2: 使用@getidsbot

1. 在Telegram中搜索 `@getidsbot`
2. 发送 `/start` 命令
3. 它会返回您的Chat ID

#### 方法3: 通过API获取

```bash
# 替换 YOUR_BOT_TOKEN 为您的bot token
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates"
```

发送消息给bot后，在返回的JSON中查找 `"chat":{"id":123456789}`

### 步骤3: 配置

编辑 `.env` 文件：

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

或使用配置脚本：

```bash
python3 ../scripts/server/configure_notifications.py
# 选择选项 2
```

### 步骤4: 启动Bot

1. 在Telegram中找到您的bot（通过用户名搜索）
2. 发送 `/start` 命令启动bot
3. 现在bot可以接收消息了

### 步骤5: 测试

重启服务后，告警触发时会自动发送Telegram消息。

## Webhook通知配置

### Slack Webhook

1. **创建Slack应用**
   - 访问 https://api.slack.com/apps
   - 点击"Create New App"
   - 选择"From scratch"
   - 输入应用名称和工作区

2. **启用Incoming Webhooks**
   - 在应用设置中，找到"Incoming Webhooks"
   - 启用"Incoming Webhooks"
   - 点击"Add New Webhook to Workspace"
   - 选择要接收通知的频道
   - 复制Webhook URL

3. **配置**

```env
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Discord Webhook

1. **创建Webhook**
   - 在Discord服务器设置中，选择"集成" > "Webhooks"
   - 点击"新建Webhook"
   - 复制Webhook URL

2. **配置**

```env
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
```

### 自定义Webhook

如果使用自定义Webhook服务，确保：

1. 服务接受POST请求
2. Content-Type: `application/json`
3. 请求体格式：

```json
{
  "type": "alert",
  "alert_level": "high",
  "alert_name": "告警名称",
  "message": "告警消息",
  "timestamp": "2025-12-09 07:00:00"
}
```

## 告警级别配置

在 `admin-backend/app/config/alert_rules.yaml` 中配置哪些级别的告警发送通知：

```yaml
notifications:
  email:
    enabled: true
    severity_levels: ["critical", "high"]  # 只通知严重和高级别告警
  
  telegram:
    enabled: true
    severity_levels: ["critical"]  # 只通知严重告警
  
  webhook:
    enabled: true
    severity_levels: ["critical", "high", "medium"]  # 通知所有级别
```

## 测试通知

### 方法1: 通过告警管理页面

1. 访问告警管理页面
2. 手动触发测试告警
3. 检查是否收到通知

### 方法2: 通过API

```bash
# 需要认证token
curl -X POST http://localhost:8000/api/v1/group-ai/alert-management/test \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## 故障排查

### 邮件发送失败

**检查清单**:
- [ ] SMTP服务器地址和端口是否正确
- [ ] 用户名和密码是否正确（Gmail需要使用应用专用密码）
- [ ] 防火墙是否阻止SMTP端口（587/25）
- [ ] 查看后端日志: `pm2 logs backend | grep -i email`

**常见错误**:
- `535 Authentication failed`: 用户名或密码错误
- `Connection timeout`: 防火墙阻止或SMTP服务器不可达
- `SSL/TLS error`: 端口配置错误（应使用587而不是465）

### Telegram通知失败

**检查清单**:
- [ ] Bot Token是否正确
- [ ] Chat ID是否正确
- [ ] Bot是否已启动（发送 `/start` 给bot）
- [ ] 网络连接是否正常
- [ ] 查看后端日志: `pm2 logs backend | grep -i telegram`

**常见错误**:
- `401 Unauthorized`: Bot Token错误
- `400 Bad Request: chat not found`: Chat ID错误或bot未启动
- `403 Forbidden`: Bot被禁用或用户阻止了bot

### Webhook通知失败

**检查清单**:
- [ ] Webhook URL是否正确
- [ ] 目标服务是否可访问
- [ ] 是否需要认证头
- [ ] 查看后端日志: `pm2 logs backend | grep -i webhook`

**常见错误**:
- `404 Not Found`: Webhook URL错误
- `401 Unauthorized`: 需要认证（某些服务需要token）
- `Connection timeout`: 目标服务不可达

## 通知格式示例

### 邮件通知

**主题**: `[告警] 系统告警 - 高级别`

**正文**:
```
告警级别: high
告警名称: API响应时间超过阈值
时间: 2025-12-09 07:00:00

消息:
API响应时间超过阈值: /api/v1/group-ai/dashboard 响应时间 1200ms
```

### Telegram通知

```
🔔 API响应时间超过阈值

级别：high
时间：2025-12-09 07:00:00

消息：
API响应时间超过阈值: /api/v1/group-ai/dashboard 响应时间 1200ms
```

### Webhook通知

```json
{
  "type": "alert",
  "alert_level": "high",
  "alert_name": "API响应时间超过阈值",
  "message": "API响应时间超过阈值: /api/v1/group-ai/dashboard 响应时间 1200ms",
  "timestamp": "2025-12-09 07:00:00",
  "data": {
    "endpoint": "/api/v1/group-ai/dashboard",
    "response_time_ms": 1200
  }
}
```

## 最佳实践

1. **多通道冗余**: 配置多个通知渠道，确保重要告警不会遗漏
2. **级别过滤**: 只对重要告警发送通知，避免通知疲劳
3. **定期测试**: 每月测试一次通知功能，确保正常工作
4. **日志监控**: 定期检查通知发送日志，发现并解决问题
5. **安全存储**: 妥善保管Token和密码，不要泄露

---

**最后更新**: 2025-12-09

