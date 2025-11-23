# Telegram 注册模拟模式使用指南

> **功能**: 在服务器上模拟手机注册效果，用于测试和开发  
> **状态**: ✅ 已实现

---

## 📋 功能说明

模拟模式允许您在**不调用真实 Telegram API** 的情况下测试注册流程，包括：

- ✅ 模拟发送验证码
- ✅ 模拟验证码验证
- ✅ 生成模拟的 Session 文件
- ✅ 完整的注册流程测试

---

## ⚙️ 配置方法

### 方式 1: 环境变量（推荐）

在 `.env` 文件或系统环境变量中设置：

```bash
# 启用模拟模式
TELEGRAM_REGISTRATION_MOCK_MODE=true

# 设置模拟验证码（可选，默认: 123456）
TELEGRAM_REGISTRATION_MOCK_CODE=123456
```

### 方式 2: 修改配置文件

编辑 `admin-backend/app/core/config.py`:

```python
# Telegram 注册模拟模式（可选）
telegram_registration_mock_mode: bool = Field(
    default=True,  # 改为 True 启用
    description="是否启用 Telegram 注册模拟模式"
)
telegram_registration_mock_code: str = Field(
    default="123456",  # 自定义验证码
    description="模拟模式下的验证码"
)
```

---

## 🚀 使用方法

### 1. 启用模拟模式

设置环境变量后，重启后端服务：

```bash
cd admin-backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 使用前端注册

1. 访问: http://localhost:3001/group-ai/telegram-register
2. 填写手机号（必须包含国家代码，例如: `+1234567890`）
3. 选择服务器
4. 点击"开始注册"

### 3. 输入验证码

- **模拟模式下的验证码**: `123456`（或您配置的值）
- 输入验证码后点击"验证"
- 系统会自动生成模拟的 Session 文件

---

## 📝 模拟模式特性

### ✅ 已实现的功能

1. **模拟验证码发送**
   - 不调用真实 Telegram API
   - 立即返回成功状态
   - 验证码存储在系统中

2. **模拟验证码验证**
   - 检查输入的验证码是否匹配
   - 如果错误，显示提示信息（包含正确验证码）

3. **模拟 Session 文件生成**
   - 在服务器上创建 SQLite 数据库文件
   - 文件格式与真实 Session 文件相同
   - **注意**: 这是测试文件，不能用于真实登录

4. **完整的注册流程**
   - 支持所有注册步骤
   - 记录注册日志
   - 保存注册记录到数据库

---

## ⚠️ 注意事项

1. **Session 文件无效**
   - 模拟模式生成的 Session 文件**不能用于真实登录**
   - 仅用于测试注册流程

2. **验证码固定**
   - 模拟模式下验证码是固定的（默认: `123456`）
   - 可以在配置中修改

3. **不调用真实 API**
   - 不会向 Telegram 发送任何请求
   - 不会消耗 API 配额
   - 不会触发速率限制

4. **测试环境使用**
   - 建议仅在开发和测试环境使用
   - 生产环境应禁用模拟模式

---

## 🔍 验证模拟模式

### 检查日志

启用模拟模式后，后端日志会显示：

```
[MOCK MODE] 模拟发送验证码到 +1234567890
[MOCK MODE] 模拟验证码: 123456 (仅用于测试)
[MOCK MODE] 验证码验证成功: 123456
[MOCK MODE] 创建模拟 Session 文件: /path/to/session.session
[MOCK MODE] 模拟 Session 文件已创建
```

### 检查 API 响应

注册开始后，API 响应会包含：

```json
{
  "registration_id": "...",
  "status": "code_sent",
  "message": "验证码已发送 (模拟模式，验证码: 123456)",
  "mock_mode": true,
  "mock_code": "123456",
  ...
}
```

---

## 📊 模拟模式 vs 真实模式

| 特性 | 模拟模式 | 真实模式 |
|------|---------|---------|
| API 调用 | ❌ 不调用 | ✅ 调用真实 Telegram API |
| 验证码 | 固定（可配置） | 真实验证码（通过 Telegram 发送） |
| Session 文件 | 模拟文件（无效） | 真实 Session 文件（有效） |
| 速率限制 | ❌ 不受限制 | ✅ 受 Telegram 限制 |
| 用途 | 测试/开发 | 生产环境 |

---

## 🛠️ 故障排查

### 问题 1: 模拟模式未启用

**症状**: 仍然调用真实 Telegram API

**解决**:
1. 检查环境变量是否正确设置
2. 确认后端服务已重启
3. 查看日志确认模拟模式状态

### 问题 2: 验证码不匹配

**症状**: 输入验证码后提示错误

**解决**:
1. 确认使用的是配置的模拟验证码（默认: `123456`）
2. 检查 API 响应中的 `mock_code` 字段
3. 查看后端日志确认验证码

### 问题 3: Session 文件未创建

**症状**: 注册完成但找不到 Session 文件

**解决**:
1. 检查服务器配置是否正确
2. 查看后端日志中的错误信息
3. 确认服务器有写入权限

---

## 📚 相关文件

- **配置文件**: `admin-backend/app/core/config.py`
- **服务实现**: `admin-backend/app/services/telegram_registration_service.py`
- **API 路由**: `admin-backend/app/api/telegram_registration.py`
- **前端页面**: `saas-demo/src/app/group-ai/telegram-register/page.tsx`

---

## ✅ 总结

模拟模式是一个强大的测试工具，允许您：

- ✅ 测试注册流程而不消耗真实资源
- ✅ 快速验证前端和后端集成
- ✅ 开发新功能而不受速率限制
- ✅ 安全地测试各种场景

**记住**: 模拟模式仅用于测试，生成的 Session 文件不能用于真实登录！

