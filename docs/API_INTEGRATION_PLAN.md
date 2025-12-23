# 三个展示网站 API 对接方案

## 📋 当前问题分析

### 1. AI KEY 优先级问题
- **当前逻辑**: OpenAI → Gemini → 模拟模式
- **需求**: 只使用 OpenAI，移除 Gemini 依赖
- **影响文件**: 
  - `aizkw20251219/contexts/AIChatContext.tsx`
  - `hbwy20251220/contexts/AIChatContext.tsx`
  - `tgmini20251220/contexts/AIChatContext.tsx`
  - `aizkw20251219/utils/aiConfig.ts`
  - `hbwy20251220/utils/aiConfig.ts`
  - `tgmini20251220/utils/aiConfig.ts`

### 2. 后端 API 地址问题
- **当前配置**: `https://admin.usdt2026.cc`（可能不正确）
- **需要确认**: 
  - 后端实际部署地址（IP 或域名）
  - 端口号（默认 8000）
  - 是否需要通过 Nginx 反向代理

### 3. 项目架构分析
- **aizkw20251219**: 智控王产品展示（无后台管理）
- **hbwy20251220**: 红包游戏展示（无后台管理）
- **tgmini20251220**: TON Mini App 展示（无后台管理）
- **admin-backend**: 统一后端服务（为 saas-demo 提供 API）

## 🎯 解决方案

### 方案 A: 使用现有 admin-backend（推荐）

**优点**:
- 复用现有后端基础设施
- 统一管理 AI Keys
- 无需额外部署

**架构**:
```
┌─────────────────────────────────────────┐
│  展示网站 (aizkw/hongbao/tgmini)         │
│  └─ 请求: /api/v1/frontend-config/ai-keys│
└─────────────────────────────────────────┘
              ↓ HTTP/HTTPS
┌─────────────────────────────────────────┐
│  admin-backend (FastAPI)                │
│  └─ 端口: 8000                          │
│  └─ 域名: [待确认]                      │
└─────────────────────────────────────────┘
```

**需要配置**:
1. 确认后端实际地址（IP 或域名）
2. 配置 CORS 允许三个前端域名
3. 确保 `.env` 中有 `OPENAI_API_KEY`

### 方案 B: 为三个网站创建独立后端（可选）

**适用场景**:
- 需要独立的后台管理功能
- 需要独立的数据库
- 需要独立的业务逻辑

**架构**:
```
┌─────────────────────────────────────────┐
│  展示网站 + 独立后台                     │
│  ├─ aizkw-backend (可选)                │
│  ├─ hongbao-backend (可选)              │
│  └─ tgmini-backend (可选)              │
└─────────────────────────────────────────┘
```

**缺点**:
- 需要额外部署和维护
- 增加服务器资源消耗
- 代码重复

## 📝 详细修改方案

### 第一步: 移除 Gemini 依赖

#### 1.1 修改 `utils/aiConfig.ts`（三个项目）

**当前代码**:
```typescript
let cachedConfig: {
  openai_api_key: string;
  gemini_api_key: string;  // ❌ 需要移除
  default_language: string;
  ai_model: string;
} | null = null;
```

**修改为**:
```typescript
let cachedConfig: {
  openai_api_key: string;
  default_language: string;
  ai_model: string;
} | null = null;
```

**移除**:
- `gemini_api_key` 字段
- 环境变量回退中的 `VITE_GEMINI_API_KEY`

#### 1.2 修改 `contexts/AIChatContext.tsx`（三个项目）

**需要修改的地方**:

1. **移除 Gemini 客户端引用**:
```typescript
// ❌ 删除
const geminiClientRef = useRef<GoogleGenAI | null>(null);

// ❌ 删除
if (config.gemini_api_key) {
  geminiClientRef.current = new GoogleGenAI({ apiKey: config.gemini_api_key });
}
```

2. **修改 AI 客户端选择逻辑**:
```typescript
// ❌ 当前代码
const aiClient = openaiClientRef.current || geminiClientRef.current;

// ✅ 修改为
const aiClient = openaiClientRef.current;
```

