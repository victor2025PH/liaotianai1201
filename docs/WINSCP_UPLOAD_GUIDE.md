# WinSCP 正确上传指南

## 问题分析

根据您的情况，**只有 `tgmini20251220` 有内容，其他两个文件夹上传后几乎是空的**，主要原因可能是：

### 1. WinSCP 拖拽操作的问题

**常见错误操作：**
- ❌ 直接拖拽文件夹本身（只创建空目录）
- ❌ 拖拽时选择了错误的源路径
- ❌ 上传过程中网络中断
- ❌ 权限问题导致部分文件上传失败

**正确操作：**
- ✅ 拖拽文件夹**内部的所有文件和子文件夹**
- ✅ 或者使用 WinSCP 的"同步"功能
- ✅ 或者使用命令行工具（更可靠）

---

## 方法 1：WinSCP 正确上传步骤（推荐）

### 步骤 1：打开 WinSCP 并连接到服务器

1. 打开 WinSCP
2. 新建会话：
   - **主机名**：`10-56-61-200`（或 `165.154.242.60`）
   - **用户名**：`ubuntu`
   - **协议**：SFTP
   - **端口**：22
3. 点击"登录"

### 步骤 2：上传 hongbao 项目（hbwy20251220）

**重要：不要拖拽文件夹本身，要拖拽文件夹内的内容！**

1. **左侧（本地）**：
   - 导航到：`D:\telegram-ai-system\hbwy20251220`
   - **进入文件夹内部**，看到所有文件（package.json, App.tsx, components/ 等）

2. **右侧（服务器）**：
   - 导航到：`/home/ubuntu/telegram-ai-system/hbwy20251220`
   - 如果目录不存在，先创建它

3. **选择文件**：
   - 在左侧，**全选所有文件和文件夹**（Ctrl+A）
   - 或者手动选择：
     - ✅ `package.json`
     - ✅ `vite.config.ts`
     - ✅ `tsconfig.json`
     - ✅ `index.html`
     - ✅ `App.tsx`
     - ✅ `components/` 文件夹
     - ✅ `contexts/` 文件夹
     - ✅ `src/` 文件夹
     - ❌ **不要选择** `node_modules/`（如果存在）
     - ❌ **不要选择** `dist/`（如果存在）

4. **拖拽上传**：
   - 将选中的文件和文件夹**拖拽到右侧的 `hbwy20251220` 目录中**
   - 等待上传完成（查看底部进度条）

5. **验证上传**：
   - 在右侧，检查 `hbwy20251220` 目录中是否有：
     - ✅ `package.json`
     - ✅ `components/` 文件夹
     - ✅ 其他源文件

### 步骤 3：上传 aizkw 项目（aizkw20251219）

重复步骤 2，但使用：
- **本地**：`D:\telegram-ai-system\aizkw20251219`
- **服务器**：`/home/ubuntu/telegram-ai-system/aizkw20251219`

---

## 方法 2：使用 WinSCP 同步功能（更可靠）

### 步骤 1：打开同步功能

1. 在 WinSCP 中，导航到本地项目目录
2. 点击菜单：**命令 → 同步**

### 步骤 2：配置同步

1. **本地目录**：`D:\telegram-ai-system\hbwy20251220`
2. **远程目录**：`/home/ubuntu/telegram-ai-system/hbwy20251220`
3. **同步方向**：本地 → 远程
4. **排除文件**：
   - `node_modules`
   - `dist`
   - `.git`
5. 点击"确定"

### 步骤 3：执行同步

1. WinSCP 会显示需要上传的文件列表
2. 检查列表，确保包含 `package.json` 和所有源文件
3. 点击"确定"开始同步

---

## 方法 3：使用 PowerShell 脚本（最可靠）

### 使用可靠的上传脚本

```powershell
cd D:\telegram-ai-system
.\scripts\local\upload_projects_reliable.ps1
```

按提示输入服务器 IP：`10-56-61-200`

这个脚本会：
- ✅ 自动排除 `node_modules` 和 `dist`
- ✅ 逐个文件上传（更可靠）
- ✅ 显示上传进度
- ✅ 验证上传结果

---

## 方法 4：使用 scp 命令（命令行）

### 在 PowerShell 中执行

```powershell
# 上传 hongbao
scp -r D:\telegram-ai-system\hbwy20251220\* ubuntu@10-56-61-200:/home/ubuntu/telegram-ai-system/hbwy20251220/

# 上传 aizkw
scp -r D:\telegram-ai-system\aizkw20251219\* ubuntu@10-56-61-200:/home/ubuntu/telegram-ai-system/aizkw20251219/
```

**注意**：使用 `\*` 而不是文件夹名，这样可以上传文件夹内的内容。

---

## 上传后验证

### 在服务器上执行

```bash
# 检查 hongbao
ls -la /home/ubuntu/telegram-ai-system/hbwy20251220/package.json
ls -la /home/ubuntu/telegram-ai-system/hbwy20251220/components/

# 检查 aizkw
ls -la /home/ubuntu/telegram-ai-system/aizkw20251219/package.json
ls -la /home/ubuntu/telegram-ai-system/aizkw20251219/components/

# 应该看到文件存在，而不是 "No such file or directory"
```

### 如果文件仍然缺失

1. **检查本地文件**：
   ```powershell
   # 在本地 PowerShell 中
   ls D:\telegram-ai-system\hbwy20251220\package.json
   ls D:\telegram-ai-system\aizkw20251219\package.json
   ```

2. **重新上传**：使用上述方法之一重新上传

3. **使用 tar 压缩上传**（最可靠）：
   ```powershell
   # 在本地压缩
   cd D:\telegram-ai-system
   tar -czf hbwy20251220.tar.gz -C hbwy20251220 --exclude=node_modules --exclude=dist --exclude=.git .
   
   # 上传压缩包
   scp hbwy20251220.tar.gz ubuntu@10-56-61-200:/tmp/
   
   # 在服务器上解压
   ssh ubuntu@10-56-61-200 "cd /home/ubuntu/telegram-ai-system/hbwy20251220 && tar -xzf /tmp/hbwy20251220.tar.gz && rm /tmp/hbwy20251220.tar.gz"
   ```

---

## 常见问题

### Q1: 为什么拖拽文件夹后，服务器上只有空目录？

**A:** 因为 WinSCP 拖拽文件夹时，可能只创建了目录结构，而没有上传内容。**解决方法**：进入文件夹内部，选择所有文件后再拖拽。

### Q2: 上传后为什么只有 package-lock.json？

**A:** 这可能是因为：
1. 上传过程中断，只上传了部分文件
2. 权限问题导致其他文件上传失败
3. 网络问题

**解决方法**：使用同步功能或 PowerShell 脚本重新上传。

### Q3: 如何确保所有文件都上传成功？

**A:** 
1. 使用 WinSCP 的"同步"功能（会显示差异）
2. 使用 PowerShell 脚本（会显示上传进度）
3. 上传后验证文件是否存在

---

## 推荐流程

1. **第一次上传**：使用 WinSCP 同步功能
2. **验证**：在服务器上检查 `package.json` 是否存在
3. **如果失败**：使用 PowerShell 脚本 `upload_projects_reliable.ps1`
4. **最后验证**：运行 `build_and_start_all.sh` 构建项目

---

## 上传完成后

在服务器上执行：

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
sudo bash scripts/server/build_and_start_all.sh
```

这将会：
- ✅ 安装依赖（npm install）
- ✅ 构建项目（npm run build）
- ✅ 启动服务（PM2）
- ✅ 验证端口监听
