# SSH 连接超时排查指南

## 问题现象

- SSH 连接超时（端口 22 和 8822 都失败）
- 网站无法访问（ERR_CONNECTION_TIMED_OUT）
- 所有服务都无法连接

## 可能原因

1. **服务器宕机或关机**
2. **云服务商安全组/防火墙规则问题**
3. **服务器网络配置问题**
4. **服务器 IP 地址变更**
5. **服务器上的服务全部停止**

## 排查步骤

### 1. 通过云服务商控制台检查服务器状态

#### UCloud 控制台检查：

1. **登录 UCloud 控制台**
   - 访问：https://console.ucloud.cn/
   - 进入"云主机"或"UHost"页面

2. **检查服务器状态**
   - 找到服务器 `uhost-1kgb7nabqyq0`
   - 检查服务器状态：
     - ✅ **运行中**：服务器正常，问题在配置
     - ❌ **已停止**：需要启动服务器
     - ❌ **异常**：服务器可能有问题

3. **检查服务器 IP 地址**
   - 确认公网 IP 是否为 `165.154.254.24`
   - 如果 IP 已变更，使用新 IP 连接

4. **检查防火墙规则**
   - 从截图看，防火墙规则已配置：
     - TCP: 22 (SSH)
     - TCP: 80 (HTTP)
     - TCP: 443 (HTTPS)
   - 确认防火墙已绑定到服务器
   - 检查规则是否生效

### 2. 检查安全组/防火墙规则

#### 在 UCloud 控制台：

1. **进入防火墙管理**
   - 找到防火墙 `firewall-eadrljlj`
   - 检查规则是否正确

2. **确认规则配置**
   - ✅ TCP: 22 (SSH) - 源地址: 0.0.0.0/0
   - ✅ TCP: 80 (HTTP) - 源地址: 0.0.0.0/0
   - ✅ TCP: 443 (HTTPS) - 源地址: 0.0.0.0/0

3. **检查防火墙绑定**
   - 确认防火墙已绑定到服务器 `uhost-1kgb7nabqyq0`
   - 如果未绑定，需要绑定防火墙

### 3. 通过控制台登录服务器（如果支持）

#### UCloud VNC 控制台：

1. **进入服务器详情页**
2. **点击"VNC 登录"或"控制台登录"**
3. **使用 root 或 ubuntu 用户登录**
4. **检查服务状态**：
   ```bash
   # 检查系统负载
   uptime
   
   # 检查服务状态
   sudo systemctl status nginx
   sudo systemctl status liaotian-frontend
   sudo systemctl status luckyred-api
   
   # 检查端口监听
   sudo ss -tlnp | grep -E ":(22|80|443|3000|8000)"
   
   # 检查网络连接
   ping -c 3 8.8.8.8
   
   # 检查防火墙
   sudo ufw status
   ```

### 4. 检查服务器网络配置

如果可以通过 VNC 登录，检查：

```bash
# 检查网络接口
ip addr show

# 检查路由
ip route show

# 检查 DNS
cat /etc/resolv.conf

# 检查网络连接
ping -c 3 google.com
```

### 5. 重启服务器（如果必要）

如果服务器状态异常，可以尝试：

1. **在 UCloud 控制台重启服务器**
   - 进入服务器详情页
   - 点击"重启"按钮
   - 等待服务器重启完成（通常 1-2 分钟）

2. **重启后检查**
   - 等待 2-3 分钟让服务完全启动
   - 再次尝试 SSH 连接
   - 检查网站是否可以访问

## 快速修复步骤

### 方案 1：通过 UCloud 控制台重启服务器

1. 登录 UCloud 控制台
2. 进入"云主机"页面
3. 找到服务器 `uhost-1kgb7nabqyq0`
4. 点击"重启"按钮
5. 等待重启完成（1-2 分钟）
6. 再次尝试 SSH 连接

### 方案 2：检查并修复防火墙规则

1. 进入防火墙管理页面
2. 确认防火墙 `firewall-eadrljlj` 已绑定到服务器
3. 检查规则是否正确：
   - TCP: 22 (SSH)
   - TCP: 80 (HTTP)
   - TCP: 443 (HTTPS)
4. 如果规则缺失，添加相应规则

### 方案 3：通过 VNC 控制台检查服务

1. 使用 VNC 登录服务器
2. 检查服务状态：
   ```bash
   # 重启所有服务
   sudo systemctl restart nginx
   sudo systemctl restart liaotian-frontend
   sudo systemctl restart luckyred-api
   
   # 检查服务状态
   sudo systemctl status nginx
   sudo systemctl status liaotian-frontend
   sudo systemctl status luckyred-api
   ```

## 常见问题

### Q1: 服务器显示"运行中"但无法连接

**可能原因：**
- 服务器上的服务未启动
- 服务器防火墙（UFW）阻止了连接
- 服务器网络配置问题

**解决方法：**
1. 通过 VNC 登录服务器
2. 检查服务状态并重启
3. 检查 UFW 防火墙规则

### Q2: 防火墙规则正确但仍无法连接

**可能原因：**
- 防火墙未绑定到服务器
- 服务器上的服务未运行
- 服务器网络接口配置问题

**解决方法：**
1. 确认防火墙已绑定
2. 通过 VNC 检查服务器状态
3. 重启服务器

### Q3: SSH 端口 22 和 8822 都超时

**可能原因：**
- 服务器未运行 SSH 服务
- 防火墙规则未生效
- 服务器网络完全断开

**解决方法：**
1. 通过 VNC 登录检查 SSH 服务：
   ```bash
   sudo systemctl status ssh
   sudo systemctl start ssh
   ```
2. 检查防火墙规则
3. 检查服务器网络连接

## 紧急恢复步骤

如果完全无法连接，按以下步骤操作：

1. **通过 UCloud 控制台重启服务器**
   - 这是最安全的方法
   - 等待 2-3 分钟让服务启动

2. **通过 VNC 控制台登录**
   - 检查服务状态
   - 手动启动服务

3. **检查服务器日志**
   ```bash
   # 查看系统日志
   sudo journalctl -xe | tail -50
   
   # 查看服务日志
   sudo journalctl -u nginx -n 50
   sudo journalctl -u liaotian-frontend -n 50
   sudo journalctl -u luckyred-api -n 50
   ```

4. **运行修复脚本**（如果可以通过 VNC 登录）
   ```bash
   cd /home/ubuntu/telegram-ai-system
   sudo bash scripts/server/fix_connection_timeout.sh
   ```

## 预防措施

1. **定期检查服务器状态**
2. **设置服务自动启动**：
   ```bash
   sudo systemctl enable nginx
   sudo systemctl enable liaotian-frontend
   sudo systemctl enable luckyred-api
   ```
3. **配置监控告警**（如果云服务商支持）
4. **定期备份重要数据**

## 联系支持

如果以上步骤都无法解决问题，请：
1. 截图 UCloud 控制台的服务器状态
2. 截图防火墙规则页面
3. 提供 VNC 控制台的错误信息（如果有）
4. 联系 UCloud 技术支持

