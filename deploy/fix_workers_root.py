#!/usr/bin/env python3
"""
在 /api/workers 添加根端點
"""
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 連接成功!")

# 查看 workers.py 的內容
print("\n>>> 查看 workers.py")
stdin, stdout, stderr = client.exec_command("cat /home/ubuntu/liaotian/admin-backend/app/api/workers.py | head -60")
print(stdout.read().decode())

# 修改 workers.py 添加根端點
print("\n>>> 添加 / 端點到 workers.py")

# 需要添加一個 GET / 端點
fix_cmd = '''
cd /home/ubuntu/liaotian/admin-backend

# 檢查是否已經有 @router.get("/") 
if ! grep -q '@router.get("/")' app/api/workers.py && ! grep -q "@router.get('/')" app/api/workers.py; then
    # 在 heartbeat 端點之前添加
    python3 << 'PYEOF'
import re

with open("app/api/workers.py", "r") as f:
    content = f.read()

# 找到 router = APIRouter 之後的位置添加
new_endpoint = '''

# 內存中的 Worker 狀態存儲
_workers_store = {}

@router.get("/")
async def list_workers():
    """列出所有 Worker 節點"""
    from datetime import datetime, timedelta
    
    # 過濾掉超過 5 分鐘沒有心跳的節點
    now = datetime.now()
    active_workers = []
    
    for computer_id, worker_data in list(_workers_store.items()):
        last_hb = worker_data.get("last_heartbeat")
        if last_hb:
            if isinstance(last_hb, str):
                try:
                    last_hb = datetime.fromisoformat(last_hb.replace("Z", "+00:00").replace("+00:00", ""))
                except:
                    last_hb = datetime.now()
            if (now - last_hb).total_seconds() > 300:  # 5 分鐘超時
                worker_data["status"] = "offline"
        active_workers.append({
            "computer_id": computer_id,
            **worker_data
        })
    
    return {"workers": active_workers}

def update_worker_store(computer_id: str, data: dict):
    """更新 Worker 存儲"""
    from datetime import datetime
    if computer_id not in _workers_store:
        _workers_store[computer_id] = {}
    _workers_store[computer_id].update(data)
    _workers_store[computer_id]["last_heartbeat"] = datetime.now().isoformat()

'''

# 在 router = APIRouter 之後插入
pattern = r'(router\s*=\s*APIRouter\([^)]*\))'
if re.search(pattern, content):
    content = re.sub(pattern, r'\\1' + new_endpoint, content)
    with open("app/api/workers.py", "w") as f:
        f.write(content)
    print("已添加 / 端點")
else:
    print("未找到 router 定義")
PYEOF
else
    echo "/ 端點已存在"
fi

# 修改 heartbeat 端點以更新存儲
grep -q "update_worker_store" app/api/workers.py || echo "需要修改 heartbeat 來調用 update_worker_store"
'''

stdin, stdout, stderr = client.exec_command(fix_cmd)
print(stdout.read().decode())
print(stderr.read().decode())

# 查看修改後的內容
print("\n>>> 修改後的 workers.py（前 80 行）")
stdin, stdout, stderr = client.exec_command("head -80 /home/ubuntu/liaotian/admin-backend/app/api/workers.py")
print(stdout.read().decode())

# 重啟後端
print("\n>>> 重啟後端")
stdin, stdout, stderr = client.exec_command("sudo systemctl restart liaotian-backend && sleep 3")
stdout.channel.recv_exit_status()

# 測試
print("\n>>> 測試 /api/workers/")
stdin, stdout, stderr = client.exec_command("curl -s http://localhost:8000/api/workers/ | head -c 300")
print(stdout.read().decode())

client.close()

