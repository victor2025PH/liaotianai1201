# 服务器修复指南

**问题**: 服务器上脚本文件不存在，需要修复所有配置

---

## 🚀 快速修复步骤

### 步骤 1: 确保拉取最新代码

```bash
cd /home/ubuntu/telegram-ai-system

# 先拉取最新代码
git fetch origin
git pull origin main

# 如果还是显示 "Already up to date"，强制重置
git fetch origin
git reset --hard origin/main

# 验证文件是否存在
ls -la scripts/fix_all_system_configs.sh
ls -la scripts/fix_all_nginx_configs.sh
```

### 步骤 2: 执行修复脚本

```bash
# 执行综合修复脚本（推荐）
sudo bash scripts/fix_all_system_configs.sh

# 或者只修复 Nginx 配置
sudo bash scripts/fix_all_nginx_configs.sh
```

---

## 🔍 如果脚本文件不存在

### 检查 Git 状态

```bash
cd /home/ubuntu/telegram-ai-system

# 检查当前分支
git branch

# 检查远程分支
git branch -r

# 检查文件是否在 Git 中
git ls-files scripts/fix_all_system_configs.sh

# 如果文件不在 Git 中，强制拉取
git fetch --all
git reset --hard origin/main
```

### 手动验证文件

```bash
# 列出 scripts 目录
ls -la scripts/ | grep fix_all

# 应该看到：
# - fix_all_nginx_configs.sh
# - fix_all_system_configs.sh
```

---

## 📋 完整的修复流程

### 1. 拉取最新代码

```bash
cd /home/ubuntu/telegram-ai-system

# 方法 A: 正常拉取
git pull origin main

# 方法 B: 如果拉取失败，强制同步
git fetch origin
git reset --hard origin/main
```

### 2. 执行修复

```bash
# 执行综合修复脚本
sudo bash scripts/fix_all_system_configs.sh
```

这个脚本会：
- ✅ 备份现有配置
- ✅ 修复 aikz.usdt2026.cc 端口（3003 → 3000）
- ✅ 验证所有网站配置
- ✅ 测试并重新加载 Nginx

### 3. 验证修复结果

```bash
# 检查端口监听
sudo lsof -i :3000  # aikz.usdt2026.cc
sudo lsof -i :3001  # tgmini.usdt2026.cc
sudo lsof -i :3002  # hongbao.usdt2026.cc
sudo lsof -i :3003  # aizkw.usdt2026.cc

# 检查 Nginx 配置
sudo nginx -t

# 测试网站访问
curl -I http://127.0.0.1:3000
curl -I http://127.0.0.1:3001
```

---

## ⚠️ 常见问题

### 问题 1: "Already up to date" 但文件不存在

**原因**: Git 缓存问题或分支不同步

**解决**:
```bash
git fetch --all
git reset --hard origin/main
git clean -fd  # 清理未跟踪的文件
```

### 问题 2: Git push 被拒绝

**原因**: 远程有本地没有的提交

**解决**:
```bash
# 先拉取远程更改
git fetch origin
git pull origin main --rebase

# 如果有冲突，解决后推送
git push origin main
```

### 问题 3: 权限问题

**解决**:
```bash
# 确保脚本有执行权限
chmod +x scripts/fix_all_system_configs.sh
chmod +x scripts/fix_all_nginx_configs.sh

# 使用 sudo 执行
sudo bash scripts/fix_all_system_configs.sh
```

---

## 🔧 手动修复（如果脚本不可用）

如果脚本文件无法获取，可以手动修复：

### 修复 aikz.usdt2026.cc 端口

```bash
sudo nano /etc/nginx/sites-available/aikz.usdt2026.cc
```

将所有的 `3003` 改为 `3000`:
```nginx
location / {
    proxy_pass http://127.0.0.1:3000;  # 改为 3000
    ...
}
```

然后测试并重新加载：
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

**最后更新**: 2025-12-24

