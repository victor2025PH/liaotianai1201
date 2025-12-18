# 后端环境变量配置指南

本文档说明如何配置服务器上的 `.env` 文件，以确保后端服务正常运行。

## 配置文件位置

```bash
/home/ubuntu/telegram-ai-system/admin-backend/.env
```

## 编辑配置文件

### 方法一：使用 nano 编辑器（推荐新手）

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
sudo nano .env
```

**nano 编辑器快捷键：**
- `Ctrl + O` - 保存文件
- `Ctrl + X` - 退出编辑器
- `Ctrl + W` - 搜索

### 方法二：使用 vim 编辑器

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
sudo vim .env
```

**vim 编辑器快捷键：**
- 按 `i` 进入编辑模式
- 编辑完成后，按 `Esc` 退出编辑模式
- 输入 `:wq` 保存并退出
- 输入 `:q!` 不保存退出

### 方法三：直接使用命令修改（适合简单配置）

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend

# 添加或修改 OPENAI_API_KEY
sed -i 's/^OPENAI_API_KEY=.*/OPENAI_API_KEY=your-actual-api-key-here/' .env

# 如果不存在该行，添加它
grep -q "^OPENAI_API_KEY=" .env || echo "OPENAI_API_KEY=your-actual-api-key-here" >> .env
```

## 必需配置项

### 🔴 核心安全配置（生产环境必须修改）

#### 1. JWT_SECRET
```bash
JWT_SECRET=your-strong-random-secret-key-here
```
- **说明**：用于签名和验证 JWT Token
- **要求**：至少 32 字符的强随机值
- **生成方法**：
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(64))"
  ```

#### 2. ADMIN_DEFAULT_PASSWORD
```bash
ADMIN_DEFAULT_PASSWORD=your-strong-password-here
```
- **说明**：管理员默认密码（首次登录后应立即修改）
- **要求**：至少 12 字符的强密码

#### 3. CORS_ORIGINS
```bash
CORS_ORIGINS=https://aikz.usdt2026.cc,https://www.aikz.usdt2026.cc
```
- **说明**：允许的前端应用地址（逗号分隔）
- **注意**：生产环境必须配置实际域名，不能使用 localhost

### ⚙️ 可选但重要的配置

#### 4. OPENAI_API_KEY
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```
- **说明**：OpenAI API 密钥（如果使用 AI 功能）
- **获取方式**：访问 [OpenAI Platform](https://platform.openai.com/api-keys) 创建 API Key

#### 5. REDIS_URL
```bash
REDIS_URL=redis://localhost:6379/0
```
- **说明**：Redis 连接 URL（用于缓存和会话存储）
- **默认值**：`redis://localhost:6379/0`
- **注意**：如果 Redis 安装在不同服务器或使用密码，需要修改此值

#### 6. DATABASE_URL
```bash
# SQLite (开发环境)
DATABASE_URL=sqlite:///./admin.db

# PostgreSQL (生产环境推荐)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 📧 其他可选配置

#### Telegram API 配置（如果使用 Telegram 功能）
```bash
TELEGRAM_API_ID=your-telegram-api-id
TELEGRAM_API_HASH=your-telegram-api-hash
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

#### 邮件通知配置（可选）
```bash
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
```

## 配置完成后重启服务

修改 `.env` 文件后，需要重启后端服务以应用更改：

```bash
sudo -u ubuntu pm2 restart backend
sudo -u ubuntu pm2 save
```

验证服务是否正常：

```bash
# 查看服务状态
sudo -u ubuntu pm2 list

# 查看日志
sudo -u ubuntu pm2 logs backend --lines 50
```

## 快速配置示例

如果你只想快速配置必需项，可以执行以下命令：

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend

# 1. 生成 JWT_SECRET
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# 2. 更新 .env 文件
sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
sed -i "s/^CORS_ORIGINS=.*/CORS_ORIGINS=https:\/\/aikz.usdt2026.cc/" .env

# 3. 添加 OPENAI_API_KEY（需要手动替换为实际值）
grep -q "^OPENAI_API_KEY=" .env || echo "OPENAI_API_KEY=your-actual-api-key-here" >> .env

# 4. 重启服务
sudo -u ubuntu pm2 restart backend
sudo -u ubuntu pm2 save
```

## 验证配置

执行以下命令验证配置是否正确：

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend

# 检查配置文件是否存在
test -f .env && echo "✅ .env 文件存在" || echo "❌ .env 文件不存在"

# 检查关键配置项（隐藏敏感信息）
echo "配置项检查："
grep -E "^(JWT_SECRET|CORS_ORIGINS|OPENAI_API_KEY|REDIS_URL|DATABASE_URL)=" .env | sed 's/=.*/=***/' || echo "⚠️  某些配置项未设置"
```

## 注意事项

1. **不要将 `.env` 文件提交到 Git**：`.env` 文件包含敏感信息，应添加到 `.gitignore`
2. **定期轮换密钥**：生产环境应定期更换 JWT_SECRET 和其他敏感配置
3. **使用强密码**：所有密码和密钥都应使用强随机值
4. **备份配置**：修改前建议备份 `.env` 文件
