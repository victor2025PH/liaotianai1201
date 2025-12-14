# 修复频繁 502 Bad Gateway 错误

## 问题描述

网站经常出现 502 Bad Gateway 错误，这通常表示 Nginx 无法连接到后端服务（FastAPI）。

## 常见原因

### 1. 后端服务未运行或崩溃
- **症状**: 后端服务 (`luckyred-api`) 未运行或频繁重启
- **检查**: `sudo systemctl status luckyred-api`
- **解决**: 重启服务并查看日志找出崩溃原因

### 2. 端口冲突
- **症状**: 端口 8000 被其他进程占用
- **检查**: `sudo lsof -i:8000` 或 `sudo ss -tlnp | grep 8000`
- **解决**: 终止占用端口的进程

### 3. 内存不足 (OOM)
- **症状**: 系统内存使用率过高，进程被 OOM Killer 杀死
- **检查**: `free -h` 和 `dmesg | grep -i oom`
- **解决**: 增加服务器内存或优化代码内存使用

### 4. 后端服务响应超时
- **症状**: 后端服务响应时间过长，Nginx 超时
- **检查**: Nginx 错误日志 `/var/log/nginx/error.log`
- **解决**: 增加 Nginx 超时时间或优化后端性能

### 5. 代码错误导致崩溃
- **症状**: 后端服务启动后立即崩溃
- **检查**: `sudo journalctl -u luckyred-api -n 100`
- **解决**: 修复代码错误

## 快速诊断

在服务器上运行诊断脚本：

```bash
cd /home/ubuntu/telegram-ai-system
chmod +x scripts/server/diagnose-502-frequent.sh
bash scripts/server/diagnose-502-frequent.sh
```

诊断脚本会检查：
1. ✅ 后端服务状态
2. ✅ 服务重启频率
3. ✅ 端口监听状态
4. ✅ 后端进程
5. ✅ 错误日志
6. ✅ 内存使用
7. ✅ CPU 使用
8. ✅ Nginx 配置和状态

## 快速修复

运行自动修复脚本：

```bash
cd /home/ubuntu/telegram-ai-system
chmod +x scripts/server/fix-502-frequent.sh
bash scripts/server/fix-502-frequent.sh
```

修复脚本会：
1. 运行诊断
2. 停止冲突进程
3. 检查项目目录
4. 检查虚拟环境
5. 重启后端服务
6. 验证服务

## 手动排查步骤

### 步骤 1: 检查后端服务状态

```bash
sudo systemctl status luckyred-api
```

如果服务未运行：
```bash
sudo systemctl start luckyred-api
sudo systemctl status luckyred-api
```

### 步骤 2: 检查服务重启频率

```bash
# 查看最近1小时的重启次数
sudo journalctl -u luckyred-api --since "1 hour ago" | grep -c "Started\|Stopped"

# 查看最近的重启记录
sudo journalctl -u luckyred-api --since "1 hour ago" | grep "Started\|Stopped" | tail -10
```

如果频繁重启，查看错误日志：
```bash
sudo journalctl -u luckyred-api -n 100 --no-pager | grep -iE "error|exception|traceback"
```

### 步骤 3: 检查端口监听

```bash
# 检查端口 8000 是否监听
sudo ss -tlnp | grep 8000

# 如果未监听，检查是否有进程占用
sudo lsof -i:8000
```

### 步骤 4: 检查内存使用

```bash
# 查看内存使用
free -h

# 检查是否有 OOM 杀死进程
dmesg | grep -i "out of memory\|oom" | tail -10
```

如果内存不足：
- 增加服务器内存
- 或优化代码减少内存使用
- 或重启服务释放内存

### 步骤 5: 检查 Nginx 配置

```bash
# 检查 Nginx 配置语法
sudo nginx -t

# 查看 Nginx 错误日志
sudo tail -50 /var/log/nginx/error.log | grep -i "502\|upstream\|connect"
```

### 步骤 6: 检查后端日志

```bash
# 查看最近的后端日志
sudo journalctl -u luckyred-api -n 200 --no-pager

# 查看错误日志
sudo journalctl -u luckyred-api -n 200 --no-pager | grep -iE "error|exception|traceback|failed"
```

## 常见解决方案

### 方案 1: 重启后端服务

```bash
sudo systemctl restart luckyred-api
sleep 5
sudo systemctl status luckyred-api
```

### 方案 2: 清理端口冲突

```bash
# 停止后端服务
sudo systemctl stop luckyred-api

# 杀死占用端口的进程
sudo lsof -ti:8000 | xargs sudo kill -9

# 重启服务
sudo systemctl start luckyred-api
```

### 方案 3: 增加 Nginx 超时时间

编辑 Nginx 配置（通常在 `/etc/nginx/sites-available/default` 或 `/etc/nginx/nginx.conf`）：

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

然后重新加载 Nginx：
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 方案 4: 检查代码错误

如果后端服务启动后立即崩溃，可能是代码错误：

```bash
# 查看详细错误
sudo journalctl -u luckyred-api -n 100 --no-pager

# 手动测试启动
cd /home/ubuntu/telegram-ai-system/admin-backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 方案 5: 监控服务状态

设置自动重启（如果服务崩溃）：

编辑 systemd 服务文件 `/etc/systemd/system/luckyred-api.service`：

```ini
[Service]
Restart=always
RestartSec=10
```

然后重新加载：
```bash
sudo systemctl daemon-reload
sudo systemctl restart luckyred-api
```

## 预防措施

1. **监控服务状态**: 定期检查服务是否运行
2. **监控资源使用**: 监控内存和 CPU 使用率
3. **日志轮转**: 定期清理日志文件，避免磁盘满
4. **错误告警**: 设置告警，当服务崩溃时及时通知
5. **代码优化**: 优化代码性能，减少内存和 CPU 使用

## 联系支持

如果以上方法都无法解决问题，请提供：
1. 诊断脚本输出: `bash scripts/server/diagnose-502-frequent.sh`
2. 后端服务日志: `sudo journalctl -u luckyred-api -n 200 --no-pager`
3. Nginx 错误日志: `sudo tail -100 /var/log/nginx/error.log`
4. 系统资源: `free -h` 和 `top -bn1 | head -20`

