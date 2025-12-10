# AI 账号建群聊天测试指南

## 📋 测试前准备

### 1. 检查后端服务状态

确保后端服务正常运行：

```bash
# 检查后端服务
sudo systemctl status telegram-backend

# 查看后端日志
sudo journalctl -u telegram-backend -n 50

# 检查端口
ss -tlnp | grep :8000
```

### 2. 检查账号状态

在开始测试前，需要确保：
- ✅ 至少有一个已注册的 AI 账号
- ✅ 账号的 session 文件存在且有效
- ✅ 账号状态为 `online` 或可以启动

## 🚀 测试步骤

### 方法一：通过"智能聊天"页面启动（推荐）

这是最简单的启动方式，适用于已有群组的情况：

1. **打开智能聊天页面**
   - 访问：`https://aikz.usdt2026.cc/group-ai/chat-features`
   - 或点击左侧菜单 → "智能聊天"

2. **配置聊天设置**
   - 在"基本設置"标签页中：
     - ✅ 启用"自動聊天"
     - ✅ 启用"遊戲功能"（可选）
     - ✅ 启用"劇本功能"（可选）
     - 设置"聊天間隔"（30-120秒）
     - 点击"保存設置"

3. **启动聊天**
   - 点击页面右上角的"啟動聊天"按钮
   - 系统会向所有在线节点发送启动命令
   - 等待几秒钟，查看是否显示成功提示

4. **验证启动**
   - 在 Telegram 群组中发送消息
   - 观察 AI 是否自动回复
   - 查看"數據分析"标签页的统计数据

### 方法二：通过"账号管理"页面创建群组并启动

适用于需要创建新群组的情况：

1. **打开账号管理页面**
   - 访问：`https://aikz.usdt2026.cc/group-ai/accounts`
   - 或点击左侧菜单 → "② 账号管理 步骤 2"

2. **检查账号状态**
   - 在账号列表中，找到要使用的账号
   - 检查账号状态：
     - 如果状态为 `offline`，点击"启动"按钮
     - 等待账号状态变为 `online`

3. **创建群组**
   - 在账号操作列，点击"创建群组"按钮
   - 填写群组信息：
     - **群组标题**：例如 "测试群组"
     - **群组描述**：可选
     - **自动回复**：勾选（启用自动聊天）
   - 点击"创建"
   - 系统会自动创建群组并启动群聊

4. **加入现有群组**
   - 如果已有群组，点击"加入群组"按钮
   - 输入群组 ID 或邀请链接
   - 点击"加入"
   - 然后点击"启动群聊"按钮

5. **测试群聊**
   - 在 Telegram 中打开创建的群组
   - 发送测试消息，例如："大家好"
   - 观察 AI 是否自动回复

### 方法三：通过 API 直接启动

适用于需要自动化测试的场景：

```bash
# 1. 启动账号（如果未启动）
curl -X POST "http://localhost:8000/api/v1/group-ai/accounts/{account_id}/start" \
  -H "Authorization: Bearer {token}"

# 2. 创建群组并启动群聊
curl -X POST "http://localhost:8000/api/v1/group-ai/groups/create" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "your_account_id",
    "title": "测试群组",
    "description": "用于测试的群组",
    "auto_reply": true
  }'

# 3. 或者启动已有群组的聊天
curl -X POST "http://localhost:8000/api/v1/group-ai/groups/start-chat" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "your_account_id",
    "group_id": 123456789,
    "auto_reply": true
  }'

# 4. 通过智能聊天 API 启动（适用于所有节点）
curl -X POST "http://localhost:8000/api/v1/group-ai/chat-features/chat/start" \
  -H "Authorization: Bearer {token}"
```

## 🧪 测试检查清单

### 基础功能测试

- [ ] **账号启动**
  - [ ] 账号状态显示为 `online`
  - [ ] 账号可以正常连接 Telegram

- [ ] **群组创建/加入**
  - [ ] 群组创建成功
  - [ ] 或成功加入现有群组
  - [ ] 群组信息正确显示

- [ ] **自动聊天启动**
  - [ ] 点击"啟動聊天"后显示成功提示
  - [ ] 在群组中发送消息，AI 能够自动回复
  - [ ] 回复内容符合预期（如果有剧本）

### 高级功能测试

- [ ] **剧本功能**
  - [ ] 如果配置了剧本，AI 按照剧本回复
  - [ ] 剧本切换正常

