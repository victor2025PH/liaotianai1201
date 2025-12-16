"""
Workers API - 分布式节点管理系统
用于管理本地电脑和远程服务器节点
"""

import logging
import json
import time
import base64
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File
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
_worker_responses: Dict[str, Dict[str, Any]] = {}  # 存储 Worker 节点的响应结果

# Redis 客户端（如果可用）
_redis_client = None
_redis_pubsub = None
try:
    import redis
    settings = get_settings()
    if settings.redis_url:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        _redis_pubsub = _redis_client.pubsub()
        logger.info("Workers API: Redis 已启用")
    else:
        logger.info("Workers API: Redis 未配置，使用内存存储")
except Exception as e:
    logger.warning(f"Workers API: Redis 不可用，使用内存存储: {e}")
    _redis_client = None
    _redis_pubsub = None


# ============ 数据模型 ============

class WorkerHeartbeatRequest(BaseModel):
    """Worker 节点心跳请求"""
    node_id: str = Field(..., description="节点ID，如 computer_001, computer_002")
    status: str = Field(default="online", description="节点状态: online, offline")
    account_count: int = Field(default=0, description="账号数量")
    accounts: List[Dict[str, Any]] = Field(default_factory=list, description="账号列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")
    # 新增：Worker 节点可以返回命令执行结果
    command_responses: Optional[Dict[str, Any]] = Field(default=None, description="命令执行结果")


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


class SessionFileInfo(BaseModel):
    """Session 文件信息"""
    filename: str
    size: int
    modified_time: Optional[str] = None
    path: Optional[str] = None


class SessionListResponse(BaseModel):
    """Session 列表响应"""
    success: bool
    node_id: str
    sessions: List[SessionFileInfo]
    total: int
    message: str


class SessionUploadResponse(BaseModel):
    """Session 上传响应"""
    success: bool
    node_id: str
    filename: str
    message: str


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


def _get_response_key(node_id: str, command_id: str) -> str:
    """获取命令响应存储的键"""
    return f"worker:response:{node_id}:{command_id}"


def _save_worker_status(node_id: str, data: Dict[str, Any]) -> None:
    """保存 Worker 节点状态"""
    data["last_heartbeat"] = datetime.now().isoformat()
    
    if _redis_client:
        try:
            key = _get_worker_key(node_id)
            _redis_client.setex(key, 120, json.dumps(data))
            _redis_client.sadd(_get_workers_set_key(), node_id)
            _redis_client.expire(_get_workers_set_key(), 120)
        except Exception as e:
            logger.error(f"保存 Worker 状态到 Redis 失败: {e}")
            _workers_memory_store[node_id] = data
    else:
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
            return _workers_memory_store.get(node_id)
    else:
        return _workers_memory_store.get(node_id)


def _get_all_workers() -> Dict[str, Dict[str, Any]]:
    """获取所有 Worker 节点状态"""
    workers = {}
    
    if _redis_client:
        try:
            node_ids = _redis_client.smembers(_get_workers_set_key())
            for node_id in node_ids:
                status_data = _get_worker_status(node_id)
                if status_data:
                    workers[node_id] = status_data
        except Exception as e:
            logger.error(f"从 Redis 获取所有 Workers 失败: {e}")
            workers = _workers_memory_store.copy()
    else:
        workers = _workers_memory_store.copy()
    
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


def _save_response(node_id: str, command_id: str, response: Dict[str, Any]) -> None:
    """保存 Worker 节点的响应结果"""
    response["timestamp"] = datetime.now().isoformat()
    
    if _redis_client:
        try:
            key = _get_response_key(node_id, command_id)
            _redis_client.setex(key, 60, json.dumps(response))  # TTL: 60秒
        except Exception as e:
            logger.error(f"保存响应到 Redis 失败: {e}")
            if node_id not in _worker_responses:
                _worker_responses[node_id] = {}
            _worker_responses[node_id][command_id] = response
    else:
        if node_id not in _worker_responses:
            _worker_responses[node_id] = {}
        _worker_responses[node_id][command_id] = response


def _get_response(node_id: str, command_id: str) -> Optional[Dict[str, Any]]:
    """获取 Worker 节点的响应结果"""
    if _redis_client:
        try:
            key = _get_response_key(node_id, command_id)
            data = _redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"从 Redis 获取响应失败: {e}")
            return _worker_responses.get(node_id, {}).get(command_id)
    else:
        return _worker_responses.get(node_id, {}).get(command_id)


