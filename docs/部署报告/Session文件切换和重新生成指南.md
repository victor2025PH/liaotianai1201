# Session 文件切换和重新生成指南

生成时间: 2025-01-23

## 📊 当前状态

### ✅ 已完成
1. **API 凭证已更新**
   - API_ID: 24782266
   - API_HASH: 48ccfcd14b237d4f6753c122f6a798606
   - 所有服务器已配置

2. **找到多个 Session 文件**
   - 洛杉矶: 5 个 Session 文件
   - 马尼拉: 5 个 Session 文件
   - worker-01: 2 个 Session 文件

3. **已创建工具脚本**
   - `scripts/try_all_sessions.ps1` - 尝试所有 Session 文件
   - `scripts/generate_new_session.ps1` - 重新生成 Session 文件

### ⚠️ 当前问题
所有现有的 Session 文件都无效，Pyrogram 仍在尝试交互式输入（"Enter phone number or bot token"）。

**可能的原因：**
- Session 文件已过期
- Session 文件与当前的 API_ID 和 API_HASH 不匹配
- Session 文件格式不正确

## 🔧 解决方案

### 方案 1: 重新生成 Session 文件（推荐）

#### 步骤 1: 准备生成脚本
运行以下命令在服务器上创建生成脚本：
```powershell
pwsh -ExecutionPolicy Bypass -File scripts\generate_new_session.ps1
```

#### 步骤 2: 使用交互式 SSH 连接
由于 Session 生成需要交互式输入（手机号、验证码），需要使用支持交互的 SSH 客户端：

**Windows:**
- PuTTY
- MobaXterm
- Windows Terminal (支持交互式 SSH)

**连接命令:**
```bash
ssh ubuntu@165.154.255.48    # 洛杉矶
ssh ubuntu@165.154.233.179   # 马尼拉
ssh ubuntu@165.154.254.99    # worker-01
```

**密码:**
- 洛杉矶/马尼拉: `8iDcGrYb52Fxpzee`
- worker-01: `Along2025!!!`

#### 步骤 3: 在服务器上执行生成脚本
```bash
cd /home/ubuntu
python3 scripts/generate_session.py
```

#### 步骤 4: 按提示输入
1. 输入手机号码（带国家代码，如 +1234567890）
2. 输入 Session 名称（默认: my_session）
3. 输入验证码（Telegram 会发送到手机）
4. 如果启用了两步验证，输入密码

#### 步骤 5: 验证生成结果
生成成功后，Session 文件会保存在 `/home/ubuntu/sessions/` 目录下。

### 方案 2: 使用本地工具生成 Session

如果服务器上无法交互式输入，可以在本地生成 Session 文件，然后上传到服务器：

1. **在本地运行生成脚本:**
   ```bash
   python3 scripts/login.py
   ```

2. **上传 Session 文件到服务器:**
   ```powershell
   # 使用 SCP 上传
   scp sessions/my_session.session ubuntu@165.154.255.48:/home/ubuntu/sessions/
   ```

3. **在服务器上启动服务:**
   ```powershell
   pwsh -ExecutionPolicy Bypass -File scripts\try_all_sessions.ps1
   ```

## 📝 使用说明

### 尝试所有 Session 文件
如果服务器上已有多个 Session 文件，可以运行：
```powershell
pwsh -ExecutionPolicy Bypass -File scripts\try_all_sessions.ps1
```

脚本会：
1. 查找所有 Session 文件
2. 逐个尝试启动服务
3. 验证 Session 是否有效
4. 如果找到有效的 Session，自动使用它

### 手动指定 Session 文件
如果需要手动指定 Session 文件，可以设置环境变量：
```bash
export TELEGRAM_SESSION_FILE='/home/ubuntu/sessions/my_session.session'
export TELEGRAM_SESSION_NAME='my_session'
```

## 🎯 下一步操作

1. **重新生成 Session 文件**
   - 使用交互式 SSH 连接
   - 执行生成脚本
   - 输入手机号和验证码

2. **验证 Session 文件**
   - 检查文件是否生成成功
   - 确认文件大小 > 1KB

3. **启动服务**
   - 运行 `try_all_sessions.ps1` 尝试所有 Session
   - 或手动指定 Session 文件启动

4. **测试自动回复**
   - 在 Telegram 群组中发送消息
   - 验证机器人是否自动回复

## 📚 相关文件

- `scripts/try_all_sessions.ps1` - 尝试所有 Session 文件
- `scripts/generate_new_session.ps1` - 准备生成脚本
- `scripts/generate_session.py` - Session 生成脚本（在服务器上）
- `scripts/login.py` - 本地登录脚本

## ⚠️ 注意事项

1. **Session 文件安全**
   - Session 文件包含认证信息，请妥善保管
   - 不要将 Session 文件提交到版本控制系统

2. **API 凭证配对**
   - 确保 Session 文件与正确的 API_ID 和 API_HASH 配对
   - 当前使用的 API_ID: 24782266

3. **多账号管理**
   - 每个账号需要独立的 Session 文件
   - 建议使用有意义的 Session 名称（如：account_1, account_2）

4. **Session 有效期**
   - Session 文件可能会过期
   - 如果服务无法启动，可能需要重新生成 Session

