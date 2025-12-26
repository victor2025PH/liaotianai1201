# 修复 aiadmin.usdt2026.cc Nginx 配置

## 问题

访问 `https://aiadmin.usdt2026.cc` 显示的是 "AI 智控王" (aizkw) 的内容，而不是管理后台。

## 原因

Nginx 配置可能指向了错误的端口（3003 而不是 3007），或者配置不正确。

## 解决方案

在服务器上执行修复脚本：

```bash
sudo bash scripts/server/fix_aiadmin_nginx.sh
```

或者手动修复：

```bash
# 1. 检查当前配置
sudo cat /etc/nginx/sites-available/aiadmin.usdt2026.cc

# 2. 备份配置
sudo cp /etc/nginx/sites-available/aiadmin.usdt2026.cc /etc/nginx/sites-available/aiadmin.usdt2026.cc.backup

# 3. 编辑配置
sudo nano /etc/nginx/sites-available/aiadmin.usdt2026.cc
```

确保配置文件中：
- `location /` 的 `proxy_pass` 指向 `http://127.0.0.1:3007`（管理后台前端）
- `location /api/` 的 `proxy_pass` 指向 `http://127.0.0.1:8000`（后端 API）

然后：

```bash
# 4. 测试配置
sudo nginx -t

# 5. 重载 Nginx
sudo systemctl reload nginx
```

## 验证

```bash
# 检查配置
sudo cat /etc/nginx/sites-available/aiadmin.usdt2026.cc | grep proxy_pass

# 测试本地服务
curl -I http://127.0.0.1:3007
curl -I http://127.0.0.1:8000/api/v1/sites

# 测试域名（从服务器内部）
curl -I http://aiadmin.usdt2026.cc
```

