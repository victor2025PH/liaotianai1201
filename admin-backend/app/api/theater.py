"""
智能剧场 API - Phase 3: 多账号协同表演
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.theater import TheaterScenario, TheaterExecution
from app.schemas.theater import (
    TheaterScenarioCreate,
    TheaterScenarioUpdate,
    TheaterScenarioResponse,
    TheaterExecutionCreate,
    TheaterExecutionResponse,
    TimelineAction
)
from app.api.deps import get_current_user
from app.models.user import User
from app.services.theater_scheduler import get_theater_scheduler
from app.websocket import get_websocket_manager
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/theater", tags=["Theater"])


@router.get("/scenarios", response_model=List[TheaterScenarioResponse])
async def list_scenarios(
    skip: int = 0,
    limit: int = 100,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取剧场场景列表
    """
    try:
        query = db.query(TheaterScenario)
        
        if enabled is not None:
            query = query.filter(TheaterScenario.enabled == enabled)
        
        scenarios = query.offset(skip).limit(limit).all()
        return scenarios
    except Exception as e:
        logger.error(f"获取场景列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取场景列表失败: {str(e)}"
        )


@router.get("/scenarios/{scenario_id}", response_model=TheaterScenarioResponse)
async def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定场景
    """
    scenario = db.query(TheaterScenario).filter(
        TheaterScenario.id == scenario_id
    ).first()
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"场景 {scenario_id} 未找到"
        )
    return scenario


@router.post("/scenarios", response_model=TheaterScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    scenario: TheaterScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新场景
    """
    try:
        # 检查名称是否已存在
        existing = db.query(TheaterScenario).filter(
            TheaterScenario.name == scenario.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"场景名称 '{scenario.name}' 已存在"
            )
        
        # 验证 timeline 中的角色都在 roles 列表中
        roles_in_timeline = {action.role for action in scenario.timeline}
        if not roles_in_timeline.issubset(set(scenario.roles)):
            missing_roles = roles_in_timeline - set(scenario.roles)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"时间轴中使用了未定义的角色: {missing_roles}"
            )
        
        # 转换 timeline 为 JSON（Pydantic 模型转 dict）
        timeline_json = [action.dict() for action in scenario.timeline]
        
        # 创建场景
        db_scenario = TheaterScenario(
            name=scenario.name,
            description=scenario.description,
            roles=scenario.roles,
            timeline=timeline_json,
            enabled=scenario.enabled,
            created_by=current_user.id if hasattr(current_user, 'id') else None
        )
        
        db.add(db_scenario)
        db.commit()
        db.refresh(db_scenario)
        
        logger.info(f"场景已创建: {db_scenario.id} ({db_scenario.name})")
        return db_scenario
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建场景失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建场景失败: {str(e)}"
        )


@router.put("/scenarios/{scenario_id}", response_model=TheaterScenarioResponse)
async def update_scenario(
    scenario_id: str,
    scenario: TheaterScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新场景
    """
    try:
        db_scenario = db.query(TheaterScenario).filter(
            TheaterScenario.id == scenario_id
        ).first()
        if not db_scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"场景 {scenario_id} 未找到"
            )
        
        # 检查名称是否已被其他场景使用
        if scenario.name and scenario.name != db_scenario.name:
            existing = db.query(TheaterScenario).filter(
                TheaterScenario.name == scenario.name,
                TheaterScenario.id != scenario_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"场景名称 '{scenario.name}' 已被使用"
                )
        
        # 更新字段
        update_data = scenario.dict(exclude_unset=True)
        
        # 处理 timeline（如果是 Pydantic 模型列表，转换为 dict）
        if "timeline" in update_data and update_data["timeline"]:
            timeline_data = update_data["timeline"]
            if timeline_data and isinstance(timeline_data[0], dict):
                # 已经是 dict，直接使用
                pass
            else:
                # 转换为 dict
                update_data["timeline"] = [action.dict() if hasattr(action, 'dict') else action for action in timeline_data]
        
        # 验证角色映射（如果更新了 roles 或 timeline）
        if "roles" in update_data or "timeline" in update_data:
            final_roles = update_data.get("roles", db_scenario.roles)
            final_timeline = update_data.get("timeline", db_scenario.timeline)
            
            if final_timeline:
                roles_in_timeline = {action.get("role") for action in final_timeline if isinstance(action, dict) and action.get("role")}
                if not roles_in_timeline.issubset(set(final_roles)):
                    missing_roles = roles_in_timeline - set(final_roles)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"时间轴中使用了未定义的角色: {missing_roles}"
                    )
        
        for field, value in update_data.items():
            setattr(db_scenario, field, value)
        
        db.commit()
        db.refresh(db_scenario)
        
        logger.info(f"场景已更新: {db_scenario.id} ({db_scenario.name})")
        return db_scenario
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新场景失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新场景失败: {str(e)}"
        )


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除场景
    """
    try:
        db_scenario = db.query(TheaterScenario).filter(
            TheaterScenario.id == scenario_id
        ).first()
        if not db_scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"场景 {scenario_id} 未找到"
            )
        
        scenario_name = db_scenario.name
        db.delete(db_scenario)
        db.commit()
        
        logger.info(f"场景已删除: {scenario_id} ({scenario_name})")
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除场景失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除场景失败: {str(e)}"
        )


