# 服务器测试指南 (Server Test Guide)

> **重要**: 这些命令需要在 **远程 Ubuntu 服务器** 上执行

---

## 🚀 快速开始

### 后端测试

#### 方法 1: 使用测试脚本（推荐）

```bash
# SSH 到服务器
ssh ubuntu@165.154.233.55

# 运行后端测试
cd /home/ubuntu/telegram-ai-system
bash scripts/server/run-backend-tests.sh
```

#### 方法 2: 手动运行

```bash
# SSH 到服务器
ssh ubuntu@165.154.233.55

# 进入后端目录
cd /home/ubuntu/telegram-ai-system/admin-backend

# 激活虚拟环境
source venv/bin/activate

# 安装 pytest（如果未安装）
pip install pytest pytest-asyncio pytest-cov

# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_core_config.py -v

# 运行特定测试类
pytest tests/test_core_config.py::TestSettings -v
```

---

### 前端 E2E 测试

#### 方法 1: 使用测试脚本（推荐）

```bash
# SSH 到服务器
ssh ubuntu@165.154.233.55

# 运行前端 E2E 测试
cd /home/ubuntu/telegram-ai-system
bash scripts/server/run-frontend-tests.sh
```

#### 方法 2: 手动运行

```bash
# SSH 到服务器
ssh ubuntu@165.154.233.55

# 进入前端目录
cd /home/ubuntu/telegram-ai-system/saas-demo

# 安装依赖（如果未安装）
npm install

# 安装 Playwright 浏览器（如果未安装）
npx playwright install chromium

# 运行 E2E 测试
npm run test:e2e

# 使用 UI 模式（推荐用于调试）
npm run test:e2e:ui
```

---

## ⚠️ 常见错误和解决方案

### 错误 1: `command not found: pytest`

**原因**: pytest 未安装

**解决方案**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
pip install pytest pytest-asyncio pytest-cov
```

### 错误 2: `No such file or directory: saas-demo`

**原因**: 路径不正确或目录不存在

**解决方案**:
```bash
# 检查项目结构
cd /home/ubuntu/telegram-ai-system
ls -la

# 确认 saas-demo 目录存在
ls -la saas-demo
```

### 错误 3: 尝试运行 Windows 批处理文件（`.bat`）

**原因**: 在 Linux 服务器上运行了 Windows 脚本

**解决方案**: 
- ❌ **不要使用**: `scripts\local\run-backend-tests.bat`（Windows 脚本）
- ✅ **使用**: `bash scripts/server/run-backend-tests.sh`（Linux 脚本）

### 错误 4: 虚拟环境未激活

**原因**: 未激活 Python 虚拟环境

**解决方案**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate  # Linux/Mac
# 注意: 不要使用 venv\Scripts\activate.bat（这是 Windows 命令）
```

---

## 📋 测试脚本说明

### 后端测试脚本 (`scripts/server/run-backend-tests.sh`)

**功能**:
- ✅ 检查虚拟环境是否存在
- ✅ 激活虚拟环境
- ✅ 检查并安装 pytest（如需要）
- ✅ 运行所有后端测试
- ✅ 显示详细的测试结果

**使用方法**:
```bash
bash scripts/server/run-backend-tests.sh
```

### 前端 E2E 测试脚本 (`scripts/server/run-frontend-tests.sh`)

**功能**:
- ✅ 检查并安装 npm 依赖（如需要）
- ✅ 检查并安装 Playwright（如需要）
- ✅ 检查前端服务是否运行
- ✅ 运行所有 E2E 测试

**使用方法**:
```bash
bash scripts/server/run-frontend-tests.sh
```

---

## 🔍 测试结果分析

### 后端测试

**查看测试报告**:
```bash
# 运行测试并生成覆盖率报告
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
pytest tests/ -v --cov=app --cov-report=html

# 查看 HTML 报告（需要将报告下载到本地）
# 或使用文本报告
pytest tests/ -v --cov=app --cov-report=term
```

### 前端 E2E 测试

**查看测试报告**:
```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 运行测试
npm run test:e2e

# 查看 HTML 报告
npx playwright show-report
```

---

## 📊 测试统计

### 后端测试

- **测试文件数量**: 60+ 个
- **测试用例数量**: 1288 个
- **测试类型**: 单元测试、集成测试、API 测试、性能测试

### 前端 E2E 测试

- **测试文件数量**: 10 个
- **测试用例数量**: 120 个
- **测试类型**: E2E 测试（端到端测试）

---

## 🎯 下一步

1. **运行测试**: 使用提供的脚本运行测试
2. **分析结果**: 查看测试报告，找出失败的测试
3. **修复问题**: 修复失败的测试用例
4. **提高覆盖率**: 添加缺失的测试用例

---

## 📝 注意事项

1. **环境差异**: 
   - Windows 脚本（`.bat`）只能在 Windows 上运行
   - Linux 脚本（`.sh`）只能在 Linux/Mac 上运行
   - 在服务器上必须使用 Linux 脚本

2. **路径分隔符**:
   - Windows: `\`（反斜杠）
   - Linux/Mac: `/`（正斜杠）

3. **虚拟环境激活**:
   - Windows: `venv\Scripts\activate.bat`
   - Linux/Mac: `source venv/bin/activate`

---

**最后更新**: 2025-01-XX

