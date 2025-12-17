# 修复 OOM (内存不足) 和 WebSocket 问题

## 🚨 问题诊断

如果执行命令时出现 `Killed` 错误，说明服务器内存不足，OOM (Out of Memory) killer 正在终止进程。

---

## 第一步：检查内存和 Swap

```bash
# 检查内存和 Swap 状态
free -h

# 检查 Swap 是否启用
swapon --show

# 检查 Swap 文件
ls -lh /swapfile
```

如果 Swap 显示为 `0B` 或 `0`，说明 Swap 未启用。

---

## 第二步：启用 Swap（如果未启用）

### 方法一：如果 Swap 文件已存在但未启用

```bash
# 启用现有的 Swap 文件
sudo swapon /swapfile

# 验证
swapon --show
free -h
```

### 方法二：如果 Swap 文件不存在

```bash
# 创建 8GB Swap 文件（需要几分钟）
sudo fallocate -l 8G /swapfile

# 设置权限
sudo chmod 600 /swapfile

# 格式化 Swap
sudo mkswap /swapfile

# 启用 Swap
sudo swapon /swapfile

# 添加到 /etc/fstab（开机自动启用）
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 验证
swapon --show
free -h
```

---

## 第三步：修复 WebSocket 配置（轻量级方法）

由于内存不足，使用最轻量级的方法：

### 方法一：使用 sed 直接修改（推荐，最省内存）

```bash
# 1. 备份配置
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)

# 2. 检查是否已有 WebSocket 配置
grep -q "location /api/v1/notifications/ws" /etc/nginx/sites-available/default && echo "已有配置" || echo "需要添加"

# 3. 如果没有，在 location /api/ 之前插入（使用 sed，最省内存）
sudo sed -i '/location \/api\/ {/i\
    # WebSocket 支持\
    location /api/v1/notifications/ws {\
        proxy_pass http://backend/api/v1/notifications/ws;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_connect_timeout 60s;\
        proxy_send_timeout 86400s;\
        proxy_read_timeout 86400s;\
        proxy_buffering off;\
    }\
' /etc/nginx/sites-available/default

# 4. 测试配置
sudo nginx -t

# 5. 如果测试通过，重载
sudo nginx -s reload
```

### 方法二：手动编辑（如果 sed 也被 Killed）

由于 `nano` 也可能被 Killed，使用 `cat` 和 `echo` 的组合：

```bash
# 1. 查看当前配置中的 location /api/ 位置
grep -n "location /api/" /etc/nginx/sites-available/default

# 2. 查看配置的前几行（找到 server_name 后的位置）
head -100 /etc/nginx/sites-available/default | tail -20

# 3. 如果内存极度不足，可能需要：
# - 停止一些服务释放内存
# - 或等待内存释放后再操作
```

---

## 快速修复命令（一行执行）

```bash
# 启用 Swap（如果存在）
sudo swapon /swapfile 2>/dev/null || echo "Swap 文件不存在，需要创建"

# 如果 Swap 启用了，等待几秒让系统稳定
sleep 3

# 然后添加 WebSocket 配置
sudo sed -i '/location \/api\/ {/i\
    location /api/v1/notifications/ws {\
        proxy_pass http://backend/api/v1/notifications/ws;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_connect_timeout 60s;\
        proxy_send_timeout 86400s;\
        proxy_read_timeout 86400s;\
        proxy_buffering off;\
    }\
' /etc/nginx/sites-available/default && sudo nginx -t && sudo nginx -s reload && echo "✅ 完成"
```

---

## 如果所有命令都被 Killed

### 临时释放内存

```bash
# 1. 检查哪些进程占用内存最多
ps aux --sort=-%mem | head -10

# 2. 如果有不必要的进程，可以临时停止
# 例如：如果前端或后端有多个实例，可以重启 PM2
sudo -u ubuntu pm2 restart all

# 3. 清理系统缓存（谨慎使用）
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# 4. 然后立即启用 Swap
sudo swapon /swapfile
```

---

## 验证修复

```bash
# 1. 验证 Swap 已启用
free -h
# 应该看到 Swap 有使用量

# 2. 验证 WebSocket 配置
grep -A 15 "location /api/v1/notifications/ws" /etc/nginx/sites-available/default

# 3. 验证 Nginx 配置
sudo nginx -t

# 4. 测试 WebSocket（从本地）
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://aikz.usdt2026.cc/api/v1/notifications/ws/test
```

---

## 长期解决方案

1. **增加服务器内存**（如果可能）
2. **优化应用内存使用**
3. **确保 Swap 持久化**（已在 /etc/fstab 中）
4. **监控内存使用情况**

---

## 紧急情况：如果服务器完全无响应

如果 SSH 连接都断开，可能需要：
1. 通过云服务商控制台重启服务器
2. 重启后检查 Swap 是否自动启用
3. 如果没有，手动启用 Swap
4. 然后修复 WebSocket 配置
