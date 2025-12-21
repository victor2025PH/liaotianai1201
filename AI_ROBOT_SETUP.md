# AI 机器人集成指南

## 已完成的工作

### 1. 为两个网站创建了 AI 上下文
- ✅ `hbwy20251220/contexts/AIChatContext.tsx` - RedEnvelope.fi 游戏网站专用
- ✅ `tgmini20251220/contexts/AIChatContext.tsx` - TON Mini App Studio 专用

### 2. 更新了依赖配置
- ✅ `hbwy20251220/package.json` - 添加了 `@google/genai` 和 `openai`
- ✅ `tgmini20251220/package.json` - 添加了 `@google/genai` 和 `openai`
- ✅ `hbwy20251220/vite.config.ts` - 添加了 `OPENAI_API_KEY` 环境变量支持
- ✅ `tgmini20251220/vite.config.ts` - 添加了 `OPENAI_API_KEY` 环境变量支持

### 3. 在 App.tsx 中集成了 AI 功能
- ✅ `hbwy20251220/App.tsx` - 添加了 `AIChatProvider`、`AISprite` 和 `AIChatTerminal`
- ✅ `tgmini20251220/App.tsx` - 添加了 `AIChatProvider`、`AISprite` 和 `AIChatTerminal`

## 需要完成的工作

### 1. 复制组件文件

由于文件较大，需要手动复制以下文件：

**从 `aizkw20251219/components/` 复制到 `hbwy20251220/components/`：**
- `AISprite.tsx` (完整版本)
- `AIChatTerminal.tsx` (完整版本)

**从 `aizkw20251219/components/` 复制到 `tgmini20251220/components/`：**
- `AISprite.tsx` (完整版本)
- `AIChatTerminal.tsx` (完整版本)

### 2. 安装依赖

在每个网站目录下运行：

```bash
cd hbwy20251220
npm install

cd ../tgmini20251220
npm install
```

### 3. 配置环境变量

在每个网站目录下创建 `.env.local` 文件：

**hbwy20251220/.env.local:**
```
# 注意：将 YOUR_OPENAI_API_KEY 替换为实际的 OpenAI API Key
# 获取方式：https://platform.openai.com/api-keys
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
GEMINI_API_KEY=your_gemini_key_here
```

**tgmini20251220/.env.local:**
```
# 注意：将 YOUR_OPENAI_API_KEY 替换为实际的 OpenAI API Key
# 获取方式：https://platform.openai.com/api-keys
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
GEMINI_API_KEY=your_gemini_key_here
```

## AI 提示词配置

### RedEnvelope.fi (hbwy20251220)
AI 已配置为游戏顾问，专门介绍：
- 红包游戏机制
- Web3 支付集成
- 病毒式传播策略
- 变现模式

### TON Mini App Studio (tgmini20251220)
AI 已配置为开发顾问，专门介绍：
- Mini App 开发流程
- 技术栈详情
- 服务范围
- 开发周期和成本

## 测试

1. 启动开发服务器：
```bash
cd hbwy20251220
npm run dev

# 或

cd tgmini20251220
npm run dev
```

2. 测试 AI 功能：
- 点击页面右下角的机器人
- 与 AI 对话，测试不同网站的主题回复
- 验证 AI 能根据网站类型给出相应的回答

## 注意事项

- 确保 `.env.local` 文件不被提交到 Git（已在 `.gitignore` 中）
- 如果 OpenAI API 不可用，系统会自动回退到 Gemini API
- 每个网站的 AI 提示词已针对其业务场景进行了优化

