# 三个展示网站统一后台管理系统方案

## 📊 项目背景

### 当前架构
- **aizkw.usdt2026.cc**: 智控王产品展示（无后台管理）
- **hongbao.usdt2026.cc**: 红包游戏展示（无后台管理）
- **tgmini.usdt2026.cc**: TON Mini App 展示（无后台管理）
- **aiadmin.usdt2026.cc**: 统一后端服务（FastAPI，端口 8000）

### 需求
为三个展示网站创建统一的后台管理系统，提供数据统计、用户管理等功能。

## 🎯 系统架构设计

### 方案 A: 扩展现有 admin-backend（推荐）

**架构图**:
```
┌─────────────────────────────────────────────────────────────┐
│              统一后台管理系统 (Unified Admin)                  │
├─────────────────────────────────────────────────────────────┤
│  URL: https://aiadmin.usdt2026.cc/admin                     │
│  技术栈: Next.js 16 + React 19 + TypeScript                 │
│                                                               │
│  功能模块:                                                    │
│  ├─ 多站点管理 (Multi-Site Management)                      │
│  │  ├─ aizkw 站点数据                                        │
│  │  ├─ hongbao 站点数据                                      │
│  │  └─ tgmini 站点数据                                       │
│  │                                                             │
│  ├─ 数据统计 (Analytics)                                     │
│  │  ├─ 访问统计 (PV/UV)                                      │
│  │  ├─ AI 对话统计                                           │
│  │  ├─ 用户行为分析                                          │
│  │  └─ 转化率分析                                            │
│  │                                                             │
│  ├─ 内容管理 (Content Management)                           │
│  │  ├─ 页面内容编辑                                          │
│  │  ├─ AI 提示词管理                                         │
│  │  └─ 价格方案管理                                          │
│  │                                                             │
│  ├─ 用户管理 (User Management)                             │
│  │  ├─ 访客记录                                              │
│  │  ├─ 联系表单管理                                          │
│  │  └─ 潜在客户管理                                          │
│  │                                                             │
│  └─ 系统配置 (System Configuration)                         │
│     ├─ AI Key 管理                                           │
│     ├─ API 配置                                              │
│     └─ 站点配置                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓ API 调用
┌─────────────────────────────────────────────────────────────┐
│              后端服务 (admin-backend)                        │
├─────────────────────────────────────────────────────────────┤
│  FastAPI (端口 8000)                                         │
│  ├─ 现有 API (为 saas-demo 服务)                             │
│  └─ 新增 API (为三个展示网站服务)                             │
│     ├─ /api/v1/sites/* - 站点管理                            │
│     ├─ /api/v1/analytics/* - 数据统计                        │
│     ├─ /api/v1/content/* - 内容管理                          │
│     └─ /api/v1/contacts/* - 联系表单管理                      │
└─────────────────────────────────────────────────────────────┘
                            ↓ 数据收集
┌─────────────────────────────────────────────────────────────┐
│              展示网站 (Landing Pages)                        │
├─────────────────────────────────────────────────────────────┤
│  aizkw / hongbao / tgmini                                    │
│  └─ 通过埋点收集数据 → 发送到后端                             │
└─────────────────────────────────────────────────────────────┘
```

## 📋 功能模块详细设计

### 1. 多站点管理模块

#### 1.1 站点列表
- **功能**: 显示三个站点的基本信息
- **数据字段**:
  - 站点名称
  - 站点 URL
  - 状态（在线/离线）
  - 最后更新时间
  - 访问统计（今日/本周/本月）

#### 1.2 站点配置
- **功能**: 管理每个站点的配置
- **配置项**:
  - AI 模型选择（Gemini/OpenAI）
  - 默认语言
  - 联系方式
  - 价格方案
  - 自定义样式

### 2. 数据统计模块

#### 2.1 访问统计
- **指标**:
  - PV (Page Views): 页面访问量
  - UV (Unique Visitors): 独立访客数
  - 访问时长
  - 跳出率
  - 访问来源（直接访问/搜索引擎/社交媒体）

