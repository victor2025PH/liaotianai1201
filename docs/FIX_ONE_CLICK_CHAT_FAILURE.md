# 一键聊天失败修复指南

## 问题诊断

从日志看到两个主要问题：

1. **Session 文件错误**：
   - `no such column: server_address`
   - `no such column: version`
   - `Accounts with Telegram ID: 0/3` - 无法获取账号 ID

2. **API 路由 404 错误**：
   - `/api/v1/group-ai/chat-features/chat/start-all-accounts` 返回 404

## 修复步骤

### 步骤 1: 修复 Worker 节点 Session 文件

#### 方法 A: 使用诊断工具（推荐）

1. 在 Worker 节点电脑上，打开命令提示符
2. 进入项目目录：`cd D:\telegram-ai-system`
3. 运行诊断工具：
   ```bash
   scripts\local\diagnose-and-fix-worker.bat
   ```
4. 选择要修复的节点（pc-001 或 pc-002，或全部）
5. 工具会自动：
   - 检查 Session 文件
   - 修复缺失的列和表
   - 检查 Excel 配置
   - 验证修复结果

#### 方法 B: 手动修复

1. 进入 Worker 节点目录（如 `D:\worker-deploy-pc-001`）
2. 运行修复脚本：
   ```bash
   python fix_session.py sessions
   ```
3. 如果修复脚本不存在，使用 Python 直接修复：
   ```python
   python -c "import sqlite3; from pathlib import Path; [sqlite3.connect(str(f)).execute('CREATE TABLE IF NOT EXISTS version (version INTEGER)') or sqlite3.connect(str(f)).execute('INSERT OR IGNORE INTO version (version) VALUES (1)') or print(f'✅ 已修复 {f.name}') for f in Path('sessions').glob('*.session')]"
   ```

### 步骤 2: 验证 Session 文件修复

运行以下命令验证修复结果：

```python
python -c "import sqlite3; from pathlib import Path; [print(f'✅ {f.name}: version 表存在') if sqlite3.connect(str(f)).execute('SELECT 1 FROM version').fetchone() else print(f'❌ {f.name}: version 表缺失') for f in Path('sessions').glob('*.session')]"
```

应该看到所有 Session 文件都显示 `✅`。

### 步骤 3: 重启 Worker 节点

1. **停止当前 Worker 节点**：
   - 在运行 Worker 的命令提示符窗口按 `Ctrl+C`
   - 或关闭命令提示符窗口

2. **重新启动 Worker 节点**：
   ```bash
   start_worker.bat
   ```

3. **检查日志**：
   - 应该看到 `Accounts with Telegram ID: 3/3`（而不是 `0/3`）
   - 不应该再看到 `no such column: version` 错误

### 步骤 4: 检查后端服务

#### 4.1 检查后端服务是否运行

在服务器上运行：

```bash
sudo systemctl status luckyred-api
```

如果服务未运行，启动它：

```bash
sudo systemctl start luckyred-api
sudo systemctl enable luckyred-api
```

#### 4.2 检查 API 路由是否注册

在服务器上运行：

```bash
curl -X GET "http://localhost:8000/api/v1/group-ai/chat-features/chat/start-all-accounts" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

如果返回 404，说明路由未注册，需要重启后端服务。

#### 4.3 重启后端服务

```bash
sudo systemctl restart luckyred-api
```

等待 10-20 秒后，检查服务状态：

```bash
sudo systemctl status luckyred-api
```

### 步骤 5: 验证修复

1. **检查 Worker 节点日志**：
   - 应该看到账号成功加载
   - 应该看到 `user_id` 已提取
   - 应该看到心跳成功发送

2. **检查前端页面**：
   - 访问 **节点管理** 页面
   - 应该看到节点显示为 **在线**
   - **活跃账号** 应该显示正确的数量（如 6）

3. **测试一键启动**：
   - 访问 **智能聊天** 页面
   - 点击 **一键启动所有账号**
   - 应该能够成功启动，不再出现 404 错误

## 常见问题

### Q1: 修复后仍然无法获取 user_id？

**A:** 确保：
1. Excel 配置文件中填写了正确的 `api_id` 和 `api_hash`
2. Session 文件有效（可以正常登录 Telegram）
3. Telethon 已安装：`pip install telethon`

### Q2: 后端服务重启后仍然 404？

**A:** 检查：
1. 后端日志是否有错误：
   ```bash
   sudo journalctl -u luckyred-api -n 50
   ```
2. 路由是否正确注册：
   ```bash
   curl http://localhost:8000/docs
   ```
   打开 Swagger 文档，查找 `/api/v1/group-ai/chat-features/chat/start-all-accounts`

### Q3: Worker 节点无法连接到服务器？

**A:** 检查：
1. 网络连接是否正常
2. 防火墙是否允许出站 HTTPS（端口 443）
3. 服务器 URL 是否正确：`https://aikz.usdt2026.cc`

### Q4: 账号仍然显示"未在 AccountManager 中"？

**A:** 确保：
1. Worker 节点正在运行并发送心跳
2. 账号在 Excel 中标记为 `enabled=1`
3. Session 文件存在且文件名与 Excel 中的 `phone` 匹配
4. 账号已成功同步到数据库（检查数据库或前端账号管理页面）

## 快速修复脚本

如果上述步骤太复杂，可以使用一键修复脚本：

```bash
# 在 Worker 节点电脑上运行
cd D:\telegram-ai-system
scripts\local\diagnose-and-fix-worker.bat
```

然后重启 Worker 节点即可。

## 验证清单

修复完成后，请确认：

- [ ] Session 文件已修复（无 `no such column` 错误）
- [ ] Worker 节点能够获取 `user_id`（日志显示 `Accounts with Telegram ID: X/X`）
- [ ] Worker 节点正在发送心跳（前端显示节点在线）
- [ ] 后端服务正在运行（`systemctl status` 显示 `active`）
- [ ] API 路由可访问（不再返回 404）
- [ ] 前端页面显示活跃账号数量正确
- [ ] "一键启动所有账号"功能正常工作

## 如果问题仍然存在

1. **收集日志**：
   - Worker 节点日志（命令提示符窗口）
   - 后端服务日志：`sudo journalctl -u luckyred-api -n 100`
   - 前端浏览器控制台（F12）

2. **检查数据库**：
   ```bash
   sqlite3 /home/ubuntu/telegram-ai-system/admin-backend/data/app.db "SELECT account_id, server_id, user_id, active FROM group_ai_accounts LIMIT 10;"
   ```

3. **联系支持**：提供上述日志和错误信息

