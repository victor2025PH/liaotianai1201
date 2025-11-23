# Session 文件跨服务器部署指南

本文档说明如何将 Session 文件部署到其他服务器，并在该服务器上正常进行聊天和剧本演绎。

---

## 概述

Session 文件跨服务器部署功能允许您：

- ✅ 导出 Session 文件（支持加密和明文）
- ✅ 打包部署包（包含 Session 文件和配置模板）
- ✅ 验证 Session 文件有效性
- ✅ 在其他服务器上部署并运行

---

## 部署方式

### 方式 1: 通过 API 导出（推荐）

#### 1.1 导出单个 Session 文件

**API 端点**: `GET /api/v1/group-ai/sessions/export-session/{session_name}`

**参数**:
- `session_name`: Session 文件名（不含扩展名）
- `include_config`: 是否包含配置文件（默认: false）
- `decrypt`: 是否解密后导出（默认: false）

**示例**:

```bash
# 导出单个文件（不含配置）
curl -X GET "http://localhost:8000/api/v1/group-ai/sessions/export-session/account1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o account1.session

# 导出包含配置的部署包
curl -X GET "http://localhost:8000/api/v1/group-ai/sessions/export-session/account1?include_config=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o account1_deploy.zip
```

#### 1.2 批量导出 Session 文件

**API 端点**: `GET /api/v1/group-ai/sessions/export-sessions-batch`

**参数**:
- `session_names`: Session 文件名列表（逗号分隔）
- `include_config`: 是否包含配置文件（默认: true）
- `decrypt`: 是否解密后导出（默认: false）

**示例**:

```bash
curl -X GET "http://localhost:8000/api/v1/group-ai/sessions/export-sessions-batch?session_names=account1,account2,account3" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o sessions_batch_deploy.zip
```

#### 1.3 验证 Session 文件

**API 端点**: `GET /api/v1/group-ai/sessions/verify-session/{session_name}`

**示例**:

```bash
curl -X GET "http://localhost:8000/api/v1/group-ai/sessions/verify-session/account1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:

```json
{
  "success": true,
  "verification": {
    "session_name": "account1",
    "file_path": "/path/to/account1.session",
    "file_size": 1024,
    "is_encrypted": false,
    "readable": true,
    "valid": true,
    "permissions": "-rw-------",
    "issues": []
  }
}
```

### 方式 2: 使用部署脚本

#### 2.1 使用部署脚本

```bash
# 基本用法
./scripts/deploy_session_to_server.sh account1 server.example.com

# 指定 SSH 用户和端口
./scripts/deploy_session_to_server.sh account1 server.example.com \
  --user deploy \
  --port 2222

# 指定远程目录
./scripts/deploy_session_to_server.sh account1 server.example.com \
  --remote-dir /opt/group-ai

# 解密后部署（如果已加密）
./scripts/deploy_session_to_server.sh account1 server.example.com \
  --decrypt
```

#### 2.2 手动验证 Session 文件

```bash
# 验证 Session 文件
python3 scripts/verify_session.py account1

# 指定 Session 目录
python3 scripts/verify_session.py account1 --sessions-dir /path/to/sessions
```

---

## 部署步骤

### 步骤 1: 导出 Session 文件

#### 选项 A: 通过 API 导出（推荐）

```bash
# 导出包含配置的部署包
curl -X GET "http://localhost:8000/api/v1/group-ai/sessions/export-session/account1?include_config=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o account1_deploy.zip
```

#### 选项 B: 直接复制文件

```bash
# 如果 Session 文件未加密，可以直接复制
cp sessions/account1.session /path/to/deploy/
```

### 步骤 2: 传输到目标服务器

```bash
# 使用 SCP
scp account1_deploy.zip user@server.example.com:/opt/group-ai/

# 或使用 SFTP
sftp user@server.example.com
put account1_deploy.zip /opt/group-ai/
```

### 步骤 3: 在目标服务器上解压

```bash
# SSH 到目标服务器
ssh user@server.example.com

# 解压部署包
cd /opt/group-ai
unzip account1_deploy.zip
cd account1_deploy
```

### 步骤 4: 配置环境变量

```bash
# 复制配置模板
cp env.example .env

# 编辑配置文件
nano .env
```

**必需配置**:

```env
# Telegram API 配置（必需）
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Session 文件配置
SESSION_FILE=account1.session
SESSION_FILES_DIRECTORY=sessions

# Session 加密配置（如果 Session 文件已加密）
SESSION_ENCRYPTION_ENABLED=true
SESSION_ENCRYPTION_KEY=your_encryption_key_here

# OpenAI 配置（用于 AI 聊天）
OPENAI_API_KEY=your_openai_api_key
```

### 步骤 5: 创建 sessions 目录并放置文件

```bash
# 创建 sessions 目录
mkdir -p sessions

# 移动 Session 文件到 sessions 目录
mv account1.session sessions/
# 或如果已加密
mv account1.enc sessions/

