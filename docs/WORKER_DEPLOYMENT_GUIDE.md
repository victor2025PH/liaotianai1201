# Worker 节点部署完整指南

## 功能概述

Worker 节点部署功能允许您：
1. **在部署包生成页面输入电脑名字（节点ID）**
2. **下载部署包到每台电脑**
3. **每台电脑保存各自的 session 文件和 API 凭证（Excel 配置）**
4. **服务器自动调用和管理所有节点**
5. **进行一键聊天等操作**

## 部署流程

### 步骤 1: 生成部署包

1. 访问 **Worker 部署** 页面：`https://aikz.usdt2026.cc/group-ai/worker-deploy`
2. 填写配置信息：
   - **节点 ID**：给这台电脑起个名字，如 `pc-001`、`pc-002`、`office-pc-1` 等
   - **服务器地址**：`https://aikz.usdt2026.cc`（默认已填写）
   - **API 密钥**：可选，留空则不使用认证
   - **心跳间隔**：30 秒（默认）
   - **Telegram API ID/Hash**：可选，如果填写，会作为默认值；建议在 Excel 中为每个账号单独配置
3. 点击 **生成部署包**
4. 点击 **下载 ZIP**

### 步骤 2: 在每台电脑上部署

#### 2.1 解压部署包

```bash
# 解压下载的 ZIP 文件
unzip worker-deploy-pc-002.zip
cd worker-deploy-pc-002
```

#### 2.2 准备 Session 文件

将 Telegram `.session` 文件放入 `sessions` 目录：

```
sessions/
  ├── 639277358115.session
  ├── 639454959591.session
  └── 639950375245.session
```

**重要**：Session 文件名必须与 Excel 配置中的 `phone` 列匹配。

#### 2.3 创建 Excel 配置文件

运行脚本创建 Excel 模板：

```bash
# Windows
python create_excel_template.py

# Linux/Mac
python3 create_excel_template.py
```

这会创建 `sessions/{节点ID}.xlsx` 文件，例如 `sessions/pc-002.xlsx`。

#### 2.4 编辑 Excel 配置文件

打开 Excel 文件，填写每个账号的信息：

| api_id | api_hash | phone | username | name | user_id | friends | groups | group | remark | node | enabled | last_update |
|--------|----------|-------|----------|------|---------|---------|--------|-------|---------|------|---------|-------------|
| 30390800 | 471481f784... | 639277358115 | | | | | | Group A | Main | pc-002 | 1 | |
| 34593653 | d6f998b5b1... | 639454959591 | | | | | | Group B | Backup | pc-002 | 1 | |
| 33590305 | 62bc570473... | 639950375245 | | | | | | Group A | Test | pc-002 | 1 | |

**必需列**：
- `api_id`: Telegram API ID（从 my.telegram.org 获取）
- `api_hash`: Telegram API Hash（从 my.telegram.org 获取）
- `phone`: 电话号码（**必须与 session 文件名匹配**）
- `enabled`: 1=启用，0=禁用

**自动填充列**（Worker 运行后会自动填充）：
- `username`: 用户名
- `name`: 昵称
- `user_id`: Telegram 数字 ID
- `friends`: 好友数量
- `groups`: 群组数量
- `last_update`: 最后更新时间

**管理列**（可选）：
- `group`: 分组名称
- `remark`: 备注
- `node`: 指定节点（通常与节点 ID 相同）

#### 2.5 修复 Session 文件（如果需要）

如果遇到 Session 文件读取错误，运行修复脚本：

```bash
# Windows
python fix_session.py sessions

# Linux/Mac
python3 fix_session.py sessions
```

这会自动修复：
- 添加缺失的 `server_address` 列
- 添加缺失的 `port` 列
- 创建缺失的 `version` 表

#### 2.6 启动 Worker 节点

**Windows**：
```bash
# 双击运行
start_worker.bat

# 或在命令行运行
start_worker.bat
```

**Linux/Mac**：
```bash
chmod +x start_worker.sh
./start_worker.sh
```

启动脚本会自动：
1. 检查 Python 环境
2. 安装依赖（requests, httpx, openpyxl, telethon）
3. 修复 Session 文件（如果需要）
4. 创建 Excel 模板（如果不存在）
5. 启动 Worker 节点

### 步骤 3: 验证部署

#### 3.1 检查 Worker 节点日志

启动后，应该看到：

```
========================================
  WORKER NODE STARTING
========================================
  Node ID:    pc-002
  Server:     https://aikz.usdt2026.cc
  Sessions:   ./sessions
  Heartbeat:  30s

  Telethon:   YES
  API ID:     SET
  API Hash:   SET
  openpyxl:   YES
========================================

[EXCEL] Loading: pc-002.xlsx
[EXCEL] Columns found: ['api_id', 'api_hash', 'phone']
[EXCEL] Loaded 3 accounts from Excel

[INIT] Scanning sessions folder...
[SCAN] Found 3 session files
[SCAN] Matched Excel: 639277358115 -> 639277358115

[INIT] Fetching account details via Telethon...
[TELETHON] Got user: id=123456789, @username, phone=639277358115

========================================
  ACCOUNTS SUMMARY (3 total)
========================================
#   Telegram ID     Username            Phone          Name
------------------------------------------------------------
1   123456789       @username           639277358115   John Doe
2   987654321       @user2             639454959591   Jane Smith
3   456789123       @user3             639950375245   Bob Wilson
------------------------------------------------------------
  Accounts with Telegram ID: 3/3
========================================

[WORKER] Starting heartbeat loop...

[OK] 3 accounts, 150 friends, 45 groups
```

