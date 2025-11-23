"""
请求优化中间件
自动优化请求处理，包括请求去重、批量处理等
"""
import logging
import hashlib
import json
import time
from typing import Callable, Dict, Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestOptimizerMiddleware(BaseHTTPMiddleware):
    """请求优化中间件"""
    
    def __init__(
        self,
        app: ASGIApp,
        enable_deduplication: bool = True,
        deduplication_window: int = 5,  # 秒
        enable_batch_processing: bool = False
    ):
        super().__init__(app)
        self.enable_deduplication = enable_deduplication
        self.deduplication_window = deduplication_window
        self.enable_batch_processing = enable_batch_processing
        self.request_cache: Dict[str, tuple] = {}  # key -> (response, timestamp)
        self.pending_requests: Dict[str, Set] = {}  # key -> set of waiting tasks
    
    def _generate_request_key(self, request: Request) -> str:
        """生成请求唯一键"""
        key_data = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "body": ""  # 对于 POST 请求，可以包含 body hash
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()
        
        # 请求去重
        if self.enable_deduplication and request.method in ["GET", "HEAD"]:
            request_key = self._generate_request_key(request)
            current_time = time.time()
            
            # 检查是否有相同的请求正在处理
            if request_key in self.pending_requests:
                # 等待正在处理的请求完成
                logger.debug(f"请求去重: 等待相同请求完成 {request_key[:8]}")
                # 这里可以实现等待逻辑，简化版本直接处理
            
            # 检查缓存
            if request_key in self.request_cache:
                cached_response, cache_time = self.request_cache[request_key]
                if current_time - cache_time < self.deduplication_window:
                    logger.debug(f"请求缓存命中: {request_key[:8]}")
                    return cached_response
            
            # 处理请求
            response = await call_next(request)
            
            # 缓存响应（仅 GET 请求）
            if request.method == "GET" and response.status_code == 200:
                # 创建响应副本用于缓存
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                cached_response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                
                self.request_cache[request_key] = (cached_response, current_time)
                
                # 清理过期缓存
                expired_keys = [
                    k for k, (_, t) in self.request_cache.items()
                    if current_time - t > self.deduplication_window
                ]
                for k in expired_keys:
                    del self.request_cache[k]
                
                return cached_response
            
            return response
        else:
            # 非 GET 请求直接处理
            response = await call_next(request)
        
        # 记录处理时间
        process_time = time.time() - start_time
        if process_time > 1.0:  # 超过 1 秒的请求
            logger.warning(f"慢请求: {request.method} {request.url.path} 耗时 {process_time:.2f}s")
        
        return response

