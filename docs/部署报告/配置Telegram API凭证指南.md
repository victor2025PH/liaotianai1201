# 配置 Telegram API 凭证指南

生成时间: 2025-01-23

## 🎯 当前状态

- ✅ 本地服务已启动
- ✅ 远程服务器已部署
- ❌ 需要配置 Telegram API 凭证才能启动 `main.py`

## 📝 获取 Telegram API 凭证

### 步骤 1: 访问 Telegram 开发者平台

1. 打开浏览器，访问：**https://my.telegram.org**
2. 使用您的手机号码登录
3. 输入验证码（会发送到您的 Telegram 应用）

### 步骤 2: 进入 API 开发工具

1. 登录后，点击 **"API development tools"**
2. 如果还没有创建应用，点击 **"Create a new application"**
3. 填写应用信息：
   - **App title**: 应用名称（例如：My Bot）
   - **Short name**: 简短名称（例如：mybot）
   - **Platform**: 选择 "Other"
   - **Description**: 应用描述（可选）

### 步骤 3: 获取凭证

创建应用后，您会看到：
- **api_id**: 一个数字（例如：12345678）
- **api_hash**: 一个字符串（例如：abcdef1234567890abcdef1234567890）

⚠️ **重要**: 请妥善保管这些凭证，不要泄露给他人。

## 🚀 配置方法

### 方法 1: 使用快速设置脚本（推荐）

在 Cursor 终端中运行：

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\quick_setup.ps1
```

脚本会提示您输入：
1. **TELEGRAM_API_ID**: 输入从 my.telegram.org 获取的数字 ID
2. **TELEGRAM_API_HASH**: 输入从 my.telegram.org 获取的 Hash 字符串
3. **TELEGRAM_SESSION_NAME**: 输入 Session 名称（例如：my_bot）
4. **OPENAI_API_KEY**: OpenAI API Key（可选，直接回车跳过）

配置完成后，脚本会自动：
- 创建 `.env` 文件
- 同步配置到所有远程服务器
- 启动远程服务器的 `main.py`

### 方法 2: 手动创建 .env 文件

1. 在项目根目录创建 `.env` 文件
2. 复制以下内容并填入您的凭证：

```env
# Telegram API 配置
TELEGRAM_API_ID=你的api_id
TELEGRAM_API_HASH=你的api_hash
TELEGRAM_SESSION_NAME=你的session名称

# OpenAI API 配置（可选）
OPENAI_API_KEY=你的openai_key
```

3. 保存文件后，运行同步脚本：

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\sync_env_to_remote.ps1
pwsh -ExecutionPolicy Bypass -File scripts\fix_and_start_remote_main.ps1 -StartMain
```

## ✅ 验证配置

配置完成后，运行测试脚本验证：

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\test_remote_sessions.ps1 -Detailed
```

您应该看到：
- ✅ `main.py` 正在运行
- ✅ 日志文件显示 Telegram 连接成功
- ✅ 没有环境变量错误

## 🔧 故障排查

### 问题 1: 无法访问 my.telegram.org

**解决方案**:
- 检查网络连接
- 尝试使用 VPN
- 确保可以访问 Telegram 服务

### 问题 2: 无法接收验证码

**解决方案**:
- 确保手机号码正确
- 检查 Telegram 应用是否收到验证码
- 尝试重新发送验证码

### 问题 3: API ID 或 Hash 无效

**解决方案**:
- 确保从 my.telegram.org 正确复制
- 检查是否有空格或特殊字符
- 重新创建应用获取新凭证

### 问题 4: main.py 仍然无法启动

**解决方案**:
1. 检查 `.env` 文件是否正确创建
2. 验证远程服务器的 `.env` 文件：
   ```powershell
   # 通过 SSH 检查
   ssh ubuntu@服务器IP "cat /home/ubuntu/.env | grep TELEGRAM"
   ```
3. 查看错误日志：
   ```powershell
   ssh ubuntu@服务器IP "tail -50 /home/ubuntu/logs/main.log"
   ```

## 📚 相关脚本

- `scripts/quick_setup.ps1` - 快速设置（推荐）
- `scripts/configure_telegram_api.ps1` - 交互式配置
- `scripts/sync_env_to_remote.ps1` - 同步环境变量
- `scripts/fix_and_start_remote_main.ps1` - 启动远程 main.py
- `scripts/test_remote_sessions.ps1` - 测试 Session 文件

## ⚠️ 安全提示

1. **不要提交 .env 文件到 Git**
   - 确保 `.env` 在 `.gitignore` 中
   - 只提交 `docs/env.example` 作为模板

2. **保护 API 凭证**
   - 不要分享给他人
   - 不要在公开场合显示
   - 定期更换（如发现泄露）

3. **使用环境变量**
   - 生产环境建议使用环境变量而非文件
   - 使用密钥管理服务（如 AWS Secrets Manager）

## 🎉 完成后的下一步

配置完成后，您可以：

1. **测试自动回复功能**
   - 在 Telegram 群组中发送消息
   - 检查日志查看回复记录

2. **监控服务状态**
   - 定期运行测试脚本
   - 查看日志文件

3. **部署更多 Session**
   - 上传有效的 Session 文件
   - 配置多个账号

