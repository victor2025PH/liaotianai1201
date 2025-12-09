# 构建内存不足解决方案

> **问题**: 即使设置了内存限制，`npm run build` 仍然被系统杀死

---

## 🔍 问题分析

### 当前情况
- **总内存**: 1.9GB（非常小）
- **可用内存**: 745MB
- **Swap**: 4GB（已使用 130MB）
- **问题**: 即使设置 1.5GB 限制，构建仍然失败

### 根本原因
1. **服务器内存太小**: 只有 1.9GB，无法满足 Next.js 构建需求
2. **系统进程占用**: 其他进程可能占用内存
3. **构建内存需求**: Next.js 构建通常需要 1-2GB 内存

---

## ✅ 解决方案

### 方案 1: 使用更小的内存限制（推荐先试）

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 使用 1GB 内存限制（更保守）
export NODE_OPTIONS="--max-old-space-size=1024"

# 构建
npm run build
```

如果还是失败，尝试 768MB：

```bash
export NODE_OPTIONS="--max-old-space-size=768"
npm run build
```

### 方案 2: 停止其他服务（临时）

```bash
# 临时停止后端服务（释放内存）
pm2 stop backend

# 构建前端
cd /home/ubuntu/telegram-ai-system/saas-demo
export NODE_OPTIONS="--max-old-space-size=1024"
npm run build

# 构建完成后，重启后端
cd ..
pm2 restart backend
```

### 方案 3: 在本地构建后上传（最可靠）

如果服务器内存确实不足，可以在本地构建后上传：

#### 步骤 1: 在本地构建

```bash
# 在本地 Windows 机器上
cd D:\telegram-ai-system\saas-demo
npm run build
```

#### 步骤 2: 上传构建文件

```bash
# 使用 SCP 上传（在本地执行）
scp -r saas-demo/.next ubuntu@165.154.233.55:/home/ubuntu/telegram-ai-system/saas-demo/
```

或者使用 Git（如果 `.next` 不在 `.gitignore` 中）：

```bash
# 在本地
git add saas-demo/.next
git commit -m "build: Add built frontend files"
git push origin main

# 在服务器上
cd /home/ubuntu/telegram-ai-system
git pull origin main
pm2 restart frontend
```

### 方案 4: 优化构建配置（减少内存使用）

编辑 `saas-demo/next.config.ts`，添加内存优化配置：

```typescript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // ... 现有配置
  
  // 减少构建内存使用
  swcMinify: true,
  compress: true,
  
  // 禁用不必要的功能
  experimental: {
    optimizeCss: false, // 禁用 CSS 优化（减少内存）
  },
  
  // 减少并发构建
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        minimize: true,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
```

### 方案 5: 升级服务器内存（长期方案）

如果经常遇到内存问题，考虑：
- 升级到 4GB 内存的服务器
- 或使用更大的 VPS 实例

---

## 🚀 推荐执行流程

### 立即尝试（按顺序）

#### 尝试 1: 使用 1GB 内存限制

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo
rm -rf .next node_modules/.cache
export NODE_OPTIONS="--max-old-space-size=1024"
npm run build
```

#### 尝试 2: 停止后端后构建

```bash
# 停止后端
pm2 stop backend

# 构建
cd /home/ubuntu/telegram-ai-system/saas-demo
rm -rf .next node_modules/.cache
export NODE_OPTIONS="--max-old-space-size=1024"
npm run build

# 重启后端
cd ..
pm2 restart backend
```

#### 尝试 3: 使用 768MB 限制

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo
rm -rf .next node_modules/.cache
export NODE_OPTIONS="--max-old-space-size=768"
npm run build
```

#### 尝试 4: 本地构建后上传

如果以上都失败，使用本地构建：

```bash
# 在本地 Windows 机器上
cd D:\telegram-ai-system\saas-demo
npm run build

# 压缩构建文件
tar -czf .next.tar.gz .next

# 上传到服务器（使用 SCP 或 SFTP）
# 然后在服务器上解压
cd /home/ubuntu/telegram-ai-system/saas-demo
tar -xzf .next.tar.gz
pm2 restart frontend
```

---

## 📋 检查清单

### 构建前检查

- [ ] 内存使用率 < 80%
- [ ] Swap 已启用（4GB）
- [ ] 已停止不必要的服务
- [ ] 已清理旧的构建文件

### 构建后验证

- [ ] `.next` 目录存在
- [ ] `.next/static` 目录存在
- [ ] 文件大小合理（> 10MB）
- [ ] 服务可以正常启动

---

## 🐛 如果仍然失败

### 检查系统日志

```bash
# 查看 OOM 日志
sudo dmesg | grep -i "killed\|oom" | tail -n 20

# 查看系统日志
sudo journalctl -n 50 | grep -i "killed\|oom"
```

### 检查进程内存

```bash
# 查看所有进程内存使用
ps aux --sort=-%mem | head -n 20

# 查看 Node.js 进程
ps aux | grep node
```

### 考虑升级服务器

如果内存确实不足，考虑：
- 升级到 4GB 内存的服务器
- 或使用云服务商的更大实例

---

## 💡 最佳实践

### 1. 定期清理

```bash
# 清理 PM2 日志
pm2 flush

# 清理系统日志
sudo journalctl --vacuum-time=7d

# 清理 npm 缓存
npm cache clean --force
```

### 2. 监控内存

```bash
# 设置内存监控
watch -n 5 free -h
```

### 3. 优化构建

- 使用生产环境构建（`NODE_ENV=production`）
- 禁用不必要的优化
- 使用更小的内存限制

---

**最后更新**: 2025-12-09