@router.post("/execute", response_model=TheaterExecutionResponse)
async def execute_scenario(
    execution: TheaterExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行剧场场景
    """
    try:
        # 获取场景
        scenario = db.query(TheaterScenario).filter(
            TheaterScenario.id == execution.scenario_id
        ).first()
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"场景 {execution.scenario_id} 未找到"
            )
        
        if not scenario.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="场景已禁用，无法执行"
            )
        
        # 创建执行记录
        db_execution = TheaterExecution(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            group_id=execution.group_id,
            agent_mapping=execution.agent_mapping,
            status="pending",
            created_by=current_user.id if hasattr(current_user, 'id') else None
        )
        
        db.add(db_execution)
        db.commit()
        db.refresh(db_execution)
        
        # 启动调度器执行
        scheduler = get_theater_scheduler()
        try:
            execution_id = await scheduler.execute_scenario(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                group_id=execution.group_id,
                timeline=scenario.timeline,
                agent_mapping=execution.agent_mapping
            )
            
            # 更新执行记录
            db_execution.status = "running"
            db_execution.started_at = datetime.now()
            db.commit()
            db.refresh(db_execution)
            
            logger.info(f"场景执行已启动: {scenario.name} (执行ID: {execution_id})")
            
        except Exception as e:
            db_execution.status = "failed"
            db_execution.error_message = str(e)
            db.commit()
            logger.error(f"场景执行启动失败: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"场景执行启动失败: {str(e)}"
            )
        
        return db_execution
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"执行场景失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行场景失败: {str(e)}"
        )


@router.get("/executions", response_model=List[TheaterExecutionResponse])
async def list_executions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取执行记录列表
    """
    try:
        query = db.query(TheaterExecution)
        
        if status:
            query = query.filter(TheaterExecution.status == status)
        
        executions = query.order_by(TheaterExecution.created_at.desc()).offset(skip).limit(limit).all()
        return executions
    except Exception as e:
        logger.error(f"获取执行记录列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行记录列表失败: {str(e)}"
        )


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    取消执行
    """
    try:
        execution = db.query(TheaterExecution).filter(
            TheaterExecution.id == execution_id
        ).first()
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"执行记录 {execution_id} 未找到"
            )
        
        if execution.status not in ["pending", "running"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"执行记录状态为 {execution.status}，无法取消"
            )
        
        # 取消调度器中的执行
        scheduler = get_theater_scheduler()
        success = scheduler.cancel_execution(execution_id)
        
        if success:
            execution.status = "cancelled"
            execution.completed_at = datetime.now()
            db.commit()
            logger.info(f"执行已取消: {execution_id}")
        else:
            logger.warning(f"执行未在调度器中运行: {execution_id}")
        
        return {"success": True, "message": "执行已取消"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"取消执行失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消执行失败: {str(e)}"
        )