#### 2.2 AI 对话统计
- **指标**:
  - 对话总数
  - 平均对话轮数
  - 对话成功率
  - AI 响应时间
  - 常用问题统计
  - Gemini vs OpenAI 使用比例

#### 2.3 用户行为分析
- **功能**:
  - 热力图分析
  - 点击热区
  - 滚动深度
  - 转化漏斗分析

#### 2.4 转化率分析
- **指标**:
  - 访问 → 对话转化率
  - 对话 → 联系转化率
  - 联系 → 成交转化率（如果有）

### 3. 内容管理模块

#### 3.1 页面内容编辑
- **功能**: 可视化编辑页面内容
- **支持内容**:
  - Hero 区域文案
  - 产品介绍
  - 价格方案
  - 客户案例
  - FAQ

#### 3.2 AI 提示词管理
- **功能**: 管理每个站点的 AI 系统提示词
- **功能点**:
  - 编辑提示词模板
  - A/B 测试不同提示词
  - 查看提示词效果

#### 3.3 价格方案管理
- **功能**: 动态管理价格方案
- **功能点**:
  - 添加/编辑/删除价格方案
  - 设置价格
  - 设置功能列表
  - 设置优惠活动

### 4. 用户管理模块

#### 4.1 访客记录
- **功能**: 记录所有访客信息
- **数据字段**:
  - IP 地址
  - 访问时间
  - 访问页面
  - 停留时长
  - 设备信息
  - 地理位置

#### 4.2 联系表单管理
- **功能**: 管理通过网站提交的联系表单
- **数据字段**:
  - 提交时间
  - 联系方式（Telegram/WhatsApp/Email）
  - 咨询内容
  - 来源站点
  - 处理状态

#### 4.3 潜在客户管理
- **功能**: CRM 功能，管理潜在客户
- **功能点**:
  - 客户标签
  - 跟进记录
  - 转化状态
  - 备注信息

### 5. 系统配置模块

#### 5.1 AI Key 管理
- **功能**: 统一管理 AI API Keys
- **功能点**:
  - 设置 OpenAI API Key
  - 设置 Gemini API Key
  - 查看使用量统计
  - 设置使用限制

#### 5.2 API 配置
- **功能**: 管理 API 相关配置
- **配置项**:
  - API 地址
  - 超时设置
  - 重试策略
  - 限流配置

#### 5.3 站点配置
- **功能**: 全局配置管理
- **配置项**:
  - CORS 设置
  - 缓存策略
  - 日志级别
  - 通知设置

## 🗄️ 数据库设计

### 新增数据表

