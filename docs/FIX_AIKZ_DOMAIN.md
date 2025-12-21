# 修复 aikz.usdt2026.cc 域名配置

## 问题分析

**当前状态：**
- `aikz.usdt2026.cc` 当前指向端口 3003（`aizkw20251219` 项目）
- 但应该指向端口 3000（`saas-demo` 聊天AI后台）

**其他三个网站正常：**
- ✅ `tgmini.usdt2026.cc` → 端口 3001 (tgmini20251220)
- ✅ `hongbao.usdt2026.cc` → 端口 3002 (hbwy20251220)
- ✅ `aizkw.usdt2026.cc` → 端口 3003 (aizkw20251219)

**需要修复：**
- ❌ `aikz.usdt2026.cc` → 应该指向端口 3000 (saas-demo)

---

## 解决方案

### 步骤 1：启动 saas-demo 服务

在服务器上执行：

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/server/start_saas_demo.sh
```

这个脚本会：
1. 检查 `saas-demo` 目录
2. 安装依赖（如果需要）
3. 构建项目（如果需要）
4. 使用 PM2 启动服务（端口 3000）

### 步骤 2：修复 Nginx 配置

在服务器上执行：

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/fix_aikz_nginx.sh
```

这个脚本会：
1. 检查 SSL 证书
2. 生成新的 Nginx 配置（指向端口 3000）
3. 测试配置
4. 重启 Nginx

---

## 一键修复（推荐）

在服务器上执行：

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main

# 1. 启动 saas-demo
bash scripts/server/start_saas_demo.sh

# 2. 修复 Nginx 配置
sudo bash scripts/server/fix_aikz_nginx.sh
```

---

## 验证修复

修复后，检查：

```bash
# 检查 saas-demo 是否在运行
pm2 list | grep saas-demo

# 检查端口 3000 是否在监听
lsof -i :3000 || ss -tlnp | grep :3000

# 测试本地访问
curl -I http://127.0.0.1:3000

# 测试外部访问
curl -I https://aikz.usdt2026.cc
```

---

## 如果 saas-demo 未运行

如果 `start_saas_demo.sh` 失败，手动启动：

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 安装依赖（如果需要）
npm install

# 构建项目（如果需要）
npm run build

# 使用 PM2 启动
pm2 start npm --name saas-demo -- start
pm2 save
```

---

## 当前配置总结

修复后的配置：

| 域名 | 端口 | 项目 | 说明 |
|------|------|------|------|
| `tgmini.usdt2026.cc` | 3001 | tgmini20251220 | ✅ 正常 |
| `hongbao.usdt2026.cc` | 3002 | hbwy20251220 | ✅ 正常 |
| `aizkw.usdt2026.cc` | 3003 | aizkw20251219 | ✅ 正常 |
| `aikz.usdt2026.cc` | 3000 | saas-demo | 🔧 需要修复 |

---

## 注意事项

1. **端口冲突**：确保端口 3000 没有被其他服务占用
2. **saas-demo 构建**：首次运行需要 `npm run build`，可能需要几分钟
3. **PM2 进程**：使用 PM2 管理服务，确保服务自动重启

---

## 故障排除

### 问题 1：端口 3000 被占用

```bash
# 检查占用端口的进程
sudo lsof -i :3000

# 停止占用端口的进程
sudo lsof -ti :3000 | xargs sudo kill -9
```

### 问题 2：saas-demo 构建失败

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 清理并重新构建
rm -rf .next node_modules
npm install
npm run build
```

### 问题 3：Nginx 配置测试失败

```bash
# 查看详细错误
sudo nginx -t

# 检查配置文件
sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc
```

---

## 完成后的验证

修复完成后，访问 `https://aikz.usdt2026.cc` 应该看到：
- ✅ 聊天AI管理后台的登录页面
- ✅ 不再是 "AI 智控王" 的营销页面
