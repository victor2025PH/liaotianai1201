# 真实 Telegram 账号注册指南

> **功能**: 使用真实的 Telegram API 注册真实的 Telegram 账号  
> **状态**: ✅ 已支持

---

## 📋 功能说明

系统完全支持使用**真实的 Telegram API** 注册**真实的 Telegram 账号**。当模拟模式关闭时，系统会：

- ✅ 调用真实的 Telegram API
- ✅ 发送真实的验证码到手机
- ✅ 验证真实的验证码
- ✅ 生成真实有效的 Session 文件
- ✅ 可以用于真实登录和使用

---

## ⚙️ 前提条件

### 1. 获取 Telegram API 凭证

在开始之前，您需要：

1. 访问 https://my.telegram.org/apps
2. 使用您的 Telegram 账号登录
3. 创建新应用或使用现有应用
4. 获取以下信息：
   - **API ID**: 数字（例如: `12345678`）
   - **API Hash**: 字符串（例如: `abcdef1234567890abcdef1234567890`）

### 2. 准备手机号

- 必须是**真实有效的手机号**
- 必须包含**国家代码**（例如: `+8613800138000`）
- 手机必须能够接收短信验证码

### 3. 确保模拟模式已关闭

确保以下配置为 `False`：

```bash
# 环境变量
TELEGRAM_REGISTRATION_MOCK_MODE=false

# 或配置文件
telegram_registration_mock_mode: bool = False
```

---

## 🚀 使用步骤

### 步骤 1: 访问注册页面

1. 打开浏览器，访问: http://localhost:3001/group-ai/telegram-register
2. 确保已登录系统

### 步骤 2: 填写注册信息

#### 2.1 手机号
- **格式**: 必须包含国家代码
- **示例**:
  - 中国: `+8613800138000`
  - 美国: `+1234567890`
  - 英国: `+441234567890`

#### 2.2 API 凭证
- **API ID**: 从 https://my.telegram.org/apps 获取的数字
- **API Hash**: 从 https://my.telegram.org/apps 获取的字符串

#### 2.3 服务器选择
- 选择一个可用的服务器节点
- 系统会在该服务器上执行注册流程

#### 2.4 Session 名称（可选）
- 如果不填写，系统会自动生成
- 格式: 手机号（去除特殊字符）

#### 2.5 代理设置（可选）
- 如果需要使用代理，勾选"使用代理"
- 填写代理地址，格式:
  - `socks5://127.0.0.1:1080`
  - `http://user:pass@proxy.com:8080`

### 步骤 3: 开始注册

1. 点击"开始注册"按钮
2. 系统会：
   - 验证输入信息
   - 进行风险评估
   - 在服务器上调用 Telegram API
   - 发送验证码到您的手机

### 步骤 4: 接收验证码

1. **查看手机短信**
   - Telegram 会发送验证码到您的手机
   - 验证码通常是 5 位数字
   - 格式: `Telegram code is 12345`

2. **验证码有效期**
   - 通常为 5 分钟
   - 页面会显示倒计时

### 步骤 5: 输入验证码

1. 在页面输入收到的验证码
2. 点击"验证"按钮
3. 系统会：
   - 验证验证码
   - 创建 Session 文件
   - 完成注册

### 步骤 6: 两步验证（如果启用）

如果您的账号启用了两步验证（2FA）：

1. 系统会提示输入密码
2. 输入您的两步验证密码
3. 完成注册

---

## 📝 注册流程详解

### 真实 API 调用流程

```
1. 用户填写信息
   ↓
2. 后端验证信息
   ↓
3. 风险评估
   ↓
4. 在服务器上执行脚本
   ↓
5. 调用 Telegram API (send_code)
   ↓
6. Telegram 发送验证码到手机
   ↓
7. 用户输入验证码
   ↓
8. 调用 Telegram API (sign_in)
   ↓
9. 如果需要，调用 check_password
   ↓
10. 生成 Session 文件
   ↓
11. 注册完成
```

### 服务器端执行

系统会在您选择的服务器上执行以下操作：

1. **创建 Pyrogram Client**
   ```python
   client = Client(
       session_name,
       api_id=API_ID,
       api_hash=API_HASH,
       workdir="/home/ubuntu/sessions",
       proxy=proxy  # 如果使用代理
   )
   ```

2. **发送验证码**
   ```python
   sent_code = await client.send_code(phone)
   ```

3. **验证并登录**
   ```python
   await client.sign_in(phone, phone_code_hash, code)
   # 如果需要两步验证
   await client.check_password(password)
   ```

