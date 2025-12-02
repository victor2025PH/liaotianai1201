"""
Workers API - 分布式节点管理系统
用于管理本地电脑和远程服务器节点
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workers", tags=["workers"])

# 内存存储（当 Redis 不可用时使用）
_workers_memory_store: Dict[str, Dict[str, Any]] = {}
_worker_commands: Dict[str, List[Dict[str, Any]]] = {}  # 存储待执行的命令

# Redis 客户端（如果可用）
_redis_client = None
try:
    import redis
    settings = get_settings()
    if settings.redis_url:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        logger.info("Workers API: Redis 已启用")
    else:
        logger.info("Workers API: Redis 未配置，使用内存存储")
except Exception as e:
    logger.warning(f"Workers API: Redis 不可用，使用内存存储: {e}")
    _redis_client = None


# ============ 数据模型 ============

class WorkerHeartbeatRequest(BaseModel):
    """Worker 节点心跳请求"""
    node_id: str = Field(..., description="节点ID，如 computer_001, computer_002")
    status: str = Field(default="online", description="节点状态: online, offline")
    account_count: int = Field(default=0, description="账号数量")
    accounts: List[Dict[str, Any]] = Field(default_factory=list, description="账号列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class WorkerCommandRequest(BaseModel):
    """向 Worker 节点发送命令请求"""
    action: str = Field(..., description="命令动作，如 start_auto_chat, stop_auto_chat, set_config, create_group")
    params: Dict[str, Any] = Field(default_factory=dict, description="命令参数")


class WorkerBroadcastRequest(BaseModel):
    """广播命令到所有节点请求"""
    action: str = Field(..., description="命令动作")
    params: Dict[str, Any] = Field(default_factory=dict, description="命令参数")


class WorkerStatus(BaseModel):
    """Worker 节点状态"""
    node_id: str
    status: str
    account_count: int
    last_heartbeat: str
    accounts: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class WorkersListResponse(BaseModel):
    """Workers 列表响应"""
    workers: Dict[str, WorkerStatus]


# ============ 辅助函数 ============

def _get_worker_key(node_id: str) -> str:
    """获取 Worker 在 Redis 中的键"""
    return f"worker:node:{node_id}"


def _get_workers_set_key() -> str:
    """获取所有 Worker 节点集合的键"""
    return "worker:nodes:all"


def _get_commands_key(node_id: str) -> str:
    """获取节点命令队列的键"""
    return f"worker:commands:{node_id}"


def _save_worker_status(node_id: str, data: Dict[str, Any]) -> None:
    """保存 Worker 节点状态"""
    data["last_heartbeat"] = datetime.now().isoformat()
    
    if _redis_client:
        try:
            # 保存节点状态（TTL: 120秒，如果120秒内没有心跳则认为离线）
            key = _get_worker_key(node_id)
            _redis_client.setex(key, 120, json.dumps(data))
            
            # 添加到节点集合
            _redis_client.sadd(_get_workers_set_key(), node_id)
            _redis_client.expire(_get_workers_set_key(), 120)
        except Exception as e:
            logger.error(f"保存 Worker 状态到 Redis 失败: {e}")
            # 降级到内存存储
            _workers_memory_store[node_id] = data
    else:
        # 使用内存存储
        _workers_memory_store[node_id] = data


def _get_worker_status(node_id: str) -> Optional[Dict[str, Any]]:
    """获取 Worker 节点状态"""
    if _redis_client:
        try:
            key = _get_worker_key(node_id)
            data = _redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"从 Redis 获取 Worker 状态失败: {e}")
    
    # 从内存存储获取
    return _workers_memory_store.get(node_id)


def _get_all_workers() -> Dict[str, Dict[str, Any]]:
    """获取所有 Worker 节点状态"""
    workers = {}
    
    if _redis_client:
        try:
            # 获取所有节点ID
            node_ids = _redis_client.smembers(_get_workers_set_key())
            for node_id in node_ids:
                worker_data = _get_worker_status(node_id)
                if worker_data:
                    # 检查是否过期（超过120秒没有心跳）
                    last_heartbeat = datetime.fromisoformat(worker_data.get("last_heartbeat", "1970-01-01T00:00:00"))
                    if datetime.now() - last_heartbeat < timedelta(seconds=120):
                        workers[node_id] = worker_data
                    else:
                        # 节点已过期，标记为离线
                        worker_data["status"] = "offline"
                        workers[node_id] = worker_data
        except Exception as e:
            logger.error(f"从 Redis 获取所有 Workers 失败: {e}")
            workers = _workers_memory_store.copy()
    else:
        # 从内存存储获取
        workers = _workers_memory_store.copy()
        # 清理过期的节点（超过120秒没有心跳）
        now = datetime.now()
        expired_nodes = []
        for node_id, data in workers.items():
            last_heartbeat = datetime.fromisoformat(data.get("last_heartbeat", "1970-01-01T00:00:00"))
            if now - last_heartbeat >= timedelta(seconds=120):
                expired_nodes.append(node_id)
        
        for node_id in expired_nodes:
            workers[node_id]["status"] = "offline"
    
    return workers


def _add_command(node_id: str, command: Dict[str, Any]) -> None:
    """添加命令到节点命令队列"""
    if _redis_client:
        try:
            key = _get_commands_key(node_id)
            _redis_client.lpush(key, json.dumps(command))
            _redis_client.expire(key, 300)  # 命令队列TTL: 5分钟
        except Exception as e:
            logger.error(f"添加命令到 Redis 失败: {e}")
            # 降级到内存存储
            if node_id not in _worker_commands:
                _worker_commands[node_id] = []
            _worker_commands[node_id].append(command)
    else:
        # 使用内存存储
        if node_id not in _worker_commands:
            _worker_commands[node_id] = []
        _worker_commands[node_id].append(command)


def _get_commands(node_id: str) -> List[Dict[str, Any]]:
    """获取节点的待执行命令"""
    if _redis_client:
        try:
            key = _get_commands_key(node_id)
            commands = _redis_client.lrange(key, 0, -1)
            return [json.loads(cmd) for cmd in commands]
        except Exception as e:
            logger.error(f"从 Redis 获取命令失败: {e}")
            return _worker_commands.get(node_id, [])
    else:
        return _worker_commands.get(node_id, [])


def _clear_commands(node_id: str) -> None:
    """清除节点的命令队列"""
    if _redis_client:
        try:
            key = _get_commands_key(node_id)
            _redis_client.delete(key)
        except Exception as e:
            logger.error(f"清除 Redis 命令队列失败: {e}")
            if node_id in _worker_commands:
                del _worker_commands[node_id]
    else:
        if node_id in _worker_commands:
            del _worker_commands[node_id]


# ============ API 端点 ============

@router.post("/heartbeat", status_code=status.HTTP_200_OK)
async def worker_heartbeat(
    request: WorkerHeartbeatRequest,
    db: Session = Depends(get_db_session)
):
    """
    Worker 节点心跳端点
    节点应每30秒调用一次此端点来报告状态
    """
    try:
        worker_data = {
            "node_id": request.node_id,
            "status": request.status,
            "account_count": request.account_count,
            "accounts": request.accounts,
            "metadata": request.metadata or {},
            "last_heartbeat": datetime.now().isoformat()
        }
        
        _save_worker_status(request.node_id, worker_data)
        
        # 同步賬號信息到數據庫
        if request.accounts:
            try:
                from app.api.group_ai.remote_account_sync import sync_accounts_from_worker
                sync_result = sync_accounts_from_worker(
                    node_id=request.node_id,
                    accounts=request.accounts,
                    db=db
                )
                logger.info(f"從節點 {request.node_id} 同步了 {sync_result['synced_count']} 個賬號")
            except Exception as sync_error:
                logger.error(f"同步賬號信息失敗: {sync_error}", exc_info=True)
        
        # 检查是否有待执行的命令
        commands = _get_commands(request.node_id)
        
        logger.info(f"Worker {request.node_id} 心跳: {request.account_count} 账号, {len(commands)} 待执行命令")
        
        return {
            "success": True,
            "node_id": request.node_id,
            "pending_commands": commands,
            "message": "心跳已接收"
        }
    except Exception as e:
        logger.error(f"处理 Worker 心跳失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理心跳失败: {str(e)}"
        )


@router.get("/", response_model=WorkersListResponse)
async def list_workers(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    获取所有 Worker 节点状态列表
    注意：如果禁用认证（DISABLE_AUTH=true），则允许匿名访问
    """
    # 如果禁用认证，current_user 可能为 None，这是允许的
    """
    获取所有 Worker 节点状态列表
    """
    try:
        workers_data = _get_all_workers()
        
        # 转换为响应格式
        workers = {}
        for node_id, data in workers_data.items():
            workers[node_id] = WorkerStatus(
                node_id=node_id,
                status=data.get("status", "offline"),
                account_count=data.get("account_count", 0),
                last_heartbeat=data.get("last_heartbeat", datetime.now().isoformat()),
                accounts=data.get("accounts", []),
                metadata=data.get("metadata")
            )
        
        return WorkersListResponse(workers=workers)
    except Exception as e:
        logger.error(f"获取 Workers 列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Workers 列表失败: {str(e)}"
        )


