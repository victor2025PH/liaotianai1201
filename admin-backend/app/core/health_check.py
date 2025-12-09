"""
增强的健康检查模块
检查系统各个组件的健康状态
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # 部分功能不可用
    UNHEALTHY = "unhealthy"  # 关键功能不可用
    UNKNOWN = "unknown"


class ComponentHealth:
    """组件健康状态"""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: Optional[str] = None,
        response_time_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.status = status
        self.message = message
        self.response_time_ms = response_time_ms
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": self.response_time_ms,
            "details": self.details,
            "timestamp": self.timestamp
        }


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, timeout: float = 5.0):
        """
        初始化健康检查器
        
        Args:
            timeout: 每个检查的超时时间（秒）
        """
        self.timeout = timeout
        self.components: Dict[str, ComponentHealth] = {}
    
    async def check_database(self) -> ComponentHealth:
        """检查数据库连接"""
        start_time = time.time()
        try:
            from app.db import SessionLocal
            from sqlalchemy import text
            
            db = SessionLocal()
            try:
                # 执行简单查询测试连接
                result = db.execute(text("SELECT 1"))
                result.fetchone()
                
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="数据库连接正常",
                    response_time_ms=response_time,
                    details={"type": "sqlite"}  # 可以根据实际数据库类型设置
                )
            finally:
                db.close()
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"数据库健康检查失败: {e}")
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"数据库连接失败: {str(e)}",
                response_time_ms=response_time
            )
    
    async def check_redis(self) -> ComponentHealth:
        """检查 Redis 连接（如果启用）"""
        start_time = time.time()
        try:
            from app.core.config import get_settings
            settings = get_settings()
            
            redis_url = getattr(settings, 'redis_url', None)
            if not redis_url:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis 未配置（可选组件）",
                    response_time_ms=0
                )
            
            try:
                import redis
                redis_client = redis.from_url(redis_url, socket_connect_timeout=self.timeout)
                redis_client.ping()
                
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis 连接正常",
                    response_time_ms=response_time
                )
            except ImportError:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.UNKNOWN,
                    message="Redis 客户端未安装",
                    response_time_ms=(time.time() - start_time) * 1000
                )
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                logger.warning(f"Redis 健康检查失败: {e}")
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    message=f"Redis 连接失败: {str(e)}",
                    response_time_ms=response_time
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNKNOWN,
                message=f"Redis 检查异常: {str(e)}",
                response_time_ms=response_time
            )
    
    async def check_telegram_api(self) -> ComponentHealth:
        """检查 Telegram API 连接"""
        start_time = time.time()
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                try:
                    async with session.get("https://api.telegram.org") as response:
                        response_time = (time.time() - start_time) * 1000
                        if response.status < 500:
                            return ComponentHealth(
                                name="telegram_api",
                                status=HealthStatus.HEALTHY,
                                message="Telegram API 连接正常",
                                response_time_ms=response_time,
                                details={"status_code": response.status}
                            )
                        else:
                            return ComponentHealth(
                                name="telegram_api",
                                status=HealthStatus.DEGRADED,
                                message=f"Telegram API 返回错误: {response.status}",
                                response_time_ms=response_time,
                                details={"status_code": response.status}
                            )
                except asyncio.TimeoutError:
                    response_time = (time.time() - start_time) * 1000
                    return ComponentHealth(
                        name="telegram_api",
                        status=HealthStatus.DEGRADED,
                        message="Telegram API 连接超时",
                        response_time_ms=response_time
                    )
        except ImportError:
            return ComponentHealth(
                name="telegram_api",
                status=HealthStatus.UNKNOWN,
                message="aiohttp 未安装，无法检查 Telegram API",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"Telegram API 健康检查失败: {e}")
            return ComponentHealth(
                name="telegram_api",
                status=HealthStatus.DEGRADED,
                message=f"Telegram API 检查失败: {str(e)}",
                response_time_ms=response_time
            )
    
    async def check_session_files(self) -> ComponentHealth:
        """检查 Session 文件目录"""
        start_time = time.time()
        try:
            from group_ai_service.config import get_group_ai_config
            from pathlib import Path
            
            config = get_group_ai_config()
            sessions_dir = Path(config.session_files_directory)
            
            # 检查目录是否存在
            if not sessions_dir.exists():
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="session_files",
                    status=HealthStatus.DEGRADED,
                    message=f"Session 目录不存在: {sessions_dir}",
                    response_time_ms=response_time
                )
            
            # 统计 Session 文件数量
            session_files = list(sessions_dir.glob("*.session"))
            encrypted_files = list(sessions_dir.glob("*.encrypted"))
            
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="session_files",
                status=HealthStatus.HEALTHY,
                message="Session 文件目录正常",
                response_time_ms=response_time,
                details={
                    "directory": str(sessions_dir),
                    "session_files_count": len(session_files),
                    "encrypted_files_count": len(encrypted_files),
                    "total_files": len(session_files) + len(encrypted_files)
                }
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"Session 文件健康检查失败: {e}")
            return ComponentHealth(
                name="session_files",
                status=HealthStatus.DEGRADED,
                message=f"Session 文件检查失败: {str(e)}",
                response_time_ms=response_time
            )
    
    async def check_accounts(self) -> ComponentHealth:
        """检查账号服务状态"""
        start_time = time.time()
        try:
            from app.services.service_manager import get_service_manager
            from app.api.deps import get_db
            from app.db import SessionLocal
            
            db = SessionLocal()
            try:
                service_manager = get_service_manager()
                account_manager = service_manager.account_manager
                
                # 统计账号状态
                accounts = account_manager.list_accounts()
                online_count = sum(1 for acc in accounts if acc.status.value == "online")
                offline_count = sum(1 for acc in accounts if acc.status.value == "offline")
                error_count = sum(1 for acc in accounts if acc.status.value == "error")
                
                response_time = (time.time() - start_time) * 1000
                
                # 判断健康状态
                if error_count > len(accounts) * 0.5:  # 超过50%账号错误
                    status = HealthStatus.UNHEALTHY
                    message = f"账号服务异常：{error_count}/{len(accounts)} 账号错误"
                elif offline_count > len(accounts) * 0.7:  # 超过70%账号离线
                    status = HealthStatus.DEGRADED
                    message = f"账号服务降级：{offline_count}/{len(accounts)} 账号离线"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"账号服务正常：{online_count}/{len(accounts)} 账号在线"
                
                return ComponentHealth(
                    name="accounts",
                    status=status,
                    message=message,
                    response_time_ms=response_time,
                    details={
                        "total_accounts": len(accounts),
                        "online_count": online_count,
                        "offline_count": offline_count,
                        "error_count": error_count
                    }
                )
            finally:
                db.close()
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"账号服务健康检查失败: {e}")
            return ComponentHealth(
                name="accounts",
                status=HealthStatus.UNKNOWN,
                message=f"账号服务检查失败: {str(e)}",
                response_time_ms=response_time
            )
    
    async def check_cache(self) -> ComponentHealth:
        """检查缓存服务状态"""
        start_time = time.time()
        try:
            from app.core.cache import get_cache_manager
            cache_manager = get_cache_manager()
            stats = cache_manager.get_stats()
            
            response_time = (time.time() - start_time) * 1000
            
            # 判断健康状态
            hit_rate = stats.get("hit_rate", 0.0)
            if hit_rate < 0.3:  # 命中率过低
                status = HealthStatus.DEGRADED
                message = f"缓存命中率较低：{hit_rate:.1%}"
            else:
                status = HealthStatus.HEALTHY
                message = f"缓存服务正常：命中率 {hit_rate:.1%}"
            
            return ComponentHealth(
                name="cache",
                status=status,
                message=message,
                response_time_ms=response_time,
                details={
                    "hit_rate": hit_rate,
                    "hits": stats.get("hits", 0),
                    "misses": stats.get("misses", 0),
                    "backend": stats.get("backend", "memory"),
                    "memory_cache_size": stats.get("memory_cache_size", 0)
                }
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"缓存服务健康检查失败: {e}")
            return ComponentHealth(
                name="cache",
                status=HealthStatus.UNKNOWN,
                message=f"缓存服务检查失败: {str(e)}",
                response_time_ms=response_time
            )
    
    async def check_service_manager(self) -> ComponentHealth:
        """检查服务管理器状态"""
        start_time = time.time()
        try:
            from app.services.service_manager import get_service_manager
            service_manager = get_service_manager()
            
            # 检查服务管理器是否正常
            account_manager = service_manager.account_manager
            accounts = account_manager.list_accounts()
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="service_manager",
                status=HealthStatus.HEALTHY,
                message="服务管理器正常",
                response_time_ms=response_time,
                details={
                    "managed_accounts": len(accounts),
                    "service_type": "ServiceManager"
                }
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"服务管理器健康检查失败: {e}")
            return ComponentHealth(
                name="service_manager",
                status=HealthStatus.DEGRADED,
                message=f"服务管理器检查失败: {str(e)}",
                response_time_ms=response_time
            )
    
    async def check_all(self, include_optional: bool = True) -> Dict[str, Any]:
        """
        检查所有组件
        
        Args:
            include_optional: 是否包含可选组件（Redis、Telegram API）
        
        Returns:
            健康检查结果字典
        """
        checks = [
            self.check_database(),
            self.check_session_files(),
            self.check_accounts(),
            self.check_cache(),
            self.check_service_manager(),
        ]
        
        if include_optional:
            checks.extend([
                self.check_redis(),
                self.check_telegram_api(),
            ])
        
        # 并行执行所有检查
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        components = []
        overall_status = HealthStatus.HEALTHY
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"健康检查异常: {result}")
                components.append(ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNKNOWN,
                    message=f"检查异常: {str(result)}"
                ).to_dict())
                overall_status = HealthStatus.DEGRADED
            else:
                component = result
                components.append(component.to_dict())
                self.components[component.name] = component
                
                # 更新整体状态
                if component.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif component.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "summary": {
                "healthy": sum(1 for c in components if c["status"] == "healthy"),
                "degraded": sum(1 for c in components if c["status"] == "degraded"),
                "unhealthy": sum(1 for c in components if c["status"] == "unhealthy"),
                "unknown": sum(1 for c in components if c["status"] == "unknown"),
            }
        }
    
    def get_cached_status(self) -> Optional[Dict[str, Any]]:
        """
        获取缓存的健康状态（不执行检查）
        
        Returns:
            缓存的健康状态或 None
        """
        if not self.components:
            return None
        
        components = [comp.to_dict() for comp in self.components.values()]
        
        # 计算整体状态
        if any(c["status"] == "unhealthy" for c in components):
            overall_status = HealthStatus.UNHEALTHY
        elif any(c["status"] == "degraded" for c in components):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "cached": True
        }


# 全局健康检查器实例
_health_checker: Optional[HealthChecker] = None


def get_health_checker(timeout: float = 5.0) -> HealthChecker:
    """获取全局健康检查器实例"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(timeout=timeout)
    return _health_checker