# 设置文件权限
chmod 600 sessions/account1.*
```

### 步骤 6: 验证 Session 文件

```bash
# 验证 Session 文件
python3 scripts/verify_session.py account1

# 如果验证通过，应该看到：
# ✅ Session 文件验证通过: account1
```

### 步骤 7: 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 或使用 Poetry
poetry install
```

### 步骤 8: 启动服务

```bash
# 启动主服务
python3 main.py

# 或使用 systemd（如果已配置）
sudo systemctl start group-ai-service
```

---

## 验证清单

部署完成后，请检查以下项目：

- [ ] Session 文件已放置在 `sessions/` 目录
- [ ] 环境变量已正确配置（`.env` 文件）
- [ ] 如果 Session 文件已加密，加密密钥已配置
- [ ] Telegram API ID 和 Hash 已配置
- [ ] 文件权限已设置（600）
- [ ] 依赖已安装
- [ ] Session 文件验证通过
- [ ] 服务可以正常启动
- [ ] 可以成功连接 Telegram
- [ ] 可以接收和发送消息
- [ ] 剧本演绎功能正常

---

## 故障排查

### Session 文件无法读取

**问题**: Session 文件无法读取或解密失败

**解决方案**:

1. **检查文件权限**:
   ```bash
   ls -l sessions/account1.*
   chmod 600 sessions/account1.*
   ```

2. **检查加密配置**:
   - 如果 Session 文件已加密（.enc），确保配置了 `SESSION_ENCRYPTION_KEY`
   - 验证加密密钥是否正确

3. **检查文件完整性**:
   ```bash
   # 检查文件大小（应该 > 0）
   ls -lh sessions/account1.*
   ```

### 无法连接 Telegram

**问题**: 服务启动后无法连接 Telegram

**解决方案**:

1. **检查网络连接**:
   ```bash
   ping api.telegram.org
   ```

2. **检查 API 配置**:
   - 验证 `TELEGRAM_API_ID` 和 `TELEGRAM_API_HASH` 是否正确
   - 确保 API 凭据有效

3. **检查 Session 文件有效性**:
   ```bash
   python3 scripts/verify_session.py account1
   ```

4. **查看日志**:
   ```bash
   tail -f logs/app.log
   ```

### 加密文件无法解密

**问题**: 加密的 Session 文件无法解密

**解决方案**:

1. **检查加密密钥**:
   - 确保 `SESSION_ENCRYPTION_KEY` 与导出时使用的密钥一致
   - 如果使用密码，确保 `SESSION_ENCRYPTION_PASSWORD` 正确

2. **验证加密状态**:
   ```bash
   # 检查文件扩展名
   ls -l sessions/account1.*
   # .enc 表示已加密，.session 表示明文
   ```

3. **重新导出（如果需要）**:
   ```bash
   # 使用 --decrypt 参数导出明文版本
   curl -X GET "http://localhost:8000/api/v1/group-ai/sessions/export-session/account1?decrypt=true" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -o account1.session
   ```

### 服务无法启动

**问题**: 服务启动失败

**解决方案**:

1. **检查依赖**:
   ```bash
   pip list | grep pyrogram
   pip list | grep openai
   ```

2. **检查环境变量**:
   ```bash
   # 加载环境变量
   source .env
   # 或
   export $(cat .env | xargs)
   ```

3. **查看错误日志**:
   ```bash
   python3 main.py 2>&1 | tee error.log
   ```

---

## 安全建议

### 1. Session 文件安全

- ✅ 使用加密存储（`.enc` 文件）
- ✅ 设置安全的文件权限（600）
- ✅ 使用强加密密钥
- ✅ 定期备份 Session 文件

### 2. 传输安全

- ✅ 使用 SFTP/SCP 传输（加密传输）
- ✅ 避免通过 HTTP 传输 Session 文件
- ✅ 使用 VPN 或专用网络

### 3. 服务器安全

- ✅ 使用 SSH 密钥认证（避免密码）
- ✅ 限制 SSH 访问（IP 白名单）
- ✅ 定期更新系统和依赖
- ✅ 使用防火墙限制端口访问

---

## 多服务器部署

### 场景 1: 独立部署

每个服务器独立运行，使用各自的 Session 文件：

```
服务器 A: account1.session, account2.session
服务器 B: account3.session, account4.session
```

### 场景 2: 负载均衡

多个服务器共享相同的 Session 文件（需要同步）：

```
服务器 A: account1.session (主)
服务器 B: account1.session (从，需要同步)
```

**注意**: Session 文件不能同时在多个服务器上使用，会导致冲突。

### 场景 3: 高可用部署

使用主备模式，主服务器故障时切换到备用服务器：

```
主服务器: account1.session (运行中)
备用服务器: account1.session (待机，定期同步)
```

---

## 相关文档

- [Session 文件管理](../开发笔记/Session加密功能开发完成报告.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [Docker 部署](DOCKER_DEPLOYMENT.md)
- [Kubernetes 部署](../部署方案/k8s/README.md)

---

**文档结束**

