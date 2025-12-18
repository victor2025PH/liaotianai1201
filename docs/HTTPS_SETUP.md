# HTTPS SSL 证书配置指南

本文档说明如何为 `aikz.usdt2026.cc` 域名配置 HTTPS SSL 证书。

## 自动配置（推荐）

部署脚本已经自动集成了 Certbot，会在部署时自动尝试获取 SSL 证书。前提是：

1. **域名已正确解析**：`aikz.usdt2026.cc` 必须指向服务器 IP
2. **防火墙允许端口 80 和 443**：
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

## 手动配置 SSL 证书

如果自动配置失败，可以手动执行以下步骤：

### 步骤 1：安装 Certbot

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
```

### 步骤 2：确保域名已解析

```bash
# 检查服务器 IP
curl ifconfig.me

# 检查域名解析
dig +short aikz.usdt2026.cc
```

确保域名解析的 IP 与服务器 IP 一致。

### 步骤 3：使用 Certbot 获取证书

```bash
sudo certbot --nginx -d aikz.usdt2026.cc
```

Certbot 会：
1. 验证域名所有权
2. 获取 SSL 证书
3. 自动配置 Nginx

### 步骤 4：验证配置

```bash
# 检查证书状态
sudo certbot certificates

# 测试 Nginx 配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx

# 检查 HTTPS 是否正常工作
curl -I https://aikz.usdt2026.cc
```

## 自动续期

Let's Encrypt 证书有效期为 90 天，Certbot 会自动续期。可以通过以下命令测试续期：

```bash
sudo certbot renew --dry-run
```

续期任务已自动配置在 systemd timer 中，无需手动干预。

## 验证 HTTPS 配置

部署完成后，访问以下地址验证：

- ✅ HTTP 自动跳转到 HTTPS：`http://aikz.usdt2026.cc`
- ✅ HTTPS 正常访问：`https://aikz.usdt2026.cc`
- ✅ API 正常工作：`https://aikz.usdt2026.cc/api/v1/health`

## 后端 CORS 配置更新

配置 HTTPS 后，需要确保后端的 `.env` 文件中包含 HTTPS 域名：

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
sudo nano .env
```

确保 `CORS_ORIGINS` 包含 HTTPS 地址：

```env
CORS_ORIGINS=https://aikz.usdt2026.cc,http://aikz.usdt2026.cc,http://localhost:3000
```

然后重启后端服务：

```bash
sudo -u ubuntu pm2 restart backend
sudo -u ubuntu pm2 save
```

## 故障排查

### 问题 1：Certbot 证书获取失败

**错误信息**：`Failed to obtain certificate`

**可能原因**：
- 域名未正确解析到服务器
- 防火墙阻止了端口 80
- Let's Encrypt 速率限制（每个域名每周最多 5 次）

**解决方法**：
```bash
# 检查域名解析
dig +short aikz.usdt2026.cc

# 检查防火墙
sudo ufw status

# 检查 Nginx 是否正在监听端口 80
sudo netstat -tulpn | grep :80
```

### 问题 2：证书续期失败

**检查续期日志**：
```bash
sudo journalctl -u certbot.timer
sudo certbot renew --dry-run
```

### 问题 3：HTTPS 无法访问

**检查 Nginx 配置**：
```bash
sudo nginx -t
sudo systemctl status nginx
```

**检查证书文件**：
```bash
sudo ls -la /etc/letsencrypt/live/aikz.usdt2026.cc/
```

**检查端口 443**：
```bash
sudo netstat -tulpn | grep :443
sudo ufw allow 443/tcp
```

## 配置 HTTPS 后需要更新的地方

1. ✅ **Nginx 配置**：已自动使用 `deploy/nginx/aikz-https.conf`
2. ✅ **后端 CORS**：需要在 `.env` 中添加 HTTPS 域名
3. ✅ **前端 API URL**：前端会自动使用当前协议（通过 `getApiBaseUrl()` 函数）
4. ⚠️  **前端环境变量**（可选）：如果想强制使用 HTTPS，可以在 `.env.local` 中设置：
   ```env
   NEXT_PUBLIC_API_BASE_URL=https://aikz.usdt2026.cc/api/v1
   ```

## 安全建议

1. **启用 HSTS**：已在 Nginx 配置中添加 `Strict-Transport-Security` 头
2. **定期检查证书**：Let's Encrypt 证书每 90 天自动续期
3. **监控证书过期**：可以设置监控告警
4. **使用强密码**：确保服务器安全
