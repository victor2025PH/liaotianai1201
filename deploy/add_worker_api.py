#!/usr/bin/env python3
"""
添加 Worker API 端點到主控服務器
"""

import paramiko
import sys

# 服務器配置
SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
PROJECT_DIR = "/home/ubuntu/liaotian"

def create_ssh_client():
    """創建 SSH 客戶端"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"正在連接服務器 {SERVER}...")
    client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("✓ SSH 連接成功!")
    return client

def run_command(client, command, description=""):
    """執行遠程命令"""
    if description:
        print(f"\n>>> {description}")
    
    stdin, stdout, stderr = client.exec_command(command, timeout=180)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        for line in output.strip().split('\n')[-15:]:
            print(f"  {line}")
    if error and exit_code != 0:
        print(f"  錯誤: {error[:500]}")
    
    return exit_code == 0, output

def add_worker_api():
    """添加 Worker API"""
    client = None
    try:
        client = create_ssh_client()
        
        print("\n" + "="*60)
        print("添加 Worker API 端點")
        print("="*60)
        
        # 創建 Worker API 文件
        worker_api_code = '''
"""
Worker 節點 API - 與遠程 Worker 節點通信
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger("WorkerAPI")

router = APIRouter(tags=["Workers"])

# 存儲 Worker 節點狀態
worker_nodes: Dict[str, Dict[str, Any]] = {}
# 存儲消息
messages_store: List[Dict[str, Any]] = []
# 存儲群組
groups_store: Dict[int, Dict[str, Any]] = {}

# ============== 請求/響應模型 ==============

class WorkerHeartbeat(BaseModel):
    """Worker 心跳請求"""
    computer_id: str
    status: str = "online"
    accounts: Optional[List[dict]] = []

class AccountStatus(BaseModel):
    """賬號狀態上報"""
    phone: str
    status: str

class MessageCreate(BaseModel):
    """消息創建"""
    chat_id: int
    chat_type: str
    sender_id: int
    content: str
    is_ai_sender: bool = False

class GroupCreate(BaseModel):
    """群組創建"""
    chat_id: int
    title: str

class GroupMemberAdd(BaseModel):
    """添加群組成員"""
    telegram_id: int
    is_ai: bool = False

# ============== API 端點 ==============

@router.post("/workers/heartbeat")
async def worker_heartbeat(data: WorkerHeartbeat):
    """接收 Worker 心跳"""
    now = datetime.now()
    
    worker_nodes[data.computer_id] = {
        "computer_id": data.computer_id,
        "status": data.status,
        "accounts": data.accounts,
        "last_heartbeat": now.isoformat(),
        "accounts_count": len(data.accounts) if data.accounts else 0
    }
    
    logger.info(f"收到心跳: {data.computer_id}, 賬號數: {len(data.accounts) if data.accounts else 0}")
    
    return {"status": "ok", "server_time": now.isoformat()}

@router.get("/workers/{computer_id}/accounts")
async def get_worker_accounts(computer_id: str):
    """獲取 Worker 應該運行的賬號列表"""
    # 這裡可以從數據庫查詢，暫時返回空列表
    return {"accounts": []}

@router.get("/workers")
async def list_workers():
    """列出所有 Worker 節點"""
    return {"workers": list(worker_nodes.values())}

@router.post("/accounts/status")
async def report_account_status(data: AccountStatus):
    """上報賬號狀態"""
    logger.info(f"賬號狀態: {data.phone} -> {data.status}")
    return {"status": "ok"}

@router.post("/messages/")
async def save_message(data: MessageCreate):
    """保存消息"""
    message = {
        "id": len(messages_store) + 1,
        "chat_id": data.chat_id,
        "chat_type": data.chat_type,
        "sender_id": data.sender_id,
        "content": data.content,
        "is_ai_sender": data.is_ai_sender,
        "created_at": datetime.now().isoformat()
    }
    messages_store.append(message)
    
    # 只保留最近 1000 條消息
    if len(messages_store) > 1000:
        messages_store.pop(0)
    
    return {"status": "ok", "message_id": message["id"]}

