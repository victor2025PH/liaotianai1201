# Nginx 配置恢复指南

## 问题描述

当 Nginx 服务启动但 `netstat` 看不到任何端口监听时，通常是因为 `/etc/nginx/sites-enabled/` 目录下的配置文件被删除了。

这可能是由于：
- 部署脚本检测到缺少 SSL 证书时自动清理了无效配置
- 手动删除了配置文件
- 系统维护或清理操作

## 解决方案

使用 `restore_nginx.sh` 脚本自动恢复所有网站的 Nginx 配置。

## 脚本功能

`restore_nginx.sh` 脚本会：

1. **自动检测三个网站**：
   - `tgmini.usdt2026.cc` (端口 3001)
   - `hongbao.usdt2026.cc` (端口 3002)
   - `aikz.usdt2026.cc` (端口 3003)

2. **智能配置选择**：
   - 如果 SSL 证书存在 → 生成 HTTPS 配置（包含 HTTP 到 HTTPS 重定向）
   - 如果 SSL 证书不存在 → 生成 HTTP only 配置

3. **证书路径自动检测**：
   - 支持标准路径：`/etc/letsencrypt/live/$domain/fullchain.pem`
   - 支持 Certbot 自动添加的后缀：`/etc/letsencrypt/live/$domain-0001/fullchain.pem`

4. **自动部署**：
   - 复制配置到 `/etc/nginx/sites-available/`
   - 创建符号链接到 `/etc/nginx/sites-enabled/`
   - 测试配置语法
   - 重启 Nginx 服务
   - 验证服务状态和端口监听

## 使用方法

### 方法 1：在服务器上直接运行（推荐）

```bash
# 1. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 2. 拉取最新代码（确保脚本是最新的）
git pull origin main

# 3. 给脚本添加执行权限
chmod +x scripts/server/restore_nginx.sh

# 4. 运行脚本
bash scripts/server/restore_nginx.sh
```

### 方法 2：从本地通过 SSH 运行

```bash
# 在本地执行（需要配置 SSH）
ssh ubuntu@your-server-ip "cd /home/ubuntu/telegram-ai-system && git pull origin main && bash scripts/server/restore_nginx.sh"
```

### 方法 3：使用 GitHub Actions 部署后运行

如果脚本已推送到 GitHub，可以在服务器上：

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/server/restore_nginx.sh
```

## 脚本输出说明

脚本会显示以下信息：

1. **配置恢复进度**：每个网站的配置生成和部署状态
2. **SSL 证书检测**：是否找到证书，使用 HTTPS 还是 HTTP
3. **配置测试结果**：Nginx 配置语法是否正确
4. **服务状态**：Nginx 是否成功重启并运行
5. **端口监听检查**：端口 80/443 是否正在监听
6. **已启用的配置列表**：`/etc/nginx/sites-enabled/` 下的所有配置

## 预期输出示例

```
==========================================
🔧 恢复 Nginx 配置
时间: Sun Dec 21 17:30:00 PST 2025
==========================================

📋 需要恢复的网站配置:
  - tgmini: tgmini.usdt2026.cc (端口 3001)
  - hongbao: hongbao.usdt2026.cc (端口 3002)
  - aizkw: aikz.usdt2026.cc (端口 3003)

✅ Nginx 已安装: nginx version: nginx/1.24.0 (Ubuntu)

==========================================
📝 处理网站: tgmini
域名: tgmini.usdt2026.cc
端口: 3001
==========================================

✅ SSL 证书存在，配置 HTTPS
✅ Nginx 配置已生成: /tmp/tgmini-nginx.conf
✅ 配置已复制到: /etc/nginx/sites-available/tgmini.usdt2026.cc
✅ 符号链接已创建: /etc/nginx/sites-enabled/tgmini.usdt2026.cc

...

==========================================
📊 配置恢复结果
==========================================
成功恢复: 3 / 3

🧪 测试 Nginx 配置...
----------------------------------------
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
✅ Nginx 配置测试通过

🔄 重启 Nginx...
----------------------------------------
✅ Nginx 重启成功！

