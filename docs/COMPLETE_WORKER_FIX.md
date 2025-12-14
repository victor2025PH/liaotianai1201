# Worker 节点完整修复方案

## 问题总结

从错误日志和截图分析，发现以下问题：

### 1. Session 文件读取错误
- `[SESSION] sessions table error: no such column: server_address`
- `[SESSION] sessions table error: no such column: version`
- `[SESSION] No user_id found for XXXXXXXXXX. session`
- `[TELETHON] Error for ... session: no such column: version`
- `Accounts with Telegram ID: 0/3` - 所有账号都无法获取 Telegram ID

### 2. API 路由 404 错误
- `POST https://aikz.usdt2026.cc/api/v1/group-ai/chat-features/chat/start-all-accounts 404 (Not Found)`
- `GET https://aikz.usdt2026.cc/api/v1/group-ai/ai-provider/providers 404 (Not Found)`

### 3. Worker 节点问题
- Worker 节点能够运行并发送心跳
- 但无法正确读取 session 文件
- 无法提取账号的 Telegram ID

## 完整修复方案

### 步骤 1: 修复 Session 文件（在 Windows Worker 节点上执行）

#### 1.1 运行修复脚本

在 Windows 电脑上，进入 Worker 节点目录：

```bash
cd D:\worker-deploy-pc-002  # 或你的 Worker 节点目录

# 运行修复脚本
python ..\telegram-ai-system\scripts\local\fix-worker-session-reader.py sessions
```

或者手动修复：

```python
# 在 Python 中执行
import sqlite3
import os
from pathlib import Path

sessions_dir = "./sessions"
for session_file in Path(sessions_dir).glob("*.session"):
    try:
        conn = sqlite3.connect(str(session_file))
        cursor = conn.cursor()
        
        # 添加缺失的列
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN server_address TEXT")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN port INTEGER")
        except:
            pass
        
        # 创建 version 表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS version (version INTEGER)
        """)
        cursor.execute("SELECT COUNT(*) FROM version")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO version (version) VALUES (1)")
        
        conn.commit()
        conn.close()
        print(f"✅ 修复成功: {session_file.name}")
    except Exception as e:
        print(f"❌ 修复失败 {session_file.name}: {e}")
```

#### 1.2 验证修复结果

```bash
# 检查 Session 文件
python -c "
import sqlite3
from pathlib import Path

for f in Path('sessions').glob('*.session'):
    conn = sqlite3.connect(str(f))
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(sessions)')
    cols = [r[1] for r in cursor.fetchall()]
    print(f'{f.name}: {cols}')
    conn.close()
"
```

### 步骤 2: 修复 Worker 节点代码（更新 session 读取逻辑）

#### 2.1 创建修复后的 Worker 节点代码

在 `worker-deploy-pc-002` 目录中，更新 `worker_client.py` 的 session 读取部分：

```python
# 在 worker_client.py 中添加以下函数

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

def read_session_file(session_path: str) -> Optional[Dict[str, Any]]:
    """
    安全读取 Session 文件，兼容不同版本的数据库架构
    
    Args:
        session_path: Session 文件路径
        
    Returns:
        包含账号信息的字典，或 None
    """
    try:
        if not os.path.exists(session_path):
            return None
        
        conn = sqlite3.connect(session_path)
        cursor = conn.cursor()
        
        account_info = {}
        
        # 读取 sessions 表（兼容不同架构）
        try:
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # 构建查询（只查询存在的列）
            select_cols = []
            if 'dc_id' in columns:
                select_cols.append('dc_id')
            if 'server_address' in columns:
                select_cols.append('server_address')
            if 'port' in columns:
                select_cols.append('port')
            if 'auth_key' in columns:
                select_cols.append('auth_key')
            
            if select_cols:
                query = f"SELECT {', '.join(select_cols)} FROM sessions LIMIT 1"
                cursor.execute(query)
                row = cursor.fetchone()
                if row:
                    for i, col in enumerate(select_cols):
                        account_info[col] = row[i]
        except Exception as e:
            logger.warning(f"读取 sessions 表失败: {e}")
        
        # 尝试从 peers 表获取 user_id
        try:
            cursor.execute("SELECT id FROM peers WHERE id > 0 LIMIT 1")
            row = cursor.fetchone()
            if row:
                account_info['user_id'] = str(row[0])
        except Exception as e:
            logger.warning(f"读取 peers 表失败: {e}")
        
        # 如果无法从数据库获取 user_id，尝试从文件名提取
        if 'user_id' not in account_info:
            filename = Path(session_path).stem
            if filename.isdigit():
                account_info['user_id'] = filename
        
        conn.close()
        return account_info if account_info else None
        
    except Exception as e:
        logger.error(f"读取 Session 文件失败 {session_path}: {e}")
        return None
```

#### 2.2 更新账号加载逻辑

在 Worker 节点的账号加载代码中，使用修复后的读取函数：

```python
def load_accounts_from_sessions(self):
    """从 Session 文件加载账号"""
    session_dir = Path("./sessions")
    accounts = []
    
    for session_file in session_dir.glob("*.session"):
        account_id = session_file.stem
        
        # 使用修复后的读取函数
        session_info = read_session_file(str(session_file))
        
        if session_info:
            account = {
                "account_id": account_id,
                "user_id": session_info.get('user_id', account_id),
                "session_file": str(session_file),
                "status": "online" if session_info.get('user_id') else "offline"
            }
            accounts.append(account)
            logger.info(f"加载账号: {account_id}, user_id: {account.get('user_id')}")
        else:
            logger.warning(f"无法读取 Session 文件: {session_file.name}")
    
    return accounts
```

### 步骤 3: 修复后端 API 路由（在服务器上执行）

