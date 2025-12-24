# 端口修复后的验证和后续步骤

**修复内容**: admin-frontend 端口从 3006 改为 3008

---

## ✅ 验证修复结果

### 步骤 1: 验证脚本和文档已更新

```bash
cd /home/ubuntu/telegram-ai-system

# 检查是否还有 3006 的引用（应该没有）
grep -r "admin-frontend.*3006\|3006.*admin-frontend" scripts/ docs/ | grep -v ".backup\|backup/" | grep -v "fix_admin_frontend_port.sh\|ADMIN_SYSTEM"

# 检查新端口 3008 的引用（应该有）
grep -r "admin-frontend.*3008\|3008.*admin-frontend" scripts/ docs/ | head -10
```

**预期结果**:
- ❌ 不应找到 admin-frontend 使用 3006 的引用
- ✅ 应该找到 admin-frontend 使用 3008 的引用

---

### 步骤 2: 检查端口占用情况

```bash
# 检查各个端口的状态
echo "=== 检查端口占用 ==="
sudo lsof -i :3006 | grep LISTEN || echo "端口 3006 未被占用（或应由 ai-monitor-frontend 使用）"
sudo lsof -i :3007 | grep LISTEN || echo "端口 3007 未被占用（或应由 sites-admin-frontend 使用）"
sudo lsof -i :3008 | grep LISTEN || echo "端口 3008 未被占用（修复后应由 admin-frontend 使用）"
sudo lsof -i :8000 | grep LISTEN || echo "端口 8000 未被占用（或应由 admin-backend 使用）"
```

---

### 步骤 3: 检查 PM2 进程状态

```bash
# 查看所有相关进程
pm2 list | grep -E "admin-frontend|sites-admin-frontend|ai-monitor-frontend|backend"

# 预期看到：
# - admin-frontend (如果已部署，应使用端口 3008)
# - sites-admin-frontend (使用端口 3007)
# - ai-monitor-frontend (使用端口 3006)
# - backend (使用端口 8000)
```

---

## 🚀 重新部署服务（如果需要）

### 如果 admin-frontend 需要部署

```bash
# 使用更新后的脚本重新部署
bash scripts/deploy_admin_frontend.sh

# 验证部署
bash scripts/verify_admin_frontend.sh
```

### 验证其他服务是否正常

```bash
# 验证 sites-admin-frontend (端口 3007)
curl -s http://127.0.0.1:3007 | head -20

# 验证 ai-monitor-frontend (端口 3006)
curl -s http://127.0.0.1:3006 | head -20

# 验证 admin-backend (端口 8000)
curl -s http://127.0.0.1:8000/health || curl -s http://127.0.0.1:8000/api/health
```

---

## 🔧 Nginx 配置检查

### 检查 Nginx 配置是否正确

```bash
# 验证 Nginx 配置
sudo nginx -t

# 查看相关配置
sudo grep -A 10 "location /admin\|location /ai-monitor\|location /api" /etc/nginx/sites-enabled/aiadmin.usdt2026.cc
```

**预期配置**:
- `/api/` → 8000 (admin-backend)
- `/admin` → 3007 (sites-admin-frontend)
- `/ai-monitor` → 3006 (ai-monitor-frontend)

### 如果需要添加 admin-frontend 的 Nginx 路由（可选）

如果需要在 `aiadmin.usdt2026.cc` 下访问 admin-frontend，可以添加：

```bash
# 运行配置脚本（如果脚本支持）
bash scripts/configure_admin_nginx.sh

# 或者手动编辑（如果需要）
sudo nano /etc/nginx/sites-available/aiadmin.usdt2026.cc
```

添加配置（如果需要）:
```nginx
# 管理后台前端 (端口 3008) - 可选
location /admin-frontend {
    proxy_pass http://127.0.0.1:3008;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    rewrite ^/admin-frontend/?(.*) /$1 break;
}
```

然后重新加载 Nginx:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 📋 完整验证清单

执行以下检查，确保所有服务正常：

- [ ] **脚本和文档已更新为 3008**
  ```bash
  grep -r "admin-frontend.*3008" scripts/ docs/ | wc -l
  # 应该 > 0
  ```

- [ ] **端口占用正确**
  - 3006: ai-monitor-frontend ✅
  - 3007: sites-admin-frontend ✅
  - 3008: admin-frontend ✅
  - 8000: admin-backend ✅

- [ ] **服务可以访问**
  ```bash
  curl -s http://127.0.0.1:3008 | head -5  # admin-frontend
  curl -s http://127.0.0.1:3007 | head -5  # sites-admin-frontend
  curl -s http://127.0.0.1:3006 | head -5  # ai-monitor-frontend
  curl -s http://127.0.0.1:8000/health     # admin-backend
  ```

- [ ] **Nginx 配置正确**
  ```bash
  sudo nginx -t
  bash scripts/verify_admin_nginx.sh
  ```

- [ ] **PM2 进程运行正常**
  ```bash
  pm2 list
  pm2 logs --lines 20
  ```

---

## 🎯 后续建议

### 1. 确认 admin-frontend 的用途

- 如果 `admin-frontend` 不再需要，可以考虑移除相关脚本和文档
- 如果需要，确认是否需要通过 Nginx 对外提供访问

### 2. 确认 ai-monitor-frontend 文件夹

- 检查 `ai-monitor-frontend/` 文件夹是否存在
- 如果不存在，需要创建或找到正确的项目位置

### 3. 文档更新

- 确保所有相关文档反映正确的端口配置
- 更新部署文档和运维手册

### 4. 监控和告警

- 确保监控系统能正确识别各个服务
- 更新告警规则（如果端口改变影响了监控）

---

## 🔍 故障排查

### 问题 1: admin-frontend 无法启动

```bash
# 检查端口是否被占用
sudo lsof -i :3008

# 检查 PM2 日志
pm2 logs admin-frontend --lines 50

# 手动测试启动
cd admin-frontend
export PORT=3008
npm start
```

### 问题 2: 端口冲突仍然存在

```bash
# 检查所有使用 3006 的进程
sudo lsof -i :3006

# 确认哪个服务在使用
ps aux | grep $(sudo lsof -t -i:3006)
```

### 问题 3: Nginx 代理失败

```bash
# 检查 Nginx 错误日志
sudo tail -50 /var/log/nginx/aiadmin-error.log

# 测试代理
curl -v -H "Host: aiadmin.usdt2026.cc" http://127.0.0.1/admin
```

---

**最后更新**: 2025-12-24  
**状态**: 端口修复已完成，待验证

