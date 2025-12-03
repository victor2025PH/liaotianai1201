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
        # 生成 Windows 批處理腳本 (使用英文避免編碼問題)
        windows_script = f'''@echo off
echo ========================================
echo   Worker Node Auto Deploy
echo ========================================
echo.

set LIAOTIAN_SERVER={config.server_url}
set LIAOTIAN_NODE_ID={config.node_id}
set LIAOTIAN_API_KEY={config.api_key}
set LIAOTIAN_HEARTBEAT_INTERVAL={config.heartbeat_interval}
set TELEGRAM_API_ID={config.telegram_api_id}
set TELEGRAM_API_HASH={config.telegram_api_hash}

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\\Scripts\\activate.bat
pip install requests telethon python-dotenv openpyxl -q

if not exist "sessions" mkdir sessions

echo.
echo Starting Worker: {config.node_id}
echo Server: {config.server_url}
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
pip install requests telethon python-dotenv openpyxl -q

# 創建 sessions 目錄
mkdir -p sessions

# 運行 Worker
echo ""
echo "啟動 Worker 節點: {config.node_id}"
echo "服務器: {config.server_url}"
echo ""
python worker_client.py
'''

        # 生成 Python Worker 客戶端 (完整版 - 支持 Excel 配置和 Telethon)
        worker_client = '''#!/usr/bin/env python3
"""
Worker Node Client - Full Version with Excel Config Support
- Reads account config from Excel file in sessions folder
- Supports Telethon for account statistics
"""

import os
import sys
import json
import time
import asyncio
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Default Configuration (can be overridden by Excel)
CONFIG = {
    "server_url": os.getenv("LIAOTIAN_SERVER", "https://aikz.usdt2026.cc"),
    "node_id": os.getenv("LIAOTIAN_NODE_ID", "worker_default"),
    "api_key": os.getenv("LIAOTIAN_API_KEY", ""),
    "heartbeat_interval": int(os.getenv("LIAOTIAN_HEARTBEAT_INTERVAL", "30")),
    "sessions_dir": "./sessions",
    "api_id": None,
    "api_hash": None,
    "stats_interval": 300,
}

# Account config from Excel
excel_config = {}
account_cache = {}
last_stats_update = None
telethon_available = False
openpyxl_available = False

# Try imports
try:
    from telethon import TelegramClient
    from telethon.tl.functions.contacts import GetContactsRequest
    from telethon.tl.types import User
    telethon_available = True
except ImportError:
    pass

try:
    import openpyxl
    openpyxl_available = True
except ImportError:
    pass

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_excel_config():
    """Load account configuration from Excel file in sessions folder"""
    global excel_config, CONFIG
    
    sessions_dir = Path(CONFIG["sessions_dir"])
    excel_files = list(sessions_dir.glob("*.xlsx")) + list(sessions_dir.glob("*.xls"))
    
    if not excel_files:
        log("[CONFIG] No Excel config file found in sessions folder")
        return None
    
    if not openpyxl_available:
        log("[CONFIG] openpyxl not installed. Run: pip install openpyxl")
        return None
    
    excel_file = excel_files[0]
    log(f"[CONFIG] Loading: {excel_file.name}")
    
    try:
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
        
        # Read headers
        headers = [str(cell.value).lower().strip() if cell.value else "" for cell in ws[1]]
        log(f"[CONFIG] Columns: {[h for h in headers if h]}")
        
        # Map columns
        col_map = {}
        for idx, h in enumerate(headers):
            if h in ['api_id', 'apiid']:
                col_map['api_id'] = idx
            elif h in ['api_hash', 'apihash']:
                col_map['api_hash'] = idx
            elif h in ['phone', '手机', '手機', '电话']:
                col_map['phone'] = idx
            elif h in ['node', '电脑', '節點']:
                col_map['node'] = idx
            elif h in ['group', '分组', '分組']:
                col_map['group'] = idx
            elif h in ['username', '用户名', '用戶名']:
                col_map['username'] = idx
            elif h in ['name', '名字', '昵称', '暱稱']:
                col_map['name'] = idx
            elif h in ['friends', '好友', '好友数']:
                col_map['friends'] = idx
            elif h in ['groups', '群组', '群組', '群数']:
                col_map['groups'] = idx
            elif h in ['remark', '备注', '備註']:
                col_map['remark'] = idx
        
        # Read data
        api_id_found = None
        api_hash_found = None
        
        for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
            row_data = [cell.value for cell in row]
            
            if 'api_id' in col_map and row_data[col_map['api_id']] and not api_id_found:
                api_id_found = int(row_data[col_map['api_id']])
            if 'api_hash' in col_map and row_data[col_map['api_hash']] and not api_hash_found:
                api_hash_found = str(row_data[col_map['api_hash']])
            
            if 'phone' in col_map and row_data[col_map['phone']]:
                phone = str(row_data[col_map['phone']]).strip()
                phone_key = phone.replace(' ', '').replace('+', '').replace('-', '')
                
                excel_config[phone_key] = {
                    'phone': phone,
                    'row_idx': row_idx,  # Save row index for updating
                    'node': row_data[col_map['node']] if 'node' in col_map else None,
                    'group': row_data[col_map['group']] if 'group' in col_map else None,
                    'name': row_data[col_map['name']] if 'name' in col_map else None,
                    'remark': row_data[col_map['remark']] if 'remark' in col_map else None,
                }
        
        if api_id_found:
            CONFIG['api_id'] = api_id_found
            log(f"[CONFIG] API ID: {api_id_found}")
        if api_hash_found:
            CONFIG['api_hash'] = api_hash_found
            log(f"[CONFIG] API Hash: {api_hash_found[:10]}...")
        
        log(f"[CONFIG] Loaded {len(excel_config)} accounts")
        
        return {'wb': wb, 'ws': ws, 'col_map': col_map, 'file': excel_file}
        
    except Exception as e:
        log(f"[CONFIG] Error: {e}")
        return None

excel_workbook = None  # Global reference for updating

async def fetch_and_update_excel():
    """Fetch account details from Telegram and update Excel file"""
    global excel_workbook
    
    if not telethon_available or not CONFIG['api_id'] or not CONFIG['api_hash']:
        log("[EXCEL] Telethon or API config not available")
        return
    
    if not openpyxl_available:
        log("[EXCEL] openpyxl not installed")
        return
    
    sessions_dir = Path(CONFIG["sessions_dir"])
    excel_files = list(sessions_dir.glob("*.xlsx"))
    if not excel_files:
        log("[EXCEL] No Excel file to update")
        return
    
    excel_file = excel_files[0]
    log(f"[EXCEL] Updating: {excel_file.name}")
    
    try:
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
        
        # Check/add columns for auto-fill data
        headers = [str(cell.value).lower().strip() if cell.value else "" for cell in ws[1]]
        
        # Add missing columns
        needed_cols = ['username', 'name', 'friends', 'groups', 'last_update']
        col_map = {}
        next_col = len(headers) + 1
        
        for idx, h in enumerate(headers):
            if h in ['phone', '手机']:
                col_map['phone'] = idx
            elif h in ['username', '用户名']:
                col_map['username'] = idx
            elif h in ['name', '名字', '昵称']:
                col_map['name'] = idx
            elif h in ['friends', '好友', '好友数']:
                col_map['friends'] = idx
            elif h in ['groups', '群组', '群数']:
                col_map['groups'] = idx
            elif h in ['last_update', '更新时间']:
                col_map['last_update'] = idx
        
        # Add missing columns to Excel
        if 'username' not in col_map:
            ws.cell(row=1, column=next_col, value='username')
            col_map['username'] = next_col - 1
            next_col += 1
        if 'name' not in col_map:
            ws.cell(row=1, column=next_col, value='name')
            col_map['name'] = next_col - 1
            next_col += 1
        if 'friends' not in col_map:
            ws.cell(row=1, column=next_col, value='friends')
            col_map['friends'] = next_col - 1
            next_col += 1
        if 'groups' not in col_map:
            ws.cell(row=1, column=next_col, value='groups')
            col_map['groups'] = next_col - 1
            next_col += 1
        if 'last_update' not in col_map:
            ws.cell(row=1, column=next_col, value='last_update')
            col_map['last_update'] = next_col - 1
        
        # Fetch data for each session
        updated_count = 0
        for session_file in sessions_dir.glob("*.session"):
            phone_key = session_file.stem.replace('+', '').replace('-', '').replace(' ', '')
            
            # Find row for this phone
            target_row = None
            for row_idx in range(2, ws.max_row + 1):
                cell_phone = ws.cell(row=row_idx, column=col_map['phone'] + 1).value
                if cell_phone:
                    cell_phone_key = str(cell_phone).replace('+', '').replace('-', '').replace(' ', '')
                    if cell_phone_key == phone_key:
                        target_row = row_idx
                        break
            
            if not target_row:
                continue
            
            # Connect and get account info
            try:
                client = TelegramClient(
                    str(session_file).replace('.session', ''),
                    CONFIG['api_id'],
                    CONFIG['api_hash']
                )
                await client.connect()
                
                if await client.is_user_authorized():
                    me = await client.get_me()
                    
                    # Get contacts count
                    friends_count = 0
                    try:
                        contacts = await client(GetContactsRequest(hash=0))
                        friends_count = len(contacts.users) if hasattr(contacts, 'users') else 0
                    except: pass
                    
                    # Get groups count
                    groups_count = 0
                    try:
                        dialogs = await client.get_dialogs(limit=500)
                        groups_count = sum(1 for d in dialogs if d.is_group)
                    except: pass
                    
                    # Update Excel
                    username = me.username or ""
                    name = f"{me.first_name or ''} {me.last_name or ''}".strip()
                    
                    ws.cell(row=target_row, column=col_map['username'] + 1, value=username)
                    ws.cell(row=target_row, column=col_map['name'] + 1, value=name)
                    ws.cell(row=target_row, column=col_map['friends'] + 1, value=friends_count)
                    ws.cell(row=target_row, column=col_map['groups'] + 1, value=groups_count)
                    ws.cell(row=target_row, column=col_map['last_update'] + 1, value=datetime.now().strftime("%Y-%m-%d %H:%M"))
                    
                    log(f"[EXCEL] Updated: {phone_key} -> @{username}, {name}, {friends_count} friends, {groups_count} groups")
                    updated_count += 1
                
                await client.disconnect()
                await asyncio.sleep(2)  # Rate limit
                
            except Exception as e:
                log(f"[EXCEL] Error for {phone_key}: {e}")
        
        # Save Excel
        wb.save(excel_file)
        wb.close()
        log(f"[EXCEL] Saved! Updated {updated_count} accounts")
        
    except Exception as e:
        log(f"[EXCEL] Error updating Excel: {e}")

async def export_accounts_to_excel():
    """Export all account details to a new Excel file"""
    if not openpyxl_available:
        log("[EXPORT] openpyxl not installed")
        return None
    
    sessions_dir = Path(CONFIG["sessions_dir"])
    export_file = sessions_dir / f"accounts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Accounts"
    
    # Headers
    headers = ['phone', 'username', 'name', 'user_id', 'friends', 'groups', 'channels', 'node_id', 'status', 'last_update']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    # Data from cache
    row = 2
    for cache_key, acc in account_cache.items():
        ws.cell(row=row, column=1, value=acc.get('phone', ''))
        ws.cell(row=row, column=2, value=acc.get('username', ''))
        ws.cell(row=row, column=3, value=acc.get('name', ''))
        ws.cell(row=row, column=4, value=acc.get('user_id', ''))
        ws.cell(row=row, column=5, value=acc.get('friends_count', 0))
        ws.cell(row=row, column=6, value=acc.get('groups_count', 0))
        ws.cell(row=row, column=7, value=acc.get('channels_count', 0))
        ws.cell(row=row, column=8, value=acc.get('node_id', ''))
        ws.cell(row=row, column=9, value=acc.get('status', ''))
        ws.cell(row=row, column=10, value=datetime.now().strftime('%Y-%m-%d %H:%M'))
        row += 1
    
    wb.save(export_file)
    wb.close()
    log(f"[EXPORT] Exported to: {export_file.name}")
    return str(export_file)

def read_session_basic(session_path):
    """Read basic info from session file (SQLite)"""
    try:
        conn = sqlite3.connect(str(session_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        info = {"session_file": session_path.name, "account_id": session_path.stem}
        
        if 'entities' in tables:
            cursor.execute("SELECT id, username, name, phone FROM entities WHERE id > 0 LIMIT 10")
            for entity in cursor.fetchall():
                if entity[3]:  # Has phone
                    info["user_id"] = entity[0]
                    info["username"] = entity[1] or ""
                    info["name"] = entity[2] or ""
                    info["phone"] = entity[3] or ""
                    break
        
        conn.close()
        return info
    except Exception as e:
        return {"session_file": session_path.name, "account_id": session_path.stem, "error": str(e)}

async def get_account_stats(session_path):
    """Get detailed account stats using Telethon"""
    if not telethon_available or not CONFIG["api_id"] or not CONFIG["api_hash"]:
        return None
    
    try:
        client = TelegramClient(
            str(session_path).replace('.session', ''),
            CONFIG["api_id"],
            CONFIG["api_hash"]
        )
        
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return {"error": "Not authorized"}
        
        # Get current user info
        me = await client.get_me()
        stats = {
            "user_id": me.id,
            "username": me.username or "",
            "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
            "phone": me.phone or "",
        }
        
        # Get contacts (friends)
        try:
            contacts = await client(GetContactsRequest(hash=0))
            stats["friends_count"] = len(contacts.users) if hasattr(contacts, 'users') else 0
        except:
            stats["friends_count"] = 0
        
        # Get dialogs (chats, groups, channels)
        try:
            dialogs = await client.get_dialogs(limit=500)
            groups = 0
            channels = 0
            private_chats = 0
            
            for d in dialogs:
                if d.is_group:
                    groups += 1
                elif d.is_channel:
                    channels += 1
                else:
                    private_chats += 1
            
            stats["groups_count"] = groups
            stats["channels_count"] = channels
            stats["private_chats"] = private_chats
            stats["total_dialogs"] = len(dialogs)
        except:
            stats["groups_count"] = 0
            stats["channels_count"] = 0
        
        # Get recent contacts added (last 24h) - estimate from recent dialogs
        try:
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            recent_contacts = 0
            
            for d in dialogs[:100]:
                if d.date and d.date.replace(tzinfo=None) > yesterday:
                    if isinstance(d.entity, User) and not d.entity.bot:
                        recent_contacts += 1
            
            stats["new_contacts_24h"] = recent_contacts
        except:
            stats["new_contacts_24h"] = 0
        
        await client.disconnect()
        return stats
        
    except Exception as e:
        return {"error": str(e)}

def scan_sessions_sync():
    """Scan sessions and merge with Excel config"""
    sessions_dir = Path(CONFIG["sessions_dir"])
    accounts = []
    
    if not sessions_dir.exists():
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return accounts
    
    for f in sessions_dir.glob("*.session"):
        cache_key = f.name
        if cache_key in account_cache:
            cached = account_cache[cache_key].copy()
            cached["status"] = "available"
            accounts.append(cached)
        else:
            info = read_session_basic(f)
            info["status"] = "available"
            info["node_id"] = CONFIG["node_id"]
            info["session_path"] = str(f)
            
            # Merge with Excel config
            phone = info.get("phone", "").replace(' ', '').replace('+', '').replace('-', '')
            account_id = f.stem.replace(' ', '').replace('+', '').replace('-', '')
            
            # Try to match by phone or filename
            excel_data = excel_config.get(phone) or excel_config.get(account_id)
            if excel_data:
                info["excel_name"] = excel_data.get("name")
                info["excel_group"] = excel_data.get("group")
                info["excel_remark"] = excel_data.get("remark")
                info["excel_node"] = excel_data.get("node")
                # Use Excel name if available
                if excel_data.get("name"):
                    info["name"] = excel_data["name"]
            
            account_cache[cache_key] = info
            accounts.append(info)
    
    return accounts

async def update_all_stats():
    """Update detailed stats for all accounts"""
    global last_stats_update
    
    if not telethon_available or not CONFIG["api_id"]:
        log("[STATS] Telethon not available, skipping detailed stats")
        return
    
    sessions_dir = Path(CONFIG["sessions_dir"])
    log("[STATS] Updating account statistics...")
    
    for f in sessions_dir.glob("*.session"):
        cache_key = f.name
        try:
            stats = await get_account_stats(f)
            if stats and "error" not in stats:
                if cache_key in account_cache:
                    account_cache[cache_key].update(stats)
                else:
                    stats["session_file"] = f.name
                    stats["account_id"] = f.stem
                    stats["status"] = "available"
                    stats["node_id"] = CONFIG["node_id"]
                    account_cache[cache_key] = stats
                
                phone = stats.get("phone", f.stem)
                log(f"[STATS] {phone}: {stats.get('friends_count', 0)} friends, {stats.get('groups_count', 0)} groups")
            
            await asyncio.sleep(2)  # Rate limit
        except Exception as e:
            log(f"[STATS] Error for {f.name}: {e}")
    
    last_stats_update = datetime.now()
    log("[STATS] Update complete")

def send_heartbeat():
    """Send heartbeat to server"""
    try:
        accounts = scan_sessions_sync()
        hostname = os.environ.get('COMPUTERNAME', os.uname().nodename if hasattr(os, 'uname') else 'unknown')
        
        # Calculate totals
        total_friends = sum(a.get("friends_count", 0) for a in accounts)
        total_groups = sum(a.get("groups_count", 0) for a in accounts)
        new_contacts = sum(a.get("new_contacts_24h", 0) for a in accounts)
        
        payload = {
            "node_id": CONFIG["node_id"],
            "status": "online",
            "account_count": len(accounts),
            "accounts": accounts,
            "metadata": {
                "hostname": hostname,
                "timestamp": datetime.now().isoformat(),
                "platform": sys.platform,
                "telethon_enabled": telethon_available and bool(CONFIG["api_id"]),
                "total_friends": total_friends,
                "total_groups": total_groups,
                "new_contacts_24h": new_contacts,
            }
        }

        headers = {"Content-Type": "application/json"}
        if CONFIG["api_key"]:
            headers["Authorization"] = f"Bearer {CONFIG['api_key']}"

        response = requests.post(
            f"{CONFIG['server_url']}/api/v1/workers/heartbeat",
            json=payload,
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            summary = f"{len(accounts)} accounts"
            if total_friends > 0:
                summary += f", {total_friends} friends, {total_groups} groups"
            if new_contacts > 0:
                summary += f", +{new_contacts} new today"
            
            log(f"[OK] {summary}")
            
            if data.get("pending_commands"):
                process_commands(data["pending_commands"])
                try:
                    requests.delete(
                        f"{CONFIG['server_url']}/api/v1/workers/{CONFIG['node_id']}/commands",
                        headers=headers, timeout=10
                    )
                except: pass
        else:
            log(f"[ERR] Heartbeat: {response.status_code}")

    except requests.exceptions.ConnectionError:
        log("[ERR] Cannot connect to server")
    except Exception as e:
        log(f"[ERR] {e}")

def process_commands(commands):
    """Process commands from server"""
    for cmd in commands:
        action = cmd.get("action")
        params = cmd.get("params", {})
        log(f"[CMD] {action}")
        
        if action == "refresh_accounts":
            account_cache.clear()
            log("[CMD] Cache cleared")
        elif action == "refresh_stats":
            asyncio.get_event_loop().run_until_complete(update_all_stats())
        elif action == "update_excel":
            # Update Excel with account details
            asyncio.get_event_loop().run_until_complete(fetch_and_update_excel())
        elif action == "export_accounts":
            # Export all accounts to new Excel
            asyncio.get_event_loop().run_until_complete(export_accounts_to_excel())
        elif action == "get_status":
            log(f"[CMD] {len(account_cache)} accounts")
        else:
            log(f"[CMD] Unknown: {action}")

async def main_async():
    """Async main loop"""
    global last_stats_update
    
    log("=" * 50)
    log("Worker Node Starting (Full Version)")
    log(f"  Node ID: {CONFIG['node_id']}")
    log(f"  Server: {CONFIG['server_url']}")
    log(f"  Sessions: {CONFIG['sessions_dir']}")
    log("=" * 50)
    
    # Load Excel config first
    load_excel_config()
    
    log(f"  Telethon: {'Enabled' if telethon_available and CONFIG['api_id'] else 'Disabled'}")
    log(f"  openpyxl: {'Installed' if openpyxl_available else 'Not installed'}")
    log("=" * 50)
    
    # Initial stats update
    if telethon_available and CONFIG["api_id"]:
        await update_all_stats()
    
    heartbeat_count = 0
    while True:
        send_heartbeat()
        heartbeat_count += 1
        
        # Update stats every N heartbeats (5 min interval)
        stats_interval_beats = CONFIG["stats_interval"] // CONFIG["heartbeat_interval"]
        if telethon_available and CONFIG["api_id"] and heartbeat_count >= stats_interval_beats:
            await update_all_stats()
            heartbeat_count = 0
        
        await asyncio.sleep(CONFIG["heartbeat_interval"])

def main():
    """Main entry point"""
    try:
        asyncio.get_event_loop().run_until_complete(main_async())
    except KeyboardInterrupt:
        log("Worker stopped")

if __name__ == "__main__":
    main()
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

