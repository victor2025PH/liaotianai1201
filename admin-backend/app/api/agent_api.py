"""
Agent REST API - Phase 7: 后端 Agent API 实现
提供 Agent 注册、心跳、任务领取和结果汇报的 REST API 接口
"""

import logging
import secrets
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db import get_db
from app.models.agent_api import Agent, AgentTask
from app.schemas.agent_api import (
    AgentRegisterRequest,
    AgentRegisterResponse,
    HeartbeatRequest,
    HeartbeatResponse,
    TaskResultRequest,
    TaskResultResponse,
    TaskResponse,
    AgentInfo
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["agent-api"])


def generate_api_key() -> str:
    """生成 API 密钥"""
    return secrets.token_urlsafe(32)


@router.post("/agents/register", response_model=AgentRegisterResponse, status_code=status.HTTP_200_OK)
async def register_agent(
    request: AgentRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    设备注册接口
    
    Agent 启动时调用此接口注册设备信息。
    如果 Agent 已存在，则更新设备信息；如果不存在，则创建新记录。
    """
    try:
        # 查找或创建 Agent
        agent = db.query(Agent).filter(Agent.agent_id == request.agent_id).first()
        
        if agent:
            # 更新现有 Agent
            agent.phone_number = request.phone_number or agent.phone_number
            agent.device_info = request.device_info or agent.device_info
            agent.proxy_url = request.proxy_url or agent.proxy_url
            agent.agent_metadata = request.metadata or agent.agent_metadata
            agent.status = "online"
            agent.last_active_time = datetime.now()
            
            # 如果没有 API 密钥，生成一个
            if not agent.api_key:
                agent.api_key = generate_api_key()
            
            db.commit()
            db.refresh(agent)
            
            logger.info(f"Agent 已更新: {request.agent_id}")
            
            return AgentRegisterResponse(
                success=True,
                agent_id=agent.agent_id,
                api_key=agent.api_key,
                message="Agent 已更新"
            )
        else:
            # 创建新 Agent
            api_key = generate_api_key()
            agent = Agent(
                agent_id=request.agent_id,
                phone_number=request.phone_number,
                device_info=request.device_info,
                proxy_url=request.proxy_url,
                agent_metadata=request.metadata or {},
                status="online",
                api_key=api_key,
                last_active_time=datetime.now()
            )
            
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
            logger.info(f"新 Agent 已注册: {request.agent_id}")
            
            return AgentRegisterResponse(
                success=True,
                agent_id=agent.agent_id,
                api_key=agent.api_key,
                message="Agent 已注册"
            )
    
    except Exception as e:
        db.rollback()
        logger.error(f"注册 Agent 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/agents/{agent_id}/heartbeat", response_model=HeartbeatResponse, status_code=status.HTTP_200_OK)
async def send_heartbeat(
    agent_id: str,
    request: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    """
    发送心跳接口
    
    Agent 定期调用此接口发送心跳，保持在线状态。
    """
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} 未找到，请先注册"
            )
        
        # 更新状态和最后活跃时间
        agent.status = request.status or "online"
        agent.current_task_id = request.current_task_id
        agent.last_active_time = datetime.now()
        
        db.commit()
        
        return HeartbeatResponse(
            status="ok",
            message="心跳已接收"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"处理心跳失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理心跳失败: {str(e)}"
        )


@router.get("/tasks/pending", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def fetch_pending_task(
    agent_id: str = Query(..., description="Agent ID"),
    db: Session = Depends(get_db)
):
    """
    获取待执行任务接口
    
    Agent 调用此接口获取分配给它的待执行任务。
    关键逻辑：取出一个任务，将其状态更新为 `in_progress`，并返回任务详情。
    
    如果没有任务，返回 `{"task": null}`。
    """
    try:
        # 验证 Agent 是否存在
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} 未找到，请先注册"
            )
        
        # 查找待执行任务
        # 优先级：1. 分配给该 Agent 的 pending 任务
        #         2. 未分配但符合条件的 pending 任务（按优先级和创建时间排序）
        task = (
            db.query(AgentTask)
            .filter(
                and_(
                    AgentTask.status == "pending",
                    or_(
                        AgentTask.agent_id == agent_id,
                        AgentTask.agent_id.is_(None)
                    )
                )
            )
            .order_by(AgentTask.priority.desc(), AgentTask.created_at.asc())
            .first()
        )
        
        if not task:
            # 没有任务
            return TaskResponse(task=None)
        
        # 更新任务状态为 in_progress，并分配给该 Agent
        task.status = "in_progress"
        task.agent_id = agent_id
        task.assigned_at = datetime.now()
        task.started_at = datetime.now()
        
        # 更新 Agent 的当前任务ID
        agent.current_task_id = task.task_id
        agent.status = "busy"
        
        db.commit()
        db.refresh(task)
        
        logger.info(f"任务已分配给 Agent: {task.task_id} -> {agent_id}")
        
        # 构建任务响应
        task_data = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "scenario_data": task.scenario_data,
            "variables": task.variables or {},
            "priority": task.priority,
            "created_at": task.created_at.isoformat() if task.created_at else None
        }
        
        return TaskResponse(task=task_data)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"获取待执行任务失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务失败: {str(e)}"
        )


@router.post("/tasks/{task_id}/status", response_model=TaskResultResponse, status_code=status.HTTP_200_OK)
async def update_task_status(
    task_id: str,
    request: TaskResultRequest,
    db: Session = Depends(get_db)
):
    """
    汇报任务执行结果接口
    
    Agent 执行完任务后调用此接口汇报结果。
    """
    try:
        task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 未找到"
            )
        
        if task.status != "in_progress":
            logger.warning(f"任务 {task_id} 状态为 {task.status}，不是 in_progress")
        
        # 更新任务状态
        if request.status == "completed":
            task.status = "completed"
            task.result_data = request.result_data
            task.error_message = None
        elif request.status == "failed":
            task.status = "failed"
            task.error_message = request.error
            task.result_data = request.result_data
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态: {request.status}，应为 completed 或 failed"
            )
        
        task.executed_at = datetime.now()
        
        # 更新 Agent 状态
        if request.agent_id:
            agent = db.query(Agent).filter(Agent.agent_id == request.agent_id).first()
            if agent and agent.current_task_id == task_id:
                agent.current_task_id = None
                agent.status = "online"
        
        db.commit()
        
        logger.info(f"任务状态已更新: {task_id} -> {request.status}")
        
        return TaskResultResponse(
            success=True,
            message=f"任务状态已更新为 {request.status}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新任务状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务状态失败: {str(e)}"
        )


@router.get("/agents/{agent_id}", response_model=AgentInfo, status_code=status.HTTP_200_OK)
async def get_agent_info(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    获取 Agent 信息接口（可选，用于调试和监控）
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} 未找到"
        )
    
    return agent
