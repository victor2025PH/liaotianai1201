# API 配置一键应用工具

## 📖 简介

这个工具可以一键批量修改所有 API 配置文件，在开发环境和生产环境之间快速切换。

## 🚀 快速开始

### 切换到开发环境 (localhost:8000)
```bash
npm run apply:dev
```

### 切换到生产环境 (jblt.usdt2026.cc)
```bash
npm run apply:prod
```

## 📋 会修改的文件

脚本会自动修改以下 13 个文件：

1. `src/lib/api-client.ts`
2. `src/lib/api/auth.ts`
3. `src/lib/api/notifications.ts`
4. `src/lib/api/users.ts`
5. `src/lib/api/servers.ts`
6. `src/lib/api/permissions.ts`
7. `src/lib/api/roles.ts`
8. `src/lib/api/audit-logs.ts`
9. `src/lib/api/telegram-registration.ts`
10. `src/lib/api/group-ai.ts`
11. `src/lib/api/user-roles.ts`
12. `src/hooks/useAccountsQuery.ts`
13. `src/components/notification-center.tsx`

## ⚙️ 配置说明

### 开发环境配置
- API Base URL: `http://localhost:8000/api/v1`
- API URL: `http://localhost:8000/api/v1/group-ai`
- WebSocket: `ws://localhost:8000/api/v1/notifications/ws`
- 错误提示: "無法連接到後端服務，請檢查服務是否運行（http://localhost:8000）"

### 生产环境配置
- API Base URL: `http://jblt.usdt2026.cc/api/v1`
- API URL: `http://jblt.usdt2026.cc/api/v1/group-ai`
- WebSocket: `ws://jblt.usdt2026.cc/api/v1/notifications/ws`
- 错误提示: "無法連接到後端服務，請檢查網絡連接"

## 🔧 高级用法

### 直接运行脚本
```bash
# 开发环境
node scripts/apply-api-config.js dev

# 生产环境
node scripts/apply-api-config.js prod
```

### 修改配置
如果需要修改配置地址，编辑 `scripts/apply-api-config.js` 文件中的 `configs` 对象。

## ⚠️ 注意事项

1. **环境变量优先级**: 脚本只修改默认值，环境变量 (`NEXT_PUBLIC_API_BASE_URL` 等) 的优先级更高
2. **Git 提交**: 修改后记得提交到 Git
3. **测试**: 切换环境后务必测试 API 连接是否正常

## 📝 示例输出

```
🔄 切换到 开发环境配置...

✅ src/lib/api-client.ts
✅ src/lib/api/auth.ts
✅ src/lib/api/notifications.ts
...

✨ 完成! 修改了 13 个文件，共 15 处更改
```

## 🐛 故障排除

### 脚本无法运行
确保 Node.js 版本 >= 14，并且已安装所有依赖：
```bash
npm install
```

### 文件未修改
检查文件路径是否正确，确保在项目根目录运行脚本。

### 部分文件未修改
可能是文件内容格式不匹配，检查脚本中的正则表达式规则。




















