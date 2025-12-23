# OpenAI API 配置指南

## 已完成的配置

✅ 已添加 OpenAI SDK 依赖  
✅ 已更新代码以支持 OpenAI（优先使用）  
✅ 已配置环境变量支持  

## 配置步骤

### 1. 安装依赖

```bash
npm install
```

### 2. 配置 API Key

#### 方法 A: 创建 `.env.local` 文件（推荐）

在项目根目录创建 `.env.local` 文件：

```bash
# .env.local
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# 可选：Gemini API Key（作为备用）
GEMINI_API_KEY=your-gemini-api-key-here
```

#### 方法 B: 在服务器上配置环境变量

```bash
# 在服务器上设置环境变量
export OPENAI_API_KEY="sk-proj-your-openai-api-key-here"

# 或者添加到 ~/.bashrc 或 ~/.profile
echo 'export OPENAI_API_KEY="sk-proj-your-openai-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. 重启应用

```bash
# 开发环境
npm run dev

# 生产环境（如果使用 PM2）
pm2 restart <app_name>
# 或
pm2 restart all
```

## 工作原理

### AI 提供商优先级

1. **OpenAI** (优先) - 如果配置了 `OPENAI_API_KEY`，将使用 OpenAI GPT-4o-mini
2. **Gemini** (备用) - 如果没有 OpenAI key，将使用 Gemini API
3. **模拟模式** - 如果都没有配置，将使用本地模拟响应

### 使用的模型

- **OpenAI**: `gpt-4o-mini` (快速且经济)
- **Gemini**: `gemini-2.5-flash-latest` (备用)

## 验证配置

### 检查环境变量

```bash
# 在浏览器控制台或代码中
console.log('OpenAI Key:', process.env.OPENAI_API_KEY ? '已配置' : '未配置');
console.log('Gemini Key:', process.env.GEMINI_API_KEY ? '已配置' : '未配置');
```

### 测试 AI 对话

1. 打开网站
2. 点击 AI 聊天按钮
3. 发送一条消息
4. 检查是否收到 AI 回复

## 服务器部署配置

### 在服务器上创建 `.env.local`

```bash
cd /home/ubuntu/aizkw20251219
nano .env.local
```

添加以下内容：

```
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
```

### 重新构建和部署

```bash
cd /home/ubuntu/aizkw20251219
npm install
npm run build
sudo systemctl reload nginx
```

## 安全提示

⚠️ **重要**: 
- `.env.local` 文件已添加到 `.gitignore`，不会被提交到 Git
- 不要在代码中硬编码 API key
- 定期轮换 API key
- 使用环境变量或密钥管理服务

## 故障排查

### 问题 1: AI 不响应

**检查：**
1. API key 是否正确配置
2. 网络连接是否正常
3. 浏览器控制台是否有错误

**解决：**
```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 检查网络
curl https://api.openai.com/v1/models
```

### 问题 2: 仍然使用 Gemini

**原因：** OpenAI key 未正确加载

**解决：**
1. 确认 `.env.local` 文件在项目根目录
2. 重启开发服务器
3. 检查 `vite.config.ts` 中的环境变量配置

### 问题 3: API 调用失败

**可能原因：**
- API key 无效或过期
- 账户余额不足
- 网络问题

**解决：**
- 检查 OpenAI 账户状态
- 查看浏览器控制台的错误信息
- 尝试使用 Gemini 作为备用

## 更新日志

- ✅ 2025-12-20: 添加 OpenAI 支持
- ✅ 优先级：OpenAI > Gemini > 模拟模式
- ✅ 使用 GPT-4o-mini 模型

