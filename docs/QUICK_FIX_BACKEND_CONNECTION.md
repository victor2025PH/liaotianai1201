# 快速修复后端连接问题

## 🔍 问题症状

前端显示"无法连接到后端服务器"，控制台出现大量 `ERR_CONNECTION_REFUSED` 错误。

## ⚡ 快速修复（在服务器上执行）

### 方法1: 使用修复脚本（推荐）

```bash
# SSH登录到服务器
ssh ubuntu@你的服务器IP

# 执行修复脚本
cd /home/ubuntu/telegram-ai-system
chmod +x scripts/server/fix-backend-connection.sh
bash scripts/server/fix-backend-connection.sh
```

**作用：**
- 清理端口8000占用
- 重启后端服务
- 验证后端连接

---

### 方法2: 手动修复

```bash
# 1. 检查后端服务状态
sudo systemctl status luckyred-api --no-pager | head -20

# 2. 如果服务未运行，启动它
sudo systemctl start luckyred-api

# 3. 等待几秒
sleep 5

# 4. 检查服务状态
sudo systemctl status luckyred-api --no-pager | head -20

# 5. 测试后端连接
curl http://localhost:8000/health

# 6. 如果端口被占用，清理它
sudo ss -tlnp | grep ":8000"
# 找到PID后：sudo kill -9 <PID>
```

---

### 方法3: 诊断问题

```bash
# 运行诊断脚本
cd /home/ubuntu/telegram-ai-system
chmod +x scripts/server/diagnose-backend-connection.sh
bash scripts/server/diagnose-backend-connection.sh
```

**作用：** 全面检查后端服务状态、端口、连接和日志

---

## 🔧 已修复的问题

### 1. 前端API配置
- ✅ 修复生产环境API地址（使用相对路径 `/api/v1`）
- ✅ 确保通过Nginx代理，而不是直接连接 `localhost:8000`

### 2. 部署脚本改进
- ✅ 添加后端健康检查
- ✅ 确保后端服务正确启动
- ✅ 自动设置前端环境变量（`.env.local`）

### 3. 前端环境变量
- ✅ 自动创建/更新 `.env.local`
- ✅ 设置 `NEXT_PUBLIC_API_BASE_URL=/api/v1`

---

## 📋 验证步骤

修复后，验证以下内容：

### 1. 后端服务运行
```bash
sudo systemctl status luckyred-api
# 应该显示 "active (running)"
```

### 2. 端口8000监听
```bash
sudo ss -tlnp | grep ":8000"
# 应该显示端口正在监听
```

### 3. 后端健康检查
```bash
curl http://localhost:8000/health
# 应该返回JSON响应
```

### 4. Nginx代理
```bash
curl http://localhost/api/v1/health
# 应该返回相同的JSON响应
```

### 5. 前端页面
- 清除浏览器缓存（`Ctrl + Shift + Delete`）
- 硬刷新页面（`Ctrl + F5`）
- 检查控制台，应该没有 `ERR_CONNECTION_REFUSED` 错误

---

## 🎯 如果问题仍然存在

### 检查后端日志
```bash
sudo journalctl -u luckyred-api -n 100 --no-pager
```

### 检查Nginx日志
```bash
sudo tail -50 /var/log/nginx/aikz-error.log
```

### 检查前端服务
```bash
sudo systemctl status liaotian-frontend --no-pager | head -20
sudo journalctl -u liaotian-frontend -n 50 --no-pager
```

---

## ✅ 预期结果

修复后：
- ✅ 后端服务运行中（`active`）
- ✅ 端口8000正在监听
- ✅ 健康检查返回成功
- ✅ 前端可以正常连接后端
- ✅ 控制台没有连接错误
- ✅ AI Key输入框正常显示

---

## 📝 注意事项

1. **清除浏览器缓存**：修复后必须清除缓存才能看到新功能
2. **等待服务启动**：重启服务后需要等待10-30秒
3. **检查防火墙**：确保端口8000和3000没有被防火墙阻止

