# 服务器安全加固指南

## 📋 脚本功能

`scripts/server/secure_server.sh` 脚本将执行以下安全加固：

1. **Redis 安全加固**
   - 绑定到本地（127.0.0.1），禁止公网访问
   - 设置强密码
   - 重启 Redis 服务

2. **UFW 防火墙配置**
   - 只开放必要端口：22 (SSH), 80 (HTTP), 443 (HTTPS)
   - 明确拒绝数据库端口：6379 (Redis), 3306 (MySQL), 5432 (PostgreSQL)

3. **Fail2Ban SSH 防护**
   - 5 分钟内输错 3 次密码，封禁 IP 24 小时

4. **清理可疑文件和定时任务**
   - 删除 `/tmp`, `/var/tmp` 下的可疑脚本
   - 清理 crontab 中的可疑条目

## 🚀 执行脚本

### 方法 1：直接执行

```bash
cd ~/telegram-ai-system
git pull origin main

# 赋予执行权限
chmod +x scripts/server/secure_server.sh

# 执行脚本
sudo bash scripts/server/secure_server.sh
```

### 方法 2：下载并执行

```bash
# 如果脚本不在服务器上，可以创建它
cat > /tmp/secure_server.sh << 'SCRIPT_EOF'
# （脚本内容）
SCRIPT_EOF

chmod +x /tmp/secure_server.sh
sudo bash /tmp/secure_server.sh
```

## ⚠️ 执行前注意事项

1. **备份重要数据**
   - Redis 数据（如果有）
   - 系统配置文件

2. **确保 SSH 连接稳定**
   - 建议在多个终端保持 SSH 连接
   - 如果被误封，可以通过云服务商控制台恢复

3. **检查当前服务**
   - 确认哪些服务需要访问 Redis
   - 确认哪些端口需要开放

## 📝 执行后需要修改的配置

### 1. Redis 密码配置

脚本会生成一个强密码并显示。你需要更新以下位置的 Redis 连接配置：

#### Python 后端（FastAPI）

**文件位置：** `admin-backend/app/core/config.py` 或相关配置文件

**修改示例：**

```python
# 修改前
REDIS_URL = "redis://localhost:6379/0"

# 修改后
REDIS_PASSWORD = "你的Redis密码"  # 从脚本输出中获取
REDIS_URL = f"redis://:{REDIS_PASSWORD}@localhost:6379/0"
```

或者使用环境变量：

```python
import os
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "你的Redis密码")
REDIS_URL = f"redis://:{REDIS_PASSWORD}@localhost:6379/0"
```

**在 `.env` 文件中添加：**

```bash
REDIS_PASSWORD=你的Redis密码
```

#### 其他语言/框架

**Node.js (ioredis):**
```javascript
const Redis = require('ioredis');
const redis = new Redis({
  host: 'localhost',
  port: 6379,
  password: '你的Redis密码'
});
```

**Docker Compose:**
```yaml
services:
  redis:
    image: redis:alpine
    command: redis-server --requirepass 你的Redis密码
    ports:
      - "127.0.0.1:6379:6379"
```

### 2. 测试 Redis 连接

执行脚本后，测试 Redis 连接：

```bash
# 使用密码连接 Redis
redis-cli -a 你的Redis密码

# 或者
redis-cli
AUTH 你的Redis密码

# 测试命令
PING
# 应该返回: PONG
```

### 3. 重启后端服务

更新 Redis 配置后，重启后端服务：

```bash
# 如果使用 PM2
pm2 restart backend

# 如果使用 systemd
sudo systemctl restart luckyred-api.service

# 如果使用 Docker
docker-compose restart backend
```

## 🔍 验证安全加固

### 1. 验证 Redis 安全

```bash
# 测试本地连接（应该成功）
redis-cli -a 你的Redis密码 -h 127.0.0.1 PING

# 测试公网连接（应该失败）
redis-cli -h 你的服务器IP -p 6379
# 应该显示: Could not connect to Redis

# 检查 Redis 配置
sudo grep -E "bind|requirepass" /etc/redis/redis.conf
```

### 2. 验证防火墙

