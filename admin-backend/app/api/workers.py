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


@router.delete("/{node_id}", status_code=status.HTTP_200_OK)
async def delete_worker(
    node_id: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    刪除 Worker 節點
    """
    try:
        # 從 Redis 或內存中刪除
        if _redis_client:
            try:
                key = _get_worker_key(node_id)
                _redis_client.delete(key)
                _redis_client.srem(_get_workers_set_key(), node_id)
                # 清除命令隊列
                _redis_client.delete(_get_commands_key(node_id))
            except Exception as e:
                logger.error(f"從 Redis 刪除節點失敗: {e}")
        
        # 從內存存儲刪除
        if node_id in _workers_memory_store:
            del _workers_memory_store[node_id]
        if node_id in _worker_commands:
            del _worker_commands[node_id]
        
        logger.info(f"已刪除節點: {node_id}")
        
        return {
            "success": True,
            "node_id": node_id,
            "message": f"節點 {node_id} 已刪除"
        }
    except Exception as e:
        logger.error(f"刪除節點失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除節點失敗: {str(e)}"
        )


@router.get("/check/duplicates", status_code=status.HTTP_200_OK)
async def check_duplicate_accounts(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    檢測重複帳號
    返回在多個節點上出現的帳號列表
    """
    try:
        workers_data = _get_all_workers()
        
        # 建立帳號到節點的映射
        account_nodes: Dict[str, List[str]] = {}
        
        for node_id, data in workers_data.items():
            accounts = data.get("accounts", [])
            for acc in accounts:
                acc_id = str(acc.get("account_id") or acc.get("user_id") or acc.get("phone", ""))
                if acc_id:
                    if acc_id not in account_nodes:
                        account_nodes[acc_id] = []
                    account_nodes[acc_id].append(node_id)
        
        # 找出重複帳號
        duplicates = []
        for acc_id, nodes in account_nodes.items():
            if len(nodes) > 1:
                duplicates.append({
                    "account_id": acc_id,
                    "nodes": nodes,
                    "count": len(nodes)
                })
        
        return {
            "success": True,
            "has_duplicates": len(duplicates) > 0,
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
            "total_accounts": len(account_nodes),
            "message": f"發現 {len(duplicates)} 個重複帳號" if duplicates else "無重複帳號"
        }
    except Exception as e:
        logger.error(f"檢測重複帳號失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"檢測重複帳號失敗: {str(e)}"
        )


@router.post("/check/status", status_code=status.HTTP_200_OK)
async def check_workers_status(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    檢測所有節點狀態
    返回在線、離線和錯誤節點列表
    """
    try:
        workers_data = _get_all_workers()
        now = datetime.now()
        
        online_nodes = []
        offline_nodes = []
        error_nodes = []
        
        for node_id, data in workers_data.items():
            last_heartbeat_str = data.get("last_heartbeat", "1970-01-01T00:00:00")
            try:
                last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
                time_diff = (now - last_heartbeat).total_seconds()
            except:
                time_diff = 9999
            
            node_info = {
                "node_id": node_id,
                "account_count": data.get("account_count", 0),
                "last_heartbeat": last_heartbeat_str,
                "seconds_ago": int(time_diff)
            }
            
            status = data.get("status", "offline")
            
            if status == "error":
                error_nodes.append(node_info)
            elif time_diff > 120:  # 超過 120 秒沒有心跳
                offline_nodes.append(node_info)
            elif status == "online":
                online_nodes.append(node_info)
            else:
                offline_nodes.append(node_info)
        
        return {
            "success": True,
            "summary": {
                "total": len(workers_data),
                "online": len(online_nodes),
                "offline": len(offline_nodes),
                "error": len(error_nodes)
            },
            "online_nodes": online_nodes,
            "offline_nodes": offline_nodes,
            "error_nodes": error_nodes
        }
    except Exception as e:
        logger.error(f"檢測節點狀態失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"檢測節點狀態失敗: {str(e)}"
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
        # 確保 node_id 不為空
        node_id = config.node_id.strip() if config.node_id else f"node_{int(time.time())}"
        if not node_id or node_id == "worker_default":
            # 生成唯一的節點 ID
            import random
            import string
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            node_id = f"worker_{suffix}"
        
        # 生成 Windows 批處理腳本 (簡化版，避免編碼問題)
        # 使用 \r\n 確保 Windows 換行符
        windows_lines = [
            "@echo off",
            "echo ========================================",
            "echo   Worker Node Auto Deploy",
            f"echo   Node ID: {node_id}",
            "echo ========================================",
            "echo.",
            "",
            f"set LIAOTIAN_SERVER={config.server_url}",
            f"set LIAOTIAN_NODE_ID={node_id}",
            f"set LIAOTIAN_API_KEY={config.api_key}",
            f"set LIAOTIAN_HEARTBEAT_INTERVAL={config.heartbeat_interval}",
            f"set TELEGRAM_API_ID={config.telegram_api_id}",
            f"set TELEGRAM_API_HASH={config.telegram_api_hash}",
            "",
            "where python >nul 2>&1",
            "if %errorlevel% neq 0 (",
            "    echo [ERROR] Python not found. Please install Python 3.8+",
            "    pause",
            "    exit /b 1",
            ")",
            "",
            "if not exist sessions mkdir sessions",
            "",
            "echo.",
            "echo [1/3] 修复 Session 文件（如果需要）...",
            "python fix_session.py sessions 2>nul || echo   跳过修复（Session 文件可能已正常）",
            "",
            "echo [2/3] 创建 Excel 配置模板（如果不存在）...",
            "python create_excel_template.py 2>nul || echo   跳过创建（Excel 文件已存在）",
            "",
            "echo [3/3] 启动 Worker 节点...",
            "echo.",
            f"echo Starting Worker: {node_id}",
            f"echo Server: {config.server_url}",
            "echo.",
            "",
            "pip install requests httpx openpyxl telethon -q",
            "python worker_client.py",
            "",
            "pause",
        ]
        windows_script = "\r\n".join(windows_lines)

        # 生成 Linux/Mac 腳本
        linux_script = f'''#!/bin/bash
echo "========================================"
echo "  Worker Node Auto Deploy"
echo "  Node ID: {node_id}"
echo "========================================"
echo ""

# Configuration
export LIAOTIAN_SERVER="{config.server_url}"
export LIAOTIAN_NODE_ID="{node_id}"
export LIAOTIAN_API_KEY="{config.api_key}"
export LIAOTIAN_HEARTBEAT_INTERVAL="{config.heartbeat_interval}"
export TELEGRAM_API_ID="{config.telegram_api_id}"
export TELEGRAM_API_HASH="{config.telegram_api_hash}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Create sessions directory
mkdir -p sessions

# Install dependencies
pip3 install requests httpx openpyxl telethon -q

# Fix session files if needed
echo ""
echo "[1/3] 修复 Session 文件（如果需要）..."
python3 fix_session.py sessions 2>/dev/null || echo "  跳过修复（Session 文件可能已正常）"

# Create Excel template if needed
echo ""
echo "[2/3] 创建 Excel 配置模板（如果不存在）..."
python3 create_excel_template.py 2>/dev/null || echo "  跳过创建（Excel 文件已存在）"

# Run Worker
echo ""
echo "[3/3] 启动 Worker 节点..."
echo ""
echo "Starting Worker: {node_id}"
echo "Server: {config.server_url}"
echo ""
python3 worker_client.py
'''

        # 生成 Session 文件修复脚本
        fix_session_script = '''#!/usr/bin/env python3
"""
修复 Worker 节点 Session 文件
解决 "no such column: server_address" 和 "no such column: version" 错误
"""

import sqlite3
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_session_file(session_path: str) -> bool:
    """
    修复 Session 文件，添加缺失的列
    
    Args:
        session_path: Session 文件路径
        
    Returns:
        是否修复成功
    """
    try:
        if not os.path.exists(session_path):
            logger.error(f"Session 文件不存在: {session_path}")
            return False
        
        # 备份原文件
        backup_path = f"{session_path}.backup"
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(session_path, backup_path)
            logger.info(f"已备份: {backup_path}")
        
        # 连接数据库
        conn = sqlite3.connect(session_path)
        cursor = conn.cursor()
        
        # 检查 sessions 表结构
        cursor.execute("PRAGMA table_info(sessions)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # 添加缺失的列
        if 'server_address' not in columns:
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN server_address TEXT")
                logger.info(f"已添加 server_address 列到 {session_path}")
            except sqlite3.OperationalError as e:
                logger.warning(f"添加 server_address 列失败（可能已存在）: {e}")
        
        if 'port' not in columns:
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN port INTEGER")
                logger.info(f"已添加 port 列到 {session_path}")
            except sqlite3.OperationalError as e:
                logger.warning(f"添加 port 列失败（可能已存在）: {e}")
        
        # 检查 version 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='version'")
        if not cursor.fetchone():
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS version (version INTEGER)")
                cursor.execute("INSERT INTO version (version) VALUES (1)")
                logger.info(f"已创建 version 表到 {session_path}")
            except sqlite3.OperationalError as e:
                logger.warning(f"创建 version 表失败: {e}")
        else:
            # 检查 version 表是否有数据
            cursor.execute("SELECT COUNT(*) FROM version")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("INSERT INTO version (version) VALUES (1)")
                logger.info(f"已添加 version 数据到 {session_path}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Session 文件修复成功: {session_path}")
        return True
        
    except Exception as e:
        logger.error(f"修复 Session 文件失败 {session_path}: {e}", exc_info=True)
        return False


def fix_all_sessions(sessions_dir: str):
    """
    修复目录中的所有 Session 文件
    
    Args:
        sessions_dir: Session 文件目录
    """
    sessions_path = Path(sessions_dir)
    if not sessions_path.exists():
        logger.error(f"Session 目录不存在: {sessions_dir}")
        return
    
    session_files = list(sessions_path.glob("*.session"))
    logger.info(f"找到 {len(session_files)} 个 Session 文件")
    
    fixed_count = 0
    for session_file in session_files:
        if fix_session_file(str(session_file)):
            fixed_count += 1
    
    logger.info(f"修复完成: {fixed_count}/{len(session_files)} 个文件")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        sessions_dir = sys.argv[1]
    else:
        # 默认使用当前目录下的 sessions 文件夹
        sessions_dir = "./sessions"
    
    fix_all_sessions(sessions_dir)
'''

        # 生成 Excel 模板文件内容（Base64 编码的 Excel 文件）
        # 由于无法直接生成 Excel 二进制，我们生成一个 Python 脚本来创建 Excel 模板
        create_excel_template = '''#!/usr/bin/env python3
"""
创建 Excel 配置模板文件
"""

import sys
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Font
    
    sessions_dir = Path("./sessions")
    sessions_dir.mkdir(exist_ok=True)
    
    # 检查是否已存在 Excel 文件
    excel_files = list(sessions_dir.glob("*.xlsx"))
    if excel_files:
        print(f"Excel 配置文件已存在: {excel_files[0].name}")
        print("如需重新创建，请先删除现有文件")
        sys.exit(0)
    
    # 创建新的 Excel 文件
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Accounts"
    
    # 设置表头（加粗）
    headers = [
        'api_id', 'api_hash', 'phone', 'username', 'name', 'user_id',
        'friends', 'groups', 'group', 'remark', 'node', 'enabled', 'last_update'
    ]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
    
    # 设置列宽
    col_widths = [12, 35, 18, 15, 15, 15, 10, 10, 12, 20, 15, 10, 18]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
    
    # 保存文件（使用节点ID作为文件名）
    node_id = os.getenv("LIAOTIAN_NODE_ID", "worker_default")
    excel_file = sessions_dir / f"{node_id}.xlsx"
    wb.save(excel_file)
    wb.close()
    
    print(f"✅ Excel 模板已创建: {excel_file.name}")
    print("")
    print("请编辑此文件，添加您的账号信息：")
    print("  - api_id: Telegram API ID（从 my.telegram.org 获取）")
    print("  - api_hash: Telegram API Hash（从 my.telegram.org 获取）")
    print("  - phone: 电话号码（必须与 session 文件名匹配）")
    print("  - enabled: 1=启用，0=禁用")
    print("")
    print("示例：")
    print("  api_id: 30390800")
    print("  api_hash: 471481f784e6d78893e53b88ee43e62b")
    print("  phone: 639277358115")
    print("  enabled: 1")
    
except ImportError:
    print("⚠️  openpyxl 未安装，无法创建 Excel 模板")
    print("请运行: pip install openpyxl")
    print("")
    print("或者手动创建 Excel 文件，包含以下列：")
    print("  api_id, api_hash, phone, username, name, user_id, friends, groups, group, remark, node, enabled, last_update")
    sys.exit(1)
except Exception as e:
    print(f"❌ 创建 Excel 模板失败: {e}")
    sys.exit(1)
'''

        # 生成 Python Worker 客戶端 (完整版 - 支持 Telegram user_id 讀取，已修复 Session 读取)
        worker_client = '''#!/usr/bin/env python3
"""
Worker Node Client - Full Version
- Automatically reads Telegram user_id from session files
- Supports Telethon for detailed account statistics
- Auto-reports all account info to server via heartbeat
- Supports Excel configuration (optional)
"""

import os
import sys
import json
import time
import asyncio
import sqlite3
import struct
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Default Configuration
CONFIG = {
    "server_url": os.getenv("LIAOTIAN_SERVER", "https://aikz.usdt2026.cc"),
    "node_id": os.getenv("LIAOTIAN_NODE_ID", "worker_default"),
    "api_key": os.getenv("LIAOTIAN_API_KEY", ""),
    "heartbeat_interval": int(os.getenv("LIAOTIAN_HEARTBEAT_INTERVAL", "30")),
    "sessions_dir": "./sessions",
    "api_id": os.getenv("TELEGRAM_API_ID", None),
    "api_hash": os.getenv("TELEGRAM_API_HASH", None),
    "stats_interval": 300,
    # Red packet game config
    "redpacket_api_url": os.getenv("REDPACKET_API_URL", ""),
    "redpacket_api_key": os.getenv("REDPACKET_API_KEY", ""),
    "redpacket_enabled": os.getenv("REDPACKET_ENABLED", "false").lower() == "true",
}

# Convert API ID to int if provided
if CONFIG["api_id"]:
    try:
        CONFIG["api_id"] = int(CONFIG["api_id"])
    except:
        CONFIG["api_id"] = None

# Account storage
excel_config = {}
account_cache = {}
last_stats_update = None
telethon_available = False
openpyxl_available = False
redpacket_available = False
redpacket_client = None

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

# Try import red packet SDK (simple HTTP client)
try:
    import httpx
    redpacket_available = True
except ImportError:
    pass

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def init_redpacket_client():
    """Initialize red packet game client"""
    global redpacket_client
    
    if not redpacket_available:
        log("[REDPACKET] httpx not installed, red packet features disabled")
        return False
    
    if not CONFIG.get("redpacket_api_url") or not CONFIG.get("redpacket_api_key"):
        log("[REDPACKET] API URL or Key not configured")
        return False
    
    try:
        # Simple HTTP client for red packet API
        # Note: Full SDK integration can be added later
        redpacket_client = {
            "api_url": CONFIG["redpacket_api_url"].rstrip('/'),
            "api_key": CONFIG["redpacket_api_key"],
            "enabled": CONFIG.get("redpacket_enabled", False),
        }
        log(f"[REDPACKET] Client initialized: {redpacket_client['api_url']}")
        return True
    except Exception as e:
        log(f"[REDPACKET] Initialization error: {e}")
        return False


async def redpacket_get_balance(tg_id: int) -> dict:
    """Get red packet balance for a Telegram user"""
    if not redpacket_client or not redpacket_available:
        return {"error": "Red packet client not available"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{redpacket_client['api_url']}/wallet/balance",
                headers={
                    "Authorization": f"Bearer {redpacket_client['api_key']}",
                    "X-Telegram-User-Id": str(tg_id),
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
    except Exception as e:
        return {"error": str(e)}


async def redpacket_send_packet(tg_id: int, amount: float, count: int, message: str = "🤖 AI 紅包") -> dict:
    """Send a red packet"""
    if not redpacket_client or not redpacket_available:
        return {"error": "Red packet client not available"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{redpacket_client['api_url']}/packets/send",
                headers={
                    "Authorization": f"Bearer {redpacket_client['api_key']}",
                    "X-Telegram-User-Id": str(tg_id),
                    "Content-Type": "application/json",
                },
                json={
                    "total_amount": amount,
                    "total_count": count,
                    "currency": "usdt",
                    "packet_type": "random",
                    "message": message,
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
    except Exception as e:
        return {"error": str(e)}


async def redpacket_claim_packet(tg_id: int, packet_uuid: str) -> dict:
    """Claim a red packet"""
    if not redpacket_client or not redpacket_available:
        return {"error": "Red packet client not available"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{redpacket_client['api_url']}/packets/claim",
                headers={
                    "Authorization": f"Bearer {redpacket_client['api_key']}",
                    "X-Telegram-User-Id": str(tg_id),
                    "Content-Type": "application/json",
                },
                json={"packet_uuid": packet_uuid}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
    except Exception as e:
        return {"error": str(e)}

def load_excel_config():
    """
    Load account configuration from Excel file in sessions folder
    
    === EXCEL 格式規範 ===
    
    必需列（至少需要 phone）:
    - api_id     : Telegram API ID（數字）
    - api_hash   : Telegram API Hash（32位字符串）
    - phone      : 電話號碼（用於匹配 session 文件）
    
    可選列（用於帳號管理）:
    - username   : 用戶名（自動填充）
    - name       : 昵稱/名字（自動填充）
    - user_id    : Telegram 數字 ID（自動填充）
    - friends    : 好友數量（自動填充）
    - groups     : 群組數量（自動填充）
    - group      : 分組名稱（手動填寫，用於分類）
    - remark     : 備註（手動填寫）
    - node       : 指定節點（可選，如 computer_001）
    - enabled    : 是否啟用（1=啟用，0=禁用）
    - last_update: 最後更新時間（自動填充）
    
    === 列名別名支持 ===
    - api_id: apiid, API_ID, APIID
    - api_hash: apihash, API_HASH, APIHASH
    - phone: 手机, 手機, 电话, 電話, mobile
    - name: 名字, 昵称, 暱稱, nickname
    - group: 分组, 分組, category
    - remark: 备注, 備註, note, notes
    """
    global excel_config, CONFIG
    
    sessions_dir = Path(CONFIG["sessions_dir"])
    excel_files = list(sessions_dir.glob("*.xlsx")) + list(sessions_dir.glob("*.xls"))
    
    if not excel_files:
        log("[EXCEL] No config file found in sessions folder")
        log("[EXCEL] Expected: sessions/*.xlsx with columns: api_id, api_hash, phone")
        return None
    
    if not openpyxl_available:
        log("[EXCEL] openpyxl not installed. Run: pip install openpyxl")
        return None
    
    excel_file = excel_files[0]
    log(f"[EXCEL] Loading: {excel_file.name}")
    
    try:
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
        
        # Read headers (first row)
        headers = [str(cell.value).lower().strip() if cell.value else "" for cell in ws[1]]
        log(f"[EXCEL] Columns found: {[h for h in headers if h]}")
        
        # Map column names to indices (支持多種別名)
        col_map = {}
        column_aliases = {
            'api_id': ['api_id', 'apiid', 'api-id', 'telegram_api_id'],
            'api_hash': ['api_hash', 'apihash', 'api-hash', 'telegram_api_hash'],
            'phone': ['phone', '手机', '手機', '电话', '電話', 'mobile', 'tel'],
            'username': ['username', '用户名', '用戶名', 'user'],
            'name': ['name', '名字', '昵称', '暱稱', 'nickname', 'first_name'],
            'user_id': ['user_id', 'userid', 'tg_id', 'telegram_id', 'id'],
            'node': ['node', '节点', '節點', '电脑', '電腦', 'computer'],
            'group': ['group', '分组', '分組', 'category', '类别', '類別'],
            'remark': ['remark', '备注', '備註', 'note', 'notes', '说明'],
            'friends': ['friends', '好友', '好友数', 'contacts'],
            'groups': ['groups', '群组', '群組', '群数', 'chats'],
            'enabled': ['enabled', '启用', '啟用', 'active', 'status'],
            'last_update': ['last_update', '更新时间', '更新時間', 'updated'],
            'redpacket_enabled': ['redpacket_enabled', '红包启用', '紅包啟用', 'redpacket'],
        }
        
        for col_name, aliases in column_aliases.items():
            for idx, h in enumerate(headers):
                if h in aliases:
                    col_map[col_name] = idx
                    break
        
        log(f"[EXCEL] Mapped columns: {list(col_map.keys())}")
        
        # Validate required columns
        if 'phone' not in col_map:
            log("[EXCEL] ERROR: 'phone' column is required!")
            return None
        
        # Read account data
        accounts_loaded = 0
        
        for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
            row_data = [cell.value for cell in row]
            
            # Skip empty rows
            if not row_data or not any(row_data):
                continue
            
            # Get phone (required)
            phone_val = row_data[col_map['phone']] if 'phone' in col_map else None
            if not phone_val:
                continue
            
            phone = str(phone_val).strip()
            phone_key = phone.replace(' ', '').replace('+', '').replace('-', '')
            
            # Get api_id and api_hash for this account
            api_id = None
            api_hash = None
            
            if 'api_id' in col_map and row_data[col_map['api_id']]:
                try:
                    api_id = int(row_data[col_map['api_id']])
                except:
                    pass
            
            if 'api_hash' in col_map and row_data[col_map['api_hash']]:
                api_hash = str(row_data[col_map['api_hash']]).strip()
            
            # Check if enabled (default: True)
            enabled = True
            if 'enabled' in col_map and row_data[col_map['enabled']] is not None:
                enabled = bool(row_data[col_map['enabled']])
            
            # Get redpacket enabled status
            redpacket_enabled = True
            if 'redpacket_enabled' in col_map and row_data[col_map['redpacket_enabled']] is not None:
                redpacket_enabled = bool(row_data[col_map['redpacket_enabled']])
            
            # Store config
            excel_config[phone_key] = {
                'phone': phone,
                'api_id': api_id,
                'api_hash': api_hash,
                'row_idx': row_idx,
                'enabled': enabled,
                'redpacket_enabled': redpacket_enabled,
                'node': row_data[col_map['node']] if 'node' in col_map and row_data[col_map['node']] else None,
                'group': row_data[col_map['group']] if 'group' in col_map and row_data[col_map['group']] else None,
                'name': row_data[col_map['name']] if 'name' in col_map and row_data[col_map['name']] else None,
                'remark': row_data[col_map['remark']] if 'remark' in col_map and row_data[col_map['remark']] else None,
                'username': row_data[col_map['username']] if 'username' in col_map and row_data[col_map['username']] else None,
                'user_id': int(row_data[col_map['user_id']]) if 'user_id' in col_map and row_data[col_map['user_id']] else None,
            }
            accounts_loaded += 1
            
            if api_id and api_hash:
                log(f"[EXCEL] Account: {phone} -> API_ID={api_id}, enabled={enabled}")
        
        # Set default API credentials from first account (fallback)
        if not CONFIG['api_id'] or not CONFIG['api_hash']:
            for phone_key, acc in excel_config.items():
                if acc.get('api_id') and acc.get('api_hash'):
                    CONFIG['api_id'] = acc['api_id']
                    CONFIG['api_hash'] = acc['api_hash']
                    log(f"[EXCEL] Default API credentials from: {acc['phone']}")
                    break
        
        log(f"[EXCEL] Loaded {accounts_loaded} accounts from Excel")
        
        # Store workbook info for later updates
        return {'wb': wb, 'ws': ws, 'col_map': col_map, 'file': excel_file}
        
    except Exception as e:
        log(f"[EXCEL] Error loading: {e}")
        import traceback
        traceback.print_exc()
        return None

excel_workbook_info = None  # Global reference for updating Excel


def create_sample_excel():
    """
    Create a sample Excel config file if none exists
    """
    if not openpyxl_available:
        log("[EXCEL] Cannot create sample: openpyxl not installed")
        return None
    
    sessions_dir = Path(CONFIG["sessions_dir"])
    if not sessions_dir.exists():
        sessions_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if Excel already exists
    excel_files = list(sessions_dir.glob("*.xlsx"))
    if excel_files:
        log(f"[EXCEL] Config file already exists: {excel_files[0].name}")
        return None
    
    sample_file = sessions_dir / "accounts_config.xlsx"
    log(f"[EXCEL] Creating sample config: {sample_file.name}")
    
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Accounts"
        
        # Headers
        headers = [
            'api_id', 'api_hash', 'phone', 'username', 'name', 'user_id',
            'friends', 'groups', 'group', 'remark', 'enabled', 'last_update'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = openpyxl.styles.Font(bold=True)
        
        # Sample data row
        sample_data = [
            30390800,  # api_id
            '471481f784e6d78893e53b88ee43e62b',  # api_hash
            '+639277358115',  # phone
            '',  # username (auto-fill)
            '',  # name (auto-fill)
            '',  # user_id (auto-fill)
            '',  # friends (auto-fill)
            '',  # groups (auto-fill)
            'Group A',  # group
            'Main account',  # remark
            1,  # enabled
            '',  # last_update (auto-fill)
        ]
        
        for col, value in enumerate(sample_data, 1):
            ws.cell(row=2, column=col, value=value)
        
        # Adjust column widths
        col_widths = [12, 35, 18, 15, 15, 15, 10, 10, 12, 20, 10, 18]
        for i, width in enumerate(col_widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
        
        wb.save(sample_file)
        wb.close()
        
        log(f"[EXCEL] Sample config created: {sample_file.name}")
        log("[EXCEL] Please edit this file and add your accounts!")
        
        return sample_file
        
    except Exception as e:
        log(f"[EXCEL] Error creating sample: {e}")
        return None


def auto_match_sessions_to_excel():
    """
    Auto-match session files to Excel config by phone number
    Reports unmatched sessions
    """
    sessions_dir = Path(CONFIG["sessions_dir"])
    session_files = list(sessions_dir.glob("*.session"))
    
    if not session_files:
        log("[MATCH] No session files found")
        return
    
    if not excel_config:
        log("[MATCH] No Excel config loaded")
        return
    
    matched = []
    unmatched = []
    
    for session_file in session_files:
        session_phone = session_file.stem.replace('+', '').replace('-', '').replace(' ', '')
        
        # Try to find matching Excel entry
        found = False
        for phone_key in excel_config.keys():
            if (phone_key == session_phone or 
                session_phone.endswith(phone_key) or 
                phone_key.endswith(session_phone)):
                matched.append((session_file.name, phone_key))
                found = True
                break
        
        if not found:
            unmatched.append(session_file.name)
    
    log(f"[MATCH] Matched: {len(matched)}, Unmatched: {len(unmatched)}")
    
    if unmatched:
        log("[MATCH] Unmatched sessions (add to Excel):")
        for name in unmatched:
            log(f"  - {name}")
    
    return {"matched": matched, "unmatched": unmatched}

async def fetch_and_update_excel():
    """
    Fetch account details from Telegram and update Excel file
    Auto-fills: username, name, user_id, friends, groups, last_update
    """
    if not telethon_available:
        log("[EXCEL-UPDATE] Telethon not installed")
        return
    
    if not openpyxl_available:
        log("[EXCEL-UPDATE] openpyxl not installed")
        return
    
    sessions_dir = Path(CONFIG["sessions_dir"])
    excel_files = list(sessions_dir.glob("*.xlsx"))
    if not excel_files:
        log("[EXCEL-UPDATE] No Excel file to update")
        return
    
    excel_file = excel_files[0]
    log(f"[EXCEL-UPDATE] Updating: {excel_file.name}")
    
    try:
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
        
        # Read existing headers
        headers = [str(cell.value).lower().strip() if cell.value else "" for cell in ws[1]]
        
        # Build column map with aliases
        col_map = {}
        column_aliases = {
            'api_id': ['api_id', 'apiid'],
            'api_hash': ['api_hash', 'apihash'],
            'phone': ['phone', '手机', '手機', '电话'],
            'username': ['username', '用户名', '用戶名'],
            'name': ['name', '名字', '昵称', '暱稱'],
            'user_id': ['user_id', 'userid', 'tg_id', 'telegram_id'],
            'friends': ['friends', '好友', '好友数'],
            'groups': ['groups', '群组', '群組', '群数'],
            'last_update': ['last_update', '更新时间', '更新時間'],
        }
        
        for col_name, aliases in column_aliases.items():
            for idx, h in enumerate(headers):
                if h in aliases:
                    col_map[col_name] = idx
                    break
        
        # Add missing columns for auto-fill
        next_col = len(headers) + 1
        auto_cols = ['user_id', 'username', 'name', 'friends', 'groups', 'last_update']
        
        for col_name in auto_cols:
            if col_name not in col_map:
                ws.cell(row=1, column=next_col, value=col_name)
                col_map[col_name] = next_col - 1
                next_col += 1
                log(f"[EXCEL-UPDATE] Added column: {col_name}")
        
        # Fetch and update each account
        updated_count = 0
        
        for session_file in sessions_dir.glob("*.session"):
            session_phone = session_file.stem.replace('+', '').replace('-', '').replace(' ', '')
            
            # Find row for this phone
            target_row = None
            row_api_id = None
            row_api_hash = None
            
            for row_idx in range(2, ws.max_row + 1):
                cell_phone = ws.cell(row=row_idx, column=col_map['phone'] + 1).value
                if cell_phone:
                    cell_phone_key = str(cell_phone).replace('+', '').replace('-', '').replace(' ', '')
                    # Match by phone number
                    if cell_phone_key == session_phone or session_phone.endswith(cell_phone_key) or cell_phone_key.endswith(session_phone):
                        target_row = row_idx
                        # Get API credentials from this row
                        if 'api_id' in col_map:
                            try:
                                row_api_id = int(ws.cell(row=row_idx, column=col_map['api_id'] + 1).value)
                            except: pass
                        if 'api_hash' in col_map:
                            row_api_hash = ws.cell(row=row_idx, column=col_map['api_hash'] + 1).value
                        break
            
            if not target_row:
                log(f"[EXCEL-UPDATE] No matching row for: {session_phone}")
                continue
            
            # Use row-specific or fallback API credentials
            api_id = row_api_id or CONFIG.get('api_id')
            api_hash = row_api_hash or CONFIG.get('api_hash')
            
            if not api_id or not api_hash:
                log(f"[EXCEL-UPDATE] No API credentials for: {session_phone}")
                continue
            
            # Connect and fetch account info
            try:
                client = TelegramClient(
                    str(session_file).replace('.session', ''),
                    api_id,
                    api_hash
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
                    
                    # Update Excel cells
                    username = me.username or ""
                    name = f"{me.first_name or ''} {me.last_name or ''}".strip()
                    
                    ws.cell(row=target_row, column=col_map['user_id'] + 1, value=me.id)
                    ws.cell(row=target_row, column=col_map['username'] + 1, value=username)
                    ws.cell(row=target_row, column=col_map['name'] + 1, value=name)
                    ws.cell(row=target_row, column=col_map['friends'] + 1, value=friends_count)
                    ws.cell(row=target_row, column=col_map['groups'] + 1, value=groups_count)
                    ws.cell(row=target_row, column=col_map['last_update'] + 1, value=datetime.now().strftime("%Y-%m-%d %H:%M"))
                    
                    log(f"[EXCEL-UPDATE] {session_phone}: ID={me.id}, @{username}, {friends_count} friends, {groups_count} groups")
                    updated_count += 1
                else:
                    log(f"[EXCEL-UPDATE] Not authorized: {session_phone}")
                
                await client.disconnect()
                await asyncio.sleep(2)  # Rate limit
                
            except Exception as e:
                log(f"[EXCEL-UPDATE] Error for {session_phone}: {e}")
        
        # Save Excel
        wb.save(excel_file)
        wb.close()
        log(f"[EXCEL-UPDATE] Saved! Updated {updated_count} accounts")
        
    except Exception as e:
        log(f"[EXCEL-UPDATE] Error: {e}")
        import traceback
        traceback.print_exc()

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
    """
    Read basic info from Telethon session file (SQLite)
    Extracts: user_id, username, name, phone, dc_id
    """
    info = {
        "session_file": session_path.name, 
        "account_id": session_path.stem,
        "user_id": None,
        "username": "",
        "name": "",
        "phone": "",
        "dc_id": None,
    }
    
    try:
        conn = sqlite3.connect(str(session_path))
        cursor = conn.cursor()
        
        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        log(f"[SESSION] {session_path.name} tables: {tables}")
        
        # Method 1: Read from 'sessions' table (Telethon v1.24+)
        # 兼容不同版本的数据库架构
        if 'sessions' in tables:
            try:
                # 先检查表结构，只查询存在的列
                cursor.execute("PRAGMA table_info(sessions)")
                session_columns = [row[1] for row in cursor.fetchall()]
                
                # 构建查询（只查询存在的列）
                select_cols = []
                if 'dc_id' in session_columns:
                    select_cols.append('dc_id')
                if 'server_address' in session_columns:
                    select_cols.append('server_address')
                if 'port' in session_columns:
                    select_cols.append('port')
                if 'auth_key' in session_columns:
                    select_cols.append('auth_key')
                
                if select_cols:
                    query = f"SELECT {', '.join(select_cols)} FROM sessions LIMIT 1"
                    cursor.execute(query)
                    row = cursor.fetchone()
                    if row:
                        # 根据列顺序获取值
                        for i, col in enumerate(select_cols):
                            if col == 'dc_id':
                                info["dc_id"] = row[i]
                            # auth_key contains encrypted user data
            except Exception as e:
                log(f"[SESSION] sessions table error: {e}")
                # 如果读取失败，尝试修复 Session 文件
                try:
                    # 添加缺失的列
                    if 'server_address' not in session_columns:
                        cursor.execute("ALTER TABLE sessions ADD COLUMN server_address TEXT")
                    if 'port' not in session_columns:
                        cursor.execute("ALTER TABLE sessions ADD COLUMN port INTEGER")
                    conn.commit()
                    log(f"[SESSION] 已修复 sessions 表结构")
                except:
                    pass
        
        # Method 2: Read from 'entities' table - this has user info
        if 'entities' in tables:
            try:
                # First, try to find "self" entity (the account owner)
                cursor.execute("SELECT id, username, name, phone FROM entities ORDER BY id ASC LIMIT 20")
                entities = cursor.fetchall()
                
                for entity in entities:
                    eid, username, name, phone = entity
                    log(f"[SESSION] Entity: id={eid}, user={username}, name={name}, phone={phone}")
                    
                    # Positive IDs are users, negative are chats/channels
                    if eid and eid > 0:
                        # If has phone, it's likely the account owner
                        if phone:
                            info["user_id"] = int(eid)
                            info["username"] = username or ""
                            info["name"] = name or ""
                            info["phone"] = phone
                            break
                        # If no phone but has username, it might be self
                        elif username and not info["user_id"]:
                            info["user_id"] = int(eid)
                            info["username"] = username or ""
                            info["name"] = name or ""
                
            except Exception as e:
                log(f"[SESSION] entities table error: {e}")
        
        # Method 3: Read from 'peers' table (older Telethon versions)
        if 'peers' in tables and not info["user_id"]:
            try:
                cursor.execute("SELECT id FROM peers WHERE id > 0 LIMIT 1")
                row = cursor.fetchone()
                if row:
                    info["user_id"] = int(row[0])
                    log(f"[SESSION] Found user_id from peers: {info['user_id']}")
            except Exception as e:
                log(f"[SESSION] peers table error: {e}")
        
        # Method 4: Read from 'sent_files' or 'update_state' for self info
        if 'update_state' in tables and not info["user_id"]:
            try:
                cursor.execute("SELECT * FROM update_state LIMIT 1")
                row = cursor.fetchone()
                if row:
                    log(f"[SESSION] update_state: {row}")
            except:
                pass
        
        # Method 5: 检查并修复 version 表（如果缺失）
        if 'version' not in tables:
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS version (version INTEGER)")
                cursor.execute("INSERT OR IGNORE INTO version (version) VALUES (1)")
                conn.commit()
                log(f"[SESSION] 已自动创建 version 表")
            except Exception as e:
                log(f"[SESSION] 创建 version 表失败: {e}")
        else:
            # 检查 version 表是否有数据
            try:
                cursor.execute("SELECT COUNT(*) FROM version")
                count = cursor.fetchone()[0]
                if count == 0:
                    cursor.execute("INSERT OR IGNORE INTO version (version) VALUES (1)")
                    conn.commit()
                    log(f"[SESSION] 已自动填充 version 表数据")
            except:
                pass
        
        # Method 4: Try to get user_id from session filename if it's a phone number
        if not info["user_id"]:
            filename = session_path.stem
            # Check if filename looks like a phone number
            clean_name = filename.replace('+', '').replace('-', '').replace(' ', '')
            if clean_name.isdigit() and len(clean_name) >= 10:
                info["phone"] = filename
                log(f"[SESSION] Phone from filename: {filename}")
        
        conn.close()
        
        if info["user_id"]:
            log(f"[SESSION] Found: user_id={info['user_id']}, @{info['username']}, {info['name']}, phone={info['phone']}")
        else:
            log(f"[SESSION] No user_id found for {session_path.name}")
        
        return info
        
    except Exception as e:
        log(f"[SESSION] Error reading {session_path.name}: {e}")
        return info

async def get_account_stats(session_path):
    """
    Get detailed account stats using Telethon
    This is the MOST RELIABLE way to get user_id
    
    Uses per-account API credentials from Excel if available
    """
    if not telethon_available:
        log(f"[TELETHON] Not available: telethon not installed")
        return None
    
    # Get phone from session filename
    session_phone = session_path.stem.replace('+', '').replace('-', '').replace(' ', '')
    
    # Look up API credentials for this account from Excel config
    api_id = None
    api_hash = None
    
    # Try to find matching config by phone
    for phone_key, acc_config in excel_config.items():
        if phone_key == session_phone or session_phone.endswith(phone_key) or phone_key.endswith(session_phone):
            api_id = acc_config.get('api_id')
            api_hash = acc_config.get('api_hash')
            if api_id and api_hash:
                log(f"[TELETHON] Using Excel config for {session_phone}: API_ID={api_id}")
                break
    
    # Fallback to global config
    if not api_id or not api_hash:
        api_id = CONFIG.get("api_id")
        api_hash = CONFIG.get("api_hash")
    
    if not api_id or not api_hash:
        log(f"[TELETHON] No API credentials for: {session_path.name}")
        return None
    
    try:
        session_name = str(session_path).replace('.session', '')
        log(f"[TELETHON] Connecting: {session_path.name} (API_ID={api_id})")
        
        client = TelegramClient(
            session_name,
            api_id,
            api_hash
        )
        
        await client.connect()
        
        if not await client.is_user_authorized():
            log(f"[TELETHON] Not authorized: {session_path.name}")
            await client.disconnect()
            return {"error": "Not authorized", "session_file": session_path.name}
        
        # Get current user info - THIS IS THE KEY!
        me = await client.get_me()
        
        stats = {
            "user_id": me.id,  # This is the numeric Telegram user ID!
            "tg_id": me.id,    # Alias for red packet system
            "username": me.username or "",
            "first_name": me.first_name or "",
            "last_name": me.last_name or "",
            "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
            "phone": me.phone or "",
            "is_bot": me.bot,
            "session_file": session_path.name,
        }
        
        log(f"[TELETHON] Got user: id={me.id}, @{me.username}, phone={me.phone}")
        
        # Get contacts (friends)
        try:
            contacts = await client(GetContactsRequest(hash=0))
            stats["friends_count"] = len(contacts.users) if hasattr(contacts, 'users') else 0
        except Exception as e:
            log(f"[TELETHON] Contacts error: {e}")
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
        except Exception as e:
            log(f"[TELETHON] Dialogs error: {e}")
            stats["groups_count"] = 0
            stats["channels_count"] = 0
        
        # Get recent contacts added (last 24h)
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
        log(f"[TELETHON] Error for {session_path.name}: {e}")
        return {"error": str(e), "session_file": session_path.name}

def scan_sessions_sync():
    """
    Scan sessions folder and collect account info
    Merges data from: session file + Excel config + cache
    
    Priority: Cache > Telethon > Excel > Session file
    """
    sessions_dir = Path(CONFIG["sessions_dir"])
    accounts = []
    
    if not sessions_dir.exists():
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return accounts
    
    session_files = list(sessions_dir.glob("*.session"))
    log(f"[SCAN] Found {len(session_files)} session files")
    
    for f in session_files:
        cache_key = f.name
        session_phone = f.stem.replace(' ', '').replace('+', '').replace('-', '')
        
        if cache_key in account_cache:
            # Use cached data
            cached = account_cache[cache_key].copy()
            cached["status"] = "available"
            accounts.append(cached)
        else:
            # Read basic info from session file
            info = read_session_basic(f)
            info["status"] = "available"
            info["node_id"] = CONFIG["node_id"]
            info["session_path"] = str(f)
            
            # Try to find matching Excel config
            excel_data = None
            phone = info.get("phone", "").replace(' ', '').replace('+', '').replace('-', '')
            
            # Try multiple matching strategies
            for phone_key, acc_config in excel_config.items():
                if (phone_key == session_phone or 
                    phone_key == phone or
                    session_phone.endswith(phone_key) or 
                    phone_key.endswith(session_phone)):
                    excel_data = acc_config
                    break
            
            if excel_data:
                # Merge Excel data
                info["excel_phone"] = excel_data.get("phone")
                info["excel_name"] = excel_data.get("name")
                info["excel_group"] = excel_data.get("group")
                info["excel_remark"] = excel_data.get("remark")
                info["excel_node"] = excel_data.get("node")
                info["excel_enabled"] = excel_data.get("enabled", True)
                
                # Use Excel user_id if available and not already set
                if excel_data.get("user_id") and not info.get("user_id"):
                    info["user_id"] = excel_data["user_id"]
                    info["tg_id"] = excel_data["user_id"]
                
                # Use Excel username if available
                if excel_data.get("username") and not info.get("username"):
                    info["username"] = excel_data["username"]
                
                # Use Excel name if available
                if excel_data.get("name"):
                    info["name"] = excel_data["name"]
                
                # Store API credentials for this account
                if excel_data.get("api_id") and excel_data.get("api_hash"):
                    info["has_api_credentials"] = True
                
                log(f"[SCAN] Matched Excel: {session_phone} -> {excel_data.get('phone')}")
            
            account_cache[cache_key] = info
            accounts.append(info)
    
    return accounts


def print_accounts_summary():
    """Print a nice summary of all accounts found"""
    accounts = list(account_cache.values())
    
    if not accounts:
        log("=" * 60)
        log("  NO ACCOUNTS FOUND")
        log("  Please add .session files to the 'sessions' folder")
        log("=" * 60)
        return
    
    log("=" * 60)
    log(f"  ACCOUNTS SUMMARY ({len(accounts)} total)")
    log("=" * 60)
    
    # Print table header
    log(f"{'#':<3} {'Telegram ID':<15} {'Username':<20} {'Phone':<15} {'Name':<15}")
    log("-" * 60)
    
    # Print each account
    for i, acc in enumerate(accounts, 1):
        tg_id = acc.get('user_id') or acc.get('tg_id') or 'N/A'
        username = acc.get('username', '')[:18] or '-'
        phone = acc.get('phone', '')[:13] or '-'
        name = acc.get('name', '')[:13] or '-'
        
        log(f"{i:<3} {str(tg_id):<15} @{username:<19} {phone:<15} {name:<15}")
    
    log("-" * 60)
    
    # Count accounts with user_id
    with_id = sum(1 for a in accounts if a.get('user_id') or a.get('tg_id'))
    log(f"  Accounts with Telegram ID: {with_id}/{len(accounts)}")
    
    # If missing IDs, suggest using Telethon
    if with_id < len(accounts):
        log("")
        log("  TIP: Install Telethon and set API_ID/API_HASH to get all IDs")
        log("       pip install telethon")
    
    log("=" * 60)
    
    # Export as JSON for red packet system
    export_data = []
    for acc in accounts:
        if acc.get('user_id') or acc.get('tg_id'):
            export_data.append({
                "tg_id": acc.get('user_id') or acc.get('tg_id'),
                "username": acc.get('username', ''),
                "phone": acc.get('phone', ''),
                "name": acc.get('name', '') or acc.get('first_name', ''),
            })
    
    if export_data:
        log("")
        log("  JSON FOR RED PACKET SYSTEM (copy this):")
        log("-" * 60)
        print(json.dumps(export_data, indent=2, ensure_ascii=False))
        log("-" * 60)

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
        elif action == "redpacket_balance":
            # Get red packet balance for an account
            tg_id = params.get("tg_id")
            if tg_id:
                result = asyncio.get_event_loop().run_until_complete(redpacket_get_balance(tg_id))
                log(f"[CMD] Red packet balance: {result}")
        elif action == "redpacket_send":
            # Send a red packet
            tg_id = params.get("tg_id")
            amount = params.get("amount", 1.0)
            count = params.get("count", 5)
            message = params.get("message", "🤖 AI 紅包")
            if tg_id:
                result = asyncio.get_event_loop().run_until_complete(
                    redpacket_send_packet(tg_id, amount, count, message)
                )
                log(f"[CMD] Red packet sent: {result}")
        elif action == "redpacket_claim":
            # Claim a red packet
            tg_id = params.get("tg_id")
            packet_uuid = params.get("packet_uuid")
            if tg_id and packet_uuid:
                result = asyncio.get_event_loop().run_until_complete(
                    redpacket_claim_packet(tg_id, packet_uuid)
                )
                log(f"[CMD] Red packet claimed: {result}")
        else:
            log(f"[CMD] Unknown: {action}")

async def main_async():
    """Async main loop"""
    global last_stats_update
    
    log("")
    log("=" * 60)
    log("  WORKER NODE STARTING")
    log("=" * 60)
    log(f"  Node ID:    {CONFIG['node_id']}")
    log(f"  Server:     {CONFIG['server_url']}")
    log(f"  Sessions:   {CONFIG['sessions_dir']}")
    log(f"  Heartbeat:  {CONFIG['heartbeat_interval']}s")
    log("")
    log(f"  Telethon:   {'YES' if telethon_available else 'NO (pip install telethon)'}")
    log(f"  API ID:     {'SET' if CONFIG['api_id'] else 'NOT SET'}")
    log(f"  API Hash:   {'SET' if CONFIG['api_hash'] else 'NOT SET'}")
    log(f"  openpyxl:   {'YES' if openpyxl_available else 'NO (pip install openpyxl)'}")
    log(f"  Red Packet: {'YES' if redpacket_available else 'NO (pip install httpx)'}")
    log("=" * 60)
    
    # Load Excel config first
    load_excel_config()
    
    # Initialize red packet client
    if CONFIG.get("redpacket_api_url"):
        init_redpacket_client()
    
    # Do initial session scan
    log("")
    log("[INIT] Scanning sessions folder...")
    scan_sessions_sync()
    
    # If Telethon is available, fetch detailed stats
    if telethon_available and CONFIG["api_id"] and CONFIG["api_hash"]:
        log("")
        log("[INIT] Fetching account details via Telethon...")
        await update_all_stats()
    else:
        log("")
        log("[INIT] Telethon not configured - using basic session info only")
        log("[INIT] To get Telegram user_id, set TELEGRAM_API_ID and TELEGRAM_API_HASH")
    
    # Print summary of all accounts found
    print_accounts_summary()
    
    log("")
    log("[WORKER] Starting heartbeat loop...")
    log("")
    
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
                "worker_client": worker_client,
                "fix_session": fix_session_script,
                "create_excel_template": create_excel_template
            },
            "instructions": {
                "windows": "1. 下載所有文件到同一目錄\n2. 將 Telegram .session 文件放入 sessions 目錄\n3. 運行 create_excel_template.py 創建 Excel 配置模板\n4. 編輯 Excel 文件，添加 API ID/Hash 和電話號碼\n5. 如果 Session 文件讀取錯誤，運行: python fix_session.py sessions\n6. 雙擊 start_worker.bat 運行",
                "linux": "1. 下載所有文件到同一目錄\n2. 將 Telegram .session 文件放入 sessions 目錄\n3. 運行 python3 create_excel_template.py 創建 Excel 配置模板\n4. 編輯 Excel 文件，添加 API ID/Hash 和電話號碼\n5. 如果 Session 文件讀取錯誤，運行: python3 fix_session.py sessions\n6. 運行: chmod +x start_worker.sh && ./start_worker.sh"
            }
        }
    except Exception as e:
        logger.error(f"生成部署包失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成部署包失敗: {str(e)}"
        )


@router.get("/accounts/telegram-ids", status_code=status.HTTP_200_OK)
async def get_all_telegram_ids(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    獲取所有 Worker 節點上的 Telegram 帳號 ID 列表
    用於紅包遊戲系統對接
    """
    try:
        workers_data = _get_all_workers()
        
        # 收集所有帳號
        all_accounts = []
        seen_ids = set()
        
        for node_id, data in workers_data.items():
            accounts = data.get("accounts", [])
            for acc in accounts:
                # 獲取 user_id 或 tg_id
                tg_id = acc.get("user_id") or acc.get("tg_id")
                if tg_id and tg_id not in seen_ids:
                    seen_ids.add(tg_id)
                    all_accounts.append({
                        "tg_id": tg_id,
                        "username": acc.get("username", ""),
                        "name": acc.get("name", "") or acc.get("first_name", ""),
                        "phone": acc.get("phone", ""),
                        "node_id": node_id,
                        "status": acc.get("status", "available"),
                    })
        
        # 按 tg_id 排序
        all_accounts.sort(key=lambda x: x["tg_id"] if x["tg_id"] else 0)
        
        return {
            "success": True,
            "total_count": len(all_accounts),
            "accounts": all_accounts,
            "format_for_redpacket": [
                {"tg_id": a["tg_id"], "name": a["name"] or a["username"] or f"AI_{a['tg_id']}"} 
                for a in all_accounts if a["tg_id"]
            ]
        }
    except Exception as e:
        logger.error(f"獲取 Telegram ID 列表失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取 Telegram ID 列表失敗: {str(e)}"
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

