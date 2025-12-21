# 修复权限问题指南

## 问题分析

从错误日志可以看到两个问题：

### 1. 权限问题 (EACCES)

**错误信息：**
```
npm error code EACCES
npm error syscall mkdir
Error: EACCES: permission denied, mkdir '/home/ubuntu/telegram-ai-system/aizkw20251219/node_modules/@esbuild/aix-ppc64'
```

**原因：**
- `node_modules` 目录或父目录的权限不正确
- 文件可能是用 `root` 用户创建的，导致 `ubuntu` 用户无法写入

### 2. 路径问题

**错误信息：**
```
-bash: cd: hbwy20251220: No such file or directory
-bash: cd: tgmini20251220: No such file or directory
bash: scripts/server/build_and_start_all.sh: No such file or directory
```

**原因：**
- 在 `aizkw20251219` 目录下执行命令，需要先返回父目录

---

## 解决方案

### 方法 1：使用修复脚本（推荐）

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/fix_permissions_and_build.sh
```

这个脚本会：
1. 修复所有项目的文件权限
2. 安装依赖（使用正确的用户）
3. 构建所有项目
4. 启动服务

### 方法 2：手动修复

#### 步骤 1：修复权限

```bash
cd /home/ubuntu/telegram-ai-system

# 修复项目根目录权限
sudo chown -R ubuntu:ubuntu /home/ubuntu/telegram-ai-system

# 修复三个项目的权限
sudo chown -R ubuntu:ubuntu aizkw20251219
sudo chown -R ubuntu:ubuntu hbwy20251220
sudo chown -R ubuntu:ubuntu tgmini20251220

# 确保有写权限
sudo chmod -R u+w aizkw20251219
sudo chmod -R u+w hbwy20251220
sudo chmod -R u+w tgmini20251220
```

#### 步骤 2：安装依赖（使用 ubuntu 用户）

```bash
# 确保在项目根目录
cd /home/ubuntu/telegram-ai-system

# 安装 aizkw 依赖
cd aizkw20251219
sudo -u ubuntu npm install
cd ..

# 安装 hongbao 依赖
cd hbwy20251220
sudo -u ubuntu npm install
cd ..

# 安装 tgmini 依赖
cd tgmini20251220
sudo -u ubuntu npm install
cd ..
```

#### 步骤 3：构建项目

```bash
# 确保在项目根目录
cd /home/ubuntu/telegram-ai-system

# 构建 aizkw
cd aizkw20251219
sudo -u ubuntu npm run build
cd ..

# 构建 hongbao
cd hbwy20251220
sudo -u ubuntu npm run build
cd ..

# 构建 tgmini
cd tgmini20251220
sudo -u ubuntu npm run build
cd ..
```

#### 步骤 4：启动服务

```bash
# 确保在项目根目录
cd /home/ubuntu/telegram-ai-system

# 启动所有服务
sudo bash scripts/server/build_and_start_all.sh
```

---

## 为什么使用 `sudo -u ubuntu`？

- `sudo npm install` - 以 root 用户运行，可能导致权限问题
- `sudo -u ubuntu npm install` - 以 ubuntu 用户运行，权限正确

---

## 快速修复命令（一键执行）

```bash
cd /home/ubuntu/telegram-ai-system && \
sudo chown -R ubuntu:ubuntu . && \
sudo chmod -R u+w . && \
cd aizkw20251219 && sudo -u ubuntu npm install && sudo -u ubuntu npm run build && cd .. && \
cd hbwy20251220 && sudo -u ubuntu npm install && sudo -u ubuntu npm run build && cd .. && \
cd tgmini20251220 && sudo -u ubuntu npm install && sudo -u ubuntu npm run build && cd .. && \
sudo bash scripts/server/build_and_start_all.sh
```

---

## 验证修复

修复后，检查：

```bash
# 检查权限
ls -la /home/ubuntu/telegram-ai-system/aizkw20251219/node_modules | head -5

# 应该显示 ubuntu 用户拥有文件

# 检查构建输出
ls -la /home/ubuntu/telegram-ai-system/*/dist/assets/

# 应该看到 CSS 和 JS 文件
```

---

## 常见问题

### Q: 为什么不能直接用 `npm install`？

**A:** 如果文件权限不正确，`npm install` 会失败。需要先修复权限。

### Q: 为什么不能直接用 `sudo npm install`？

**A:** `sudo npm install` 会以 root 用户创建文件，导致后续操作需要 root 权限。应该使用 `sudo -u ubuntu npm install`。

### Q: 如何避免权限问题？

**A:** 
1. 确保上传文件时使用 `ubuntu` 用户
2. 如果使用 `root` 上传，上传后执行 `chown -R ubuntu:ubuntu`
3. 使用修复脚本自动处理权限
