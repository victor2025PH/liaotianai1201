# SSL 证书申请指南

## 问题描述

部署失败的根本原因是缺少 SSL 证书文件。Nginx 配置中引用了不存在的证书文件，导致配置测试失败。

## 解决方案

使用 `scripts/server/setup_ssl.sh` 脚本自动申请所有需要的 SSL 证书。

## 使用方法

### 方法 1：通过 GitHub Actions 部署后手动执行

1. **SSH 连接到服务器**
   ```bash
   ssh ubuntu@your-server-ip
   ```

2. **进入项目目录**
   ```bash
   cd /home/ubuntu/telegram-ai-system
   ```

3. **拉取最新代码**
   ```bash
   git pull origin main
   ```

4. **运行 SSL 证书申请脚本**
   ```bash
   # 使用默认邮箱
   bash scripts/server/setup_ssl.sh
   
   # 或指定邮箱
   SSL_EMAIL=your-email@example.com bash scripts/server/setup_ssl.sh
   ```

### 方法 2：直接在服务器上执行

如果脚本还未同步到服务器，可以手动创建：

```bash
# 创建脚本目录
mkdir -p ~/telegram-ai-system/scripts/server

# 创建脚本文件（复制脚本内容）
nano ~/telegram-ai-system/scripts/server/setup_ssl.sh
# 粘贴脚本内容，保存退出

# 添加执行权限
chmod +x ~/telegram-ai-system/scripts/server/setup_ssl.sh

# 运行脚本
bash ~/telegram-ai-system/scripts/server/setup_ssl.sh
```

## 脚本功能

1. **自动安装 Certbot**：如果未安装，会自动安装
2. **智能选择模式**：
   - 如果 Nginx 正在运行，使用 `--nginx` 模式（自动配置）
   - 如果 Nginx 未运行，使用 `--standalone` 模式（临时占用端口）
3. **批量申请证书**：为以下域名申请证书：
   - `hongbao.usdt2026.cc`
   - `tgmini.usdt2026.cc`
   - `aikz.usdt2026.cc`
4. **自动验证**：检查证书是否成功申请
5. **自动重启 Nginx**：申请成功后自动重启 Nginx
6. **设置自动续期**：启用 Certbot 自动续期定时任务

## 前置条件

1. **域名 DNS 已正确配置**
   - 所有域名必须指向此服务器的 IP 地址
   - 可以通过 `dig hongbao.usdt2026.cc` 或 `nslookup hongbao.usdt2026.cc` 验证

2. **端口 80 和 443 可访问**
   - 确保防火墙开放了这些端口
   - 如果使用 UFW：`sudo ufw allow 80 && sudo ufw allow 443`
   - 如果使用其他防火墙，请相应配置

3. **服务器有 root 或 sudo 权限**

## 注意事项

1. **Let's Encrypt 限制**：
   - 每个域名每周最多申请 5 次证书
   - 如果频繁申请失败，可能需要等待

2. **DNS 传播时间**：
   - DNS 更改可能需要几分钟到几小时才能生效
   - 如果申请失败，请先验证 DNS 是否正确

3. **端口占用**：
   - 使用 `--standalone` 模式时，需要临时占用 80 和 443 端口
   - 确保没有其他服务占用这些端口

4. **邮箱地址**：
   - Let's Encrypt 会发送证书到期提醒邮件
   - 默认使用 `admin@usdt2026.cc`，可通过环境变量 `SSL_EMAIL` 覆盖

## 验证证书

申请成功后，可以通过以下命令验证：

```bash
# 查看证书信息
sudo certbot certificates

# 查看特定域名的证书
sudo openssl x509 -in /etc/letsencrypt/live/hongbao.usdt2026.cc/fullchain.pem -noout -text

# 测试证书续期
sudo certbot renew --dry-run
```

## 故障排查

### 问题 1：证书申请失败 - DNS 验证失败

**原因**：域名 DNS 未正确指向服务器

**解决**：
```bash
# 检查 DNS 记录
dig hongbao.usdt2026.cc
nslookup hongbao.usdt2026.cc

# 确保返回的 IP 地址是服务器 IP
```

### 问题 2：端口被占用

**原因**：端口 80 或 443 被其他服务占用

**解决**：
```bash
# 查看端口占用
sudo lsof -i :80
sudo lsof -i :443

# 停止占用端口的服务（如果是 Nginx，可以临时停止）
sudo systemctl stop nginx
# 然后重新运行脚本
```

### 问题 3：防火墙阻止

**原因**：防火墙未开放 80 和 443 端口

**解决**：
```bash
# UFW 防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# 检查防火墙状态
sudo ufw status
```

### 问题 4：证书已存在但配置仍失败

**原因**：可能是证书路径不匹配或权限问题

**解决**：
```bash
# 检查证书文件
ls -la /etc/letsencrypt/live/

# 检查证书权限
sudo ls -la /etc/letsencrypt/live/hongbao.usdt2026.cc/

# 如果证书存在，检查 Nginx 配置中的路径是否正确
```

## 后续步骤

证书申请成功后：

1. **重新运行部署**：证书申请成功后，重新触发 GitHub Actions 部署
2. **验证 HTTPS**：访问 `https://hongbao.usdt2026.cc` 验证 HTTPS 是否正常工作
3. **检查自动续期**：确保 Certbot 自动续期已启用

## 相关文件

- 脚本位置：`scripts/server/setup_ssl.sh`
- 证书存储：`/etc/letsencrypt/live/`
- Nginx 配置：`/etc/nginx/sites-enabled/`