```bash
# 查看 UFW 状态
sudo ufw status verbose

# 应该看到：
# - 22/tcp (SSH) ALLOW
# - 80/tcp (HTTP) ALLOW
# - 443/tcp (HTTPS) ALLOW
# - 6379/tcp (Redis) DENY
# - 3306/tcp (MySQL) DENY

# 测试端口（从外部）
# 应该无法连接到 6379
telnet 你的服务器IP 6379
```

### 3. 验证 Fail2Ban

```bash
# 查看 Fail2Ban 状态
sudo fail2ban-client status

# 查看 SSH jail 状态
sudo fail2ban-client status sshd

# 查看被封禁的 IP
sudo fail2ban-client status sshd | grep "Banned IP"
```

### 4. 验证定时任务清理

```bash
# 查看当前用户 crontab
crontab -l

# 查看 root 用户 crontab
sudo crontab -l

# 应该只看到合法的监控脚本，没有可疑条目
```

## 🛡️ 持续安全建议

### 1. 定期检查

```bash
# 每周检查一次
sudo fail2ban-client status
sudo ufw status
crontab -l
sudo crontab -l
```

### 2. 监控日志

```bash
# 查看 Fail2Ban 日志
sudo tail -f /var/log/fail2ban.log

# 查看 SSH 登录尝试
sudo tail -f /var/log/auth.log | grep sshd

# 查看可疑活动
sudo grep -E "\.update|startup|base64" /var/log/syslog
```

### 3. 更新系统

```bash
# 定期更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 更新安全工具
sudo rkhunter --update
sudo chkrootkit
```

### 4. 备份 Redis 密码

**重要：** 将 Redis 密码保存在安全的地方：

```bash
# 保存到安全文件（设置权限）
echo "Redis密码: 你的Redis密码" | sudo tee /root/redis_password.txt
sudo chmod 600 /root/redis_password.txt
```

## ⚠️ 常见问题

### Q1: 执行脚本后无法连接 Redis？

**A:** 检查：
1. Redis 密码是否正确
2. 连接字符串格式是否正确
3. Redis 服务是否运行：`sudo systemctl status redis`

### Q2: SSH 被误封怎么办？

**A:** 
1. 通过云服务商控制台登录
2. 手动解封 IP：
   ```bash
   sudo fail2ban-client set sshd unbanip 你的IP地址
   ```
3. 调整 Fail2Ban 配置，增加 `maxretry` 或减少 `bantime`

### Q3: 需要开放其他端口怎么办？

**A:** 
```bash
# 临时开放（测试用）
sudo ufw allow 端口号/tcp

# 永久开放
sudo ufw allow 端口号/tcp comment '服务名称'
sudo ufw reload
```

### Q4: Redis 密码忘记了？

**A:**
1. 查看备份的配置文件：`/etc/redis/redis.conf.backup.*`
2. 或者重置密码：
   ```bash
   # 编辑配置文件
   sudo nano /etc/redis/redis.conf
   # 修改 requirepass 行
   # 重启 Redis
   sudo systemctl restart redis
   ```

## 📞 紧急恢复

如果脚本执行后出现问题：

1. **恢复 Redis 配置：**
   ```bash
   sudo cp /etc/redis/redis.conf.backup.* /etc/redis/redis.conf
   sudo systemctl restart redis
   ```

2. **临时禁用 UFW：**
   ```bash
   sudo ufw disable
   ```

3. **停止 Fail2Ban：**
   ```bash
   sudo systemctl stop fail2ban
   ```

4. **查看日志：**
   ```bash
   cat /tmp/secure_server_*.log
   ```

## 📊 安全加固检查清单

- [ ] Redis 已绑定到本地
- [ ] Redis 密码已设置并保存
- [ ] 后端代码已更新 Redis 连接配置
- [ ] UFW 防火墙已启用
- [ ] 只开放必要端口（22, 80, 443）
- [ ] 数据库端口已拒绝（6379, 3306, 5432）
- [ ] Fail2Ban 已安装并运行
- [ ] SSH 保护已启用
- [ ] 可疑文件已清理
- [ ] Crontab 已清理
- [ ] 已测试所有服务正常运行
- [ ] Redis 密码已备份到安全位置
