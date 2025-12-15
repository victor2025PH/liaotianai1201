# 前端服务部署方案建议

## 📊 当前情况分析

### 后端服务
- ✅ **已使用 systemd**: `luckyred-api.service`
- ✅ **运行稳定**: 通过 systemd 管理
- ✅ **开机自启**: 已配置

### 前端服务
- ⚠️ **当前使用 PM2**: 刚才手动启动
- ✅ **有 systemd 配置**: `liaotian-frontend.service` 已存在
- ⚠️ **配置不一致**: 后端用 systemd，前端用 PM2

## 🎯 推荐方案：统一使用 Systemd

### 为什么选择 Systemd？

#### ✅ 优势

1. **统一管理**
   - 后端和前端使用相同的管理方式
   - 统一的日志系统（`journalctl`）
   - 统一的启动/停止命令

2. **系统集成**
   - 系统级服务管理
   - 开机自启（`systemctl enable`）
   - 更好的资源控制（CPU、内存限制）
   - 安全隔离（`NoNewPrivileges`, `PrivateTmp`）

3. **生产环境标准**
   - Linux 标准服务管理方式
   - 更好的稳定性和可靠性
   - 符合运维最佳实践

4. **日志管理**
   - 统一使用 `journalctl` 查看日志
   - 日志自动轮转
   - 更好的日志查询和过滤

#### ❌ PM2 的劣势（在生产环境）

1. **不一致性**
   - 后端用 systemd，前端用 PM2，管理方式不统一
   - 需要学习两套命令

2. **系统集成差**
   - 不是系统级服务
   - 开机自启需要额外配置（`pm2 startup`）
   - 日志管理不如 systemd 统一

3. **资源管理**
   - systemd 可以更好地控制资源限制
   - systemd 有更好的安全隔离

## 🚫 为什么不建议两种都用？

### 问题 1: 端口冲突
- 如果同时运行 systemd 和 PM2，都会尝试占用端口 3000
- 导致服务冲突和不可预测的行为

### 问题 2: 资源浪费
- 两个进程同时运行，浪费 CPU 和内存
- 增加系统负载

### 问题 3: 管理混乱
- 不知道哪个服务在运行
- 日志分散在两个地方
- 重启时不知道应该重启哪个

## 📋 迁移步骤（从 PM2 到 Systemd）

### 步骤 1: 停止 PM2 服务

```bash
# 停止并删除 PM2 进程
pm2 stop frontend
pm2 delete frontend
pm2 save  # 清除开机自启配置
```

### 步骤 2: 确保前端已构建

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 检查是否有 standalone 构建
if [ ! -d ".next/standalone" ]; then
    echo "需要构建前端..."
    npm run build
fi
```

### 步骤 3: 部署 Systemd 服务

```bash
cd /home/ubuntu/telegram-ai-system

# 方式 1: 使用自动化脚本（推荐）
sudo bash scripts/server/deploy-systemd.sh

# 方式 2: 手动部署
sudo cp deploy/systemd/liaotian-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 步骤 4: 启动 Systemd 服务

```bash
# 启动服务
sudo systemctl start liaotian-frontend

# 设置开机自启
sudo systemctl enable liaotian-frontend

# 检查状态
sudo systemctl status liaotian-frontend
```

### 步骤 5: 验证

```bash
# 检查端口
sudo ss -tlnp | grep 3000

# 检查服务状态
sudo systemctl is-active liaotian-frontend

# 查看日志
sudo journalctl -u liaotian-frontend -n 50 --no-pager

# 测试访问
curl -I http://127.0.0.1:3000/login
```

## 🔄 如果必须使用 PM2（临时方案）

如果暂时无法切换到 systemd，至少要做到：

1. **停止 systemd 服务**（如果存在）
   ```bash
   sudo systemctl stop liaotian-frontend
   sudo systemctl disable liaotian-frontend
   ```

2. **确保 PM2 配置正确**
   ```bash
   cd /home/ubuntu/telegram-ai-system/saas-demo
   pm2 start ecosystem.config.js
   pm2 save
   pm2 startup  # 设置开机自启
   ```

3. **统一使用 PM2 管理**（不推荐，但比混用好）

## ✅ 最终建议

### 生产环境：统一使用 Systemd

```bash
# 后端：systemd ✅
sudo systemctl status luckyred-api

# 前端：systemd ✅（推荐）
sudo systemctl status liaotian-frontend
```

### 开发环境：可以使用 PM2 或手动启动

```bash
# 开发时可以使用
cd saas-demo
npm run dev
```

## 📝 管理命令对比

### Systemd（推荐）

```bash
# 启动
sudo systemctl start liaotian-frontend

# 停止
sudo systemctl stop liaotian-frontend

# 重启
sudo systemctl restart liaotian-frontend

# 状态
sudo systemctl status liaotian-frontend

# 日志
sudo journalctl -u liaotian-frontend -f

# 开机自启
sudo systemctl enable liaotian-frontend
```

### PM2（不推荐用于生产）

```bash
# 启动
pm2 start ecosystem.config.js

# 停止
pm2 stop frontend

# 重启
pm2 restart frontend

# 状态
pm2 list

# 日志
pm2 logs frontend

# 开机自启
pm2 save
pm2 startup
```

## 🎯 总结

**强烈建议：统一使用 Systemd**

- ✅ 与后端保持一致
- ✅ 更好的系统集成
- ✅ 生产环境标准
- ✅ 统一的管理方式
- ✅ 更好的日志管理

**不要混用两种方式！**