3. **修改 sendMessage 函数中的调用逻辑**:
```typescript
// ❌ 删除 Gemini 分支
if (useOpenAI && openaiClientRef.current) {
  // OpenAI 调用
} else if (geminiClientRef.current) {
  // ❌ 删除这个分支
}

// ✅ 修改为
if (openaiClientRef.current) {
  // OpenAI 调用
} else {
  // 如果没有 OpenAI，使用模拟模式
  throw new Error("OpenAI API Key not available");
}
```

4. **移除 GoogleGenAI 导入**:
```typescript
// ❌ 删除
import { GoogleGenAI } from "@google/genai";
```

#### 1.3 修改 `package.json`（三个项目，可选）

如果不再使用 Gemini，可以移除依赖：
```json
// ❌ 可以移除（如果确定不再使用）
"@google/genai": "^1.34.0"
```

### 第二步: 配置后端 API 地址

#### 2.1 确认后端实际地址

**需要您提供的信息**:
1. 后端服务器的 IP 地址或域名
2. 端口号（默认 8000）
3. 是否使用 HTTPS
4. 是否通过 Nginx 反向代理

**可能的配置选项**:
- `http://[IP地址]:8000`（直接访问）
- `https://admin.usdt2026.cc`（域名访问）
- `https://api.usdt2026.cc`（API 专用域名）

#### 2.2 修改 `utils/aiConfig.ts`（三个项目）

**当前代码**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://admin.usdt2026.cc';
```

**修改为**（根据实际后端地址）:
```typescript
// 方案 1: 使用 IP 地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://[您的IP地址]:8000';

// 方案 2: 使用域名
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://admin.usdt2026.cc';

// 方案 3: 使用 API 专用域名
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.usdt2026.cc';
```

#### 2.3 环境变量配置（构建时）

在构建前端时，可以通过环境变量覆盖默认地址：

```bash
# 在构建前设置
export VITE_API_BASE_URL=http://[您的IP地址]:8000
npm run build
```

或在 `.env` 文件中：
```bash
# aizkw20251219/.env
VITE_API_BASE_URL=http://[您的IP地址]:8000
VITE_OPENAI_API_KEY=sk-xxx  # 后备方案（如果后端 API 失败）
```

### 第三步: 后端 CORS 配置

#### 3.1 确认 CORS 配置

**文件**: `admin-backend/app/core/config.py`

**当前配置**:
```python
cors_origins: str = "http://localhost:3000,...,https://aizkw.usdt2026.cc,https://hongbao.usdt2026.cc,https://tgmini.usdt2026.cc,https://aikz.usdt2026.cc"
```

**需要确认**:
- ✅ 已包含三个前端域名
- ⚠️ 如果使用 IP 地址访问，需要添加 IP 地址到 CORS

#### 3.2 后端环境变量配置

**文件**: `admin-backend/.env`

**必需配置**:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**可选配置**:
```env
# 如果使用 IP 地址，需要添加到 CORS
CORS_ORIGINS=http://localhost:3000,https://aizkw.usdt2026.cc,https://hongbao.usdt2026.cc,https://tgmini.usdt2026.cc,http://[前端IP地址]
```

### 第四步: 错误处理优化

#### 4.1 改进 API 请求错误处理

**当前问题**: 如果后端 API 失败，前端会回退到环境变量，但可能环境变量也未设置

**改进方案**:
```typescript
export async function getAIConfig(): Promise<{
  openai_api_key: string;
  default_language: string;
  ai_model: string;
}> {
  // ... 现有代码 ...
  
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
      
      // ✅ 验证 openai_api_key 是否存在
      if (!config.openai_api_key) {
        console.warn('后端返回的 openai_api_key 为空，尝试使用环境变量');
        throw new Error('OpenAI API Key not found in backend response');
      }
      
      cachedConfig = config;
      return config;
    } catch (error) {
      console.error('获取 AI 配置失败:', error);
      
      // ✅ 后备方案：使用环境变量
      const envKey = import.meta.env.VITE_OPENAI_API_KEY;
      if (envKey) {
        console.warn('使用环境变量中的 OPENAI_API_KEY');
        return {
          openai_api_key: envKey,
          default_language: 'zh-CN',
          ai_model: 'gpt-4o-mini',
        };
      }
      
      // ❌ 如果都没有，返回空配置（会触发模拟模式）
      console.error('无法获取 OpenAI API Key，将使用模拟模式');
      return {
        openai_api_key: '',
        default_language: 'zh-CN',
        ai_model: 'gpt-4o-mini',
      };
    }
  })();

  return configPromise;
}
```

## 🔧 实施步骤

### 阶段 1: 准备工作

1. **确认后端地址**
   - [ ] 获取后端服务器 IP 地址或域名
   - [ ] 确认端口号
   - [ ] 测试后端 API 可访问性

2. **验证后端配置**
   - [ ] 检查 `admin-backend/.env` 中是否有 `OPENAI_API_KEY`
   - [ ] 测试 API 端点: `curl http://[后端地址]/api/v1/frontend-config/ai-keys`
   - [ ] 确认 CORS 配置包含前端域名

