# 完整文件拉取命令清单

## 问题诊断

如果找不到 `venv/bin/activate` 文件，请检查：

1. **当前目录是否正确**
2. **虚拟环境是否存在**
3. **文件路径是否正确**

## 完整拉取和设置命令

### 方法1: 使用一键部署脚本（推荐）

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/server/deploy_all_files.sh
```

### 方法2: 手动执行每个步骤

#### 步骤1: 拉取所有代码

```bash
cd /home/ubuntu/telegram-ai-system
git fetch origin
git pull origin main
```

#### 步骤2: 检查并创建虚拟环境

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3.12 -m venv venv
fi

# 验证虚拟环境
ls -la venv/bin/activate
```

#### 步骤3: 激活虚拟环境并安装依赖

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 步骤4: 验证所有脚本文件

```bash
cd /home/ubuntu/telegram-ai-system

# 检查每个脚本文件
echo "=== 检查脚本文件 ==="
ls -lh scripts/server/generate_jwt_secret.py
ls -lh scripts/server/update_security_config.py
ls -lh scripts/server/quick_fix_security.sh
ls -lh scripts/server/configure_notifications.py
ls -lh scripts/server/performance_benchmark.py
ls -lh scripts/server/system_health_check.py
ls -lh scripts/server/check_database_performance.py

# 设置执行权限
chmod +x scripts/server/*.sh
chmod +x scripts/server/*.py
```

#### 步骤5: 验证文档文件

```bash
cd /home/ubuntu/telegram-ai-system

echo "=== 检查文档文件 ==="
ls -lh docs/SECURITY_CONFIGURATION_GUIDE.md
ls -lh docs/NOTIFICATION_SETUP_GUIDE.md
ls -lh docs/TASK_COMPLETION_SUMMARY.md
ls -lh docs/DEPLOYMENT_STATUS.md
ls -lh docs/FILE_PULL_COMMANDS.md
```

## 使用脚本文件的具体命令

### 1. 配置通知渠道

```bash
# 完整路径命令
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 /home/ubuntu/telegram-ai-system/scripts/server/configure_notifications.py
```

或者使用相对路径：

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/configure_notifications.py
```

### 2. 运行性能基准测试

```bash
# 完整路径命令
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 /home/ubuntu/telegram-ai-system/scripts/server/performance_benchmark.py
```

或者使用相对路径：

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/performance_benchmark.py
```

### 3. 更新安全配置

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/update_security_config.py
```

### 4. 生成JWT密钥

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python3 ../scripts/server/generate_jwt_secret.py
```

### 5. 快速安全修复

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/server/quick_fix_security.sh
```

## 一键验证所有文件

```bash
cd /home/ubuntu/telegram-ai-system

echo "=========================================="
echo "验证所有文件"
echo "=========================================="

# 检查虚拟环境
echo ""
echo "=== 虚拟环境 ==="
if [ -f "admin-backend/venv/bin/activate" ]; then
    echo "✓ 虚拟环境存在: admin-backend/venv/bin/activate"
else
    echo "✗ 虚拟环境不存在，需要创建"
    echo "  执行: cd admin-backend && python3.12 -m venv venv"
fi

# 检查脚本文件
echo ""
echo "=== 脚本文件 ==="
SCRIPTS=(
    "scripts/server/generate_jwt_secret.py"
    "scripts/server/update_security_config.py"
    "scripts/server/quick_fix_security.sh"
    "scripts/server/configure_notifications.py"
    "scripts/server/performance_benchmark.py"
    "scripts/server/system_health_check.py"
    "scripts/server/check_database_performance.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "✓ $script"
    else
        echo "✗ $script - 缺失！"
    fi
done

# 检查文档文件
echo ""
echo "=== 文档文件 ==="
DOCS=(
    "docs/SECURITY_CONFIGURATION_GUIDE.md"
    "docs/NOTIFICATION_SETUP_GUIDE.md"
    "docs/TASK_COMPLETION_SUMMARY.md"
    "docs/DEPLOYMENT_STATUS.md"
    "docs/FILE_PULL_COMMANDS.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "✓ $doc"
    else
        echo "✗ $doc - 缺失！"
    fi
done

echo ""
echo "=========================================="
```

## 如果文件缺失的解决方案

### 方案1: 强制拉取所有文件

```bash
cd /home/ubuntu/telegram-ai-system
git fetch origin
git reset --hard origin/main
git clean -fd
```

### 方案2: 重新创建虚拟环境

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend

# 删除旧的虚拟环境（如果存在）
rm -rf venv

# 创建新的虚拟环境
python3.12 -m venv venv

# 激活并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 方案3: 使用绝对路径

如果相对路径有问题，使用绝对路径：

```bash
# 激活虚拟环境
source /home/ubuntu/telegram-ai-system/admin-backend/venv/bin/activate

# 运行脚本
python3 /home/ubuntu/telegram-ai-system/scripts/server/configure_notifications.py
python3 /home/ubuntu/telegram-ai-system/scripts/server/performance_benchmark.py
```

## 完整执行示例

```bash
# 1. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 2. 拉取最新代码
git pull origin main

# 3. 进入admin-backend目录
cd admin-backend

# 4. 检查虚拟环境
if [ ! -f "venv/bin/activate" ]; then
    echo "创建虚拟环境..."
    python3.12 -m venv venv
fi

# 5. 激活虚拟环境
source venv/bin/activate

# 6. 验证激活成功（应该显示虚拟环境路径）
which python

# 7. 运行配置通知渠道脚本
python3 ../scripts/server/configure_notifications.py

# 8. 运行性能基准测试脚本
python3 ../scripts/server/performance_benchmark.py

# 9. 退出虚拟环境
deactivate
```

## 常见错误和解决方案

### 错误1: `venv/bin/activate: No such file or directory`

**原因**: 虚拟环境不存在或路径错误

**解决**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
python3.12 -m venv venv
source venv/bin/activate
```

### 错误2: `python3: command not found`

**原因**: Python3未安装或不在PATH中

**解决**:
```bash
# 检查Python版本
python3 --version

# 如果不存在，安装Python3.12
sudo apt update
sudo apt install python3.12 python3.12-venv -y
```

### 错误3: `ModuleNotFoundError`

**原因**: 依赖未安装

**解决**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
pip install -r requirements.txt
```

### 错误4: `Permission denied`

**原因**: 文件没有执行权限

**解决**:
```bash
chmod +x scripts/server/*.sh
chmod +x scripts/server/*.py
```

---

**提示**: 如果仍然遇到问题，请运行一键验证脚本：

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/server/deploy_all_files.sh
```