#### 3.2 检查前端页面

1. 访问 **节点管理** 页面
2. 应该看到节点 `pc-002` 显示为 **在线**
3. **活跃账号** 应该显示账号数量（如 3）

#### 3.3 测试一键启动所有账号

1. 访问 **智能聊天** 页面
2. 点击 **一键启动所有账号**
3. 应该能够成功启动所有账号，不再出现 "账号未在 AccountManager 中" 错误

## 多电脑部署示例

### 场景：3 台电脑，每台 3 个账号

#### 电脑 1: `pc-001`
```
sessions/
  ├── pc-001.xlsx
  ├── 639277358115.session
  ├── 639454959591.session
  └── 639950375245.session
```

#### 电脑 2: `pc-002`
```
sessions/
  ├── pc-002.xlsx
  ├── 639542360349.session
  ├── 639950375245.session
  └── 639952948592.session
```

#### 电脑 3: `office-pc-1`
```
sessions/
  ├── office-pc-1.xlsx
  ├── 639121795555.session
  ├── 639641837416.session
  └── 639641842001.session
```

**每台电脑**：
1. 下载对应的部署包（节点 ID 不同）
2. 解压到独立目录
3. 放入各自的 session 文件
4. 创建并编辑各自的 Excel 配置文件
5. 启动 Worker 节点

**服务器端**：
- 自动识别所有在线节点
- 自动同步所有账号信息
- 可以统一管理和调用所有账号
- 支持一键启动所有账号

## Excel 配置详细说明

### 列名别名支持

Excel 支持多种列名格式，例如：

| 标准列名 | 支持的别名 |
|---------|-----------|
| `api_id` | `apiid`, `API_ID`, `APIID` |
| `api_hash` | `apihash`, `API_HASH`, `APIHASH` |
| `phone` | `手机`, `手機`, `电话`, `電話`, `mobile`, `tel` |
| `name` | `名字`, `昵称`, `暱稱`, `nickname`, `first_name` |
| `user_id` | `userid`, `tg_id`, `telegram_id`, `id` |
| `group` | `分组`, `分組`, `category`, `类别`, `類別` |
| `remark` | `备注`, `備註`, `note`, `notes`, `说明` |
| `enabled` | `启用`, `啟用`, `active`, `status` |

### 每个账号使用不同的 API 凭证

如果不同账号使用不同的 API ID/Hash，只需在 Excel 中为每行填写不同的值：

| api_id | api_hash | phone | enabled |
|--------|----------|-------|---------|
| 30390800 | 471481f784... | 639277358115 | 1 |
| 34593653 | d6f998b5b1... | 639454959591 | 1 |
| 33590305 | 62bc570473... | 639950375245 | 1 |

Worker 节点会自动为每个账号使用对应的 API 凭证。

## 常见问题

### Q1: Session 文件读取错误？

**A:** 运行修复脚本：
```bash
python fix_session.py sessions
```

### Q2: 无法提取 user_id？

**A:** 
1. 确保 Excel 中配置了正确的 `api_id` 和 `api_hash`
2. 确保 Telethon 已安装：`pip install telethon`
3. 确保 Session 文件有效（可以正常登录 Telegram）

### Q3: Worker 节点无法连接到服务器？

**A:** 检查：
1. 网络连接是否正常
2. 防火墙是否允许出站 HTTPS 连接（端口 443）
3. 服务器 URL 是否正确：`https://aikz.usdt2026.cc`

### Q4: 账号未在 AccountManager 中？

**A:** 
1. 确保 Worker 节点正在运行
2. 确保 Worker 节点能够发送心跳
3. 确保账号在 Excel 中标记为 `enabled=1`
4. 确保 Session 文件存在且文件名与 Excel 中的 `phone` 匹配

### Q5: 如何更新 Excel 配置？

**A:** 
1. 直接编辑 Excel 文件
2. Worker 节点会在下次心跳时重新加载配置
3. 或者重启 Worker 节点

### Q6: 如何查看账号详细信息？

**A:** Worker 节点会自动通过 Telethon 获取账号信息并更新到 Excel：
- `username`: 用户名
- `name`: 昵称
- `user_id`: Telegram 数字 ID
- `friends`: 好友数量
- `groups`: 群组数量

这些信息会在 Worker 启动后自动填充。

## 部署包文件说明

部署包包含以下文件：

- `start_worker.bat` - Windows 启动脚本
- `start_worker.sh` - Linux/Mac 启动脚本
- `worker_client.py` - Worker 节点主程序
- `fix_session.py` - Session 文件修复脚本
- `create_excel_template.py` - Excel 模板创建脚本
- `README.md` - 使用说明
- `sessions/README.txt` - Session 文件说明

## 验证清单

部署完成后，请确认：

- [ ] Worker 节点正在运行
- [ ] Worker 节点能够发送心跳（日志中显示 `[OK] X accounts`）
- [ ] 前端页面显示节点在线
- [ ] 前端页面显示活跃账号数量
- [ ] Excel 配置文件已创建并填写
- [ ] Session 文件已放入 `sessions` 目录
- [ ] Session 文件能够正确读取（无错误）
- [ ] 账号能够提取 `user_id`（日志中显示 `Accounts with Telegram ID: X/X`）
- [ ] "一键启动所有账号"功能正常工作

## 下一步

部署完成后，您可以：
1. 在 **节点管理** 页面查看所有节点状态
2. 在 **账号管理** 页面查看所有账号
3. 在 **智能聊天** 页面使用一键启动功能
4. 配置剧本、角色分配等功能
5. 开始自动化聊天

