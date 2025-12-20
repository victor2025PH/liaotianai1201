# Nginx HTTPS 配置持久化指南

## 问题原因分析

### 为什么 Certbot 修改配置后 HTTPS server 块会丢失？

Certbot 在修改 Nginx 配置时，可能会：

1. **覆盖整个配置文件**
   - 当使用 `certbot --nginx` 时，Certbot 会读取现有配置
   - 如果配置格式不符合 Certbot 的预期，它可能会生成一个简化版本
   - 只保留基本的 HTTP 重定向和 HTTPS server 块，但可能丢失自定义的 location 配置

2. **配置文件被替换**
   - Certbot 可能会创建新的配置文件
   - 如果配置文件路径或命名不符合 Certbot 的查找规则，可能会创建多个配置文件

3. **证书续期时的配置重置**
   - 证书自动续期时，Certbot 的 `renewal-hooks` 可能会重新生成配置
   - 如果配置模板不完整，会导致 HTTPS server 块丢失

4. **配置语法错误导致部分配置被忽略**
   - 如果配置中有语法错误，Certbot 可能会跳过某些部分
   - 导致 HTTPS server 块不完整

## 解决方案

### 方案 1: 配置持久化脚本（推荐）

使用 `ensure-https-config-persistent.sh` 脚本确保 HTTPS 配置始终存在：

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
sudo bash scripts/server/ensure-https-config-persistent.sh
```

**功能：**
- ✅ 自动备份当前配置
- ✅ 检查并创建完整的 HTTPS server 块
- ✅ 保留所有自定义 location 配置
- ✅ 验证配置语法
- ✅ 自动重新加载 Nginx

### 方案 2: 自动恢复机制（长期保护）

使用 `setup-nginx-auto-restore.sh` 设置自动恢复机制：

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
sudo bash scripts/server/setup-nginx-auto-restore.sh
```

**保护机制：**
1. **定时检查（每 5 分钟）**
   - 自动检测 HTTPS 配置是否丢失
   - 如果丢失，自动恢复

2. **Certbot 后处理钩子**
   - 在 Certbot 执行后自动检查配置
   - 如果配置丢失，立即恢复

3. **systemd 服务**
   - 在 Nginx 启动后自动检查配置
   - 确保服务启动时配置完整

### 方案 3: 手动配置模板

使用项目中的配置模板 `deploy/nginx/aikz-https.conf`：

```bash
# 备份当前配置
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.backup

# 使用模板
sudo cp /home/ubuntu/telegram-ai-system/deploy/nginx/aikz-https.conf /etc/nginx/sites-available/aikz.usdt2026.cc

# 测试并重新加载
sudo nginx -t && sudo systemctl reload nginx
```

## 确保每次重启都能监听 443 端口

### 1. 检查 Nginx 服务状态

```bash
# 检查服务是否启用（开机自启）
sudo systemctl is-enabled nginx

# 如果未启用，执行：
sudo systemctl enable nginx
```

### 2. 验证配置文件完整性

```bash
# 检查是否有 HTTPS server 块
sudo grep -A 5 "listen 443" /etc/nginx/sites-available/aikz.usdt2026.cc

# 检查 SSL 证书路径
sudo grep "ssl_certificate" /etc/nginx/sites-available/aikz.usdt2026.cc
```

### 3. 测试配置语法

```bash
sudo nginx -t
```

### 4. 检查端口监听

```bash
# 检查 443 端口是否监听
sudo ss -tlnp | grep :443

# 如果未监听，检查 Nginx 错误日志
sudo tail -50 /var/log/nginx/error.log
```

### 5. 设置自动恢复（推荐）

运行自动恢复设置脚本：

```bash
sudo bash /home/ubuntu/telegram-ai-system/scripts/server/setup-nginx-auto-restore.sh
```

这将设置：
- ✅ 定时检查任务（cron）
- ✅ Certbot 后处理钩子
- ✅ systemd 服务（Nginx 启动后检查）

## 最佳实践

### 1. 配置管理

- **使用版本控制**
  - 将 Nginx 配置保存在 `deploy/nginx/` 目录
  - 使用 Git 管理配置变更

- **配置备份**
  - 每次修改前自动备份
  - 保留多个历史版本

### 2. Certbot 使用建议

- **使用 `--nginx` 插件时谨慎**
  ```bash
  # 推荐：先手动配置，再使用 certbot 获取证书
  sudo certbot certonly --nginx -d aikz.usdt2026.cc
  
  # 然后手动配置 SSL 证书路径
  ```

- **证书续期配置**
  ```bash
  # 编辑续期配置，添加后处理钩子
  sudo nano /etc/letsencrypt/renewal/aikz.usdt2026.cc.conf
  
  # 添加：
  # [[renewalparams]]
  # deploy_hook = /etc/letsencrypt/renewal-hooks/deploy/ensure-https.sh
  ```

### 3. 监控和告警

- **日志监控**
  ```bash
  # 监控 Nginx 错误日志
  sudo tail -f /var/log/nginx/error.log | grep -i "ssl\|443\|certificate"
  ```

- **端口监控**
  ```bash
  # 定期检查 443 端口
  */5 * * * * /usr/bin/ss -tlnp | grep :443 || systemctl restart nginx
  ```

## 故障排查

### 问题 1: 端口 443 未监听

**检查步骤：**
1. 检查 Nginx 服务状态：`sudo systemctl status nginx`
2. 检查配置文件：`sudo nginx -t`
3. 查看错误日志：`sudo tail -50 /var/log/nginx/error.log`
4. 检查防火墙：`sudo ufw status`

**解决方案：**
```bash
# 运行修复脚本
sudo bash /home/ubuntu/telegram-ai-system/scripts/server/ensure-https-config-persistent.sh
```

### 问题 2: SSL 证书路径错误

**检查步骤：**
```bash
# 检查证书文件是否存在
sudo ls -la /etc/letsencrypt/live/aikz.usdt2026.cc/

# 检查配置中的路径
sudo grep "ssl_certificate" /etc/nginx/sites-available/aikz.usdt2026.cc
```

**解决方案：**
```bash
# 重新获取证书
sudo certbot certonly --nginx -d aikz.usdt2026.cc

# 或手动更新配置中的证书路径
```

### 问题 3: 配置被 Certbot 覆盖

**解决方案：**
```bash
# 运行自动恢复脚本
sudo bash /home/ubuntu/telegram-ai-system/scripts/server/setup-nginx-auto-restore.sh

# 这将设置自动恢复机制，防止配置丢失
```

## 验证清单

每次重启后，执行以下检查：

- [ ] Nginx 服务正在运行：`sudo systemctl status nginx`
- [ ] 端口 443 正在监听：`sudo ss -tlnp | grep :443`
- [ ] HTTPS 配置存在：`sudo grep "listen 443" /etc/nginx/sites-available/aikz.usdt2026.cc`
- [ ] SSL 证书文件存在：`sudo ls /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem`
- [ ] 配置语法正确：`sudo nginx -t`
- [ ] 可以访问 HTTPS：`curl -I https://aikz.usdt2026.cc`

## 相关脚本

- `scripts/server/ensure-https-config-persistent.sh` - 确保 HTTPS 配置持久化
- `scripts/server/setup-nginx-auto-restore.sh` - 设置自动恢复机制
- `scripts/server/fix-https-completely.sh` - 完全修复 HTTPS 访问问题
- `deploy/nginx/aikz-https.conf` - HTTPS 配置模板

