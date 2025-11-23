"""
劇本版本管理 API
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_db
from app.models.group_ai import GroupAIScript, GroupAIScriptVersion

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Script Versions"])


class ScriptVersionResponse(BaseModel):
    """版本響應模型"""
    id: str
    script_id: str
    version: str
    description: Optional[str] = None
    created_by: Optional[str] = None
    change_summary: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class VersionCompareResponse(BaseModel):
    """版本對比響應"""
    version1: ScriptVersionResponse
    version2: ScriptVersionResponse
    differences: List[dict] = Field(default_factory=list)


class RestoreVersionRequest(BaseModel):
    """恢復版本請求"""
    change_summary: Optional[str] = Field(None, description="變更說明")


@router.get("/{script_id}/versions/compare", response_model=VersionCompareResponse)
async def compare_script_versions(
    script_id: str,
    version1: str = Query(..., description="第一個版本號"),
    version2: str = Query(..., description="第二個版本號"),
    db: Session = Depends(get_db)
):
    """對比兩個版本的劇本（必須放在版本詳情路由之前）"""
    # 獲取兩個版本
    v1 = db.query(GroupAIScriptVersion).filter(
        GroupAIScriptVersion.script_id == script_id,
        GroupAIScriptVersion.version == version1
    ).first()
    
    v2 = db.query(GroupAIScriptVersion).filter(
        GroupAIScriptVersion.script_id == script_id,
        GroupAIScriptVersion.version == version2
    ).first()
    
    if not v1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"版本 {version1} 不存在"
        )
    
    if not v2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"版本 {version2} 不存在"
        )
    
    # 簡單的差異檢測（可以後續增強為更詳細的diff）
    differences = []
    
    if v1.yaml_content != v2.yaml_content:
        differences.append({
            "type": "content",
            "description": "YAML內容已變更"
        })
    
    if v1.description != v2.description:
        differences.append({
            "type": "description",
            "description": "描述已變更"
        })
    
    return VersionCompareResponse(
        version1=ScriptVersionResponse(
            id=v1.id,
            script_id=v1.script_id,
            version=v1.version,
            description=v1.description,
            created_by=v1.created_by,
            change_summary=v1.change_summary,
            created_at=v1.created_at.isoformat() if v1.created_at else ""
        ),
        version2=ScriptVersionResponse(
            id=v2.id,
            script_id=v2.script_id,
            version=v2.version,
            description=v2.description,
            created_by=v2.created_by,
            change_summary=v2.change_summary,
            created_at=v2.created_at.isoformat() if v2.created_at else ""
        ),
        differences=differences
    )


@router.get("/{script_id}/versions", response_model=List[ScriptVersionResponse])
async def list_script_versions(
    script_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """獲取劇本的所有版本歷史"""
    # 檢查劇本是否存在
    script = db.query(GroupAIScript).filter(
        GroupAIScript.script_id == script_id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"劇本 {script_id} 不存在"
        )
    
    # 查詢版本歷史（按創建時間倒序）
    versions = db.query(GroupAIScriptVersion).filter(
        GroupAIScriptVersion.script_id == script_id
    ).order_by(desc(GroupAIScriptVersion.created_at)).offset(skip).limit(limit).all()
    
    return [
        ScriptVersionResponse(
            id=v.id,
            script_id=v.script_id,
            version=v.version,
            description=v.description,
            created_by=v.created_by,
            change_summary=v.change_summary,
            created_at=v.created_at.isoformat() if v.created_at else ""
        )
        for v in versions
    ]


@router.get("/{script_id}/versions/{version}", response_model=ScriptVersionResponse)
async def get_script_version(
    script_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """獲取特定版本的劇本"""
    version_record = db.query(GroupAIScriptVersion).filter(
        GroupAIScriptVersion.script_id == script_id,
        GroupAIScriptVersion.version == version
    ).first()
    
    if not version_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"劇本 {script_id} 的版本 {version} 不存在"
        )
    
    return ScriptVersionResponse(
        id=version_record.id,
        script_id=version_record.script_id,
        version=version_record.version,
        description=version_record.description,
        created_by=version_record.created_by,
        change_summary=version_record.change_summary,
        created_at=version_record.created_at.isoformat() if version_record.created_at else ""
    )


@router.get("/{script_id}/versions/{version}/content")
async def get_script_version_content(
    script_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """獲取特定版本的YAML內容"""
    version_record = db.query(GroupAIScriptVersion).filter(
        GroupAIScriptVersion.script_id == script_id,
        GroupAIScriptVersion.version == version
    ).first()
    
    if not version_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"劇本 {script_id} 的版本 {version} 不存在"
        )
    
    return {
        "script_id": version_record.script_id,
        "version": version_record.version,
        "yaml_content": version_record.yaml_content,
        "created_at": version_record.created_at.isoformat() if version_record.created_at else ""
    }


@router.post("/{script_id}/versions/{version}/restore", response_model=dict)
async def restore_script_version(
    script_id: str,
    version: str,
    request: RestoreVersionRequest,
    db: Session = Depends(get_db)
):
    """恢復劇本到指定版本"""
    # 獲取要恢復的版本
    version_record = db.query(GroupAIScriptVersion).filter(
        GroupAIScriptVersion.script_id == script_id,
        GroupAIScriptVersion.version == version
    ).first()
    
    if not version_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"劇本 {script_id} 的版本 {version} 不存在"
        )
    
    # 獲取當前劇本
    script = db.query(GroupAIScript).filter(
        GroupAIScript.script_id == script_id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"劇本 {script_id} 不存在"
        )
    
    try:
        # 保存當前版本到歷史（如果內容不同）
        if script.yaml_content != version_record.yaml_content:
            # 創建當前版本的歷史記錄
            current_version = GroupAIScriptVersion(
                script_id=script_id,
                version=script.version,
                yaml_content=script.yaml_content,
                description=script.description,
                change_summary="恢復版本前的自動備份"
            )
            db.add(current_version)
        
        # 恢復到指定版本
        script.yaml_content = version_record.yaml_content
        script.version = version_record.version
        if version_record.description:
            script.description = version_record.description
        script.updated_at = datetime.now()
        
        # 如果提供了變更說明，創建新的版本記錄
        if request.change_summary:
            new_version = GroupAIScriptVersion(
                script_id=script_id,
                version=script.version,
                yaml_content=script.yaml_content,
                description=script.description,
                change_summary=request.change_summary
            )
            db.add(new_version)
        
        db.commit()
        
        logger.info(f"劇本 {script_id} 已恢復到版本 {version}")
        
        return {
            "message": f"劇本已恢復到版本 {version}",
            "script_id": script_id,
            "version": version
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"恢復劇本版本失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢復劇本版本失敗: {str(e)}"
        )

