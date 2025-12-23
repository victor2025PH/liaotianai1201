# AI 使用监控系统

AI 对话使用统计和监控系统前端，用于监控三个展示网站的 AI 对话使用情况。

## 功能特性

- 📊 **AI 使用统计**: Token 使用量、成本分析、成功率监控
- 🔍 **AI 会话管理**: AI 对话会话查询、统计分析
- 📈 **可视化图表**: AI 使用趋势、提供商分布（Gemini vs OpenAI）
- ⚠️ **错误监控**: AI API 错误日志查看
- 🎨 **现代化 UI**: 基于 Next.js 14 + Tailwind CSS

**注意**: 这是 AI 监控系统，不是三个展示网站的业务管理后台。

## 技术栈

- **框架**: Next.js 14
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **图表**: Recharts
- **HTTP 客户端**: Axios

## 开发

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build

# 生产模式
npm start
```

## 环境变量

创建 `.env.local` 文件：

```env
API_BASE_URL=https://aiadmin.usdt2026.cc
NEXT_PUBLIC_API_BASE_URL=https://aiadmin.usdt2026.cc
```

## 部署

部署到 `https://aiadmin.usdt2026.cc/ai-monitor`

## API 端点

- `/api/v1/ai-monitoring/summary` - 使用摘要
- `/api/v1/ai-monitoring/daily` - 每日统计
- `/api/v1/ai-monitoring/providers` - 提供商统计
- `/api/v1/ai-monitoring/recent-errors` - 最近错误
- `/api/v1/ai-monitoring/session/{session_id}` - 会话统计

