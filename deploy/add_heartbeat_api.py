#!/usr/bin/env python3
"""
添加心跳 API 端點到主控服務器
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
    
    stdin, stdout, stderr = client.exec_command(command, timeout=120)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        for line in output.strip().split('\n')[-15:]:
            print(f"  {line}")
    if error and exit_code != 0:
        print(f"  錯誤: {error[:500]}")
    
    return exit_code == 0, output

def add_heartbeat_api():
    """添加心跳 API"""
    client = None
    try:
        client = create_ssh_client()
        
        print("\n" + "="*60)
        print("添加心跳 API 端點")
        print("="*60)
        
        # 創建心跳 API 文件
        heartbeat_code = '''
"""
Worker 節點心跳 API
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Worker Heartbeat"])

# 存儲 Worker 節點狀態
worker_nodes: Dict[str, Dict[str, Any]] = {}

class HeartbeatRequest(BaseModel):
    """心跳請求"""
    node_id: str
    node_name: Optional[str] = None
    accounts: Optional[List[str]] = None
    accounts_online: Optional[int] = 0
    total_messages: Optional[int] = 0
    status: Optional[str] = "online"
    version: Optional[str] = None

class HeartbeatResponse(BaseModel):
    """心跳響應"""
    success: bool
    message: str
    server_time: str
    node_id: str

class WorkerStatusResponse(BaseModel):
    """Worker 節點狀態響應"""
    node_id: str
    node_name: Optional[str]
    last_heartbeat: str
    accounts_online: int
    total_messages: int
    status: str

@router.post("/heartbeat", response_model=HeartbeatResponse)
async def receive_heartbeat(request: HeartbeatRequest):
    """
    接收 Worker 節點心跳
    """
    try:
        now = datetime.now()
        
        # 更新或創建節點狀態
        worker_nodes[request.node_id] = {
            "node_id": request.node_id,
            "node_name": request.node_name,
            "accounts": request.accounts or [],
            "accounts_online": request.accounts_online,
            "total_messages": request.total_messages,
            "status": request.status,
            "version": request.version,
            "last_heartbeat": now.isoformat()
        }
        
        logger.info(f"收到心跳: node_id={request.node_id}, accounts={request.accounts_online}")
        
        return HeartbeatResponse(
            success=True,
            message="Heartbeat received",
            server_time=now.isoformat(),
            node_id=request.node_id
        )
    except Exception as e:
        logger.error(f"處理心跳失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/workers", response_model=List[WorkerStatusResponse])
async def get_workers():
    """
    獲取所有 Worker 節點狀態
    """
    result = []
    for node_id, node_data in worker_nodes.items():
        result.append(WorkerStatusResponse(
            node_id=node_data["node_id"],
            node_name=node_data.get("node_name"),
            last_heartbeat=node_data["last_heartbeat"],
            accounts_online=node_data.get("accounts_online", 0),
            total_messages=node_data.get("total_messages", 0),
            status=node_data.get("status", "unknown")
        ))
    return result

@router.get("/workers/{node_id}")
async def get_worker(node_id: str):
    """
    獲取指定 Worker 節點狀態
    """
    if node_id not in worker_nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker node {node_id} not found"
        )
    return worker_nodes[node_id]
'''
        
        # 寫入心跳 API 文件
        run_command(client, f"""
cat > {PROJECT_DIR}/admin-backend/app/api/group_ai/heartbeat.py << 'HEARTBEAT_EOF'
{heartbeat_code}
HEARTBEAT_EOF
""", "創建心跳 API 文件")
        
        # 更新 __init__.py 以包含心跳路由
        run_command(client, f"""
cd {PROJECT_DIR}/admin-backend/app/api/group_ai

# 在 __init__.py 中導入 heartbeat 模組
if ! grep -q "from app.api.group_ai import heartbeat" __init__.py; then
    # 在導入部分添加 heartbeat
    sed -i '/from app.api.group_ai import accounts/a from app.api.group_ai import heartbeat' __init__.py
fi

# 在路由注冊部分添加 heartbeat 路由
if ! grep -q "heartbeat.router" __init__.py; then
    # 在 accounts.router 注冊之後添加 heartbeat 路由
    cat >> __init__.py << 'ROUTE_EOF'

# 心跳 API（無需認證）
router.include_router(
    heartbeat.router,
    prefix="/monitor",
    tags=["worker-heartbeat"],
)
ROUTE_EOF
fi

echo "已更新 __init__.py"
""", "更新路由配置")
        
        # 重啟後端服務
        run_command(client, """
sudo systemctl restart liaotian-backend
sleep 3
sudo systemctl status liaotian-backend --no-pager | head -10
""", "重啟後端服務")
        
        # 測試心跳端點
        run_command(client, """
curl -s -X POST http://localhost:8000/api/v1/group-ai/monitor/heartbeat \\
    -H "Content-Type: application/json" \\
    -d '{"node_id": "test_node", "accounts_online": 3}'
""", "測試心跳端點")
        
        print("\n" + "="*60)
        print("✅ 心跳 API 已添加")
        print("="*60)
        print(f"""
Worker 節點需要更新配置：

主控服務器地址: http://aikz.usdt2026.cc
心跳端點: POST /api/v1/group-ai/monitor/heartbeat

心跳請求格式:
{{
    "node_id": "computer_002",
    "node_name": "Worker Node 2",
    "accounts": ["account1", "account2"],
    "accounts_online": 3,
    "total_messages": 100,
    "status": "online"
}}
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
    success = add_heartbeat_api()
    sys.exit(0 if success else 1)

