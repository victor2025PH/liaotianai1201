"""
劇本傳送管理 API

用於將劇本推送到遠端 Worker 節點
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.group_ai import GroupAIScript
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.user import User
from app.api.workers import _add_command, _get_all_workers

logger = logging.getLogger(__name__)

router = APIRouter()


class ScriptDeploymentRequest(BaseModel):
    """劇本部署請求"""
    script_id: str
    node_ids: List[str]  # 目標節點 ID 列表
    force_update: bool = False  # 是否強制更新


class ScriptDeploymentResponse(BaseModel):
    """劇本部署響應"""
    script_id: str
    total_nodes: int
    success_count: int
    failed_count: int
    results: List[Dict]


@router.post("/deploy", response_model=ScriptDeploymentResponse)
async def deploy_script_to_nodes(
    request: ScriptDeploymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    推送劇本到遠端 Worker 節點
    
    需要權限: script:deploy
    """
    check_permission(current_user, PermissionCode.SCRIPT_CREATE.value, db)
    
    # 檢查劇本是否存在
    script = db.query(GroupAIScript).filter(
        GroupAIScript.script_id == request.script_id
    ).first()
    
    if not script:
        raise HTTPException(status_code=404, detail=f"劇本 {request.script_id} 不存在")
    
    # 獲取所有 Worker 節點
    workers = _get_all_workers()
    
    # 過濾出在線的目標節點
    online_nodes = [
        node_id for node_id in request.node_ids
        if node_id in workers and workers[node_id].get('status') == 'online'
    ]
    
    if not online_nodes:
        raise HTTPException(
            status_code=400,
            detail="沒有在線的目標節點"
        )
    
    # 構建劇本下載 URL（後台提供劇本下載端點）
    from app.core.config import get_settings
    settings = get_settings()
    # 這裡需要根據實際的 API 基礎 URL 構建下載鏈接
    # 暫時使用相對路徑，Worker 節點需要知道後台的完整 URL
    script_download_url = f"/api/v1/group-ai/scripts/{request.script_id}/download"
    
    # 向每個節點發送劇本更新命令
    results = []
    success_count = 0
    failed_count = 0
    
    for node_id in online_nodes:
        try:
            command = {
                "action": "update_script",
                "params": {
                    "script_id": request.script_id,
                    "download_url": script_download_url,
                    "force_update": request.force_update
                },
                "timestamp": datetime.now().isoformat(),
                "from": "master"
            }
            
            _add_command(node_id, command)
            results.append({
                "node_id": node_id,
                "status": "success",
                "message": "劇本推送命令已發送"
            })
            success_count += 1
            logger.info(f"已發送劇本 {request.script_id} 到節點 {node_id}")
            
        except Exception as e:
            results.append({
                "node_id": node_id,
                "status": "failed",
                "message": f"發送失敗: {str(e)}"
            })
            failed_count += 1
            logger.error(f"發送劇本到節點 {node_id} 失敗: {e}", exc_info=True)
    
    return ScriptDeploymentResponse(
        script_id=request.script_id,
        total_nodes=len(online_nodes),
        success_count=success_count,
        failed_count=failed_count,
        results=results
    )
