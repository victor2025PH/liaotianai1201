# 三个展示网站统一管理后台

aizkw、hongbao、tgmini 三个展示网站的统一管理后台前端。

## 功能特性

- 🏢 **多站点管理**: 管理三个展示网站（aizkw、hongbao、tgmini）
- 📊 **访问统计**: PV/UV 统计、访问趋势分析
- 📈 **用户行为分析**: 热力图、点击热区、转化漏斗
- 📝 **内容管理**: 页面内容编辑、AI 提示词管理、价格方案管理
- 📧 **联系表单管理**: 访客提交的联系表单、潜在客户管理
- 🎨 **现代化 UI**: 基于 Next.js 14 + Tailwind CSS

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

部署到 `https://aiadmin.usdt2026.cc/admin`（端口 3007）

## 与 AI 监控系统的区别

- **sites-admin-frontend** (本系统): 三个展示网站的业务管理后台
  - 站点管理、访问统计、内容管理、联系表单管理
  
- **ai-monitor-frontend**: AI 使用监控系统
  - AI 使用统计、Token 监控、成本分析、会话管理

---

**最后更新**: 2025-12-24

