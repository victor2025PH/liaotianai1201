# 统一 AI KEY 配置和语言设置指南

## 概述

已将四个网站的 AI KEY 配置统一为从后端 API 获取，并设置默认语言为中文。

## 已完成的修改

### 1. 后端 API（已完成并提交）

- **文件**: `admin-backend/app/api/frontend_config.py` (新建)
- **端点**: `GET /api/v1/frontend-config/ai-keys`
- **功能**: 从 `admin-backend/.env` 读取 `OPENAI_API_KEY` 并返回给前端

### 2. 前端修改（需要手动应用到子模块）

由于 `aizkw20251219`, `hbwy20251220`, `tgmini20251220` 是 Git 子模块，需要在这些子模块的仓库中提交修改。

## 需要修改的文件

### aizkw20251219

1. **创建文件**: `aizkw20251219/utils/aiConfig.ts`
   - 内容见下方代码

2. **修改文件**: `aizkw20251219/contexts/AIChatContext.tsx`
   - 添加导入: `import { getAIConfig, detectUserLanguage } from '../utils/aiConfig';`
   - 添加 `useRef` 和 `useEffect` 导入
   - 将 AI 客户端改为从后端 API 获取
   - 修改 systemPrompt，加强中文优先逻辑

3. **修改文件**: `aizkw20251219/contexts/LanguageContext.tsx`
   - 确保默认语言为 `'cn'`（中文）

### hbwy20251220

1. **创建文件**: `hbwy20251220/utils/aiConfig.ts`
   - 内容见下方代码

2. **修改文件**: `hbwy20251220/contexts/AIChatContext.tsx`
   - 添加导入和修改逻辑（同 aizkw20251219）

### tgmini20251220

1. **创建文件**: `tgmini20251220/utils/aiConfig.ts`
   - 内容见下方代码

2. **修改文件**: `tgmini20251220/contexts/AIChatContext.tsx`
   - 添加导入和修改逻辑（同 aizkw20251219）

## 代码文件内容

### utils/aiConfig.ts（三个网站通用）

```typescript
/**
 * AI 配置工具
 * 统一从后端 API 获取 AI KEY
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.usdt2026.cc';

let cachedConfig: {
  openai_api_key: string;
  gemini_api_key: string;
  default_language: string;
  ai_model: string;
} | null = null;

let configPromise: Promise<typeof cachedConfig> | null = null;

/**
 * 从后端获取 AI 配置
 */
export async function getAIConfig(): Promise<{
  openai_api_key: string;
  gemini_api_key: string;
  default_language: string;
  ai_model: string;
}> {
  if (cachedConfig) {
    return cachedConfig;
  }

  if (configPromise) {
    return configPromise;
  }

  configPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/frontend-config/ai-keys`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`获取 AI 配置失败: ${response.status}`);
      }

      const config = await response.json();
      cachedConfig = config;
      return config;
    } catch (error) {
      console.error('获取 AI 配置失败:', error);
      return {
        openai_api_key: import.meta.env.VITE_OPENAI_API_KEY || '',
        gemini_api_key: import.meta.env.VITE_GEMINI_API_KEY || '',
        default_language: 'zh-CN',
        ai_model: 'gpt-4o-mini',
      };
    }
  })();

  return configPromise;
}

/**
 * 检测用户输入的语言
 * 如果不是明确的英文或其他语言，返回中文
 */
export function detectUserLanguage(text: string): 'zh-CN' | 'en' {
  const englishChars = (text.match(/[a-zA-Z]/g) || []).length;
  const totalChars = text.length;
  const englishRatio = totalChars > 0 ? englishChars / totalChars : 0;

  if (englishRatio > 0.7 && totalChars > 5) {
    return 'en';
  }

  return 'zh-CN';
}
```

### AIChatContext.tsx 关键修改点

1. **导入修改**:
```typescript
import React, { createContext, useState, useContext, ReactNode, useEffect, useRef } from 'react';
import { getAIConfig, detectUserLanguage } from '../utils/aiConfig';
```

2. **AI 客户端初始化**（替换原有的环境变量方式）:
```typescript
const openaiClientRef = useRef<OpenAI | null>(null);
const geminiClientRef = useRef<GoogleGenAI | null>(null);
const [aiConfigLoaded, setAiConfigLoaded] = useState(false);

useEffect(() => {
  const initAIClients = async () => {
    try {
      const config = await getAIConfig();
      if (config.openai_api_key) {
        openaiClientRef.current = new OpenAI({
          apiKey: config.openai_api_key,
          dangerouslyAllowBrowser: true
        });
      }
      if (config.gemini_api_key) {
        geminiClientRef.current = new GoogleGenAI({ apiKey: config.gemini_api_key });
      }
      setAiConfigLoaded(true);
    } catch (error) {
      console.error('初始化 AI 客户端失败:', error);
      // 后备：使用环境变量
      const envKey = import.meta.env.VITE_OPENAI_API_KEY;
      if (envKey) {
        openaiClientRef.current = new OpenAI({
          apiKey: envKey,
          dangerouslyAllowBrowser: true
        });
      }
      setAiConfigLoaded(true);
    }
  };
  initAIClients();
}, []);

const aiClient = openaiClientRef.current || geminiClientRef.current;
```

3. **systemPrompt 修改**（在 sendMessage 函数中）:
```typescript
// 检测用户输入的语言
const userLang = detectUserLanguage(text);
const shouldUseChinese = userLang === 'zh-CN';

const systemPrompt = `...（原有内容）...

3. 语言规则（重要）：
   - **默认使用中文回复**，无论用户使用什么语言
   - 只有当用户明确使用英文提问（且问题完全是英文）时，才可以使用英文回复
   - 如果用户输入包含中文、日文、韩文等非英文内容，必须使用中文回复
   - 如果无法确定用户语言，优先使用中文
   - 当前用户输入语言检测：${shouldUseChinese ? '中文' : '英文'}，请${shouldUseChinese ? '使用中文' : '可以使用英文'}回复
`;
```

4. **使用 ref 调用 AI 客户端**:
```typescript
if (openaiClientRef.current) {
  const completion = await openaiClientRef.current.chat.completions.create({...});
} else if (geminiClientRef.current) {
  const response = await geminiClientRef.current.models.generateContent({...});
}
```

## 配置后端 .env

确保 `admin-backend/.env` 中包含：

```env
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
```

## 验证

1. 重启后端服务
2. 访问 `https://api.usdt2026.cc/api/v1/frontend-config/ai-keys` 应该返回配置
3. 前端网站应该能从后端获取 AI KEY
4. 测试聊天功能，应该默认使用中文回复
