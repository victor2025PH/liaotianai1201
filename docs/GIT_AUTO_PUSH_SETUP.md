# Git 自动推送设置指南

**功能**: 每次提交后自动推送到 GitHub，无需手动执行 `git push`

---

## 🚀 快速启用（推荐）

### 在本地 Windows 环境

```powershell
cd d:\telegram-ai-system
bash scripts/setup_auto_push.sh
```

或者直接执行（PowerShell）：

```powershell
cd d:\telegram-ai-system
$hookFile = ".git\hooks\post-commit"
@"
#!/bin/bash
# Git post-commit hook - 自动推送到远程仓库
CURRENT_BRANCH=`$(git rev-parse --abbrev-ref HEAD)
if [ "`$CURRENT_BRANCH" = "main" ]; then
    echo ""
    echo "🚀 自动推送到 GitHub..."
    git push origin main 2>&1 && echo "✅ 自动推送成功！" || echo "⚠️  自动推送失败，请手动执行: git push origin main"
    echo ""
fi
exit 0
"@ | Out-File -FilePath $hookFile -Encoding UTF8 -NoNewline
```

### 在服务器 Linux 环境

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/setup_auto_push.sh
```

---

## ✅ 启用后的效果

启用后，每次执行 `git commit` 后：

1. ✅ 自动执行 `git push origin main`
2. ✅ 推送成功会显示确认消息
3. ✅ 推送失败会显示警告（可能需要认证）
4. ✅ 只在 `main` 分支上触发

---

## 📋 工作原理

### Git Hook 机制

- **Hook 位置**: `.git/hooks/post-commit`
- **触发时机**: 每次 `git commit` 成功后
- **执行内容**: 自动运行 `git push origin main`

### 示例流程

```bash
# 1. 修改文件
echo "test" > test.txt

# 2. 添加并提交
git add test.txt
git commit -m "添加测试文件"

# 3. 自动推送（无需手动执行）
# 🚀 自动推送到 GitHub...
# ✅ 自动推送成功！
```

---

## ⚙️ 配置说明

### Hook 文件内容

```bash
#!/bin/bash
# Git post-commit hook - 自动推送到远程仓库
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
    echo ""
    echo "🚀 自动推送到 GitHub..."
    git push origin main 2>&1
    echo ""
fi

exit 0
```

### 特点

- ✅ 只在 `main` 分支上触发
- ✅ 推送失败不会中断流程
- ✅ 显示清晰的反馈信息

---

## 🔧 手动启用（高级）

如果需要自定义 Hook 内容：

```bash
# 编辑 Hook 文件
nano .git/hooks/post-commit

# 添加执行权限
chmod +x .git/hooks/post-commit
```

---

## ⚠️ 注意事项

### 推送失败的情况

自动推送可能失败的原因：
1. **需要认证**: GitHub 需要用户名和 Personal Access Token
2. **网络问题**: 网络连接不稳定
3. **权限问题**: 没有推送权限

**解决方法**:
- 如果推送失败，可以稍后手动执行: `git push origin main`
- 配置 GitHub 认证（参考 `docs/GIT_PUSH_CONFIGURATION.md`）

### 禁用自动推送

如果不需要自动推送功能：

```bash
# 删除 Hook 文件
rm .git/hooks/post-commit

# 或备份后删除
mv .git/hooks/post-commit .git/hooks/post-commit.bak
```

---

## 🔍 验证配置

### 检查 Hook 是否已启用

```bash
# 检查文件是否存在
ls -la .git/hooks/post-commit

# 检查文件内容
cat .git/hooks/post-commit

# 检查文件权限（应该有执行权限）
ls -l .git/hooks/post-commit
```

### 测试自动推送

```bash
# 创建一个测试提交
echo "test" > test.txt
git add test.txt
git commit -m "测试自动推送"

# 应该看到自动推送的输出
```

---

## 📝 相关文档

- `docs/GIT_PUSH_CONFIGURATION.md` - Git 推送认证配置
- `scripts/setup_auto_push.sh` - 自动推送配置脚本

---

**最后更新**: 2025-12-24  
**状态**: ✅ 配置脚本已创建

