# AI KEY 配置说明

## 问题分析

### 问题现象
- `https://aizkw.usdt2026.cc/` 网站提示"若要激活完全量子处理能力，请连接 API_KEY"
- 其他两个网站（hongbao、tgmini）可能也有同样的问题

### 根本原因

1. **后端 API 配置不完整**
   - `frontend_config.py` 中 `gemini_api_key` 被硬编码为空字符串
   - 没有从环境变量读取 `GEMINI_API_KEY`

2. **前端 API 地址错误**
   - 默认使用 `https://api.usdt2026.cc`，但实际后端在 `https://admin.usdt2026.cc:8000`
   - 导致前端无法正确请求后端 API

3. **CORS 配置缺失**
   - 前端域名没有添加到后端 CORS 允许列表

4. **环境变量未设置**
   - 后端 `.env` 文件可能缺少 `OPENAI_API_KEY` 和 `GEMINI_API_KEY`
   - 前端构建时可能没有设置环境变量

## 已修复的问题

### 1. 后端配置修复

**文件**: `admin-backend/app/core/config.py`
- ✅ 添加了 `gemini_api_key` 配置字段
- ✅ 更新了 CORS 配置，添加了所有前端域名

**文件**: `admin-backend/app/api/frontend_config.py`
- ✅ 修复了 `gemini_api_key` 从环境变量读取
- ✅ 添加了兼容性处理，支持从 `os.environ` 直接读取

### 2. 前端配置修复

**文件**: `aizkw20251219/utils/aiConfig.ts`
- ✅ 更新默认 API 地址为 `https://admin.usdt2026.cc`

**文件**: `hbwy20251220/utils/aiConfig.ts`
- ✅ 更新默认 API 地址为 `https://admin.usdt2026.cc`

**文件**: `tgmini20251220/utils/aiConfig.ts`
- ✅ 更新默认 API 地址为 `https://admin.usdt2026.cc`

## 配置步骤

### 步骤 1: 配置后端环境变量

在服务器上，编辑 `admin-backend/.env` 文件（或创建它）：

```bash
# OpenAI API Key（必需）
OPENAI_API_KEY=sk-your-openai-api-key-here

# Gemini API Key（可选，如果使用 Gemini 作为后备）
GEMINI_API_KEY=your-gemini-api-key-here

# OpenAI 模型（可选，默认 gpt-4o-mini）
OPENAI_MODEL=gpt-4o-mini
```

### 步骤 2: 配置前端环境变量（可选）

如果后端 API 无法访问，前端会回退到使用环境变量。

在构建前端时，可以设置以下环境变量：

```bash
# 在构建前设置
export VITE_API_BASE_URL=https://admin.usdt2026.cc
export VITE_OPENAI_API_KEY=sk-your-openai-api-key-here
export VITE_GEMINI_API_KEY=your-gemini-api-key-here

# 然后构建
npm run build
```

或者在 `.env` 文件中设置（Vite 会自动读取）：

```bash
# aizkw20251219/.env
VITE_API_BASE_URL=https://admin.usdt2026.cc
VITE_OPENAI_API_KEY=sk-your-openai-api-key-here
VITE_GEMINI_API_KEY=your-gemini-api-key-here
```

### 步骤 3: 重启后端服务

```bash
# 如果使用 PM2
pm2 restart backend

# 或者如果使用 systemd
sudo systemctl restart luckyred-api
```

### 步骤 4: 重新构建和部署前端

```bash
# 进入各个前端项目目录
cd aizkw20251219
npm run build

cd ../hbwy20251220
npm run build

cd ../tgmini20251220
npm run build
```

## 验证配置

### 1. 验证后端 API

访问后端 API 端点，应该返回 API Keys：

```bash
curl https://admin.usdt2026.cc/api/v1/frontend-config/ai-keys
```

预期响应：
```json
{
  "openai_api_key": "sk-...",
  "gemini_api_key": "...",
  "default_language": "zh-CN",
  "ai_model": "gpt-4o-mini"
}
```

### 2. 验证前端

1. 打开浏览器开发者工具（F12）
2. 访问 `https://aizkw.usdt2026.cc/`
3. 打开 Network 标签
4. 查看是否有请求到 `/api/v1/frontend-config/ai-keys`
5. 检查 Console 是否有错误信息

### 3. 测试 AI 聊天功能

1. 点击网站上的 AI 聊天按钮
2. 发送一条消息
3. 应该收到 AI 的真实回复，而不是模拟模式的提示

## 故障排查

### 问题 1: 后端 API 返回空字符串

**原因**: 环境变量未设置或未正确读取

**解决**:
1. 检查 `admin-backend/.env` 文件是否存在
2. 确认 `OPENAI_API_KEY` 和 `GEMINI_API_KEY` 已设置
3. 重启后端服务

### 问题 2: CORS 错误

**原因**: 前端域名未添加到 CORS 配置

**解决**:
1. 检查 `admin-backend/app/core/config.py` 中的 `cors_origins`
2. 确保包含所有前端域名
3. 重启后端服务

### 问题 3: 前端仍显示"请连接 API_KEY"

**原因**: 
- 后端 API 请求失败
- 环境变量未设置

**解决**:
1. 检查浏览器 Console 是否有错误
2. 检查 Network 标签，查看 API 请求是否成功
3. 如果 API 请求失败，检查前端环境变量是否设置
4. 重新构建前端项目

### 问题 4: API 地址不正确

**原因**: 后端实际运行在不同的地址或端口

**解决**:
1. 确认后端实际运行的地址（可能是 `https://admin.usdt2026.cc:8000`）
2. 更新前端 `aiConfig.ts` 中的 `API_BASE_URL`
3. 或者设置环境变量 `VITE_API_BASE_URL`

## 安全注意事项

⚠️ **重要**: 前端 API 端点会暴露 API Keys 给浏览器，这意味着：

1. **API Keys 会被暴露**: 任何访问网站的人都可以在浏览器中看到 API Keys
2. **建议使用限制**: 
   - 在 OpenAI/Gemini 控制台设置 API Key 的使用限制
   - 限制 IP 地址
   - 设置使用额度限制
3. **考虑使用代理**: 更好的方案是使用后端代理 API 请求，而不是直接暴露 Keys

## 后续优化建议

1. **使用后端代理**: 创建后端 API 端点代理 OpenAI/Gemini 请求，而不是直接暴露 Keys
2. **添加认证**: 为前端配置 API 添加认证，防止未授权访问
3. **缓存优化**: 优化 API Keys 的缓存策略
4. **错误处理**: 改进错误提示，让用户知道具体问题

---

**文档版本**: v1.0  
**最后更新**: 2025-01-XX  
**维护者**: 开发团队

