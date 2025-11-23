"""
性能監控中間件 - 記錄 API 響應時間和性能指標
集成 Prometheus 指標收集
"""
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

logger = logging.getLogger(__name__)

# 嘗試導入 Prometheus 指標（如果可用）
try:
    from app.monitoring.prometheus_metrics import (
        http_requests_total,
        http_request_duration_seconds,
        http_request_size_bytes,
        http_response_size_bytes
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus 指標未可用，將跳過指標收集")

# 性能統計（內存中，簡單實現）
# 生產環境建議使用 Prometheus 或其他監控系統
_performance_stats = {
    "request_count": 0,
    "total_response_time": 0.0,
    "slow_requests": []  # 存儲慢請求（> 1000ms）
}


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能監控中間件"""
    
    def __init__(self, app, slow_request_threshold_ms: float = 1000.0):
        super().__init__(app)
        self.slow_request_threshold_ms = slow_request_threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 記錄開始時間
        start_time = time.time()
        
        # 跳過健康檢查和 OpenAPI 文檔（避免統計噪聲）
        path = request.url.path
        if path in ["/health", "/healthz", "/docs", "/openapi.json", "/redoc", "/"]:
            response = await call_next(request)
            return response
        
        try:
            # 獲取請求大小（如果可用）
            request_size = 0
            try:
                if hasattr(request, '_body'):
                    request_size = len(request._body) if request._body else 0
            except Exception:
                pass
            
            # 處理請求
            response = await call_next(request)
            
            # 計算響應時間
            process_time = time.time() - start_time
            process_time_ms = process_time * 1000
            
            # 獲取響應大小
            response_size = 0
            try:
                if hasattr(response, 'body'):
                    response_size = len(response.body) if response.body else 0
            except Exception:
                pass
            
            # 更新 Prometheus 指標
            if PROMETHEUS_AVAILABLE:
                try:
                    # 提取端點名稱（移除查詢參數和 ID）
                    endpoint = path
                    # 簡化端點名稱（將 ID 替換為 {id}）
                    import re
                    endpoint = re.sub(r'/\d+', '/{id}', endpoint)
                    endpoint = re.sub(r'/[a-f0-9-]{36}', '/{uuid}', endpoint)  # UUID
                    
                    # 更新 HTTP 指標
                    http_requests_total.labels(
                        method=request.method,
                        endpoint=endpoint,
                        status_code=str(response.status_code)
                    ).inc()
                    
                    http_request_duration_seconds.labels(
                        method=request.method,
                        endpoint=endpoint,
                        status_code=str(response.status_code)
                    ).observe(process_time)
                    
                    if request_size > 0:
                        http_request_size_bytes.labels(
                            method=request.method,
                            endpoint=endpoint
                        ).observe(request_size)
                    
                    if response_size > 0:
                        http_response_size_bytes.labels(
                            method=request.method,
                            endpoint=endpoint,
                            status_code=str(response.status_code)
                        ).observe(response_size)
                except Exception as e:
                    logger.debug(f"更新 Prometheus 指標失敗: {e}")
            
            # 更新統計
            _performance_stats["request_count"] += 1
            _performance_stats["total_response_time"] += process_time_ms
            
            # 記錄慢請求
            if process_time_ms > self.slow_request_threshold_ms:
                slow_request_info = {
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "response_time_ms": round(process_time_ms, 2),
                    "query_params": str(request.query_params) if request.query_params else None,
                }
                _performance_stats["slow_requests"].append(slow_request_info)
                
                # 只保留最近 100 個慢請求
                if len(_performance_stats["slow_requests"]) > 100:
                    _performance_stats["slow_requests"] = _performance_stats["slow_requests"][-100:]
                
                logger.warning(
                    f"慢請求檢測: {request.method} {path} "
                    f"- 響應時間: {process_time_ms:.2f}ms "
                    f"- 狀態碼: {response.status_code}"
                )
            
            # 添加響應頭（可選，用於前端監控）
            response.headers["X-Process-Time"] = str(round(process_time_ms, 2))
            
            # 記錄性能日誌（僅慢請求或錯誤請求）
            if process_time_ms > self.slow_request_threshold_ms or response.status_code >= 400:
                logger.info(
                    f"API 性能: {request.method} {path} "
                    f"- {process_time_ms:.2f}ms "
                    f"- {response.status_code}"
                )
            
            return response
        
        except Exception as e:
            # 記錄異常請求時間
            process_time = time.time() - start_time
            process_time_ms = process_time * 1000
            
            # 更新 Prometheus 指標（錯誤請求）
            if PROMETHEUS_AVAILABLE:
                try:
                    endpoint = path
                    import re
                    endpoint = re.sub(r'/\d+', '/{id}', endpoint)
                    endpoint = re.sub(r'/[a-f0-9-]{36}', '/{uuid}', endpoint)
                    
                    http_requests_total.labels(
                        method=request.method,
                        endpoint=endpoint,
                        status_code="500"
                    ).inc()
                    
                    http_request_duration_seconds.labels(
                        method=request.method,
                        endpoint=endpoint,
                        status_code="500"
                    ).observe(process_time)
                except Exception:
                    pass
            
            logger.error(
                f"API 異常: {request.method} {path} "
                f"- 響應時間: {process_time_ms:.2f}ms "
                f"- 錯誤: {str(e)}",
                exc_info=True
            )
            raise


def get_performance_stats() -> dict:
    """獲取性能統計"""
    avg_response_time = 0.0
    if _performance_stats["request_count"] > 0:
        avg_response_time = (
            _performance_stats["total_response_time"] / _performance_stats["request_count"]
        )
    
    return {
        "request_count": _performance_stats["request_count"],
        "average_response_time_ms": round(avg_response_time, 2),
        "total_response_time_ms": round(_performance_stats["total_response_time"], 2),
        "slow_requests_count": len(_performance_stats["slow_requests"]),
        "slow_requests": _performance_stats["slow_requests"][-20:],  # 最近 20 個慢請求
    }


def reset_performance_stats():
    """重置性能統計（用於測試）"""
    global _performance_stats
    _performance_stats = {
        "request_count": 0,
        "total_response_time": 0.0,
        "slow_requests": [],
    }

