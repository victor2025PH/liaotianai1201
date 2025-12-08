# 文件拉取命令指南

本文档提供所有文件的详细拉取命令，包括配置通知渠道和性能基准测试的文件。

## 快速部署（推荐）

使用一键部署脚本：

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/server/deploy_all_files.sh
```

## 手动拉取所有文件

### 步骤1: 拉取最新代码

```bash
cd /home/ubuntu/telegram-ai-system
git fetch origin
git pull origin main
```

### 步骤2: 检查并创建虚拟环境

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend

# 如果虚拟环境不存在，创建它
if [ ! -d "venv" ]; then
    python3.12 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装/更新依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 步骤3: 验证所有脚本文件

#### 安全配置相关脚本

```bash
# 检查JWT密钥生成器
ls -lh /home/ubuntu/telegram-ai-system/scripts/server/generate_jwt_secret.py

# 检查安全配置更新工具
ls -lh /home/ubuntu/telegram-ai-system/scripts/server/update_security_config.py

# 检查快速安全修复脚本
ls -lh /home/ubuntu/telegram-ai-system/scripts/server/quick_fix_security.sh

# 设置执行权限
chmod +x /home/ubuntu/telegram-ai-system/scripts/server/quick_fix_security.sh
```

#### 通知配置相关脚本

```bash
# 检查通知配置工具
ls -lh /home/ubuntu/telegram-ai-system/scripts/server/configure_notifications.py
```

#### 性能测试相关脚本

```bash
# 检查性能基准测试脚本
ls -lh /home/ubuntu/telegram-ai-system/scripts/server/performance_benchmark.py
```

#### 其他工具脚本

```bash
# 系统健康检查
ls -lh /home/ubuntu/telegram-ai-system/scripts/server/system_health_check.py

# 数据库性能检查
ls -lh /home/ubuntu/telegram-ai-system/scripts/server/check_database_performance.py
```

### 步骤4: 验证文档文件

```bash
# 安全配置指南
ls -lh /home/ubuntu/telegram-ai-system/docs/SECURITY_CONFIGURATION_GUIDE.md

# 通知配置指南
ls -lh /home/ubuntu/telegram-ai-system/docs/NOTIFICATION_SETUP_GUIDE.md

# 任务完成总结
ls -lh /home/ubuntu/telegram-ai-system/docs/TASK_COMPLETION_SUMMARY.md

# 部署状态报告
ls -lh /home/ubuntu/telegram-ai-system/docs/DEPLOYMENT_STATUS.md
```

## 完整文件列表

### 脚本文件（scripts/server/）

1. **generate_jwt_secret.py** - JWT密钥生成器
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/scripts/server/generate_jwt_secret.py
   ```

2. **update_security_config.py** - 安全配置更新工具
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/scripts/server/update_security_config.py
   ```

3. **quick_fix_security.sh** - 快速安全修复脚本
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/scripts/server/quick_fix_security.sh
   chmod +x /home/ubuntu/telegram-ai-system/scripts/server/quick_fix_security.sh
   ```

4. **configure_notifications.py** - 通知渠道配置工具 ⭐
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/scripts/server/configure_notifications.py
   ```

5. **performance_benchmark.py** - 性能基准测试脚本 ⭐
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/scripts/server/performance_benchmark.py
   ```

6. **system_health_check.py** - 系统健康检查脚本
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/scripts/server/system_health_check.py
   ```

7. **check_database_performance.py** - 数据库性能检查
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/scripts/server/check_database_performance.py
   ```

### 文档文件（docs/）

1. **SECURITY_CONFIGURATION_GUIDE.md** - 安全配置指南
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/docs/SECURITY_CONFIGURATION_GUIDE.md
   ```

2. **NOTIFICATION_SETUP_GUIDE.md** - 通知配置指南 ⭐
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/docs/NOTIFICATION_SETUP_GUIDE.md
   ```

3. **TASK_COMPLETION_SUMMARY.md** - 任务完成总结
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/docs/TASK_COMPLETION_SUMMARY.md
   ```

4. **DEPLOYMENT_STATUS.md** - 部署状态报告
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/docs/DEPLOYMENT_STATUS.md
   ```

### 配置文件

1. **ecosystem.config.js** - PM2配置文件
   ```bash
   ls -lh /home/ubuntu/telegram-ai-system/ecosystem.config.js
   ```

## 一键验证所有文件

```bash
cd /home/ubuntu/telegram-ai-system

echo "=== 检查所有脚本文件 ==="
for file in \
    scripts/server/generate_jwt_secret.py \
    scripts/server/update_security_config.py \
    scripts/server/quick_fix_security.sh \
    scripts/server/configure_notifications.py \
    scripts/server/performance_benchmark.py \
    scripts/server/system_health_check.py \
    scripts/server/check_database_performance.py
do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file - 缺失！"
    fi
done

echo ""
echo "=== 检查所有文档文件 ==="
for file in \
    docs/SECURITY_CONFIGURATION_GUIDE.md \
    docs/NOTIFICATION_SETUP_GUIDE.md \
    docs/TASK_COMPLETION_SUMMARY.md \
    docs/DEPLOYMENT_STATUS.md
do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file - 缺失！"
    fi
done

echo ""
echo "=== 检查配置文件 ==="
if [ -f "ecosystem.config.js" ]; then
    echo "✓ ecosystem.config.js"
else
    echo "✗ ecosystem.config.js - 缺失！"
fi
```

## 使用脚本文件

### 配置通知渠道

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/configure_notifications.py
```

### 运行性能基准测试

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/performance_benchmark.py
```

### 更新安全配置

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/update_security_config.py
```

## 如果文件缺失

如果某些文件缺失，执行以下命令强制拉取：

```bash
cd /home/ubuntu/telegram-ai-system

# 强制拉取所有文件
git fetch origin
git reset --hard origin/main

# 重新检查
bash scripts/server/deploy_all_files.sh
```

## 故障排查

### 问题1: 虚拟环境不存在

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题2: 文件权限问题

```bash
cd /home/ubuntu/telegram-ai-system
chmod +x scripts/server/*.sh
chmod +x scripts/server/*.py
```

### 问题3: Git拉取失败

```bash
cd /home/ubuntu/telegram-ai-system
git fetch origin
git reset --hard origin/main
git clean -fd
```

---

**注意**: ⭐ 标记的文件是用户特别要求的配置通知渠道和性能基准测试相关文件。