#### 1. sites (站点表)
```sql
CREATE TABLE sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,  -- 站点名称
    url VARCHAR(255) NOT NULL,     -- 站点 URL
    site_type VARCHAR(50),         -- 站点类型: aizkw/hongbao/tgmini
    status VARCHAR(20),            -- 状态: active/inactive
    config JSON,                    -- 站点配置（JSON）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. site_visits (访问记录表)
```sql
CREATE TABLE site_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,      -- 站点 ID
    ip_address VARCHAR(45),         -- IP 地址
    user_agent TEXT,                -- 用户代理
    referer VARCHAR(255),           -- 来源
    page_path VARCHAR(255),         -- 访问页面
    session_id VARCHAR(100),        -- 会话 ID
    visit_duration INTEGER,          -- 访问时长（秒）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id)
);
```

#### 3. ai_conversations (AI 对话记录表)
```sql
CREATE TABLE ai_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,       -- 站点 ID
    session_id VARCHAR(100),        -- 会话 ID
    user_message TEXT,              -- 用户消息
    ai_response TEXT,               -- AI 回复
    ai_provider VARCHAR(20),        -- AI 提供商: gemini/openai
    response_time INTEGER,          -- 响应时间（毫秒）
    tokens_used INTEGER,             -- 使用的 Token 数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id)
);
```

#### 4. contact_forms (联系表单表)
```sql
CREATE TABLE contact_forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,       -- 站点 ID
    contact_type VARCHAR(20),       -- 联系方式: telegram/whatsapp/email
    contact_value VARCHAR(255),     -- 联系值
    message TEXT,                   -- 咨询内容
    status VARCHAR(20),             -- 状态: pending/contacted/converted
    notes TEXT,                     -- 备注
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id)
);
```

#### 5. site_analytics (站点统计表，按日汇总)
```sql
CREATE TABLE site_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,       -- 站点 ID
    date DATE NOT NULL,             -- 日期
    pv INTEGER DEFAULT 0,          -- 页面访问量
    uv INTEGER DEFAULT 0,           -- 独立访客数
    conversations INTEGER DEFAULT 0, -- 对话数
    contacts INTEGER DEFAULT 0,     -- 联系表单数
    avg_session_duration INTEGER,   -- 平均会话时长
    bounce_rate DECIMAL(5,2),       -- 跳出率
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, date),
    FOREIGN KEY (site_id) REFERENCES sites(id)
);
```

## 🔌 API 设计

### 1. 站点管理 API

#### GET /api/v1/sites
获取所有站点列表

**响应**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "智控王",
      "url": "https://aizkw.usdt2026.cc",
      "site_type": "aizkw",
      "status": "active",
      "config": {...},
      "stats": {
        "today_pv": 1234,
        "today_uv": 567,
        "today_conversations": 89
      }
    }
  ],
  "total": 3
}
```

#### GET /api/v1/sites/{site_id}
获取站点详情

#### PUT /api/v1/sites/{site_id}
更新站点配置

#### GET /api/v1/sites/{site_id}/stats
获取站点统计数据

### 2. 数据统计 API

#### GET /api/v1/analytics/overview
获取概览数据

**响应**:
```json
{
  "total_pv": 50000,
  "total_uv": 12000,
  "total_conversations": 1500,
  "total_contacts": 200,
  "conversion_rate": 13.3,
  "sites": [
    {
      "site_id": 1,
      "site_name": "智控王",
      "pv": 20000,
      "uv": 5000,
      "conversations": 600
    }
  ]
}
```

#### GET /api/v1/analytics/visits
获取访问记录

**查询参数**:
- `site_id`: 站点 ID（可选）
- `start_date`: 开始日期
- `end_date`: 结束日期
- `page`: 页码
- `page_size`: 每页数量

#### GET /api/v1/analytics/conversations
获取对话记录

#### GET /api/v1/analytics/conversations/stats
获取对话统计

**响应**:
```json
{
  "total": 1500,
  "by_provider": {
    "gemini": 1200,
    "openai": 300
  },
  "avg_response_time": 1250,
  "avg_tokens": 500,
  "top_questions": [
    {"question": "如何部署流量矩阵？", "count": 50},
    {"question": "价格是多少？", "count": 45}
  ]
}
```

### 3. 内容管理 API

#### GET /api/v1/content/{site_id}
获取站点内容

#### PUT /api/v1/content/{site_id}
更新站点内容

#### GET /api/v1/content/{site_id}/prompts
获取 AI 提示词

#### PUT /api/v1/content/{site_id}/prompts
更新 AI 提示词

### 4. 联系表单 API

#### GET /api/v1/contacts
获取联系表单列表

#### GET /api/v1/contacts/{contact_id}
获取联系表单详情

#### PUT /api/v1/contacts/{contact_id}
更新联系表单状态

#### POST /api/v1/contacts
创建联系表单（前端提交）

### 5. 系统配置 API

#### GET /api/v1/config/ai-keys
获取 AI Keys（已存在）

#### PUT /api/v1/config/ai-keys
更新 AI Keys

#### GET /api/v1/config/sites
获取站点配置

## 🎨 前端界面设计

### 1. 仪表板 (Dashboard)