def _wait_for_response(node_id: str, command_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """等待 Worker 节点的响应（轮询方式）"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = _get_response(node_id, command_id)
        if response:
            return response
        time.sleep(0.5)  # 每 0.5 秒检查一次
    return None


# ============ API 端点 ============

@router.post("/heartbeat", status_code=status.HTTP_200_OK)
async def worker_heartbeat(
    request: WorkerHeartbeatRequest,
    db: Session = Depends(get_db_session)
):
    """
    Worker 节点心跳端点
    节点应每30秒调用一次此端点来报告状态
    
    新增功能：Worker 节点可以通过 command_responses 字段返回命令执行结果
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
        
        # 处理命令执行结果
        if request.command_responses:
            for command_id, response_data in request.command_responses.items():
                _save_response(request.node_id, command_id, response_data)
                logger.info(f"收到节点 {request.node_id} 的命令响应: {command_id}")
        
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
            "commands": commands,
            "count": len(commands)
        }
    except Exception as e:
        logger.error(f"获取命令失败: {e}", exc_info=True)
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
    广播命令到所有在线 Worker 节点
    """
    try:
        workers = _get_all_workers()
        online_workers = [node_id for node_id, data in workers.items() 
                         if data.get("status") == "online"]
        
        command = {
            "action": request.action,
            "params": request.params,
            "timestamp": datetime.now().isoformat(),
            "from": "master",
            "broadcast": True
        }
        
        for node_id in online_workers:
            _add_command(node_id, command)
        
        logger.info(f"广播命令 {request.action} 到 {len(online_workers)} 个节点")
        
        return {
            "success": True,
            "action": request.action,
            "nodes_count": len(online_workers),
            "nodes": online_workers,
            "message": f"命令已广播到 {len(online_workers)} 个节点"
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
    清除节点的命令队列
    """
    try:
        _clear_commands(node_id)
        logger.info(f"已清除节点 {node_id} 的命令队列")
        
        return {
            "success": True,
            "node_id": node_id,
            "message": f"节点 {node_id} 的命令队列已清除"
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


# ============ Session 管理 API ============

@router.get("/{worker_id}/sessions", response_model=SessionListResponse, status_code=status.HTTP_200_OK)
async def get_worker_sessions(
    worker_id: str,
    timeout: int = 30,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    获取 Worker 节点的 Session 文件列表
    
    工作流程：
    1. 检查 Worker 节点是否在线
    2. 生成唯一的命令 ID
    3. 通过命令队列发送 "list_sessions" 命令
    4. 等待 Worker 节点响应（通过心跳返回结果）
    5. 返回 Session 文件列表
    """
    try:
        # 检查 Worker 节点是否在线
        worker_status = _get_worker_status(worker_id)
        if not worker_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Worker 节点 {worker_id} 不存在"
            )
        
        if worker_status.get("status") != "online":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Worker 节点 {worker_id} 不在线"
            )
        
        # 生成唯一的命令 ID
        import uuid
        command_id = str(uuid.uuid4())
        
        # 发送命令到 Worker 节点
        command = {
            "action": "list_sessions",
            "params": {},
            "command_id": command_id,
            "timestamp": datetime.now().isoformat(),
            "from": "master"
        }
        
        _add_command(worker_id, command)
        logger.info(f"向节点 {worker_id} 发送 list_sessions 命令 (ID: {command_id})")
        
        # 等待响应（轮询方式）
        response = _wait_for_response(worker_id, command_id, timeout=timeout)
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"等待 Worker 节点 {worker_id} 响应超时（{timeout}秒）"
            )
        
        if not response.get("success"):
            error_msg = response.get("error", "未知错误")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Worker 节点执行失败: {error_msg}"
            )
        
        # 解析响应数据
        sessions_data = response.get("data", {}).get("sessions", [])
        sessions = []
        for session_info in sessions_data:
            sessions.append(SessionFileInfo(
                filename=session_info.get("filename", ""),
                size=session_info.get("size", 0),
                modified_time=session_info.get("modified_time"),
                path=session_info.get("path")
            ))
        
        return SessionListResponse(
            success=True,
            node_id=worker_id,
            sessions=sessions,
            total=len(sessions),
            message=f"成功获取 {len(sessions)} 个 Session 文件"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 Worker Session 列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Session 列表失败: {str(e)}"
        )


@router.post("/{worker_id}/sessions/upload", response_model=SessionUploadResponse, status_code=status.HTTP_200_OK)
async def upload_session_to_worker(
    worker_id: str,
    file: UploadFile = File(...),
    timeout: int = 60,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    上传 Session 文件到指定的 Worker 节点
    
    工作流程：
    1. 检查 Worker 节点是否在线
    2. 验证文件格式（必须是 .session 文件）
    3. 读取文件内容并编码为 base64
    4. 生成唯一的命令 ID
    5. 通过命令队列发送 "upload_session" 命令，包含文件内容
    6. 等待 Worker 节点响应
    7. 返回上传结果
    """
    try:
        # 检查 Worker 节点是否在线
        worker_status = _get_worker_status(worker_id)
        if not worker_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Worker 节点 {worker_id} 不存在"
            )
        
        if worker_status.get("status") != "online":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Worker 节点 {worker_id} 不在线"
            )
        
        # 验证文件格式
        if not file.filename or not file.filename.endswith('.session'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持 .session 文件"
            )
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 检查文件大小（限制为 10MB）
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件大小超过限制（最大 10MB），当前大小: {file_size / 1024 / 1024:.2f}MB"
            )
        
        # 编码为 base64
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        # 生成唯一的命令 ID
        import uuid
        command_id = str(uuid.uuid4())
        
        # 发送命令到 Worker 节点
        command = {
            "action": "upload_session",
            "params": {
                "filename": file.filename,
                "file_content": file_content_b64,
                "file_size": file_size
            },
            "command_id": command_id,
            "timestamp": datetime.now().isoformat(),
            "from": "master"
        }
        
        _add_command(worker_id, command)
        logger.info(f"向节点 {worker_id} 发送 upload_session 命令 (ID: {command_id}, 文件: {file.filename}, 大小: {file_size} bytes)")
        
        # 等待响应（轮询方式）
        response = _wait_for_response(worker_id, command_id, timeout=timeout)
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"等待 Worker 节点 {worker_id} 响应超时（{timeout}秒）"
            )
        
        if not response.get("success"):
            error_msg = response.get("error", "未知错误")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Worker 节点上传失败: {error_msg}"
            )
        
        # 解析响应数据
        result_data = response.get("data", {})
        saved_filename = result_data.get("filename", file.filename)
        
        return SessionUploadResponse(
            success=True,
            node_id=worker_id,
            filename=saved_filename,
            message=f"Session 文件已成功上传到节点 {worker_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传 Session 文件到 Worker 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传 Session 文件失败: {str(e)}"
        )