4. **生成 Session 文件**
   - 文件位置: `/home/ubuntu/sessions/{session_name}.session`
   - 格式: SQLite 数据库
   - 包含: 认证密钥、用户信息等

---

## ⚠️ 注意事项

### 1. API 凭证安全

- **不要**在公共场合分享您的 API ID 和 API Hash
- **不要**将 API 凭证提交到代码仓库
- 建议为每个应用创建独立的 API 凭证

### 2. 速率限制

Telegram 对 API 调用有速率限制：

- **发送验证码**: 每个手机号每天有限制
- **验证码验证**: 有重试次数限制
- 如果触发限制，需要等待指定时间

### 3. 手机号限制

- 每个手机号只能注册一个 Telegram 账号
- 如果手机号已被使用，需要先注销旧账号
- 被封禁的手机号无法注册

### 4. 网络要求

- 服务器需要能够访问 Telegram API
- 如果服务器在受限地区，建议使用代理
- 代理必须是稳定可用的

### 5. Session 文件安全

- Session 文件包含认证信息
- **不要**分享 Session 文件
- **不要**在多个地方同时使用同一个 Session
- 定期备份 Session 文件

---

## 🔍 常见问题

### Q1: 验证码收不到怎么办？

**可能原因**:
1. 手机号格式错误
2. 手机号已被使用
3. 网络问题
4. Telegram 服务异常

**解决方法**:
1. 检查手机号格式（必须包含国家代码）
2. 确认手机号未被使用
3. 检查服务器网络连接
4. 等待一段时间后重试

### Q2: 验证码错误怎么办？

**可能原因**:
1. 输入错误
2. 验证码已过期
3. 验证码已被使用

**解决方法**:
1. 仔细检查输入的验证码
2. 重新开始注册流程
3. 等待新的验证码

### Q3: 提示"手机号已被封禁"怎么办？

**可能原因**:
1. 手机号之前被滥用
2. 频繁注册导致封禁

**解决方法**:
1. 使用其他手机号
2. 联系 Telegram 支持
3. 等待一段时间后重试

### Q4: 提示"触发速率限制"怎么办？

**可能原因**:
1. 短时间内多次请求
2. 同一 IP 地址请求过多

**解决方法**:
1. 等待指定时间（系统会显示等待时间）
2. 使用不同的服务器节点
3. 使用代理分散请求

### Q5: Session 文件在哪里？

**位置**:
- 服务器: `/home/ubuntu/sessions/{session_name}.session`
- 可以通过 SSH 访问服务器查看

**下载**:
- 可以通过后端 API 下载
- 或使用 SFTP 工具下载

---

## 📊 真实模式 vs 模拟模式

| 特性 | 真实模式 | 模拟模式 |
|------|---------|---------|
| API 调用 | ✅ 调用真实 Telegram API | ❌ 不调用 |
| 验证码 | ✅ 真实验证码（手机接收） | ❌ 固定验证码 |
| Session 文件 | ✅ 真实有效 | ❌ 仅测试用 |
| 账号 | ✅ 真实 Telegram 账号 | ❌ 无效 |
| 用途 | ✅ 生产环境 | ❌ 仅测试 |

---

## 🛠️ 故障排查

### 问题 1: 无法连接到 Telegram API

**症状**: 提示网络错误或超时

**解决**:
1. 检查服务器网络连接
2. 检查防火墙设置
3. 尝试使用代理
4. 检查 Telegram API 状态

### 问题 2: API 凭证错误

**症状**: 提示 API ID 或 API Hash 错误

**解决**:
1. 确认 API ID 和 API Hash 正确
2. 从 https://my.telegram.org/apps 重新获取
3. 检查是否有空格或特殊字符

### 问题 3: Session 文件未生成

**症状**: 注册成功但找不到 Session 文件

**解决**:
1. 检查服务器目录权限
2. 查看后端日志
3. 确认服务器配置正确

---

## 📚 相关文件

- **服务实现**: `admin-backend/app/services/telegram_registration_service.py`
- **API 路由**: `admin-backend/app/api/telegram_registration.py`
- **前端页面**: `saas-demo/src/app/group-ai/telegram-register/page.tsx`
- **配置文件**: `admin-backend/app/core/config.py`

---

## ✅ 总结

使用真实 API 注册 Telegram 账号的步骤：

1. ✅ 获取 API 凭证（API ID 和 API Hash）
2. ✅ 准备真实手机号（包含国家代码）
3. ✅ 确保模拟模式已关闭
4. ✅ 填写注册信息
5. ✅ 接收并输入验证码
6. ✅ 完成注册，获得真实 Session 文件

**重要**: 真实模式会调用真实的 Telegram API，注册的账号是真实有效的，可以正常使用！

