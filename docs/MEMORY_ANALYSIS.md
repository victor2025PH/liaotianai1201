# 内存使用分析

> **问题**: 为什么会出现内存不足？

---

## 🔍 可能的原因

### 1. 服务器本身内存较小

**检查方法**:
```bash
free -h
```

**常见情况**:
- 小型 VPS 通常只有 1-2GB 内存
- 如果运行多个服务（后端、前端、数据库、Nginx），内存可能不足

### 2. PM2 进程占用内存

**检查方法**:
```bash
pm2 list
pm2 describe backend
pm2 describe frontend
```

**可能的问题**:
- Node.js 进程（前端）通常占用 200-500MB
- Python 进程（后端）通常占用 100-300MB
- 如果进程崩溃重启，可能累积内存占用

### 3. 前端构建文件较大

**检查方法**:
```bash
du -sh saas-demo/.next
du -sh saas-demo/node_modules
```

**可能的问题**:
- `.next` 构建目录可能占用 500MB-1GB
- `node_modules` 可能占用 200-500MB
- 如果构建过程中内存不足，可能导致失败

### 4. 数据库和缓存

**检查方法**:
```bash
# SQLite 数据库大小
du -sh admin-backend/data/*.db

# Redis 内存使用（如果使用）
redis-cli info memory 2>/dev/null || echo "Redis 未运行"
```

**可能的问题**:
- SQLite 数据库文件可能较大
- Redis 缓存可能占用内存（如果启用）

### 5. 系统其他进程

**检查方法**:
```bash
ps aux --sort=-%mem | head -n 10
```

**可能的问题**:
- Nginx 进程
- 系统更新进程
- 其他后台服务

---

## 📊 典型内存使用情况

### 正常情况下的内存分配

| 服务/组件 | 典型内存使用 | 说明 |
|---------|------------|------|
| **后端 (Python/FastAPI)** | 100-300MB | uvicorn 进程 |
| **前端 (Next.js)** | 200-500MB | Node.js 进程 |
| **Nginx** | 20-50MB | Web 服务器 |
| **系统基础** | 200-400MB | 操作系统和其他服务 |
| **数据库 (SQLite)** | 10-50MB | 数据库文件（磁盘） |
| **缓存 (Redis)** | 50-200MB | 如果启用 Redis |
| **总计** | **580-1500MB** | 约 0.6-1.5GB |

### 如果服务器只有 1GB 内存

- **正常使用**: 580MB-1GB ✅
- **峰值使用**: 可能超过 1GB ⚠️
- **构建时**: 可能超过 1.5GB ❌

---

## ✅ 解决方案

### 方案 1: 增加 Swap（推荐，最简单）

```bash
# 创建 2GB Swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 验证
free -h
```

**优点**: 
- 简单快速
- 不需要重启
- 可以立即缓解内存压力

**缺点**:
- Swap 使用磁盘，速度较慢
- 但总比进程被杀死好

### 方案 2: 优化 PM2 内存限制

编辑 `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [
    {
      name: "backend",
      // ... 其他配置
      max_memory_restart: "500M",  // 如果超过 500MB 自动重启
    },
    {
      name: "frontend",
      // ... 其他配置
      max_memory_restart: "800M",  // 如果超过 800MB 自动重启
    }
  ]
};
```

### 方案 3: 清理不必要的文件

```bash
# 清理 PM2 日志
pm2 flush

# 清理旧的构建文件（如果需要重新构建）
cd saas-demo
rm -rf .next
npm run build

# 清理系统日志
sudo journalctl --vacuum-time=7d
```

### 方案 4: 升级服务器内存

如果经常内存不足，考虑升级到 2GB 或 4GB 内存的服务器。

---

## 🔍 诊断步骤

### 1. 运行内存检查脚本

```bash
bash scripts/server/check_memory_usage.sh
```

### 2. 检查具体进程

```bash
# 查看所有进程内存使用
ps aux --sort=-%mem | head -n 20

# 查看 PM2 进程详情
pm2 describe backend
pm2 describe frontend
```

### 3. 检查系统资源

```bash
# 系统负载
uptime

# 内存详情
free -h

# 磁盘使用
df -h
```

---

## 📋 内存优化建议

### 1. 后端优化

- ✅ 使用连接池限制数据库连接数
- ✅ 启用缓存减少数据库查询
- ✅ 定期清理日志文件
- ✅ 使用异步处理避免阻塞

### 2. 前端优化

- ✅ 代码分割和懒加载（已完成）
- ✅ 生产环境构建优化
- ✅ 静态资源 CDN（如果可能）
- ✅ 限制并发请求

### 3. 系统优化

- ✅ 增加 Swap 内存
- ✅ 定期清理系统日志
- ✅ 监控内存使用情况
- ✅ 设置进程内存限制

---

## 🎯 立即行动

### 如果内存不足，立即执行：

```bash
# 1. 检查内存使用
bash scripts/server/check_memory_usage.sh

# 2. 如果内存使用率 > 90%，增加 Swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 3. 重启服务（释放内存）
pm2 restart all

# 4. 使用轻量级验证脚本
bash scripts/server/verify_deployment_light.sh
```

---

## 📊 预期结果

### 正常情况

- 总内存: 1-2GB
- 已使用: 600-1200MB
- 可用: 400-800MB
- 使用率: 60-80%

### 需要关注

- 使用率 > 85%: 建议增加 Swap
- 使用率 > 95%: 必须增加 Swap 或优化

---

**最后更新**: 2025-12-09

