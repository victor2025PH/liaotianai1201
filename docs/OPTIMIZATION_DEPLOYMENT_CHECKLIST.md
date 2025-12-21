# 优化代码部署检查清单

> **生成时间**: 2025-12-21  
> **状态**: 部分优化已应用，部分待部署

---

## 📊 优化状态总览

### ✅ 已应用的优化

1. **后端心跳优化** ✅
   - 位置: `admin-backend/app/api/workers.py`
   - 状态: **已应用**
   - 优化内容:
     - ✅ Redis 缓存账号信息
     - ✅ 每 3 次心跳同步一次数据库（ACCOUNT_SYNC_INTERVAL = 3）
     - ✅ 后台线程执行数据库同步
   - 验证: 代码中已包含 `_account_sync_counters` 和 `ACCOUNT_SYNC_INTERVAL`

2. **系统监控脚本优化** ✅
   - 位置: `scripts/server/improve-system-stability.sh`
   - 状态: **已应用**（需要验证服务器上的 Crontab）
   - 优化内容: Crontab 频率改为每 10 分钟

### ⚠️ 部分应用的优化

3. **前端轮询优化** ⚠️
   - 状态: **部分应用**
   - 问题: 多个文件仍使用 30 秒间隔，而不是优化后的 10 秒

#### 已优化的文件（10秒）:
- ✅ `saas-demo/src/hooks/useRealtimeMetrics.ts` - 10秒

#### 仍使用 30 秒的文件（需要优化）:
- ⚠️ `saas-demo/src/hooks/useSystemMonitor.ts` - 30秒
- ⚠️ `saas-demo/src/hooks/useMetrics.ts` - 30秒
- ⚠️ `saas-demo/src/hooks/useDashboardData.ts` - 30秒
- ⚠️ `saas-demo/src/components/layout-wrapper.tsx` - 30秒
- ⚠️ `saas-demo/src/app/group-ai/nodes/page.tsx` - 30秒
- ⚠️ `saas-demo/src/app/group-ai/servers/page.tsx` - 30秒
- ⚠️ `saas-demo/src/app/group-ai/groups/page.tsx` - 30秒
- ⚠️ `saas-demo/src/app/group-ai/chat-features/page.tsx` - 30秒
- ⚠️ `saas-demo/src/app/group-ai/group-automation/page.tsx` - 30秒

---

## 🚀 部署步骤

### 步骤 1: 检查当前状态

在服务器上执行：

```bash
cd ~/telegram-ai-system
bash scripts/server/check-optimization-status.sh
```

### 步骤 2: 拉取最新代码

```bash
cd ~/telegram-ai-system

# 检查是否有本地修改
git status

# 如果有本地修改，先保存
git stash

# 拉取最新代码
git pull origin main

# 如果有 stash，恢复修改
git stash pop
```

### 步骤 3: 重新构建前端

```bash
cd ~/telegram-ai-system/saas-demo

# 安装依赖（如果需要）
npm install

# 重新构建
npm run build

# 验证构建产物
ls -la .next/standalone/server.js
```

### 步骤 4: 重启服务

```bash
cd ~/telegram-ai-system

# 重启所有服务
pm2 restart all

# 等待启动
sleep 5

# 检查状态
pm2 list

# 检查日志
pm2 logs backend --lines 20 --nostream
pm2 logs frontend --lines 20 --nostream
```

---

## 📝 需要完成的优化

### 前端轮询优化（如果目标是 10 秒）

以下文件需要从 30 秒改为 10 秒：

1. `saas-demo/src/hooks/useSystemMonitor.ts`
   - 修改: `refetchInterval: 30 * 1000` → `refetchInterval: 10 * 1000`
   - 修改: `staleTime: 30 * 1000` → `staleTime: 10 * 1000`

2. `saas-demo/src/hooks/useMetrics.ts`
   - 修改: `refetchInterval: 30 * 1000` → `refetchInterval: 10 * 1000`

3. `saas-demo/src/hooks/useDashboardData.ts`
   - 修改: `refetchInterval: 30 * 1000` → `refetchInterval: 10 * 1000`
   - 修改: `staleTime: 30 * 1000` → `staleTime: 10 * 1000`

4. `saas-demo/src/components/layout-wrapper.tsx`
   - 修改: `setInterval(checkAuth, 30000)` → `setInterval(checkAuth, 10000)`

5. `saas-demo/src/app/group-ai/nodes/page.tsx`
   - 修改: `setInterval(fetchWorkers, 30000)` → `setInterval(fetchWorkers, 10000)`

6. `saas-demo/src/app/group-ai/servers/page.tsx`
   - 修改: `setInterval(() => fetchServers(false), 30000)` → `setInterval(() => fetchServers(false), 10000)`

7. `saas-demo/src/app/group-ai/groups/page.tsx`
   - 修改: `setInterval(fetchGroups, 30000)` → `setInterval(fetchGroups, 10000)`

8. `saas-demo/src/app/group-ai/chat-features/page.tsx`
   - 修改: `setInterval(fetchNodeStats, 30000)` → `setInterval(fetchNodeStats, 10000)`

9. `saas-demo/src/app/group-ai/group-automation/page.tsx`
   - 修改: `setInterval(fetchWorkers, 30000)` → `setInterval(fetchWorkers, 10000)`

---

## ✅ 验证优化效果

### 1. 检查前端轮询间隔

在浏览器中：
1. 打开开发者工具 (F12)
2. Network 标签
3. 观察 API 请求间隔
4. 应该看到请求间隔约为 **10 秒**（如果已优化）或 **30 秒**（如果未优化）

### 2. 检查后端心跳日志

```bash
# 查看心跳日志（应该很少，因为改为 debug 级别）
pm2 logs backend | grep -i heartbeat | head -5

# 查看账号同步频率（应该每 90 秒左右一次）
pm2 logs backend | grep -i "同步.*賬號" | head -5
```

### 3. 检查 Crontab

```bash
# 查看监控脚本的执行频率
crontab -u ubuntu -l | grep monitor-system

# 应该显示: */10 * * * *
```

### 4. 检查 CPU 使用率

```bash
# 实时监控 CPU
top

# 或查看 CPU 历史
sar -u 1 10
```

---

## 📋 Git 状态

### 本地未推送的提交（12个）

主要包含：
1. 修复 SQLAlchemy metadata 保留字冲突
2. 添加 GROUP_AI_MANAGE 权限
3. 修复 check_permission 装饰器
4. 修复 cached 装饰器
5. 修复前端工作目录和 PM2 配置
6. 添加各种修复脚本

### 推送状态

⚠️ **注意**: 由于 GitHub Push Protection（API 密钥问题），代码可能无法直接推送。

**解决方案**:
1. 从历史提交中移除敏感信息，或
2. 使用 GitHub 提供的链接允许该密钥

---

## 🎯 总结

### 已完成的优化
- ✅ 后端心跳优化（已应用）
- ✅ 系统监控脚本优化（已应用）

### 待完成的优化
- ⚠️ 前端轮询优化（部分文件仍为 30 秒）

### 部署状态
- ⚠️ 本地有 12 个未推送的提交
- ✅ 服务正常运行（后端和前端都是 online）

### 下一步行动
1. 完成前端轮询优化（将 30 秒改为 10 秒）
2. 解决 GitHub Push Protection 问题
3. 推送所有代码到 GitHub
4. 在服务器上拉取最新代码
5. 重新构建前端
6. 重启服务
7. 验证优化效果
