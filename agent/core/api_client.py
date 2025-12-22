"""
API 客户端 - Phase 6: 云端协同与任务调度
封装与后端 REST API 的交互逻辑
"""

import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    try:
        import requests
        REQUESTS_AVAILABLE = True
    except ImportError:
        REQUESTS_AVAILABLE = False

from agent.config import get_agent_id, get_metadata

logger = logging.getLogger(__name__)


class ApiClient:
    """API 客户端 - 与后端 REST API 交互"""
    
    def __init__(
        self,
        api_base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        初始化 API 客户端
        
        Args:
            api_base_url: API 基础 URL，例如 "https://api.usdt2026.cc" 或 "http://127.0.0.1:8000"
            api_key: API 密钥（用于鉴权，可选）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        # 确保 URL 以 / 结尾
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.agent_id = get_agent_id()
        
        # 选择 HTTP 客户端
        if HTTPX_AVAILABLE:
            self.client = httpx.AsyncClient(
                base_url=self.api_base_url,
                timeout=timeout,
                headers=self._get_headers()
            )
            self.is_async = True
        elif REQUESTS_AVAILABLE:
            self.client = None  # requests 是同步的，需要特殊处理
            self.is_async = False
        else:
            raise ImportError("需要安装 httpx 或 requests 库: pip install httpx 或 pip install requests")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"Telegram-Agent/{self.agent_id}"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求（带重试机制）
        
        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            endpoint: API 端点路径（例如 "/api/v1/tasks/pending"）
            data: 请求体数据（可选）
            params: URL 查询参数（可选）
        
        Returns:
            响应 JSON 数据
        """
        url = f"{self.api_base_url}{endpoint}"
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                if self.is_async:
                    # 使用 httpx
                    response = await self.client.request(
                        method=method,
                        url=endpoint,  # httpx 会自动拼接 base_url
                        json=data,
                        params=params,
                        headers=self._get_headers()
                    )
                    response.raise_for_status()
                    return response.json()
                else:
                    # 使用 requests（同步，需要在线程池中运行）
                    import requests
                    response = requests.request(
                        method=method,
                        url=url,
                        json=data,
                        params=params,
                        headers=self._get_headers(),
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    return response.json()
            
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(
                        f"API 请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}, "
                        f"{wait_time:.1f}秒后重试..."
                    )
                    if self.is_async:
                        import asyncio
                        await asyncio.sleep(wait_time)
                    else:
                        time.sleep(wait_time)
                else:
                    logger.error(f"API 请求最终失败: {e}")
                    raise
        
        raise Exception(f"API 请求失败: {last_error}")
    
    async def register_device(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        注册/更新设备状态（启动时调用）
        
        Args:
            metadata: 设备元数据（可选）
        
        Returns:
            注册结果
        """
        if metadata is None:
            metadata = get_metadata()
        
        payload = {
            "agent_id": self.agent_id,
            "status": "online",
            "metadata": metadata
        }
        
        try:
            result = await self._request(
                method="POST",
                endpoint="/api/v1/agents/register",
                data=payload
            )
            logger.info(f"设备注册成功: {self.agent_id}")
            return result
        except Exception as e:
            logger.error(f"设备注册失败: {e}")
            # 注册失败不应该阻止 Agent 启动，只记录错误
            return {"success": False, "error": str(e)}
    
    async def send_heartbeat(self) -> Dict[str, Any]:
        """
        发送心跳（保持在线状态）
        
        Returns:
            心跳响应
        """
        try:
            result = await self._request(
                method="POST",
                endpoint=f"/api/v1/agents/{self.agent_id}/heartbeat",
                data={"timestamp": time.time()}
            )
            return result
        except Exception as e:
            logger.warning(f"心跳发送失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def fetch_pending_task(self) -> Optional[Dict[str, Any]]:
        """
        获取当前分配给该 Agent 的待执行任务
        
        Returns:
            任务数据字典，如果没有任务则返回 None
        
        任务格式:
        {
            "task_id": "task_xxx",
            "task_type": "scenario_execute",
            "scenario_data": {
                "name": "测试剧本",
                "timeline": [...]
            },
            "variables": {
                "target_user": "张三",
                "group_id": "-1001234567890"
            },
            "priority": 1,
            "created_at": "2025-12-22T10:00:00Z"
        }
        """
        try:
            result = await self._request(
                method="GET",
                endpoint=f"/api/v1/tasks/pending",
                params={"agent_id": self.agent_id}
            )
            
            # 如果返回空列表或 None，表示没有任务
            if not result or result.get("task") is None:
                return None
            
            return result.get("task")
        
        except Exception as e:
            # 404 表示没有任务，这是正常的
            if "404" in str(e) or "Not Found" in str(e):
                return None
            logger.warning(f"获取待执行任务失败: {e}")
            return None
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        汇报任务执行结果
        
        Args:
            task_id: 任务ID
            status: 任务状态 ("running", "completed", "failed", "cancelled")
            result: 执行结果数据（可选）
            error: 错误信息（可选）
        
        Returns:
            更新结果
        """
        payload = {
            "status": status,
            "agent_id": self.agent_id
        }
        
        if result is not None:
            payload["result"] = result
        
        if error is not None:
            payload["error"] = error
        
        try:
            response = await self._request(
                method="POST",
                endpoint=f"/api/v1/tasks/{task_id}/status",
                data=payload
            )
            logger.info(f"任务状态已更新: {task_id} -> {status}")
            return response
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            raise
    
    async def close(self):
        """关闭客户端连接"""
        if self.is_async and hasattr(self.client, 'aclose'):
            await self.client.aclose()
        elif hasattr(self.client, 'close'):
            self.client.close()
