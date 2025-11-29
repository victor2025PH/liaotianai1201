# E2E 测试运行说明

## ⚠️ 重要提示

**E2E 测试需要在 `saas-demo` 目录中运行！**

## 🚀 快速开始

### 1. 切换到正确的目录

```powershell
cd saas-demo
```

### 2. 运行测试

```powershell
npm run test:e2e
```

## 📋 完整步骤

### 步骤 1: 进入 saas-demo 目录

```powershell
cd "e:\002-工作文件\重要程序\聊天AI群聊程序\saas-demo"
```

### 步骤 2: 检查并安装依赖（如需要）

```powershell
# 如果 node_modules 不存在，先安装依赖
npm install
```

### 步骤 3: 安装 Playwright 浏览器（如需要）

```powershell
npx playwright install chromium
```

### 步骤 4: 运行测试

```powershell
# 方式 1: 使用 npm 脚本（推荐）
npm run test:e2e

# 方式 2: 使用 UI 模式（调试用）
npm run test:e2e:ui

# 方式 3: 使用批处理文件（Windows）
运行E2E测试.bat
```

## 🔍 常见错误

### 错误 1: 找不到 package.json

**错误信息**:
```
npm error enoent Could not read package.json
```

**原因**: 在错误的目录中运行命令

**解决**: 切换到 `saas-demo` 目录

```powershell
cd saas-demo
```

### 错误 2: 找不到模块

**错误信息**:
```
Error: Cannot find module 'xxx.js'
```

**原因**: 脚本文件不在当前目录

**解决**: 确保在 `saas-demo` 目录中运行

### 错误 3: Playwright 未安装

**错误信息**: Playwright 相关错误

**解决**: 
```powershell
cd saas-demo
npm install
npx playwright install chromium
```

## 📁 目录结构

```
聊天AI群聊程序/
├── saas-demo/              ← 前端项目，在这里运行 E2E 测试
│   ├── package.json
│   ├── e2e/                ← 测试文件目录
│   │   ├── *.spec.ts
│   ├── playwright.config.ts
│   └── ...
├── admin-backend/          ← 后端项目
└── ...
```

## ✅ 验证是否正确

运行前检查：

```powershell
# 1. 确认目录
pwd
# 应该显示: ...\saas-demo

# 2. 检查文件
Test-Path package.json
# 应该返回: True

# 3. 检查测试文件
Get-ChildItem e2e\*.spec.ts
# 应该列出 10 个测试文件
```

## 🎯 快速命令

### Windows PowerShell

```powershell
# 进入目录并运行测试
cd saas-demo; npm run test:e2e

# 或者使用批处理文件
cd saas-demo; .\运行E2E测试.bat
```

## 📚 更多信息

详细说明请查看：
- `saas-demo/E2E测试运行说明.md`
- `saas-demo/E2E测试运行指南.md`
