# .gitignore 规则说明

## 📋 规则重新制定说明

**更新日期**: 2025-12-07  
**目的**: 简化规则，确保英文脚本和重要文件都能正常被Git跟踪

---

## 🎯 核心原则

1. **默认保留英文文件**: 所有英文命名的脚本和配置文件默认都会被跟踪
2. **忽略临时文件**: 只忽略临时、重复、或包含敏感信息的文件
3. **明确保留重要文件**: 使用 `!` 明确声明需要保留的文件
4. **清晰的分类**: 按文件类型和目录组织规则，便于维护

---

## 📁 规则分类

### 1. Python 相关
- `.venv/`, `venv/`, `__pycache__/` - 虚拟环境和缓存
- `*.pyc`, `*.pyo` - 编译文件
- `dist/`, `build/` - 构建输出

### 2. Node.js 相关
- `node_modules/` - 依赖包
- `.npm`, `.yarn/` - 包管理器缓存
- `.eslintcache` - ESLint 缓存

### 3. 构建输出
- `.next/`, `dist/`, `out/`, `build/` - 前端构建产物

### 4. 环境和配置
- `.env*` - 环境变量文件（包含敏感信息）
- `sessions/`, `*.session` - Session 文件（可能包含密钥）

### 5. 日志和临时文件
- `*.log` - 所有日志文件
- `*.bak`, `*.tmp` - 临时和备份文件
- `logs/`, `backup/` - 日志和备份目录

### 6. deploy 目录规则

#### ✅ 会被跟踪的文件：
- **所有英文脚本**: `fix_*.sh`, `deploy_*.sh`, `check_*.sh` 等
- **配置文件**: `docker-compose.yaml`, `*.conf` 等
- **明确保留的中文脚本**: `repo_config.sh`, `从GitHub拉取并部署.sh` 等

#### ❌ 会被忽略的文件：
- **中文修复脚本**: `*修复*.sh`, `*一键*.sh`, `*全自动*.sh` 等
- **临时文档**: `*问题*.md`, `*诊断*.md`, `*总结*.md` 等
- **临时脚本**: `SSH*.md`, `WebSocket*.md`, `API*.md` 等

#### 规则示例：

```gitignore
# 忽略所有中文修复脚本
deploy/*修复*.sh

# 但明确保留这个
!deploy/repo_config.sh

# 保留所有英文脚本（默认行为，无需声明）
# deploy/fix_and_deploy_frontend_complete.sh ✅ 会被跟踪
```

### 7. docs 目录规则

#### ✅ 会被跟踪的文件：
- 重要文档: `CI_CD流程完善完成报告-*.md`, `部署流程-完整指南.md` 等
- README 文件: `README.md` 等

#### ❌ 会被忽略的文件：
- 临时报告: `docs/部署报告/*.md`, `docs/测试报告/*.md`
- 临时笔记: `docs/开发笔记/*问题*.md`, `docs/开发笔记/*修复*.md` 等

---

## 🔍 如何验证规则

### 方法 1: 使用测试脚本（推荐）

```powershell
.\scripts\test_gitignore_rules.ps1
```

### 方法 2: 手动验证

```bash
# 检查文件是否被忽略
git check-ignore -v deploy/fix_and_deploy_frontend_complete.sh

# 如果返回空，说明文件未被忽略（会被跟踪）
# 如果返回规则，说明文件被忽略
```

### 方法 3: 查看Git状态

```bash
# 查看哪些文件会被添加
git status

# 查看被忽略的文件
git status --ignored
```

---

## 📝 添加新文件规则

### 如果需要忽略新的文件类型：

1. **找到合适的分类**（如"临时文件"）
2. **添加规则**（如 `*.temp`）
3. **测试验证**：
   ```powershell
   .\scripts\test_gitignore_rules.ps1
   ```

### 如果需要保留被忽略的文件：

使用 `!` 前缀强制包含：

```gitignore
# 忽略所有 .md 文件
*.md

# 但保留这个
!README.md
!docs/部署流程-完整指南.md
```

---

## ⚠️ 注意事项

1. **规则顺序很重要**: Git 按照从上到下的顺序匹配规则
2. **`!` 前缀**: 用于强制包含被忽略的文件，必须在忽略规则之后
3. **已跟踪的文件**: 如果文件已经被 Git 跟踪，`.gitignore` 不会自动忽略它
   - 需要先移除: `git rm --cached <file>`
4. **目录规则**: 以 `/` 结尾表示目录，如 `logs/` 会忽略整个目录

---

## 🚀 常见场景

### 场景 1: 新创建的英文部署脚本

**操作**: 无需任何操作，自动会被跟踪

```bash
# 创建文件
touch deploy/my_new_deployment.sh

# 检查状态
git status
# ✅ deploy/my_new_deployment.sh 会显示为未跟踪文件
```

### 场景 2: 需要保留的中文脚本

**操作**: 在 `.gitignore` 中使用 `!` 明确保留

```gitignore
# 在 deploy 规则中添加
!deploy/重要的中文脚本.sh
```

### 场景 3: 临时文件被意外跟踪

**操作**: 先移除跟踪，再确认规则

```bash
# 从 Git 移除但保留本地文件
git rm --cached deploy/临时脚本.sh

# 提交更改
git commit -m "Remove temporary script from Git"

# 验证规则
git check-ignore -v deploy/临时脚本.sh
```

---

## 📚 相关文档

- [Git 官方文档 - .gitignore](https://git-scm.com/docs/gitignore)
- [部署流程-完整指南.md](./部署流程-完整指南.md)
- [Git 工作流验证脚本](../scripts/verify_git_push.ps1)

---

**最后更新**: 2025-12-07