### 阶段 2: 代码修改

1. **移除 Gemini 依赖**（三个项目）
   - [ ] 修改 `utils/aiConfig.ts`，移除 `gemini_api_key`
   - [ ] 修改 `contexts/AIChatContext.tsx`，移除 Gemini 相关代码
   - [ ] 移除 `@google/genai` 导入
   - [ ] 更新 AI 客户端选择逻辑

2. **更新 API 地址**（三个项目）
   - [ ] 修改 `utils/aiConfig.ts` 中的默认 `API_BASE_URL`
   - [ ] 根据实际后端地址设置

3. **优化错误处理**（三个项目）
   - [ ] 改进 `getAIConfig` 函数的错误处理
   - [ ] 添加更详细的日志输出

### 阶段 3: 测试验证

1. **本地测试**
   - [ ] 在本地启动后端服务
   - [ ] 测试前端能否正确获取 API Keys
   - [ ] 测试 AI 聊天功能

2. **生产环境测试**
   - [ ] 部署修改后的代码
   - [ ] 验证三个网站都能正常使用 AI 功能
   - [ ] 检查浏览器 Console 是否有错误

## 📊 修改文件清单

### aizkw20251219
- [ ] `utils/aiConfig.ts` - 移除 Gemini，更新 API 地址
- [ ] `contexts/AIChatContext.tsx` - 移除 Gemini 客户端，只使用 OpenAI
- [ ] `package.json` - 可选：移除 `@google/genai` 依赖

### hbwy20251220
- [ ] `utils/aiConfig.ts` - 移除 Gemini，更新 API 地址
- [ ] `contexts/AIChatContext.tsx` - 移除 Gemini 客户端，只使用 OpenAI
- [ ] `package.json` - 可选：移除 `@google/genai` 依赖

### tgmini20251220
- [ ] `utils/aiConfig.ts` - 移除 Gemini，更新 API 地址
- [ ] `contexts/AIChatContext.tsx` - 移除 Gemini 客户端，只使用 OpenAI
- [ ] `package.json` - 可选：移除 `@google/genai` 依赖

### admin-backend（如果需要）
- [ ] `app/core/config.py` - 确认 CORS 配置
- [ ] `.env` - 确认 `OPENAI_API_KEY` 已设置

## ❓ 需要您确认的问题

1. **后端实际地址是什么？**
   - IP 地址: `http://[IP]:8000`？
   - 域名: `https://admin.usdt2026.cc`？
   - 其他: `https://api.usdt2026.cc`？

2. **是否需要为三个网站创建独立的后台管理？**
   - 如果只是展示网站，可能不需要
   - 如果需要数据统计、用户管理等功能，可以考虑

3. **是否使用 HTTPS？**
   - 如果使用 IP 地址，通常只能用 HTTP
   - 如果使用域名，建议使用 HTTPS

4. **环境变量配置方式？**
   - 构建时通过环境变量设置？
   - 还是通过 `.env` 文件？

## 🎯 推荐方案

基于当前架构，**推荐使用方案 A**（使用现有 admin-backend）：

1. **优点**:
   - 无需额外部署
   - 统一管理 AI Keys
   - 代码修改量小

2. **需要做的**:
   - 确认后端实际地址
   - 移除 Gemini 依赖
   - 更新 API 地址配置
   - 确保 CORS 配置正确

3. **如果未来需要独立后台**:
   - 可以基于现有 `admin-backend` 创建新的后端服务
   - 或者扩展现有后端，添加针对三个网站的专用 API

---

**请提供后端实际地址后，我将根据您的选择进行具体修改。**

