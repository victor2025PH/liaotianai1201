# 检查Nginx静态文件配置

## 问题

Chunk文件加载失败：`Failed to load chunk/_next/static/chunks/adc3be135379192a.js`

## 可能的原因

1. **Nginx配置问题**：静态文件请求没有正确路由到Next.js服务器
2. **文件不存在**：这些chunk文件在构建时没有被生成
3. **路径问题**：standalone模式下的静态文件路径不正确

## 检查步骤

### 1. 检查Nginx配置

```bash
sudo nginx -T 2>/dev/null | grep -B 5 -A 15 'server_name aikz.usdt2026.cc'
```

查看是否有 `location /_next/` 配置，或者静态文件请求是否被正确代理到Next.js服务器。

### 2. 检查文件是否存在

```bash
cd /home/ubuntu/liaotian/saas-demo

# 检查源目录
ls -la .next/static/chunks/adc3be135379192a.js

# 检查standalone目录
ls -la .next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js
```

### 3. 测试静态文件访问

```bash
# 通过Nginx访问
curl -I http://aikz.usdt2026.cc/_next/static/chunks/adc3be135379192a.js

# 直接访问Next.js服务器
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js
```

## 解决方案

### 方案1：如果文件存在但Nginx无法访问

需要在Nginx配置中添加静态文件路由：

```nginx
location /_next/static/ {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

### 方案2：如果文件不存在

需要重新构建，确保所有chunk文件都被生成：

```bash
cd /home/ubuntu/liaotian/saas-demo
sudo systemctl stop liaotian-frontend
rm -rf .next node_modules/.cache
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
npm run build
cp -r .next/static .next/standalone/liaotian/saas-demo/.next/
sudo systemctl start liaotian-frontend
```

### 方案3：如果这些chunk是动态导入的

这些chunk可能是动态导入的代码分割，在standalone模式下可能需要特殊处理。可以尝试：
1. 检查Next.js配置中是否有相关的优化设置
2. 检查是否有代码分割配置问题
3. 考虑使用Docker部署，确保一致性

## 建议

1. **使用Docker部署**（推荐）：
   - Dockerfile已经正确处理了静态文件
   - 可以确保每次部署的一致性

2. **创建部署脚本**：
   - 自动化构建和静态文件复制
   - 确保每次部署都正确包含静态文件

3. **检查Next.js配置**：
   - 确保没有禁用代码分割
   - 检查是否有优化配置导致某些chunk被合并