**布局**:
```
┌─────────────────────────────────────────────────┐
│  顶部导航栏                                      │
├─────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 总访问量  │ │ 总对话数  │ │ 总联系数  │        │
│  │  50,000  │ │  1,500   │ │   200   │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│                                                 │
│  ┌─────────────────────────────────────────┐  │
│  │  访问趋势图 (最近7天)                     │  │
│  │  [Line Chart]                            │  │
│  └─────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────┐ ┌──────────────┐            │
│  │ 站点统计     │ │ 对话统计     │            │
│  │ [Table]      │ │ [Pie Chart]  │            │
│  └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────┘
```

### 2. 站点管理页面

- 站点列表（卡片式或表格）
- 快速操作（查看统计、编辑配置）
- 站点状态监控

### 3. 数据统计页面

- 时间范围选择器
- 多维度数据展示
- 数据导出功能

### 4. 内容管理页面

- 可视化编辑器
- 实时预览
- 版本历史

### 5. 联系表单管理页面

- 表单列表
- 筛选和搜索
- 状态管理
- 导出功能

## 🛠️ 实施计划

### 阶段 1: 数据收集（1-2周）

1. **前端埋点**
   - 在三个展示网站添加数据收集脚本
   - 收集访问数据、对话数据、联系表单

2. **后端 API 开发**
   - 创建数据收集端点
   - 创建数据统计端点
   - 数据库迁移

### 阶段 2: 后台管理前端（2-3周）

1. **基础框架**
   - 创建新的 Next.js 项目或扩展现有 saas-demo
   - 设计 UI 组件库
   - 路由配置

2. **核心功能开发**
   - 仪表板
   - 站点管理
   - 数据统计
   - 内容管理

### 阶段 3: 高级功能（2-3周）

1. **用户管理**
   - 联系表单管理
   - 潜在客户管理

2. **系统配置**
   - AI Key 管理界面
   - 站点配置界面

### 阶段 4: 优化和测试（1-2周）

1. **性能优化**
2. **功能测试**
3. **用户体验优化**

## 📊 技术栈

### 前端
- **框架**: Next.js 16
- **UI 库**: 复用 saas-demo 的组件（shadcn/ui）
- **图表**: Recharts
- **状态管理**: React Query
- **样式**: TailwindCSS

### 后端
- **框架**: FastAPI（扩展现有）
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
- **ORM**: SQLAlchemy
- **迁移**: Alembic

## 🔐 安全考虑

1. **认证授权**
   - JWT Token 认证
   - RBAC 权限控制
   - API 限流

2. **数据安全**
   - 敏感数据加密
   - IP 地址脱敏
   - 访问日志审计

3. **API 安全**
   - CORS 配置
   - 请求验证
   - 错误处理

## 📈 扩展性考虑

1. **多租户支持**
   - 未来可以支持多个客户使用
   - 每个客户管理自己的站点

2. **实时数据**
   - WebSocket 实时更新统计数据
   - 实时通知新联系表单

3. **数据导出**
   - 支持 Excel/CSV 导出
   - 支持 PDF 报告生成

## 🎯 推荐实施路径

### 方案 1: 扩展现有 saas-demo（推荐）

**优点**:
- 复用现有代码和组件
- 统一的技术栈
- 快速开发

**实施**:
- 在 `saas-demo` 中添加新的路由 `/admin/sites`
- 复用现有的 Dashboard 组件
- 添加新的 API 客户端

### 方案 2: 创建独立后台项目

**优点**:
- 代码分离，更清晰
- 独立部署

**缺点**:
- 需要重复开发组件
- 维护成本更高

## 📝 下一步行动

1. **确认方案**: 选择方案 1 或方案 2
2. **数据库设计**: 创建 Alembic 迁移文件
3. **API 开发**: 实现数据收集和统计 API
4. **前端开发**: 开发后台管理界面
5. **测试部署**: 测试和部署到生产环境

---

**文档版本**: v1.0  
**最后更新**: 2025-01-XX  
**维护者**: 开发团队

