# Telegram注册系统使用说明

## 功能概述

Telegram注册系统是一个完整的网页注册系统，支持用户通过手机号码注册Telegram API，实现OTP验证、Session文件管理、防风控机制和服务器选择等功能。

## 已实现功能

### 后端功能

1. **数据库模型**
   - `UserRegistration` - 用户注册记录
   - `SessionFile` - Session文件记录
   - `AntiDetectionLog` - 风控日志

2. **核心服务**
   - `TelegramRegistrationService` - 注册服务
   - `AntiDetectionService` - 风控服务
   - `RateLimiterService` - 速率限制服务

3. **API接口**
   - `POST /api/v1/telegram-registration/start` - 开始注册
   - `POST /api/v1/telegram-registration/verify` - 验证OTP
   - `GET /api/v1/telegram-registration/status/{registration_id}` - 查询状态
   - `POST /api/v1/telegram-registration/cancel` - 取消注册

### 前端功能

1. **注册页面** (`TelegramRegister.tsx`)
   - 手机号输入与验证
   - 服务器选择
   - OTP验证码输入
   - 倒计时显示
   - 风险评分显示
   - 两步验证支持

2. **集成位置**
   - 账户中心 → Telegram注册标签页

## 使用步骤

### 1. 数据库迁移

首先需要运行数据库迁移创建新表：

```bash
cd admin-backend
alembic upgrade head
```

或者手动执行SQL（参考 `alembic/versions/xxxx_add_telegram_registration_tables.py`）

### 2. 启动服务

```bash
# 启动后端
cd admin-backend
uvicorn app.main:app --reload

# 启动前端
cd admin-frontend
npm run dev
```

### 3. 使用注册功能

1. 登录系统
2. 进入"账户中心"
3. 点击"Telegram注册"标签页
4. 填写信息：
   - 手机号（含国家代码，如 +1234567890）
   - 选择国家代码
   - 选择服务器节点
   - （可选）API ID/Hash
   - （可选）代理配置
5. 点击"开始注册"
6. 输入收到的验证码
7. 如需要，输入两步验证密码
8. 完成注册

## 配置说明

### 服务器配置

服务器配置在 `data/master_config.json` 中：

```json
{
  "servers": {
    "worker-01": {
      "host": "165.154.254.99",
      "user": "ubuntu",
      "password": "password",
      "node_id": "worker-01"
    }
  }
}
```

### 速率限制配置

在 `app/services/rate_limiter_service.py` 中配置：

```python
RATE_LIMITS = {
    'per_phone_per_hour': 3,      # 每个手机号每小时最多3次
    'per_phone_per_day': 10,       # 每个手机号每天最多10次
    'per_ip_per_hour': 5,          # 每个IP每小时最多5次
    'per_ip_per_day': 20,          # 每个IP每天最多20次
    'per_device_per_day': 15,      # 每个设备每天最多15次
    'global_per_minute': 30,       # 全局每分钟最多30次
}
```

### 风险评分阈值

在 `app/services/anti_detection_service.py` 中配置：

- 0-25: 低风险
- 26-50: 中风险
- 51-75: 高风险
- 76-100: 极高风险（自动阻止）

## 注意事项

1. **服务器要求**
   - 服务器需要安装 `paramiko` 库（用于SSH连接）
   - 服务器需要安装 `pyrogram` 库
   - 确保服务器有写入 `sessions` 目录的权限

2. **安全建议**
   - 生产环境应使用SSH密钥认证而非密码
   - 建议启用Session文件加密
   - 定期检查风控日志

3. **性能优化**
   - 使用Redis缓存服务器状态
   - 异步处理注册任务
   - 合理设置速率限制

## 故障排查

### 常见问题

1. **"paramiko未安装"**
   ```bash
   pip install paramiko
   ```

2. **"服务器连接失败"**
   - 检查服务器配置
   - 检查网络连接
   - 检查SSH服务是否运行

3. **"验证码发送失败"**
   - 检查手机号格式
   - 检查API凭证
   - 检查是否触发速率限制

4. **"风险评分过高"**
   - 等待一段时间后重试
   - 使用代理服务器
   - 检查注册历史

## 后续开发计划

1. Session文件下载功能
2. Session文件验证功能
3. 注册历史查询
4. 批量注册功能
5. 更完善的风控规则
6. WebSocket实时状态推送

## API文档

完整的API文档可通过访问 `/docs` 端点查看（Swagger UI）。