@router.get("/{node_id}/commands", status_code=status.HTTP_200_OK)
async def get_worker_commands(
    node_id: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    获取节点的待执行命令（Worker 节点调用）
    """
    try:
        commands = _get_commands(node_id)
        return {
            "success": True,
            "node_id": node_id,
            "commands": commands
        }
    except Exception as e:
        logger.error(f"获取 Worker 命令失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取命令失败: {str(e)}"
        )


@router.post("/{node_id}/commands", status_code=status.HTTP_200_OK)
async def send_worker_command(
    node_id: str,
    request: WorkerCommandRequest,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    向特定 Worker 节点发送命令
    """
    try:
        command = {
            "action": request.action,
            "params": request.params,
            "timestamp": datetime.now().isoformat(),
            "from": "master"
        }
        
        _add_command(node_id, command)
        
        logger.info(f"向节点 {node_id} 发送命令: {request.action}")
        
        return {
            "success": True,
            "node_id": node_id,
            "action": request.action,
            "message": f"命令已发送到节点 {node_id}"
        }
    except Exception as e:
        logger.error(f"发送命令到 Worker 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送命令失败: {str(e)}"
        )


@router.post("/broadcast", status_code=status.HTTP_200_OK)
async def broadcast_command(
    request: WorkerBroadcastRequest,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    广播命令到所有 Worker 节点
    """
    try:
        workers_data = _get_all_workers()
        online_nodes = [node_id for node_id, data in workers_data.items() 
                       if data.get("status") == "online"]
        
        command = {
            "action": request.action,
            "params": request.params,
            "timestamp": datetime.now().isoformat(),
            "from": "master",
            "broadcast": True
        }
        
        # 向所有在线节点发送命令
        for node_id in online_nodes:
            _add_command(node_id, command)
        
        logger.info(f"广播命令 {request.action} 到 {len(online_nodes)} 个节点")
        
        return {
            "success": True,
            "action": request.action,
            "nodes_count": len(online_nodes),
            "nodes": online_nodes,
            "message": f"命令已广播到 {len(online_nodes)} 个节点"
        }
    except Exception as e:
        logger.error(f"广播命令失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"广播命令失败: {str(e)}"
        )


@router.delete("/{node_id}/commands", status_code=status.HTTP_200_OK)
async def clear_worker_commands(
    node_id: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    清除节点的命令队列（Worker 节点执行完命令后调用）
    """
    try:
        _clear_commands(node_id)
        return {
            "success": True,
            "node_id": node_id,
            "message": "命令队列已清除"
        }
    except Exception as e:
        logger.error(f"清除命令队列失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清除命令队列失败: {str(e)}"
        )


# ============ Worker 部署包配置 ============

class WorkerDeployConfig(BaseModel):
    """Worker 部署配置"""
    node_id: str = Field(..., description="節點ID")
    server_url: str = Field(default="https://aikz.usdt2026.cc", description="服務器地址")
    api_key: str = Field(default="", description="API密鑰（可選）")
    heartbeat_interval: int = Field(default=30, description="心跳間隔（秒）")
    telegram_api_id: str = Field(default="", description="Telegram API ID")
    telegram_api_hash: str = Field(default="", description="Telegram API Hash")


@router.post("/deploy-package", status_code=status.HTTP_200_OK)
async def generate_deploy_package(
    config: WorkerDeployConfig,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    生成 Worker 部署包配置
    返回自動運行腳本的內容
    """
    try:
        # 生成 Windows 批處理腳本
        windows_script = f'''@echo off
chcp 65001 >nul
echo ========================================
echo   聊天AI Worker 節點 - 自動部署
echo ========================================
echo.

REM 配置環境變量
set LIAOTIAN_SERVER={config.server_url}
set LIAOTIAN_NODE_ID={config.node_id}
set LIAOTIAN_API_KEY={config.api_key}
set LIAOTIAN_HEARTBEAT_INTERVAL={config.heartbeat_interval}
set TELEGRAM_API_ID={config.telegram_api_id}
set TELEGRAM_API_HASH={config.telegram_api_hash}

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Python，請先安裝 Python 3.8+
    pause
    exit /b 1
)

REM 創建虛擬環境
if not exist "venv" (
    echo 正在創建虛擬環境...
    python -m venv venv
)

REM 激活虛擬環境並安裝依賴
call venv\\Scripts\\activate.bat
pip install requests telethon python-dotenv -q

REM 創建 sessions 目錄
if not exist "sessions" mkdir sessions

REM 運行 Worker
echo.
echo 啟動 Worker 節點: {config.node_id}
echo 服務器: {config.server_url}
echo.
python worker_client.py

pause
'''

        # 生成 Linux/Mac 腳本
        linux_script = f'''#!/bin/bash
echo "========================================"
echo "  聊天AI Worker 節點 - 自動部署"
echo "========================================"
echo ""

# 配置環境變量
export LIAOTIAN_SERVER="{config.server_url}"
export LIAOTIAN_NODE_ID="{config.node_id}"
export LIAOTIAN_API_KEY="{config.api_key}"
export LIAOTIAN_HEARTBEAT_INTERVAL="{config.heartbeat_interval}"
export TELEGRAM_API_ID="{config.telegram_api_id}"
export TELEGRAM_API_HASH="{config.telegram_api_hash}"

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[錯誤] 未找到 Python3，請先安裝"
    exit 1
fi

# 創建虛擬環境
if [ ! -d "venv" ]; then
    echo "正在創建虛擬環境..."
    python3 -m venv venv
fi

# 激活虛擬環境並安裝依賴
source venv/bin/activate
pip install requests telethon python-dotenv -q

# 創建 sessions 目錄
mkdir -p sessions

# 運行 Worker
echo ""
echo "啟動 Worker 節點: {config.node_id}"
echo "服務器: {config.server_url}"
echo ""
python worker_client.py
'''

        # 生成 Python Worker 客戶端
        worker_client = '''#!/usr/bin/env python3
"""
聊天AI Worker 節點客戶端
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# 從環境變量讀取配置
CONFIG = {
    "server_url": os.getenv("LIAOTIAN_SERVER", "https://aikz.usdt2026.cc"),
    "node_id": os.getenv("LIAOTIAN_NODE_ID", "worker_default"),
    "api_key": os.getenv("LIAOTIAN_API_KEY", ""),
    "heartbeat_interval": int(os.getenv("LIAOTIAN_HEARTBEAT_INTERVAL", "30")),
    "sessions_dir": "./sessions",
}

class WorkerClient:
    def __init__(self):
        self.server_url = CONFIG["server_url"]
        self.node_id = CONFIG["node_id"]
        self.api_key = CONFIG["api_key"]

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def scan_sessions(self):
        """掃描本地 session 文件"""
        sessions_dir = Path(CONFIG["sessions_dir"])
        sessions = []
        if sessions_dir.exists():
            for f in sessions_dir.glob("*.session"):
                sessions.append({
                    "filename": f.name,
                    "account_id": f.stem,
                    "status": "available"
                })
        return sessions

    def send_heartbeat(self):
        """發送心跳到主服務器"""
        try:
            sessions = self.scan_sessions()
            
            payload = {
                "node_id": self.node_id,
                "status": "online",
                "account_count": len(sessions),
                "accounts": sessions,
                "metadata": {
                    "hostname": os.uname().nodename if hasattr(os, 'uname') else os.environ.get('COMPUTERNAME', 'unknown'),
                    "timestamp": datetime.now().isoformat()
                }
            }

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.post(
                f"{self.server_url}/api/v1/workers/heartbeat",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                self.log(f"✅ 心跳成功 - {len(sessions)} 個帳號")
                data = response.json()
                if data.get("pending_commands"):
                    self.process_commands(data["pending_commands"])
            else:
                self.log(f"❌ 心跳失敗: {response.status_code} - {response.text}")

        except Exception as e:
            self.log(f"❌ 心跳錯誤: {e}")

    def process_commands(self, commands):
        """處理服務器下發的命令"""
        for cmd in commands:
            action = cmd.get("action")
            self.log(f"📥 收到命令: {action}")
            # TODO: 實現具體命令處理

    def run(self):
        """主運行循環"""
        self.log(f"🚀 Worker 節點啟動")
        self.log(f"   節點ID: {self.node_id}")
        self.log(f"   服務器: {self.server_url}")
        self.log(f"   心跳間隔: {CONFIG['heartbeat_interval']}秒")

        while True:
            self.send_heartbeat()
            time.sleep(CONFIG["heartbeat_interval"])

if __name__ == "__main__":
    client = WorkerClient()
    try:
        client.run()
    except KeyboardInterrupt:
        print("\\n👋 Worker 節點已停止")
'''

        return {
            "success": True,
            "config": config.dict(),
            "scripts": {
                "windows": windows_script,
                "linux": linux_script,
                "worker_client": worker_client
            },
            "instructions": {
                "windows": "1. 下載所有文件到同一目錄\n2. 雙擊 start_worker.bat 運行",
                "linux": "1. 下載所有文件到同一目錄\n2. 運行: chmod +x start_worker.sh && ./start_worker.sh"
            }
        }
    except Exception as e:
        logger.error(f"生成部署包失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成部署包失敗: {str(e)}"
        )


@router.get("/deploy-template", status_code=status.HTTP_200_OK)
async def get_deploy_template(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    獲取 Worker 部署配置模板
    """
    return {
        "template": {
            "node_id": "worker_001",
            "server_url": "https://aikz.usdt2026.cc",
            "api_key": "",
            "heartbeat_interval": 30,
            "telegram_api_id": "",
            "telegram_api_hash": ""
        },
        "description": {
            "node_id": "節點唯一標識，如 worker_001",
            "server_url": "主服務器地址",
            "api_key": "API密鑰（可選）",
            "heartbeat_interval": "心跳間隔（秒）",
            "telegram_api_id": "Telegram API ID（從 my.telegram.org 獲取）",
            "telegram_api_hash": "Telegram API Hash"
        }
    }

