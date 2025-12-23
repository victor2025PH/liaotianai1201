# Nginx 服务启动修复指南

## 问题描述

执行 `bash scripts/configure_admin_nginx.sh` 后出现：
```
nginx.service is not active, cannot reload.
```

访问域名时显示：
```
ERR_CONNECTION_REFUSED
Failed to connect to aiadmin.usdt2026.cc port 80
```

## 原因

Nginx 服务未运行，虽然配置已创建，但服务本身没有启动。

## 解决方案

### 方案 1: 使用启动脚本（推荐）

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/start_nginx.sh
```

这个脚本会：
1. 检查 Nginx 是否安装
2. 测试配置文件
3. 启动 Nginx 服务
4. 设置开机自启
5. 检查端口监听状态

### 方案 2: 手动启动

```bash
# 1. 测试配置
sudo nginx -t

# 2. 启动服务
sudo systemctl start nginx

# 3. 设置开机自启
sudo systemctl enable nginx

# 4. 检查状态
sudo systemctl status nginx
```

### 方案 3: 重新运行配置脚本（已修复）

修复后的配置脚本会自动尝试启动 Nginx：

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/configure_admin_nginx.sh
```

## 验证步骤

### 1. 检查 Nginx 服务状态

```bash
sudo systemctl status nginx
```

应该显示 `Active: active (running)`

### 2. 检查端口监听

```bash
sudo netstat -tlnp | grep -E ":80 |:443 "
```

应该看到 Nginx 正在监听 80 和/或 443 端口

### 3. 测试访问

```bash
# 测试 HTTP
curl http://aiadmin.usdt2026.cc/admin

# 测试 HTTPS（如果有证书）
curl https://aiadmin.usdt2026.cc/admin

# 测试 API
curl http://aiadmin.usdt2026.cc/api/v1/ai-monitoring/summary?days=7
```

## 常见问题

### Q1: Nginx 启动失败

**检查错误日志**:
```bash
sudo journalctl -u nginx -n 50 --no-pager
```

**常见原因**:
- 配置文件语法错误
- 端口被占用
- 权限问题

**解决**:
```bash
# 检查配置
sudo nginx -t

# 检查端口占用
sudo lsof -i :80
sudo lsof -i :443

# 检查权限
ls -la /etc/nginx/sites-enabled/
```

### Q2: 端口 80/443 被占用

**检查占用进程**:
```bash
sudo lsof -i :80
sudo lsof -i :443
```

**解决**:
- 停止占用端口的服务
- 或修改 Nginx 监听其他端口

### Q3: 防火墙阻止访问

**检查防火墙**:
```bash
sudo ufw status
```

**开放端口**:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

### Q4: DNS 未解析

**检查 DNS**:
```bash
nslookup aiadmin.usdt2026.cc
ping aiadmin.usdt2026.cc
```

**解决**: 确保 DNS 记录指向服务器 IP

## 完整修复流程

```bash
cd /home/ubuntu/telegram-ai-system

# 1. 拉取最新代码
git pull origin main

# 2. 启动 Nginx（如果未运行）
bash scripts/start_nginx.sh

# 3. 配置管理后台（如果未配置）
bash scripts/configure_admin_nginx.sh

# 4. 验证
curl http://aiadmin.usdt2026.cc/admin
```

## 相关脚本

- `scripts/start_nginx.sh` - 启动和检查 Nginx 服务
- `scripts/configure_admin_nginx.sh` - 配置 Nginx 反向代理（已修复，会自动启动）

---

**最后更新**: 2025-12-24

