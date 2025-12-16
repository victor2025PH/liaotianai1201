# Next.js Standalone 构建诊断

## 问题：server.js 文件未生成

Next.js 16 的 standalone 模式可能生成不同的目录结构。请执行以下诊断命令：

### 1. 检查 .next 目录结构

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 检查 .next 目录
ls -la .next/

# 检查是否有 standalone 目录
ls -la .next/standalone/ 2>/dev/null || echo "standalone 目录不存在"

# 检查 standalone 目录的完整结构
find .next/standalone -name "server.js" 2>/dev/null || echo "未找到 server.js"

# 列出 standalone 目录的所有内容
find .next/standalone -type f 2>/dev/null | head -20
```

### 2. 检查构建日志

```bash
# 重新构建并查看完整输出
cd /home/ubuntu/telegram-ai-system/saas-demo
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build 2>&1 | tee /tmp/build.log

# 检查构建日志中是否有错误
grep -i "error\|fail\|warn" /tmp/build.log | tail -20
```

### 3. Next.js 16 Standalone 结构

在 Next.js 16 中，standalone 输出可能位于：
- `.next/standalone/server.js` (直接路径)
- `.next/standalone/<project-name>/.next/standalone/server.js` (嵌套路径)

### 4. 完整诊断脚本

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

echo "=== 检查 .next 目录 ==="
ls -la .next/ | head -20

echo ""
echo "=== 查找 server.js ==="
find .next -name "server.js" -type f 2>/dev/null

echo ""
echo "=== 检查 standalone 目录结构 ==="
if [ -d ".next/standalone" ]; then
  echo "standalone 目录存在"
  find .next/standalone -type f | head -20
  find .next/standalone -type d | head -20
else
  echo "❌ standalone 目录不存在"
fi

echo ""
echo "=== 检查构建配置 ==="
grep -A 2 "output" next.config.ts

echo ""
echo "=== 检查 package.json build 脚本 ==="
grep "build" package.json
```

