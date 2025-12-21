# 代码修复工作流程

## 正确的修复流程

### 为什么不应该在服务器上直接修改代码？

1. **版本控制丢失**：服务器上的修改不会保存到 Git，下次部署会被覆盖
2. **无法追踪**：不知道谁、什么时候、为什么修改了代码
3. **协作困难**：团队成员看不到这些修改
4. **回滚困难**：如果修改有问题，难以恢复

### 正确的流程

```
本地修复 → Git 提交 → 推送到 GitHub → 服务器拉取 → 重新构建 → 重启服务
```

## 修复 Technical.tsx 的步骤

### 方法 1：使用本地修复脚本（推荐）

```bash
# 在本地（Windows/Mac）执行
bash scripts/local/fix_technical_tsx_local.sh
```

这个脚本会：
1. 查找所有 Technical.tsx 文件
2. 修复 JSX 语法错误
3. 提交到本地 Git
4. 询问是否推送到远程仓库

### 方法 2：手动修复

1. **在本地找到文件**：
   ```bash
   find . -name "Technical.tsx" -type f | grep -i hbwy
   ```

2. **编辑文件**，修复以下问题：
   ```tsx
   // 错误的写法：
   require(&lt;span className="text-yellow-400">remainingAmount > 0</span>, "Empty");
   
   // 正确的写法：
   require(`remainingAmount > 0`, "Empty");
   ```

3. **提交到 Git**：
   ```bash
   git add <文件路径>
   git commit -m "fix: 修复 Technical.tsx JSX 语法错误"
   git push origin main
   ```

4. **在服务器上拉取并重新构建**：
   ```bash
   cd /home/ubuntu/telegram-ai-system
   git pull origin main
   cd <项目目录>
   npm run build
   pm2 restart <服务名>
   ```

## 服务器端脚本的作用

服务器端的修复脚本（如 `fix_hbwy_build_and_start.sh`）应该：
- ✅ 用于**紧急情况**下的临时修复
- ✅ 用于**自动化部署**流程
- ❌ **不应该**用于常规代码修复

## 推荐的完整工作流程

### 1. 本地修复代码

```bash
# 在本地执行
bash scripts/local/fix_technical_tsx_local.sh
```

### 2. 推送到 GitHub

```bash
git push origin main
```

### 3. 在服务器上更新并部署

```bash
# 在服务器上执行
cd /home/ubuntu/telegram-ai-system
git pull origin main

# 重新构建并启动所有服务
bash scripts/server/rebuild_and_restart_all.sh
```

## 创建服务器端部署脚本

服务器端脚本应该只负责：
- 拉取最新代码
- 安装依赖
- 构建项目
- 重启服务

**不应该**修改源代码。

## 总结

- ✅ **本地修复** → 提交到 Git → 推送到 GitHub
- ✅ **服务器拉取** → 重新构建 → 重启服务
- ❌ **不要在服务器上直接修改代码**

这样可以确保：
1. 所有修改都在版本控制中
2. 团队成员可以看到修改
3. 可以轻松回滚
4. 符合最佳实践