@router.get("/messages/context/{chat_id}/{user_id}")
async def get_chat_context(chat_id: int, user_id: int, limit: int = 20):
    """獲取對話上下文"""
    # 過濾相關消息
    context = [m for m in messages_store if m["chat_id"] == chat_id]
    return {"messages": context[-limit:]}

@router.post("/groups/")
async def register_group(data: GroupCreate):
    """註冊群組"""
    if data.chat_id in groups_store:
        raise HTTPException(status_code=400, detail="Group already exists")
    
    groups_store[data.chat_id] = {
        "chat_id": data.chat_id,
        "title": data.title,
        "members": [],
        "created_at": datetime.now().isoformat()
    }
    return {"status": "ok", "chat_id": data.chat_id}

@router.post("/groups/{chat_id}/members")
async def add_group_member(chat_id: int, data: GroupMemberAdd):
    """添加群組成員"""
    if chat_id not in groups_store:
        groups_store[chat_id] = {"chat_id": chat_id, "members": []}
    
    groups_store[chat_id]["members"].append({
        "telegram_id": data.telegram_id,
        "is_ai": data.is_ai
    })
    return {"status": "ok"}

@router.get("/groups/")
async def list_groups():
    """列出所有群組"""
    return {"groups": list(groups_store.values())}
'''
        
        # 寫入 Worker API 文件
        run_command(client, f"""
cat > {PROJECT_DIR}/admin-backend/app/api/workers.py << 'WORKER_EOF'
{worker_api_code}
WORKER_EOF
""", "創建 Worker API 文件")
        
        # 更新主路由以包含 Worker API
        run_command(client, f"""
cd {PROJECT_DIR}/admin-backend/app/api

# 檢查是否已經導入 workers
if ! grep -q "from app.api import workers" __init__.py; then
    # 在文件開頭添加導入
    sed -i '1a from app.api import workers' __init__.py
fi

# 檢查是否已經注冊路由
if ! grep -q "workers.router" __init__.py; then
    # 在文件末尾添加路由注冊
    cat >> __init__.py << 'ROUTE_EOF'

# Worker API（無需認證）
router.include_router(workers.router, prefix="", tags=["workers"])
ROUTE_EOF
fi

echo "已更新路由配置"
grep -n "workers" __init__.py || echo "workers 未找到"
""", "更新主路由")
        
        # 重啟後端服務
        run_command(client, """
sudo systemctl restart liaotian-backend
sleep 5
sudo systemctl status liaotian-backend --no-pager | head -10
""", "重啟後端服務")
        
        # 測試 Worker API
        run_command(client, """
echo "測試心跳端點..."
curl -s -X POST http://localhost:8000/api/workers/heartbeat \\
    -H "Content-Type: application/json" \\
    -d '{"computer_id": "computer_002", "status": "online", "accounts": [{"name": "test"}]}'
echo ""
echo "---"
echo "測試 workers 列表..."
curl -s http://localhost:8000/api/workers
""", "測試 Worker API")
        
        print("\n" + "="*60)
        print("✅ Worker API 已添加")
        print("="*60)
        print("""
API 端點已添加：
  - POST /api/workers/heartbeat - 接收心跳
  - GET /api/workers - 列出所有 Worker
  - GET /api/workers/{computer_id}/accounts - 獲取賬號列表
  - POST /api/accounts/status - 上報賬號狀態
  - POST /api/messages/ - 保存消息
  - GET /api/messages/context/{chat_id}/{user_id} - 獲取上下文
  - POST /api/groups/ - 註冊群組
  - POST /api/groups/{chat_id}/members - 添加成員
""")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    success = add_worker_api()
    sys.exit(0 if success else 1)

