"""
网络监控模块
检测网络连接状态，辅助故障恢复
"""
import asyncio
import logging
import socket
from typing import Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """网络连接监控器"""
    
    def __init__(self, check_interval: int = 60):
        """
        初始化网络监控器
        
        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self.last_check_time: Optional[datetime] = None
        self.last_check_result: Optional[bool] = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
    
    async def check_connectivity(
        self,
        host: str = "8.8.8.8",
        port: int = 53,
        timeout: float = 3.0
    ) -> Tuple[bool, Optional[str]]:
        """
        检查网络连接
        
        Args:
            host: 测试主机（默认 Google DNS）
            port: 测试端口
            timeout: 超时时间（秒）
        
        Returns:
            (是否连通, 错误消息)
        """
        try:
            # 使用 asyncio 创建连接
            try:
                await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=timeout
                )
                self.consecutive_failures = 0
                self.last_check_result = True
                self.last_check_time = datetime.now()
                return True, None
            except asyncio.TimeoutError:
                error_msg = f"连接超时: {host}:{port}"
                self.consecutive_failures += 1
                self.last_check_result = False
                self.last_check_time = datetime.now()
                return False, error_msg
            except Exception as e:
                error_msg = f"连接失败: {str(e)}"
                self.consecutive_failures += 1
                self.last_check_result = False
                self.last_check_time = datetime.now()
                return False, error_msg
        except Exception as e:
            error_msg = f"网络检查异常: {str(e)}"
            self.consecutive_failures += 1
            self.last_check_result = False
            self.last_check_time = datetime.now()
            return False, error_msg
    
    async def check_telegram_api(self, timeout: float = 5.0) -> Tuple[bool, Optional[str]]:
        """
        检查 Telegram API 连接
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            (是否连通, 错误消息)
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                try:
                    async with session.get("https://api.telegram.org") as response:
                        if response.status < 500:
                            self.consecutive_failures = 0
                            self.last_check_result = True
                            self.last_check_time = datetime.now()
                            return True, None
                        else:
                            error_msg = f"Telegram API 返回错误: {response.status}"
                            self.consecutive_failures += 1
                            self.last_check_result = False
                            self.last_check_time = datetime.now()
                            return False, error_msg
                except asyncio.TimeoutError:
                    error_msg = "Telegram API 连接超时"
                    self.consecutive_failures += 1
                    self.last_check_result = False
                    self.last_check_time = datetime.now()
                    return False, error_msg
                except Exception as e:
                    error_msg = f"Telegram API 连接失败: {str(e)}"
                    self.consecutive_failures += 1
                    self.last_check_result = False
                    self.last_check_time = datetime.now()
                    return False, error_msg
        except ImportError:
            # aiohttp 未安装，使用简单的 socket 检查
            return await self.check_connectivity("api.telegram.org", 443, timeout)
        except Exception as e:
            error_msg = f"检查 Telegram API 异常: {str(e)}"
            self.consecutive_failures += 1
            self.last_check_result = False
            self.last_check_time = datetime.now()
            return False, error_msg
    
    def is_network_healthy(self) -> bool:
        """
        判断网络是否健康
        
        Returns:
            网络是否健康
        """
        # 如果连续失败次数超过阈值，认为网络不健康
        if self.consecutive_failures >= self.max_consecutive_failures:
            return False
        
        # 如果最近一次检查成功，认为网络健康
        if self.last_check_result is True:
            return True
        
        # 如果从未检查过，假设网络健康
        if self.last_check_result is None:
            return True
        
        return False
    
    async def start_monitoring(self, callback: Optional[callable] = None):
        """
        开始监控网络状态
        
        Args:
            callback: 网络状态变化回调函数 (is_healthy: bool) -> None
        """
        last_health_status = None
        
        while True:
            try:
                # 检查网络连接
                is_connected, error = await self.check_connectivity()
                
                # 检查 Telegram API
                telegram_ok, telegram_error = await self.check_telegram_api()
                
                # 综合判断
                is_healthy = is_connected and telegram_ok
                
                # 如果状态发生变化，调用回调
                if callback and last_health_status != is_healthy:
                    try:
                        await callback(is_healthy)
                    except Exception as e:
                        logger.error(f"网络状态回调执行失败: {e}")
                
                last_health_status = is_healthy
                
                if not is_healthy:
                    logger.warning(
                        f"网络连接异常: 基础连接={is_connected}, "
                        f"Telegram API={telegram_ok}, 连续失败={self.consecutive_failures}"
                    )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"网络监控异常: {e}")
            
            await asyncio.sleep(self.check_interval)


# 全局网络监控器实例
_network_monitor: Optional[NetworkMonitor] = None


def get_network_monitor(check_interval: int = 60) -> NetworkMonitor:
    """获取全局网络监控器实例"""
    global _network_monitor
    if _network_monitor is None:
        _network_monitor = NetworkMonitor(check_interval=check_interval)
    return _network_monitor

