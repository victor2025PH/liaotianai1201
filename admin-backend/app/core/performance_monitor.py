"""
性能监控和自动优化系统
监控系统性能，自动识别瓶颈并提供优化建议
"""
import logging
import time
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import statistics

logger = logging.getLogger(__name__)

# 可选依赖
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil 未安装，性能监控功能将受限")


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, check_interval: int = 60):
        """
        初始化性能监控器
        
        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self.metrics_history: Dict[str, deque] = {
            "cpu": deque(maxlen=100),
            "memory": deque(maxlen=100),
            "disk_io": deque(maxlen=100),
            "network_io": deque(maxlen=100),
        }
        self.alerts: List[Dict] = []
        self._monitoring_task: Optional[asyncio.Task] = None
    
    async def collect_metrics(self) -> Dict:
        """收集系统指标"""
        if not PSUTIL_AVAILABLE:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "psutil 未安装，无法收集系统指标"
            }
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            network = psutil.net_io_counters()
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                }
            }
            
            # 记录历史
            self.metrics_history["cpu"].append(cpu_percent)
            self.metrics_history["memory"].append(memory.percent)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集指标异常: {e}", exc_info=True)
            return {}
    
    def analyze_performance(self) -> Dict:
        """分析性能并生成建议"""
        suggestions = []
        warnings = []
        
        # CPU 分析
        if self.metrics_history["cpu"]:
            avg_cpu = statistics.mean(self.metrics_history["cpu"])
            max_cpu = max(self.metrics_history["cpu"])
            
            if avg_cpu > 80:
                warnings.append({
                    "type": "cpu_high",
                    "message": f"CPU 使用率持续偏高: {avg_cpu:.1f}%",
                    "severity": "high"
                })
                suggestions.append("考虑优化 CPU 密集型任务或增加计算资源")
            
            if max_cpu > 95:
                warnings.append({
                    "type": "cpu_critical",
                    "message": f"CPU 使用率达到临界值: {max_cpu:.1f}%",
                    "severity": "critical"
                })
        
        # 内存分析
        if self.metrics_history["memory"]:
            avg_memory = statistics.mean(self.metrics_history["memory"])
            max_memory = max(self.metrics_history["memory"])
            
            if avg_memory > 85:
                warnings.append({
                    "type": "memory_high",
                    "message": f"内存使用率持续偏高: {avg_memory:.1f}%",
                    "severity": "high"
                })
                suggestions.append("考虑优化内存使用或增加内存容量")
            
            if max_memory > 95:
                warnings.append({
                    "type": "memory_critical",
                    "message": f"内存使用率达到临界值: {max_memory:.1f}%",
                    "severity": "critical"
                })
                suggestions.append("立即检查内存泄漏或增加内存")
        
        return {
            "warnings": warnings,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
    
    async def start_monitoring(self):
        """启动性能监控"""
        async def monitoring_loop():
            while True:
                try:
                    metrics = await self.collect_metrics()
                    analysis = self.analyze_performance()
                    
                    # 如果有警告，记录并发送告警
                    if analysis["warnings"]:
                        for warning in analysis["warnings"]:
                            if warning["severity"] == "critical":
                                logger.critical(f"性能告警: {warning['message']}")
                            else:
                                logger.warning(f"性能警告: {warning['message']}")
                    
                    await asyncio.sleep(self.check_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"性能监控异常: {e}", exc_info=True)
                    await asyncio.sleep(self.check_interval)
        
        self._monitoring_task = asyncio.create_task(monitoring_loop())
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            logger.info("性能监控已停止")
    
    def get_current_metrics(self) -> Dict:
        """获取当前指标"""
        return asyncio.run(self.collect_metrics())
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        analysis = self.analyze_performance()
        current_metrics = self.get_current_metrics()
        
        return {
            "current": current_metrics,
            "analysis": analysis,
            "history_size": {k: len(v) for k, v in self.metrics_history.items()}
        }


# 全局性能监控器实例
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

