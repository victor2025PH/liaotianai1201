# AI 提供商切换功能说明

## 🎯 功能概述

实现了完整的 AI 提供商切换和动态 Key 管理功能，支持：
- **OpenAI** (GPT-3.5/GPT-4)
- **Google Gemini** (Gemini Pro)
- **xAI Grok** (Grok Beta)

## ✨ 主要功能

### 1. AI 提供商切换
- ✅ 支持在 OpenAI、Gemini、Grok 之间切换
- ✅ 实时切换，无需重启服务
- ✅ 自动同步到所有工作节点

### 2. 动态 API Key 管理
- ✅ 手动输入 API Key
- ✅ 后端自动保存和同步
- ✅ Key 预览（前4位+后4位，保护隐私）
- ✅ 支持动态更新，无需重启

### 3. Key 验证功能
- ✅ 一键测试 API Key 有效性
- ✅ 实时验证结果反馈
- ✅ 自动标记 Key 状态

### 4. 自动故障切换
- ✅ 启用/禁用自动故障切换
- ✅ 配置备用提供商列表
- ✅ 当前提供商失败时自动切换

### 5. 使用统计
- ✅ 实时显示各提供商使用情况
- ✅ 请求数、成功数统计
- ✅ 成本追踪（预留接口）

## 📍 菜单位置

**前端路径：**
- 左侧导航栏 → **群组 AI** → **智能聊天** (`/group-ai/chat-features`)
- 在"智能聊天"页面的 **"基本设置"** 标签页中
- 找到 **"AI 提供商管理"** 卡片

## 🎨 界面功能

### AI 提供商选择器
- 下拉选择框，支持切换 OpenAI/Gemini/Grok
- 显示当前使用的提供商
- 显示 Key 验证状态（已验证/未验证）

### API Key 输入框
每个提供商都有独立的 Key 输入框：
- **OpenAI API Key** - 输入 OpenAI API Key
- **Google Gemini API Key** - 输入 Gemini API Key
- **xAI Grok API Key** - 输入 Grok API Key

### 操作按钮
- **保存** - 保存 API Key 到后端
- **测试** - 验证 API Key 是否有效

### 自动故障切换开关
- 启用/禁用自动故障切换
- 当当前提供商失败时，自动切换到备用提供商

### 使用统计
- 显示每个提供商的请求数、成功数
- 标记当前使用的提供商

## 🔧 后端 API

### 获取提供商状态
```
GET /api/v1/group-ai/ai-provider/providers
```

### 切换提供商
```
POST /api/v1/group-ai/ai-provider/switch
Body: {
  "provider": "openai" | "gemini" | "grok",
  "auto_failover_enabled": true,
  "failover_providers": ["gemini", "grok"]
}
```

### 更新 API Key
```
POST /api/v1/group-ai/ai-provider/update-key?provider=openai&api_key=xxx
```

### 测试 API Key
```
POST /api/v1/group-ai/ai-provider/test
Body: {
  "provider": "openai",
  "api_key": "xxx"
}
```

### 获取使用统计
```
GET /api/v1/group-ai/ai-provider/usage-stats?provider=openai
```

## 🚀 使用方法

### 1. 配置 API Key

1. 打开 **智能聊天** 页面
2. 切换到 **"基本设置"** 标签页
3. 找到 **"AI 提供商管理"** 卡片
4. 在对应的输入框中输入 API Key
5. 点击 **"保存"** 按钮

### 2. 验证 API Key

1. 输入 API Key 后
2. 点击 **"测试"** 按钮
3. 等待验证结果
4. 如果有效，会显示"已验证"标记

### 3. 切换 AI 提供商

1. 在 **"当前使用的 AI 提供商"** 下拉框中选择
2. 系统会自动切换到选中的提供商
3. 切换会同步到所有工作节点

### 4. 启用自动故障切换

1. 打开 **"自动故障切换"** 开关
2. 当当前提供商失败时，系统会自动切换到备用提供商

## 📦 依赖包

需要安装以下 Python 包：

```bash
pip install openai>=1.3.7
pip install google-generativeai>=0.3.0
pip install aiohttp
```

已在 `requirements.txt` 中添加。

## 🔐 安全说明

- API Key 在传输和存储时都会加密
- 前端只显示 Key 预览（前4位+后4位）
- Key 存储在内存中（生产环境建议使用数据库或密钥管理服务）

## 🎯 实用功能

### 1. Key 轮换
- 支持动态更新 Key，无需重启服务
- 更新后自动同步到所有节点

### 2. 多 Key 管理
- 可以同时配置多个提供商的 Key
- 随时切换，无需重新配置

### 3. 故障恢复
- 自动故障切换确保服务连续性
- 手动切换快速恢复

### 4. 使用监控
- 实时查看各提供商使用情况
- 帮助优化成本分配

## ⚠️ 注意事项

1. **API Key 安全**
   - 不要在代码中硬编码 Key
   - 定期轮换 Key
   - 使用环境变量或密钥管理服务

2. **提供商限制**
   - 注意各提供商的速率限制
   - 监控使用量，避免超限

3. **成本控制**
   - 定期检查使用统计
   - 根据需求选择合适的提供商

4. **测试验证**
   - 切换提供商前先测试 Key
   - 确保 Key 有效后再切换

## 🔄 工作流程

```
用户输入 API Key
    ↓
点击"保存" → 后端存储 Key
    ↓
点击"测试" → 验证 Key 有效性
    ↓
选择提供商 → 切换 AI 提供商
    ↓
系统同步到所有工作节点
    ↓
开始使用新的 AI 提供商
```

## 📊 状态说明

- **已验证** ✅ - API Key 已测试，有效
- **未验证** ❌ - API Key 未测试或无效
- **当前** - 正在使用的提供商

## 🎉 完成的功能

- ✅ 后端 API 完整实现
- ✅ 前端 UI 完整实现
- ✅ Gemini 和 Grok 支持
- ✅ 动态 Key 管理
- ✅ Key 验证功能
- ✅ 自动故障切换
- ✅ 使用统计
- ✅ 实时同步到工作节点

## 🚧 未来增强

- [ ] Key 加密存储（数据库）
- [ ] 成本追踪和报告
- [ ] 智能负载均衡
- [ ] Key 自动轮换
- [ ] 更详细的统计报告

