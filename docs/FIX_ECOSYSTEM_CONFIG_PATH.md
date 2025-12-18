# 修复 ecosystem.config.js 路径错误

## 🚨 问题描述

如果看到以下错误：

```
[PM2] [ERROR] Error: Script not found: /home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn
[PM2] [ERROR] Could not create folder: /home/ubuntu/telegram-ai-system/logs
```

**原因：** `ecosystem.config.js` 文件中使用了错误的路径（`/home/ubuntu` 而不是 `/home/deployer`）

---

## ✅ 快速修复方法

### 方法 1：删除旧的配置文件并重新运行脚本（推荐）

```bash
# 切换到 deployer 用户
sudo su - deployer

# 进入项目目录
cd /home/deployer/telegram-ai-system

# 删除旧的配置文件（如果存在）
rm -f ecosystem.config.js

# 运行修复后的部署脚本
bash scripts/server/quick-deploy-after-build.sh
```

脚本现在会自动检测并修复路径错误。

### 方法 2：手动删除并重新创建

```bash
# 切换到 deployer 用户
sudo su - deployer
cd /home/deployer/telegram-ai-system

# 备份并删除旧配置
mv ecosystem.config.js ecosystem.config.js.backup 2>/dev/null || true

# 检查并修复目录权限
sudo chown -R deployer:deployer /home/deployer/telegram-ai-system

# 重新运行部署脚本
bash scripts/server/quick-deploy-after-build.sh
```

---

## 🔍 验证修复

修复后，检查配置文件内容：

```bash
# 查看配置文件内容
cat /home/deployer/telegram-ai-system/ecosystem.config.js | grep "cwd\|script"

# 应该看到：
# cwd: "/home/deployer/telegram-ai-system/admin-backend"
# script: "/home/deployer/telegram-ai-system/admin-backend/venv/bin/uvicorn"
# 而不是 /home/ubuntu/...
```

---

## 📋 完整的修复流程

如果仍然遇到问题，执行以下完整流程：

```bash
# 1. 确保是 deployer 用户
sudo su - deployer
cd /home/deployer/telegram-ai-system

# 2. 停止所有 PM2 服务
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true

# 3. 删除旧的配置文件
rm -f ecosystem.config.js ecosystem.config.js.backup*

# 4. 确保目录权限正确
sudo chown -R deployer:deployer /home/deployer/telegram-ai-system

# 5. 确保日志目录存在
mkdir -p /home/deployer/telegram-ai-system/logs
chmod 755 /home/deployer/telegram-ai-system/logs

# 6. 验证后端虚拟环境存在
test -f /home/deployer/telegram-ai-system/admin-backend/venv/bin/uvicorn && echo "✅ uvicorn 存在" || echo "❌ uvicorn 不存在，需要创建虚拟环境"

# 7. 运行部署脚本
bash scripts/server/quick-deploy-after-build.sh
```

---

## ⚠️ 如果后端虚拟环境不存在

如果看到 `uvicorn` 不存在，需要创建虚拟环境：

```bash
cd /home/deployer/telegram-ai-system/admin-backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate

# 返回项目根目录
cd /home/deployer/telegram-ai-system

# 再次运行部署脚本
bash scripts/server/quick-deploy-after-build.sh
```

---

## ✅ 修复完成后的验证

执行以下命令验证一切正常：

```bash
# 检查 PM2 服务状态
pm2 status

# 应该看到 backend 和 frontend 都是 online

# 检查端口监听
sudo ss -tlnp | grep -E "3000|8000"

# 检查服务日志
pm2 logs --lines 20
```

---

**修复完成后，继续按照部署指南进行下一步操作！**