#### 3.1 检查路由注册

确保 `chat_features` 路由已正确注册：

```bash
# 在服务器上检查
cd /home/ubuntu/telegram-ai-system/admin-backend
grep -r "chat_features" app/api/group_ai/__init__.py
grep -r "start-all-accounts" app/api/group_ai/chat_features.py
```

#### 3.2 验证路由路径

路由应该是：
- 定义：`/chat/start-all-accounts` (在 `chat_features.py` 中)
- 前缀：`/chat-features` (在 `__init__.py` 中)
- 完整路径：`/api/v1/group-ai/chat-features/chat/start-all-accounts`

如果路径不匹配，需要修复。

#### 3.3 重启后端服务

```bash
# 在服务器上
sudo systemctl restart luckyred-api
# 或
sudo systemctl restart liaotian-backend

# 检查服务状态
sudo systemctl status luckyred-api
```

### 步骤 4: 更新 Worker 节点并重启

#### 4.1 更新 Worker 节点代码

在 Windows 电脑上：

```bash
cd D:\worker-deploy-pc-002

# 1. 备份当前代码
copy worker_client.py worker_client.py.backup

# 2. 应用修复（手动更新代码或从 Git 拉取最新版本）
# 3. 运行 Session 文件修复脚本
python ..\telegram-ai-system\scripts\local\fix-worker-session-reader.py sessions
```

#### 4.2 重启 Worker 节点

```bash
# 停止当前 Worker
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Worker*"

# 重新启动 Worker
start_worker.bat
# 或
python worker_client.py
```

### 步骤 5: 验证修复结果

#### 5.1 检查 Session 文件

```bash
# 在 Worker 节点上
python -c "
import sqlite3
from pathlib import Path

for f in Path('sessions').glob('*.session'):
    conn = sqlite3.connect(str(f))
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute('PRAGMA table_info(sessions)')
    print(f'\n{f.name}:')
    for row in cursor.fetchall():
        print(f'  {row[1]} ({row[2]})')
    
    # 尝试读取 user_id
    try:
        cursor.execute('SELECT id FROM peers WHERE id > 0 LIMIT 1')
        row = cursor.fetchone()
        if row:
            print(f'  ✅ user_id: {row[0]}')
        else:
            print(f'  ⚠️  未找到 user_id')
    except Exception as e:
        print(f'  ❌ 读取 user_id 失败: {e}')
    
    conn.close()
"
```

#### 5.2 检查 Worker 节点日志

查看 Worker 节点是否能够：
- ✅ 正确读取 Session 文件
- ✅ 提取 user_id
- ✅ 发送心跳并上报账号列表

#### 5.3 检查后端 API

```bash
# 在服务器上测试 API
curl -X POST https://aikz.usdt2026.cc/api/v1/group-ai/chat-features/chat/start-all-accounts \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{}'
```

#### 5.4 检查前端

在前端页面：
1. 刷新页面（Ctrl+F5）
2. 检查"在线节点"是否显示 Worker 节点
3. 检查"活跃账号"是否显示账号数量
4. 点击"一键启动所有账号"，应该不再出现 404 错误

## 快速修复脚本

### Windows Worker 节点快速修复

创建 `fix_worker.bat`：

```batch
@echo off
echo ========================================
echo Worker 节点快速修复
echo ========================================

cd /d "%~dp0"

echo [1/4] 修复 Session 文件...
python ..\telegram-ai-system\scripts\local\fix-worker-session-reader.py sessions
if errorlevel 1 (
    echo ❌ Session 文件修复失败
    pause
    exit /b 1
)

echo [2/4] 停止当前 Worker 进程...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Worker*" 2>nul
timeout /t 2 /nobreak >nul

echo [3/4] 验证 Session 文件...
python -c "import sqlite3; from pathlib import Path; [print(f'{f.name}: OK') if sqlite3.connect(str(f)).execute('SELECT 1').fetchone() else None for f in Path('sessions').glob('*.session')]"

echo [4/4] 重新启动 Worker...
start_worker.bat

echo.
echo ✅ 修复完成！
echo 请检查 Worker 节点日志，确认账号已正确加载
pause
```

## 常见问题

### Q1: Session 文件修复后仍然无法读取 user_id？

**A:** 可能原因：
1. Session 文件已损坏
2. Session 文件未登录（需要重新登录）
3. Telethon 版本不兼容

解决方案：
- 尝试使用 Telethon 重新登录账号
- 检查 Session 文件是否完整（文件大小应该 > 1KB）

### Q2: API 仍然返回 404？

**A:** 检查：
1. 后端服务是否已重启
2. 路由是否正确注册（检查 `app/api/group_ai/__init__.py`）
3. Nginx 配置是否正确（如果使用反向代理）

### Q3: Worker 节点无法连接到服务器？

**A:** 检查：
1. 网络连接是否正常
2. 防火墙是否允许出站 HTTPS 连接
3. 服务器 URL 是否正确：`https://aikz.usdt2026.cc`

## 验证清单

修复后，请确认：

- [ ] Session 文件已修复（无 `server_address` 和 `version` 列错误）
- [ ] Worker 节点能够读取 Session 文件并提取 user_id
- [ ] Worker 节点能够发送心跳并上报账号列表
- [ ] 后端 API 路由可访问（无 404 错误）
- [ ] 前端能够显示在线节点和活跃账号
- [ ] "一键启动所有账号"功能正常工作

## 下一步

如果问题仍然存在，请：
1. 检查 Worker 节点日志
2. 检查后端日志：`sudo journalctl -u luckyred-api -n 100`
3. 检查前端浏览器控制台错误
4. 提供详细的错误信息以便进一步诊断