- [ ] **游戏功能**
  - [ ] 游戏触发正常
  - [ ] 游戏响应正确

- [ ] **排程任务**
  - [ ] 定时任务按时执行
  - [ ] 任务内容正确

- [ ] **数据分析**
  - [ ] 消息统计更新
  - [ ] 用户活跃度显示
  - [ ] 转化漏斗数据正确

## 🔍 故障排查

### 问题 1：账号无法启动

**症状**：账号状态一直显示 `offline` 或启动失败

**排查步骤**：
1. 检查 session 文件是否存在：
   ```bash
   ls -la /path/to/sessions/{account_id}.session
   ```
2. 检查后端日志：
   ```bash
   sudo journalctl -u telegram-backend -n 100 | grep {account_id}
   ```
3. 检查账号配置是否正确
4. 检查 Telegram API 密钥是否有效

### 问题 2：群组创建失败

**症状**：点击"创建群组"后显示错误

**排查步骤**：
1. 确认账号已启动（状态为 `online`）
2. 检查账号是否有创建群组的权限
3. 查看后端日志中的错误信息
4. 确认账号没有被限制创建群组

### 问题 3：AI 不自动回复

**症状**：群聊已启动，但 AI 不回复消息

**排查步骤**：
1. 检查"智能聊天"设置中"自動聊天"是否启用
2. 检查账号是否在监听该群组：
   - 在账号详情中查看 `group_ids` 配置
   - 确认群组 ID 在列表中
3. 检查后端日志，查看是否有错误
4. 测试发送消息到群组，观察日志输出

### 问题 4：API 返回 500 错误

**症状**：前端显示"服务器内部错误"

**排查步骤**：
1. 检查后端服务是否运行：
   ```bash
   sudo systemctl status telegram-backend
   ```
2. 查看后端详细错误日志：
   ```bash
   sudo journalctl -u telegram-backend -n 100 --no-pager
   ```
3. 检查数据库连接：
   ```bash
   # 如果使用 PostgreSQL
   sudo -u postgres psql -c "SELECT 1;"
   ```
4. 检查环境变量配置是否正确

## 📊 监控和验证

### 实时监控

1. **查看日志**
   ```bash
   # 后端日志
   sudo journalctl -u telegram-backend -f
   
   # Bot 日志（如果有）
   sudo journalctl -u telegram-bot -f
   ```

2. **查看统计数据**
   - 访问"智能聊天" → "數據分析"标签页
   - 查看消息统计、用户活跃度等

3. **查看群组监控**
   - 访问"群组监控"页面
   - 查看群组状态和消息记录

### 验证成功标志

✅ **启动成功**：
- 账号状态为 `online`
- 群组创建/加入成功
- 点击"啟動聊天"后显示成功提示
- 在 Telegram 群组中发送消息，AI 能够自动回复

✅ **功能正常**：
- AI 回复及时（在设置的间隔内）
- 回复内容符合预期
- 游戏功能正常（如果启用）
- 排程任务按时执行（如果启用）

## 🎯 快速测试命令

```bash
# 一键测试脚本（在服务器上执行）
#!/bin/bash

# 1. 检查服务状态
echo "检查后端服务..."
sudo systemctl status telegram-backend --no-pager | head -n 5

# 2. 检查端口
echo -e "\n检查端口..."
ss -tlnp | grep :8000

# 3. 测试健康检查
echo -e "\n测试健康检查..."
curl -s http://localhost:8000/health | jq .

# 4. 查看最近日志
echo -e "\n最近日志..."
sudo journalctl -u telegram-backend -n 20 --no-pager
```

## 📝 注意事项

1. **账号限制**：
   - 新注册的 Telegram 账号可能有创建群组的限制
   - 建议使用已使用一段时间的账号

2. **消息频率**：
   - 避免设置过高的消息频率，可能触发 Telegram 限制
   - 建议聊天间隔设置为 30-120 秒

3. **测试环境**：
   - 建议先在测试群组中验证功能
   - 确认无误后再应用到生产环境

4. **监控资源**：
   - 监控服务器 CPU 和内存使用
   - 确保有足够的资源运行多个账号

## 🔗 相关页面

- **智能聊天**：`/group-ai/chat-features`
- **账号管理**：`/group-ai/accounts`
- **群组监控**：`/group-ai/monitor`
- **日志查看**：`/group-ai/logs`
- **系统监控**：`/monitoring/system`

---

**最后更新**：2025-12-10

