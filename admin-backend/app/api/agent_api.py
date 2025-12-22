"""
Agent REST API - Phase 7: 后端 Agent API 实现
提供 Agent 注册、心跳、任务领取和结果汇报的 REST API 接口
"""

import logging
import secrets
import json
import tempfile
import zipfile
from datetime import datetime
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, Response
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


@router.post("/tasks", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    创建任务接口
    
    前端调用此接口创建任务并下发给 Agent。
    """
    try:
        agent_id = request.get("agent_id")
        task_type = request.get("task_type", "scenario_execute")
        scenario_data = request.get("scenario_data")
        variables = request.get("variables", {})
        priority = request.get("priority", 1)
        
        if not scenario_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少 scenario_data 字段"
            )
        
        # 生成任务ID
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:16]}"
        
        # 创建任务
        task = AgentTask(
            task_id=task_id,
            agent_id=agent_id,  # 可选，如果未指定则由 Agent 轮询时自动分配
            task_type=task_type,
            scenario_data=scenario_data,
            variables=variables,
            priority=priority,
            status="pending"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"任务已创建: {task_id} (Agent: {agent_id or '自动分配'})")
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "任务已创建"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建任务失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
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


@router.get("/agents/download-startup-scripts")
async def download_startup_scripts(
    api_base_url: str = Query(..., description="API 基础 URL，例如: https://api.usdt2026.cc"),
    api_key: Optional[str] = Query(None, description="API 密钥（可选，注册后获取）"),
    telegram_api_id: Optional[str] = Query(None, description="Telegram API ID（可选）"),
    telegram_api_hash: Optional[str] = Query(None, description="Telegram API Hash（可选）"),
    db: Session = Depends(get_db)
):
    """
    Phase 9: 下载 Agent 启动脚本和配置文件
    
    生成包含以下文件的 ZIP 包：
    - run_agent_prod.bat (Windows 启动脚本)
    - run_agent_prod.sh (Linux/Mac 启动脚本)
    - config_prod.json (生产环境配置文件)
    - README.txt (使用说明)
    """
    try:
        # 生成配置文件内容
        config_data = {
            "agent_id": None,
            "server_url": f"ws://{api_base_url.replace('https://', '').replace('http://', '')}/api/v1/agents/ws",
            "heartbeat_interval": 30,
            "reconnect_interval": 30,
            "reconnect_max_attempts": -1,
            "metadata": {
                "version": "1.0.0",
                "platform": None,
                "hostname": None
            },
            "telegram": {
                "api_id": int(telegram_api_id) if telegram_api_id and telegram_api_id.isdigit() else None,
                "api_hash": telegram_api_hash or None,
                "session_string": None,
                "session_path": "sessions/"
            },
            "api": {
                "base_url": api_base_url,
                "api_key": api_key,
                "poll_interval": 5.0,
                "heartbeat_interval": 30.0
            }
        }
        
        # 生成 Windows 启动脚本
        windows_script = f"""@echo off
REM ============================================================
REM Agent 生产环境启动脚本 (Windows)
REM 连接到生产服务器: {api_base_url}
REM ============================================================

echo ============================================================
echo 正在启动 Agent (连接至生产环境: {api_base_url})
echo ============================================================
echo.

REM 设置配置文件路径
set AGENT_CONFIG=agent\\config_prod.json

REM 检查配置文件是否存在
if not exist "%AGENT_CONFIG%" (
    echo 错误: 配置文件不存在: %AGENT_CONFIG%
    echo 请确保 agent/config_prod.json 文件存在
    pause
    exit /b 1
)

echo 使用配置文件: %AGENT_CONFIG%
echo.

REM 启动 Agent
python agent\\main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Agent 启动失败，错误代码: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

pause
"""
        
        # 生成 Linux/Mac 启动脚本
        linux_script = f"""#!/bin/bash
# ============================================================
# Agent 生产环境启动脚本 (Linux/Mac)
# 连接到生产服务器: {api_base_url}
# ============================================================

echo "============================================================"
echo "正在启动 Agent (连接至生产环境: {api_base_url})"
echo "============================================================"
echo ""

# 设置配置文件路径
export AGENT_CONFIG="agent/config_prod.json"

# 检查配置文件是否存在
if [ ! -f "$AGENT_CONFIG" ]; then
    echo "❌ 错误: 配置文件不存在: $AGENT_CONFIG"
    echo "   请确保 agent/config_prod.json 文件存在"
    exit 1
fi

echo "使用配置文件: $AGENT_CONFIG"
echo ""

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 启动 Agent
python3 agent/main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Agent 启动失败"
    exit 1
fi
"""
        
        # 生成使用说明
        readme_content = f"""Agent 启动脚本使用说明
============================================================

本 ZIP 包包含以下文件：
1. run_agent_prod.bat - Windows 启动脚本
2. run_agent_prod.sh - Linux/Mac 启动脚本  
3. config_prod.json - 生产环境配置文件

使用步骤：
============================================================

1. 解压 ZIP 包到项目根目录
   确保文件结构如下：
   telegram-ai-system/
   ├── agent/
   │   ├── main.py
   │   ├── config_prod.json  (解压后放置)
   │   └── ...
   ├── run_agent_prod.bat    (解压后放置)
   ├── run_agent_prod.sh     (解压后放置)
   └── ...

2. 编辑配置文件 (agent/config_prod.json)
   填写以下必需信息：
   - telegram.api_id: Telegram API ID
   - telegram.api_hash: Telegram API Hash
   - api.api_key: API 密钥（注册 Agent 后从后端获取）

3. 启动 Agent

   Windows:
   双击 run_agent_prod.bat 或命令行运行

   Linux/Mac:
   chmod +x run_agent_prod.sh
   ./run_agent_prod.sh

配置说明：
============================================================

API 基础 URL: {api_base_url}
WebSocket URL: ws://{api_base_url.replace('https://', '').replace('http://', '')}/api/v1/agents/ws

首次运行：
1. Agent 会自动注册到后端
2. 后端会返回 API 密钥
3. 将 API 密钥填入 config_prod.json 的 api.api_key 字段
4. 重启 Agent 以使用 API 密钥

注意事项：
============================================================
- 确保已安装 Python 3.9+
- 确保已安装所有依赖: pip install -r agent/requirements.txt
- 确保网络可以访问 {api_base_url}
- 首次运行需要填写 Telegram API 凭证
"""
        
        # 创建临时 ZIP 文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            zip_path = Path(tmp_file.name)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加 Windows 启动脚本
                zipf.writestr("run_agent_prod.bat", windows_script)
                
                # 添加 Linux/Mac 启动脚本
                zipf.writestr("run_agent_prod.sh", linux_script)
                
                # 添加配置文件
                zipf.writestr("agent/config_prod.json", json.dumps(config_data, indent=2, ensure_ascii=False))
                
                # 添加使用说明
                zipf.writestr("README.txt", readme_content)
            
            # 返回 ZIP 文件
            return FileResponse(
                path=str(zip_path),
                filename="agent_startup_scripts.zip",
                media_type="application/zip",
                headers={
                    "Content-Disposition": "attachment; filename=agent_startup_scripts.zip"
                }
            )
    
    except Exception as e:
        logger.error(f"生成启动脚本失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成启动脚本失败: {str(e)}"
        )
