# Rkhunter 扫描结果查看指南

## 📋 当前状态

从截图看到 Rkhunter 正在扫描：
- ✅ 文件已更新：搜索了 180 个文件，找到 144 个
- 🔍 正在扫描进程...
- 🔍 正在扫描 Linux 镜像...

## ⚠️ 为什么没有日志文件？

如果看到 `No such file or directory` 错误，可能的原因：

1. **首次运行**：Rkhunter 在完成第一次扫描后才会创建日志文件
2. **扫描未完成**：扫描还在进行中，日志文件尚未生成
3. **日志在其他位置**：某些系统配置可能将日志放在不同位置

## 🔍 查找日志文件位置

```bash
# 1. 检查日志文件是否存在（多个可能位置）
ls -la /var/log/rkhunter.log 2>/dev/null && echo "✅ 找到日志文件" || echo "❌ 日志文件不存在"
ls -la /var/log/rkhunter/rkhunter.log 2>/dev/null && echo "✅ 找到日志文件（备用位置）" || echo "❌ 备用位置也不存在"

# 2. 查找所有 rkhunter 相关文件
sudo find /var/log -name "*rkhunter*" -type f 2>/dev/null

# 3. 检查 Rkhunter 配置中的日志路径
sudo grep -E "LOGFILE|LOG_DIR" /etc/rkhunter.conf 2>/dev/null || \
sudo grep -E "LOGFILE|LOG_DIR" /etc/rkhunter/rkhunter.conf 2>/dev/null || \
echo "配置文件不存在"
```

## 🔍 查看完整扫描结果

### 方法 1：等待扫描完成（推荐）

```bash
# 等待当前扫描完成（可能需要 5-10 分钟）
# 扫描完成后，日志文件会自动创建

# 然后查看日志
sudo tail -100 /var/log/rkhunter.log

# 或者查看警告和错误
sudo grep -E "Warning|Error|Found|Suspicious" /var/log/rkhunter.log | tail -50
```

### 方法 2：实时查看扫描输出

```bash
# 重新运行扫描，直接查看输出（不生成日志文件）
sudo rkhunter --check --skip-keypress

# 或者只显示警告
sudo rkhunter --check --skip-keypress --report-warnings-only

# 或者将输出保存到文件
sudo rkhunter --check --skip-keypress 2>&1 | tee /tmp/rkhunter_output.txt
cat /tmp/rkhunter_output.txt
```

### 方法 3：查看扫描摘要

```bash
# 查看最后一次扫描的摘要
sudo rkhunter --check --skip-keypress --report-warnings-only

# 查看所有检查项的状态
sudo rkhunter --list
```

### 2. 查看 Rkhunter 属性数据库

```bash
# 查看可疑文件列表
sudo rkhunter --list | grep -E "Warning|Suspicious"

# 查看所有检查项
sudo rkhunter --list
```

### 3. 查看 Chkrootkit 结果

```bash
# 运行 chkrootkit 扫描（可能需要几分钟）
sudo chkrootkit

# 查看结果（会直接输出到终端）
# 注意查找以下关键词：
# - "INFECTED" - 发现感染
# - "not found" - 未发现（正常）
# - "nothing found" - 未发现（正常）
```

## 🔒 重点关注项目

### 1. 检查可疑文件

```bash
# 检查之前发现的可疑文件是否还存在
ls -la /run/user/1000/.update 2>/dev/null && echo "⚠️  文件仍存在！" || echo "✅ 文件已删除"
ls -la /var/tmp/.update 2>/dev/null && echo "⚠️  文件仍存在！" || echo "✅ 文件已删除"

# 检查是否有新的可疑文件
find /tmp /var/tmp /run -name ".update" -o -name "*update*" 2>/dev/null | grep -v ".git"
```

### 2. 检查 Crontab 状态

```bash
# 查看当前 crontab（应该只有合法条目）
crontab -l

# 如果还有可疑条目，执行清理
cd ~/telegram-ai-system
git pull origin main
bash scripts/server/cleanup-suspicious-crontab.sh
```

### 3. 检查系统进程

