# 服务器死机/重启问题诊断指南

## 概述

服务器频繁死机或需要重启可能由多种原因引起。本文档提供完整的诊断和解决方案。

## 快速诊断

### 在服务器上运行完整诊断

```bash
# 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 拉取最新代码（包含诊断脚本）
git pull origin main

# 运行完整诊断
bash scripts/server/diagnose-system-complete.sh

# 或分别运行
bash scripts/server/diagnose-system-crashes.sh  # 死机/重启诊断
bash scripts/server/check-security-threats.sh   # 安全威胁检查
```

## 常见原因和解决方案

### 1. 内存不足 (OOM Killer)

**症状：**
- 系统突然杀死进程
- 日志中出现 "Out of memory" 或 "Killed process"
- 系统响应变慢后死机

**诊断：**
```bash
# 检查 OOM 记录
grep -i "out of memory\|killed process" /var/log/kern.log
grep -i "out of memory\|killed process" /var/log/syslog

# 检查内存使用
free -h
ps aux --sort=-%mem | head -10
```

**解决方案：**
```bash
# 1. 增加 swap 空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 2. 优化应用内存使用
# 检查并关闭不必要的服务
systemctl list-units --type=service --state=running

# 3. 限制进程内存使用
# 在 systemd 服务文件中添加:
# MemoryLimit=2G
```

### 2. 硬件故障

**症状：**
- 系统突然断电或重启
- 内核崩溃 (kernel panic)
- 硬件错误日志

**诊断：**
```bash
# 检查系统崩溃日志
ls -lh /var/crash/
journalctl -k --since "7 days ago" | grep -i "panic\|crash\|segfault"

# 检查硬件错误
dmesg | grep -i "error\|fail\|hardware"
journalctl -p err --since "7 days ago"

# 检查内存
sudo memtester 1G 1  # 需要安装: sudo apt-get install memtester

# 检查硬盘
sudo smartctl -a /dev/sda  # 需要安装: sudo apt-get install smartmontools
```

**解决方案：**
- 如果发现硬件错误，联系服务器提供商检查硬件
- 考虑更换有问题的硬件组件

### 3. 系统过热

**症状：**
- 系统在高温时死机
- CPU 频率降低（thermal throttling）
- 风扇噪音异常

**诊断：**
```bash
# 检查系统温度（需要安装 sensors）
sudo apt-get install lm-sensors
sudo sensors-detect
sensors

# 检查 CPU 频率
cat /proc/cpuinfo | grep MHz

# 检查系统负载
uptime
top
```

**解决方案：**
```bash
# 1. 清理服务器内部灰尘
# 2. 检查风扇是否正常工作
# 3. 改善服务器通风
# 4. 降低 CPU 频率（临时）
sudo cpupower frequency-set -g powersave
```

### 4. 磁盘空间不足

**症状：**
- 系统无法写入日志
- 应用无法创建文件
- 系统响应变慢

**诊断：**
```bash
# 检查磁盘使用
df -h

# 查找大文件
sudo du -h --max-depth=1 / | sort -h | tail -10

# 检查日志文件大小
sudo du -sh /var/log/*
```

**解决方案：**
```bash
# 1. 清理日志文件
sudo journalctl --vacuum-time=7d  # 只保留 7 天日志
sudo find /var/log -name "*.log" -mtime +30 -delete

# 2. 清理 apt 缓存
sudo apt-get clean
sudo apt-get autoremove

# 3. 清理临时文件
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*
```

### 5. 系统服务崩溃

**症状：**
- 特定服务频繁重启
- 系统日志显示服务错误

**诊断：**
```bash
# 检查失败的服务
systemctl --failed

# 查看服务日志
sudo journalctl -u <service-name> -n 50

# 检查服务状态
systemctl status <service-name>
```

**解决方案：**
```bash
# 1. 重启失败的服务
sudo systemctl restart <service-name>

# 2. 检查服务配置
sudo systemctl cat <service-name>

# 3. 如果服务持续失败，检查依赖和资源
sudo systemctl list-dependencies <service-name>
```

### 6. 安全威胁（中毒/恶意软件）

**症状：**
- CPU/内存使用异常高
- 异常的网络连接
- 可疑的进程

**诊断：**
```bash
# 运行安全检查
bash scripts/server/check-security-threats.sh

# 检查可疑进程
ps aux | grep -iE "miner|crypto|bitcoin|monero"

# 检查异常网络连接
ss -tunp | grep ESTAB
netstat -tunp | grep ESTAB

# 检查定时任务
crontab -l
cat /etc/crontab
```

**解决方案：**
```bash
# 1. 终止可疑进程
sudo kill -9 <PID>

# 2. 删除可疑文件
sudo rm -rf <可疑文件路径>

# 3. 清理定时任务
crontab -e  # 删除可疑任务

# 4. 更改所有密码
# SSH、数据库、应用密码等

# 5. 运行安全扫描
sudo apt-get install rkhunter chkrootkit
sudo rkhunter --check
sudo chkrootkit

# 6. 检查系统完整性
sudo apt-get install debsums
sudo debsums -c

# 7. 如果严重，考虑重新安装系统
```

### 7. 内核问题

**症状：**
- 内核崩溃 (kernel panic)
- 驱动错误
- 系统无法启动

**诊断：**
```bash
# 检查内核日志
dmesg | tail -50
journalctl -k --since "7 days ago"

# 检查内核版本
uname -r

# 检查已安装的内核
dpkg -l | grep linux-image
```

**解决方案：**
```bash
# 1. 更新内核
sudo apt-get update
sudo apt-get install linux-generic

# 2. 如果新内核有问题，使用旧内核启动
# 在 GRUB 启动菜单选择旧内核版本

# 3. 移除有问题的内核
sudo apt-get remove linux-image-<version>
```

## 预防措施

### 1. 监控系统资源

```bash
# 安装监控工具
sudo apt-get install htop iotop nethogs

# 设置资源限制
# 在 systemd 服务文件中:
# MemoryLimit=2G
# CPUQuota=50%
```

### 2. 定期维护

```bash
# 每周执行
sudo apt-get update && sudo apt-get upgrade
sudo journalctl --vacuum-time=7d
sudo find /var/log -name "*.log" -mtime +30 -delete

# 每月执行
sudo rkhunter --update && sudo rkhunter --check
sudo debsums -c
```

### 3. 设置自动重启策略

```bash
# 编辑 /etc/default/grub
sudo nano /etc/default/grub

# 添加或修改:
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash panic=10"

# 更新 GRUB
sudo update-grub
```

### 4. 配置日志轮转

```bash
# 编辑 /etc/logrotate.d/custom
sudo nano /etc/logrotate.d/custom

# 添加配置:
/var/log/custom/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 紧急恢复

如果系统无法启动：

1. **使用救援模式或 Live CD**
2. **挂载文件系统并检查日志**
3. **修复损坏的文件系统**
4. **从备份恢复**

## 相关文档

- [Worker 连接诊断](./WORKER_CONNECTION_TROUBLESHOOTING.md)
- [502 错误修复](./FIX_502_AND_WORKER_ISSUES.md)
- [部署步骤](./DEPLOYMENT_STEPS.md)

