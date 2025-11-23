# Cursor 规则文件说明

## 📋 规则文件列表

本目录包含 Cursor IDE 的规则文件，用于指导 AI 助手的行为。

### 必须遵守的规则

1. **`always-run-in-cursor-terminal.mdc`** - ⚠️ **最重要**
   - **AI 助手在执行任何启动服务的命令之前，必须先读取此文件**
   - 规定所有服务必须在 Cursor 集成终端中运行
   - 禁止使用 `Start-Process` 创建外部窗口

### 其他规则文件

2. **`progress-report-agent.mdc`** - 进度报告生成规则
3. **`express-type-only-auto.mdc`** - TypeScript 类型规则
4. **`indexing-scope-always.mdc`** - 代码索引范围规则

## 🔍 如何确保规则生效

### 对于 AI 助手

在执行任何可能违反规则的操作之前：
1. ✅ 使用 `read_file` 工具读取相关规则文件
2. ✅ 检查命令是否符合规则
3. ✅ 使用 `scripts/check_service_rules.ps1` 验证命令

### 对于用户

如果发现 AI 助手违反规则：
1. 提醒 AI 助手读取规则文件
2. 运行 `.\scripts\check_service_rules.ps1 -CheckRunningServices` 检查
3. 查看 `.cursor/commands.json` 中的配置

## 📝 规则文件格式

规则文件使用 Markdown 格式 (`.mdc`)，包含：
- 规则说明
- 允许的操作
- 禁止的操作
- AI 助手使用指南

## 🔧 检查脚本

使用 `scripts/check_service_rules.ps1` 可以：
- 检查命令是否符合规则
- 检查正在运行的服务是否在 Cursor 终端中
- 验证端口占用情况

```powershell
# 检查运行中的服务
.\scripts\check_service_rules.ps1 -CheckRunningServices

# 检查命令
.\scripts\check_service_rules.ps1 -CommandToCheck "Start-Process powershell ..."
```