```bash
# 检查是否有可疑进程
ps aux | grep -E "\.update|startup|miner|crypto" | grep -v grep

# 检查 CPU 使用率（挖矿脚本会导致 CPU 100%）
top -bn1 | head -20

# 检查网络连接
sudo netstat -tulpn | grep -E "ESTABLISHED" | head -20
```

## 🛡️ 完整安全检查流程

### 步骤 1：完成 Rkhunter 扫描

```bash
# 等待当前扫描完成，然后查看结果
sudo tail -f /var/log/rkhunter.log

# 或者重新运行完整扫描（需要 5-10 分钟）
sudo rkhunter --update
sudo rkhunter --check --skip-keypress
```

### 步骤 2：运行 Chkrootkit

```bash
# 运行 chkrootkit 扫描
sudo chkrootkit > /tmp/chkrootkit_report.txt 2>&1

# 查看报告
cat /tmp/chkrootkit_report.txt

# 检查是否有感染
grep -i "infected\|suspicious\|warning" /tmp/chkrootkit_report.txt
```

### 步骤 3：清理可疑 Crontab 条目

```bash
# 执行清理脚本
cd ~/telegram-ai-system
git pull origin main
chmod +x scripts/server/cleanup-suspicious-crontab.sh
bash scripts/server/cleanup-suspicious-crontab.sh
```

### 步骤 4：检查系统完整性

```bash
# 检查系统文件完整性
sudo debsums -c 2>/dev/null | head -20

# 检查是否有未授权的 SSH 密钥
cat ~/.ssh/authorized_keys

# 检查最近的登录记录
sudo last -20

# 检查失败的登录尝试
sudo grep "Failed password" /var/log/auth.log | tail -20
```

### 步骤 5：检查网络活动

```bash
# 检查异常网络连接
sudo netstat -tulpn | grep -v "127.0.0.1\|::1" | grep "ESTABLISHED"

# 检查 DNS 查询（如果有异常域名）
sudo tcpdump -i any -n port 53 2>/dev/null | head -20

# 检查出站连接
sudo ss -tulpn | grep ESTAB
```

## 📊 扫描结果解读

### Rkhunter 结果说明

- **绿色/正常**：未发现威胁
- **黄色/警告**：可能的问题，需要检查
- **红色/错误**：发现可疑活动，需要立即处理

### Chkrootkit 结果说明

- **"not found"** 或 **"nothing found"**：正常，未发现威胁
- **"INFECTED"**：发现感染，需要立即处理
- **"suspicious"**：可疑文件，需要进一步检查

## ⚠️ 如果发现威胁

### 1. 立即隔离

```bash
# 停止可疑进程
sudo pkill -f "\.update|startup"

# 删除可疑文件
sudo rm -f /run/user/1000/.update /var/tmp/.update

# 清理 crontab
crontab -l | grep -v "\.update startup" | crontab -
```

### 2. 收集证据

```bash
# 备份日志
sudo cp /var/log/rkhunter.log ~/rkhunter_$(date +%Y%m%d).log
sudo cp /tmp/chkrootkit_report.txt ~/chkrootkit_$(date +%Y%m%d).txt

# 备份可疑文件（如果存在，用于分析）
if [ -f "/run/user/1000/.update" ]; then
  sudo cp /run/user/1000/.update ~/.update_backup_$(date +%Y%m%d)
fi
```

### 3. 加强安全

```bash
# 更改所有密码
# 检查 SSH 密钥
# 审查访问日志
# 考虑重新部署到干净系统
```

## ✅ 正常结果示例

如果扫描正常，应该看到：

```
[ Rootkit Hunter version 1.4.6 ]
File updated: searched for 180 files, found 144
Scanning processes...
Scanning linux images...
No rootkits found
```

## 📝 后续建议

1. **定期扫描**：每周运行一次 Rkhunter 和 Chkrootkit
2. **监控日志**：定期检查系统日志
3. **更新系统**：保持系统和安全工具更新
4. **防火墙**：确保 UFW 或 iptables 正确配置
5. **SSH 安全**：禁用密码登录，只使用密钥

