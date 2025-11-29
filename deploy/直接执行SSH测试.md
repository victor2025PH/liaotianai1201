# 直接执行 SSH 测试 - 用户指南

## 问题说明

由于 PowerShell 输出显示问题，自动化测试无法显示输出。但所有命令都能正常执行（退出码为 0），说明 SSH 连接正常。

## 解决方案：直接执行命令

### 方法 1：在 CMD 中执行（推荐）

1. 打开 **CMD**（不是 PowerShell）
2. 执行以下命令：

```cmd
cd E:\002-工作文件\重要程序\聊天AI群聊程序\deploy
使用CMD测试SSH.bat
```

或者直接执行：

```cmd
cd E:\002-工作文件\重要程序\聊天AI群聊程序\deploy
测试SSH并保存到文件.bat
```

### 方法 2：在 PowerShell 中手动执行

在 PowerShell 中依次执行以下命令：

```powershell
# 测试 1: 基本连接
ssh ubuntu@165.154.233.55 "echo 'SSH 连接测试成功 - TEST123'"

# 测试 2: 系统信息
ssh ubuntu@165.154.233.55 "whoami"
ssh ubuntu@165.154.233.55 "hostname"

# 测试 3: Nginx 配置
ssh ubuntu@165.154.233.55 "sudo nginx -t"

# 测试 4: WebSocket 配置（关键）
ssh ubuntu@165.154.233.55 "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"

# 测试 5: 服务状态
ssh ubuntu@165.154.233.55 "sudo systemctl is-active nginx"
ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-backend"
```

### 方法 3：使用 Python 交互式模式

在 Python 交互式环境中执行：

```python
import subprocess

# 测试基本连接
result = subprocess.run(
    'ssh ubuntu@165.154.233.55 "echo TEST123"',
    shell=True,
    capture_output=True,
    text=True,
    encoding='utf-8'
)
print(f"退出码: {result.returncode}")
print(f"输出: {result.stdout}")
print(f"错误: {result.stderr}")

# 检查 WebSocket 配置
result = subprocess.run(
    'ssh ubuntu@165.154.233.55 "sudo grep -A 15 \'location /api/v1/notifications/ws\' /etc/nginx/sites-available/aikz.usdt2026.cc"',
    shell=True,
    capture_output=True,
    text=True,
    encoding='utf-8'
)
print(f"\nWebSocket 配置:")
print(result.stdout if result.stdout else "(未找到)")
```

## 关键检查点

### 1. WebSocket 配置检查

这是最重要的检查，用于确认 WebSocket 配置是否存在：

```bash
ssh ubuntu@165.154.233.55 "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
```

**预期结果**：
- 如果配置存在：应该看到完整的 `location /api/v1/notifications/ws` 配置块
- 如果配置不存在：没有任何输出或错误信息

### 2. Nginx 配置语法检查

```bash
ssh ubuntu@165.154.233.55 "sudo nginx -t"
```

**预期结果**：
- 应该看到 "syntax is ok" 和 "test is successful"

### 3. 服务状态检查

```bash
ssh ubuntu@165.154.233.55 "sudo systemctl is-active nginx"
ssh ubuntu@165.154.233.55 "sudo systemctl is-active liaotian-backend"
```

**预期结果**：
- 应该看到 "active" 或 "inactive"

## 如果 WebSocket 配置不存在

如果检查发现 WebSocket 配置不存在，执行以下修复：

```bash
# 1. 上传修复脚本
scp deploy/最终修复WebSocket-完整版.sh ubuntu@165.154.233.55:/tmp/修复WS.sh

# 2. 执行修复
ssh ubuntu@165.154.233.55 "chmod +x /tmp/修复WS.sh && sudo bash /tmp/修复WS.sh"

# 3. 验证修复
ssh ubuntu@165.154.233.55 "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
```

## 已创建的测试脚本

1. **`deploy/使用CMD测试SSH.bat`** - CMD 版本测试脚本
2. **`deploy/测试SSH并保存到文件.bat`** - 保存结果到文件的测试脚本
3. **`deploy/最终SSH测试.py`** - Python 测试脚本
4. **`deploy/使用SSH客户端测试.ps1`** - PowerShell 测试脚本

## 建议

由于自动化测试的输出显示问题，建议：

1. **使用 CMD 执行批处理文件**（最简单）
2. **手动执行关键命令**（最可靠）
3. **使用 Python 交互式模式**（适合调试）

执行后，请告诉我测试结果，特别是：
- WebSocket 配置是否存在
- Nginx 配置是否正确
- 服务是否正常运行

