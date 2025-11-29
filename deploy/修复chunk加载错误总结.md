# 修复Chunk加载错误总结

## 问题描述

页面显示错误：
- "組件載入錯誤" (Component loading error)
- `Failed to load chunk/_next/static/chunks/c51be5118db7ed00.js`
- `Failed to load chunk/_next/static/chunks/adc3be135379192a.js`

## 根本原因

在Next.js的standalone模式下，静态文件（`.next/static`）需要被复制到standalone目录中：
- 源目录：`.next/static`
- 目标目录：`.next/standalone/liaotian/saas-demo/.next/static`

如果静态文件没有正确复制，浏览器无法加载这些chunk文件，导致页面组件加载失败。

## 解决方案

### 方案1：手动复制静态文件（快速修复）

```bash
cd /home/ubuntu/liaotian/saas-demo

# 停止服务
sudo systemctl stop liaotian-frontend

# 复制静态文件到standalone目录
cp -r .next/static .next/standalone/liaotian/saas-demo/.next/

# 重启服务
sudo systemctl start liaotian-frontend
sleep 5

# 检查状态
sudo systemctl status liaotian-frontend --no-pager | head -15
```

### 方案2：重新构建（彻底修复）

```bash
cd /home/ubuntu/liaotian/saas-demo

# 停止服务
sudo systemctl stop liaotian-frontend

# 清理构建缓存
rm -rf .next node_modules/.cache

# 重新构建
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
npm run build

# 确保静态文件已复制（Next.js应该自动处理，但可以手动验证）
if [ -d ".next/static" ] && [ -d ".next/standalone/liaotian/saas-demo/.next" ]; then
    cp -r .next/static .next/standalone/liaotian/saas-demo/.next/
fi

# 重启服务
sudo systemctl start liaotian-frontend
sleep 5

# 检查状态
sudo systemctl status liaotian-frontend --no-pager | head -15
ss -tlnp | grep ':3000'
```

## 验证步骤

1. **检查静态文件是否存在**：
   ```bash
   ls -la .next/standalone/liaotian/saas-demo/.next/static/chunks/c51be5118db7ed00.js
   ls -la .next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js
   ```

2. **检查服务状态**：
   ```bash
   sudo systemctl status liaotian-frontend --no-pager | head -15
   ss -tlnp | grep ':3000'
   ```

3. **访问页面**：
   - 清除浏览器缓存
   - 访问 `http://aikz.usdt2026.cc/group-ai/accounts`
   - 检查是否还有chunk加载错误

## 预防措施

为了避免将来出现这个问题，建议：

1. **在构建脚本中自动复制静态文件**：
   ```bash
   npm run build && cp -r .next/static .next/standalone/liaotian/saas-demo/.next/
   ```

2. **使用Docker部署**（推荐）：
   - Dockerfile中已经包含了复制静态文件的步骤
   - 这样可以确保每次构建都正确包含静态文件

3. **创建部署脚本**：
   - 自动化构建和部署流程
   - 确保静态文件始终正确复制

## 相关文件

- Next.js配置：`saas-demo/next.config.ts`
- Dockerfile：`saas-demo/Dockerfile`（第62行：`COPY --from=builder /app/.next/static ./.next/static`）
- 服务配置：`/etc/systemd/system/liaotian-frontend.service`

## 经验总结

1. **Next.js standalone模式**：
   - 静态文件需要手动复制到standalone目录
   - 或者使用Docker部署，Dockerfile会自动处理

2. **Chunk加载错误**：
   - 通常是静态文件路径问题
   - 检查standalone目录中的静态文件是否存在

3. **部署流程**：
   - 构建后必须复制静态文件
   - 或者使用Docker部署确保一致性

