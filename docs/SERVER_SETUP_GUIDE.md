# 服务器设置指南

> **问题**: 在服务器上找不到项目目录或脚本文件

---

## 🔍 问题诊断

如果遇到以下错误：
- `fatal: not a git repository`
- `No such file or directory`

说明当前不在正确的项目目录中。

---

## ✅ 解决方案

### 方法 1: 查找现有项目目录

```bash
# 查找项目目录
find /home/ubuntu -name ".git" -type d 2>/dev/null | head -n 5

# 或者检查常见位置
ls -la /home/ubuntu/telegram-ai-system 2>/dev/null
```

### 方法 2: 如果项目不存在，克隆项目

```bash
# 1. 进入用户目录
cd /home/ubuntu

# 2. 克隆项目（如果还没有）
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system

# 3. 进入项目目录
cd telegram-ai-system

# 4. 检查项目结构
ls -la

# 5. 检查脚本是否存在
ls -la scripts/server/
```

### 方法 3: 如果项目已存在但路径不同

```bash
# 1. 查找项目目录
cd /home/ubuntu
find . -name "admin-backend" -type d 2>/dev/null | head -n 1

# 2. 根据找到的路径进入项目根目录
# 例如：如果找到 /home/ubuntu/some-path/admin-backend
# 则项目根目录是 /home/ubuntu/some-path
cd /path/to/project/root

# 3. 验证是 git 仓库
git status
```

---

## 🚀 快速设置脚本

将以下内容保存为 `setup.sh` 并在服务器上运行：

```bash
#!/bin/bash
# 快速设置脚本

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 检查项目是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "项目不存在，开始克隆..."
    cd /home/ubuntu
    git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
fi

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

# 拉取最新代码
echo "拉取最新代码..."
git pull origin main

# 检查脚本
if [ -f "scripts/server/verify_deployment.sh" ]; then
    echo "✓ 验证脚本存在"
    bash scripts/server/verify_deployment.sh
else
    echo "✗ 验证脚本不存在，请检查项目结构"
fi
```

**使用方法**:
```bash
# 在服务器上创建并运行
cat > /tmp/setup.sh << 'EOF'
#!/bin/bash
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
if [ ! -d "$PROJECT_DIR" ]; then
    cd /home/ubuntu
    git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
fi
cd "$PROJECT_DIR" || exit 1
git pull origin main
bash scripts/server/verify_deployment.sh
EOF

chmod +x /tmp/setup.sh
bash /tmp/setup.sh
```

---

## 📋 验证步骤

### 1. 确认项目目录

```bash
# 应该看到项目文件
cd /home/ubuntu/telegram-ai-system
ls -la

# 应该看到以下目录：
# - admin-backend/
# - saas-demo/
# - scripts/
# - docs/
```

### 2. 确认 Git 仓库

```bash
# 应该能执行 git 命令
git status
git remote -v
```

### 3. 确认脚本存在

```bash
# 检查脚本文件
ls -la scripts/server/

# 应该看到：
# - verify_deployment.sh
# - check_security.sh
# - quick_health_check.sh
```

### 4. 执行验证

```bash
# 运行验证脚本
bash scripts/server/verify_deployment.sh
```

---

## 🔧 常见问题

### 问题 1: 项目目录不存在

**解决方案**:
```bash
cd /home/ubuntu
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
cd telegram-ai-system
```

### 问题 2: 项目存在但不在标准位置

**解决方案**:
```bash
# 查找项目
find /home/ubuntu -name "admin-backend" -type d

# 进入找到的目录的父目录
cd /path/to/found/directory/..
```

### 问题 3: Git 远程配置错误

**解决方案**:
```bash
# 检查远程配置
git remote -v

# 如果错误，更新远程 URL
git remote set-url origin https://github.com/victor2025PH/liaotianai1201.git

# 拉取代码
git pull origin main
```

### 问题 4: 权限问题

**解决方案**:
```bash
# 确保脚本有执行权限
chmod +x scripts/server/*.sh

# 如果无法执行，使用 bash 直接运行
bash scripts/server/verify_deployment.sh
```

---

## 📝 完整设置流程

```bash
# 1. 进入用户目录
cd /home/ubuntu

# 2. 克隆或更新项目
if [ -d "telegram-ai-system" ]; then
    cd telegram-ai-system
    git pull origin main
else
    git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
    cd telegram-ai-system
fi

# 3. 验证项目结构
ls -la
ls -la scripts/server/

# 4. 运行验证
bash scripts/server/verify_deployment.sh
```

---

**最后更新**: 2025-12-09

