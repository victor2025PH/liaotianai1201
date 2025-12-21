"""
角色分配管理 API
"""
import logging
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service.role_assigner import RoleAssigner, AssignmentPlan
from group_ai_service import ServiceManager
from group_ai_service.script_parser import ScriptParser
from app.api.group_ai.accounts import get_service_manager
from app.db import get_db
from app.models.group_ai import GroupAIScript, GroupAIAccount
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Role Assignments"])

# 全局實例
_role_assigner: Optional[RoleAssigner] = None
_script_parser: Optional[ScriptParser] = None


def get_role_assigner() -> RoleAssigner:
    """獲取 RoleAssigner 實例"""
    global _role_assigner
    if _role_assigner is None:
        _role_assigner = RoleAssigner()
    return _role_assigner


def get_script_parser() -> ScriptParser:
    """獲取 ScriptParser 實例"""
    global _script_parser
    if _script_parser is None:
        _script_parser = ScriptParser()
    return _script_parser


# ============ 請求/響應模型 ============

class ExtractRolesRequest(BaseModel):
    """提取角色請求"""
    script_id: str


class ExtractRolesResponse(BaseModel):
    """提取角色響應"""
    script_id: str
    roles: List[Dict]
    total_roles: int


class CreateAssignmentRequest(BaseModel):
    """創建分配方案請求"""
    script_id: str
    account_ids: List[str]
    mode: str = Field(default="auto", description="分配模式: auto 或 manual")
    manual_assignments: Optional[Dict[str, str]] = Field(
        None,
        description="手動分配映射: {role_id: account_id}"
    )


class AssignmentResponse(BaseModel):
    """分配方案響應"""
    script_id: str
    assignments: List[Dict]
    summary: Dict
    validation: Dict


# ============ API 端點 ============

@router.post("/extract-roles", response_model=ExtractRolesResponse)
async def extract_roles(
    request: ExtractRolesRequest,
    db: Session = Depends(get_db),
    assigner: RoleAssigner = Depends(get_role_assigner),
    parser: ScriptParser = Depends(get_script_parser)
):
    """從劇本中提取角色列表"""
    try:
        # 從數據庫獲取劇本
        script_record = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == request.script_id
        ).first()
        
        if not script_record:
            raise HTTPException(
                status_code=404,
                detail=f"劇本 {request.script_id} 不存在"
            )
        
        # 解析劇本
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(script_record.yaml_content)
            temp_path = f.name
        
        try:
            script = parser.load_script(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)
        
        # 提取角色
        roles = assigner.extractor.extract_roles_from_script(script)
        
        # 格式化響應
        roles_data = [
            {
                "role_id": role.role_id,
                "role_name": role.role_name,
                "dialogue_count": role.dialogue_count,
                "dialogue_weight": role.dialogue_weight,
                "metadata": role.metadata
            }
            for role in roles.values()
        ]
        
        return ExtractRolesResponse(
            script_id=request.script_id,
            roles=roles_data,
            total_roles=len(roles)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提取角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"提取角色失敗: {str(e)}"
        )


@router.post("/create-assignment", response_model=AssignmentResponse)
async def create_assignment(
    request: CreateAssignmentRequest,
    db: Session = Depends(get_db),
    assigner: RoleAssigner = Depends(get_role_assigner),
    parser: ScriptParser = Depends(get_script_parser),
    service_manager: ServiceManager = Depends(get_service_manager)
):
    """創建角色分配方案"""
    try:
        # 驗證帳號是否存在（同時檢查運行時管理器和數據庫）
        available_accounts = []
        missing_accounts = []
        
        for account_id in request.account_ids:
            # 先檢查運行時管理器
            if account_id in service_manager.account_manager.accounts:
                available_accounts.append(account_id)
                logger.info(f"帳號 {account_id} 在運行時管理器中找到")
            else:
                # 如果不在運行時管理器中，檢查數據庫
                db_account = db.query(GroupAIAccount).filter(
                    GroupAIAccount.account_id == account_id
                ).first()
                
                if db_account:
                    # 帳號在數據庫中存在，也允許分配角色（可能是遠程服務器上的帳號）
                    available_accounts.append(account_id)
                    logger.info(f"帳號 {account_id} 在數據庫中找到（可能位於遠程服務器）")
                else:
                    # 帳號既不在運行時管理器中，也不在數據庫中
                    missing_accounts.append(account_id)
                    logger.warning(f"帳號 {account_id} 不存在於運行時管理器和數據庫中，將跳過")
        
        if not available_accounts:
            error_detail = "沒有可用的帳號"
            if missing_accounts:
                error_detail += f"。請求的帳號ID: {', '.join(missing_accounts)}"
            raise HTTPException(
                status_code=400,
                detail=error_detail
            )
        
        logger.info(f"找到 {len(available_accounts)} 個可用帳號: {available_accounts}")
        
        # 從數據庫獲取劇本
        script_record = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == request.script_id
        ).first()
        
        if not script_record:
            raise HTTPException(
                status_code=404,
                detail=f"劇本 {request.script_id} 不存在"
            )
        
        # 解析劇本
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(script_record.yaml_content)
            temp_path = f.name
        
        try:
            script = parser.load_script(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)
        
        # 創建分配方案
        plan = assigner.create_assignment_plan(
            script=script,
            available_accounts=available_accounts,
            mode=request.mode,
            manual_assignments=request.manual_assignments
        )
        
        # 驗證分配方案
        is_valid, errors = assigner.validate_assignment(plan)
        
        # 獲取摘要
        summary = assigner.get_assignment_summary(plan)
        
        # 格式化響應
        assignments_data = [
            {
                "role_id": a.role_id,
                "account_id": a.account_id,
                "weight": a.weight,
                "role_name": plan.roles.get(a.role_id).role_name if a.role_id in plan.roles else a.role_id
            }
            for a in plan.assignments
        ]
        
        return AssignmentResponse(
            script_id=request.script_id,
            assignments=assignments_data,
            summary=summary,
            validation={
                "is_valid": is_valid,
                "errors": errors
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建分配方案失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"創建分配方案失敗: {str(e)}"
        )


@router.post("/apply-assignment")
async def apply_assignment(
    script_id: str,
    assignments: Dict[str, str],  # {role_id: account_id}
    service_manager: ServiceManager = Depends(get_service_manager)
):
    """應用分配方案到帳號（更新帳號的劇本配置）"""
    try:
        applied_count = 0
        
        for role_id, account_id in assignments.items():
            if account_id not in service_manager.account_manager.accounts:
                logger.warning(f"帳號 {account_id} 不存在，跳過")
                continue
            
            account = service_manager.account_manager.accounts[account_id]
            
            # 更新帳號配置（可以添加 role_id 到 extra_metadata）
            if not hasattr(account.config, 'extra_metadata'):
                account.config.extra_metadata = {}
            
            account.config.extra_metadata['assigned_role_id'] = role_id
            account.config.extra_metadata['script_id'] = script_id
            
            applied_count += 1
            logger.info(f"已為帳號 {account_id} 分配角色 {role_id}")
        
        return {
            "message": f"成功應用分配方案，已更新 {applied_count} 個帳號",
            "applied_count": applied_count
        }
    
    except Exception as e:
        logger.error(f"應用分配方案失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"應用分配方案失敗: {str(e)}"
        )

