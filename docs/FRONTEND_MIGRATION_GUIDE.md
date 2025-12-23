# 前端迁移到代理 API 指南

## 概述

为了加强安全性，我们已经将 AI 聊天功能从直接调用 AI 服务迁移到使用后端代理 API。这样可以避免在前端暴露 API Keys。

## 已完成迁移

### ✅ aizkw20251219 (AI智控王)
- ✅ 创建 `utils/aiProxy.ts` - 代理 API 工具
- ✅ 更新 `contexts/AIChatContext.tsx` - 使用代理 API
- ✅ 移除直接 AI 客户端初始化
- ✅ 添加错误处理和降级机制

## 待迁移项目

### ⏳ hbwy20251220 (红包游戏)
需要执行相同的迁移步骤

### ⏳ tgmini20251220 (TON Mini App)
需要执行相同的迁移步骤

## 迁移步骤

### 1. 创建代理工具文件

在每个项目根目录创建 `utils/aiProxy.ts`:

```typescript
/**
 * AI 代理工具
 * 使用后端代理 API，避免在前端暴露 API Keys
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://aiadmin.usdt2026.cc';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  content: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  suggestions?: string[];
}

export async function sendChatRequest(request: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/ai-proxy/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`AI 代理请求失败: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('AI 代理请求失败:', error);
    throw error;
  }
}
```

### 2. 更新 AIChatContext.tsx

#### 2.1 更新导入

**删除**:
```typescript
import { GoogleGenAI } from "@google/genai";
import OpenAI from "openai";
import { getAIConfig } from '../utils/aiConfig';
```

**添加**:
```typescript
import { sendChatRequest, ChatMessage } from '../utils/aiProxy';
import { detectUserLanguage } from '../utils/aiConfig';
```

#### 2.2 移除 AI 客户端初始化

**删除**:
```typescript
const openaiClientRef = useRef<OpenAI | null>(null);
const geminiClientRef = useRef<GoogleGenAI | null>(null);
const [aiConfigLoaded, setAiConfigLoaded] = useState(false);

useEffect(() => {
  // ... 初始化代码
}, []);
```

#### 2.3 更新 sendMessage 函数

**替换**直接 AI 调用为代理 API 调用:

```typescript
// 构建消息列表
const chatMessages: ChatMessage[] = [
  { role: 'system', content: systemPrompt },
  ...historyMessages,
  { role: 'user', content: text }
];

// 通过代理 API 发送请求
const response = await sendChatRequest({
  messages: chatMessages,
  model: 'gemini-2.5-flash-latest', // 优先使用 Gemini
  temperature: 0.7,
  max_tokens: 1000,
});

// 解析响应
const aiMessage = response.content;
const newSuggestions = response.suggestions || ['/help', '/status', '联系人工支持'];
```

### 3. 更新错误处理

添加降级到模拟模式的错误处理:

```typescript
} catch (error) {
  console.error("AI Error:", error);
  setIsTyping(false);
  
  // 降级到模拟模式
  let rawResponse = FALLBACK_RESPONSES.default;
  // ... 模拟响应逻辑
}
```

### 4. 移除依赖（可选）

如果不再需要直接调用 AI 服务，可以移除以下依赖:

```bash
npm uninstall @google/genai openai
```

**注意**: 如果保留这些依赖作为后备，可以暂时不移除。

## 验证迁移

### 1. 检查编译

```bash
npm run build
```

### 2. 测试功能

1. 打开网站
2. 点击 AI 聊天按钮
3. 发送测试消息
4. 检查是否收到 AI 回复
5. 检查浏览器控制台是否有错误

### 3. 检查网络请求

在浏览器开发者工具中:
1. 打开 Network 标签
2. 发送 AI 消息
3. 应该看到对 `/api/v1/ai-proxy/chat` 的请求
4. 不应该看到对 OpenAI 或 Gemini API 的直接请求

## 优势

### 安全性
- ✅ API Keys 不再暴露给前端
- ✅ 后端统一管理 API Keys
- ✅ 可以添加请求频率限制
- ✅ 可以添加用户认证

### 功能
- ✅ 自动故障转移（Gemini → OpenAI）
- ✅ 使用统计记录
- ✅ 成本计算
- ✅ 错误日志

### 维护
- ✅ 集中管理 AI 配置
- ✅ 更容易更新 API Keys
- ✅ 更容易切换 AI 提供商

## 回退方案

如果代理 API 出现问题，可以临时回退到直接调用:

1. 恢复旧的 `AIChatContext.tsx`
2. 恢复 `getAIConfig` 的使用
3. 重新初始化 AI 客户端

但建议优先修复代理 API 问题。

## 下一步

1. 完成其他两个项目的迁移
2. 测试所有功能
3. 移除不再需要的依赖
4. 更新文档

---

**最后更新**: 2025-12-23