🔍 验证 Nginx 状态...
----------------------------------------
✅ Nginx 服务正常运行中

🔍 检查端口监听...
----------------------------------------
✅ Nginx 正在监听端口 80/443

端口监听详情:
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      1234/nginx: master
tcp        0      0 0.0.0.0:443             0.0.0.0:*               LISTEN      1234/nginx: master

📋 已启用的 Nginx 配置:
total 0
lrwxrwxrwx 1 root root 49 Dec 21 17:30 tgmini.usdt2026.cc -> /etc/nginx/sites-available/tgmini.usdt2026.cc
lrwxrwxrwx 1 root root 51 Dec 21 17:30 hongbao.usdt2026.cc -> /etc/nginx/sites-available/hongbao.usdt2026.cc
lrwxrwxrwx 1 root root 49 Dec 21 17:30 aikz.usdt2026.cc -> /etc/nginx/sites-available/aikz.usdt2026.cc

==========================================
✅ Nginx 配置恢复完成！
时间: Sun Dec 21 17:30:15 PST 2025
==========================================
```

## 故障排查

### 问题 1：SSL 证书未找到

**症状**：脚本显示 "⚠️  SSL 证书不存在，配置 HTTP only"

**解决方案**：
1. 运行 SSL 证书申请脚本：
   ```bash
   bash scripts/server/setup_ssl.sh
   ```
2. 证书申请成功后，重新运行恢复脚本：
   ```bash
   bash scripts/server/restore_nginx.sh
   ```

### 问题 2：Nginx 配置测试失败

**症状**：脚本显示 "❌ Nginx 配置测试失败！"

**解决方案**：
1. 查看详细错误信息（脚本会输出）
2. 检查证书路径是否正确
3. 检查端口是否被其他服务占用
4. 手动测试配置：
   ```bash
   sudo nginx -t
   ```

### 问题 3：Nginx 重启失败

**症状**：脚本显示 "❌ Nginx 重启失败！"

**解决方案**：
1. 查看 Nginx 日志：
   ```bash
   sudo journalctl -u nginx --no-pager -n 50
   ```
2. 检查 Nginx 错误日志：
   ```bash
   sudo tail -50 /var/log/nginx/error.log
   ```
3. 检查端口占用：
   ```bash
   sudo lsof -i :80
   sudo lsof -i :443
   ```

### 问题 4：端口仍未监听

**症状**：脚本显示 "⚠️  未检测到端口 80/443 监听"

**解决方案**：
1. 检查 Nginx 进程是否运行：
   ```bash
   ps aux | grep nginx
   ```
2. 检查 Nginx 服务状态：
   ```bash
   sudo systemctl status nginx
   ```
3. 检查防火墙设置：
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

## 验证恢复结果

运行以下命令验证配置是否成功恢复：

```bash
# 1. 检查 Nginx 服务状态
sudo systemctl status nginx

# 2. 检查端口监听
sudo netstat -tlnp | grep -E ":(80|443)"
# 或
sudo ss -tlnp | grep -E ":(80|443)"

# 3. 检查已启用的配置
ls -la /etc/nginx/sites-enabled/

# 4. 测试网站访问
curl -I http://tgmini.usdt2026.cc
curl -I http://hongbao.usdt2026.cc
curl -I http://aikz.usdt2026.cc

# 5. 如果配置了 HTTPS，测试 HTTPS
curl -I https://tgmini.usdt2026.cc
curl -I https://hongbao.usdt2026.cc
curl -I https://aikz.usdt2026.cc
```

## 注意事项

1. **运行权限**：脚本需要 `sudo` 权限来修改 Nginx 配置和重启服务
2. **证书路径**：如果 Certbot 使用了非标准路径，可能需要手动调整脚本
3. **端口冲突**：确保端口 80、443、3001、3002、3003 未被其他服务占用
4. **前端服务**：确保前端服务（PM2）正在运行在对应端口（3001、3002、3003）

## 相关文档

- [SSL 证书设置指南](./SSL_CERTIFICATE_SETUP.md)
- [部署工作流说明](./UNIFIED_DEPLOYMENT_WORKFLOW.md)
