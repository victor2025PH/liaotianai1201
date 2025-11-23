"""
智能优化服务
自动分析系统状态，提供优化建议并自动执行优化操作
"""
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta

try:
    from app.core.cache import get_cache_manager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    from app.core.performance_monitor import get_performance_monitor
    PERFORMANCE_MONITOR_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITOR_AVAILABLE = False

try:
    from app.core.auto_backup import get_backup_manager
    BACKUP_AVAILABLE = True
except ImportError:
    BACKUP_AVAILABLE = False

logger = logging.getLogger(__name__)


class SmartOptimizer:
    """智能优化器"""
    
    def __init__(self):
        self.optimization_history: List[Dict] = []
        self.auto_optimize_enabled = True
    
    async def analyze_system(self) -> Dict:
        """分析系统状态"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "cache": {},
            "performance": {},
            "backup": {},
            "recommendations": []
        }
        
        # 分析缓存
        if CACHE_AVAILABLE:
            try:
                cache_manager = get_cache_manager()
                analysis["cache"] = {
                    "memory_cache_size": len(cache_manager.memory_cache),
                    "redis_enabled": cache_manager.redis_client is not None,
                    "recommendation": self._analyze_cache(cache_manager)
                }
            except Exception as e:
                analysis["cache"] = {"error": str(e)}
        else:
            analysis["cache"] = {"error": "缓存模块不可用"}
        
        # 分析性能
        if PERFORMANCE_MONITOR_AVAILABLE:
            try:
                monitor = get_performance_monitor()
                perf_summary = monitor.get_performance_summary()
                analysis["performance"] = perf_summary
            except Exception as e:
                analysis["performance"] = {"error": str(e)}
        else:
            analysis["performance"] = {"error": "性能监控模块不可用"}
        
        # 分析备份
        if BACKUP_AVAILABLE:
            try:
                backup_manager = get_backup_manager()
                backup_files = list(backup_manager.backup_dir.glob("*"))
                analysis["backup"] = {
                    "backup_count": len([f for f in backup_files if f.is_file()]),
                    "last_backup": self._get_last_backup_time(backup_manager),
                    "recommendation": self._analyze_backup(backup_manager)
                }
            except Exception as e:
                analysis["backup"] = {"error": str(e)}
        else:
            analysis["backup"] = {"error": "备份模块不可用"}
        
        # 生成建议
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_cache(self, cache_manager) -> Dict:
        """分析缓存状态"""
        recommendations = []
        
        if len(cache_manager.memory_cache) > 1000:
            recommendations.append("内存缓存项过多，考虑清理或使用 Redis")
        
        if not cache_manager.redis_client:
            recommendations.append("建议启用 Redis 缓存以提高性能")
        
        return {
            "status": "good" if len(recommendations) == 0 else "needs_attention",
            "recommendations": recommendations
        }
    
    def _analyze_backup(self, backup_manager) -> Dict:
        """分析备份状态"""
        recommendations = []
        
        backup_files = list(backup_manager.backup_dir.glob("*"))
        if len(backup_files) == 0:
            recommendations.append("没有备份文件，建议立即创建备份")
        
        last_backup = self._get_last_backup_time(backup_manager)
        if last_backup:
            hours_since_backup = (datetime.now() - last_backup).total_seconds() / 3600
            if hours_since_backup > 48:
                recommendations.append(f"上次备份已过去 {hours_since_backup:.1f} 小时，建议创建新备份")
        
        return {
            "status": "good" if len(recommendations) == 0 else "needs_attention",
            "recommendations": recommendations
        }
    
    def _get_last_backup_time(self, backup_manager) -> Optional[datetime]:
        """获取最后备份时间"""
        backup_files = list(backup_manager.backup_dir.glob("*"))
        if not backup_files:
            return None
        
        latest_file = max(backup_files, key=lambda f: f.stat().st_mtime)
        return datetime.fromtimestamp(latest_file.stat().st_mtime)
    
    def _generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """生成优化建议"""
        recommendations = []
        
        # 缓存建议
        cache_rec = analysis["cache"].get("recommendation", {})
        recommendations.extend([
            {"category": "cache", "priority": "medium", "message": rec}
            for rec in cache_rec.get("recommendations", [])
        ])
        
        # 性能建议
        perf_analysis = analysis["performance"].get("analysis", {})
        for warning in perf_analysis.get("warnings", []):
            recommendations.append({
                "category": "performance",
                "priority": warning.get("severity", "medium"),
                "message": warning.get("message", "")
            })
        
        for suggestion in perf_analysis.get("suggestions", []):
            recommendations.append({
                "category": "performance",
                "priority": "low",
                "message": suggestion
            })
        
        # 备份建议
        backup_rec = analysis["backup"].get("recommendation", {})
        recommendations.extend([
            {"category": "backup", "priority": "high", "message": rec}
            for rec in backup_rec.get("recommendations", [])
        ])
        
        return recommendations
    
    async def auto_optimize(self) -> Dict:
        """自动执行优化"""
        if not self.auto_optimize_enabled:
            return {"message": "自动优化未启用"}
        
        optimizations = []
        
        # 分析系统
        analysis = await self.analyze_system()
        
        # 执行缓存优化
        if CACHE_AVAILABLE:
            try:
                cache_manager = get_cache_manager()
                if len(cache_manager.memory_cache) > 1000:
                    # 清理过期缓存
                    current_time = datetime.now()
                    expired_keys = [
                        k for k, v in cache_manager.memory_cache.items()
                        if current_time >= v["expires_at"]
                    ]
                    for key in expired_keys:
                        del cache_manager.memory_cache[key]
                    if expired_keys:
                        optimizations.append(f"清理了 {len(expired_keys)} 个过期缓存项")
            except Exception as e:
                logger.warning(f"缓存优化失败: {e}")
        
        # 执行备份（如果需要）
        if BACKUP_AVAILABLE:
            try:
                backup_rec = analysis["backup"].get("recommendation", {})
                if backup_rec.get("status") == "needs_attention":
                    backup_manager = get_backup_manager()
                    last_backup = self._get_last_backup_time(backup_manager)
                    if not last_backup or (datetime.now() - last_backup).total_seconds() > 86400:
                        await backup_manager.full_backup()
                        optimizations.append("已自动创建备份")
            except Exception as e:
                logger.warning(f"备份优化失败: {e}")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "optimizations": optimizations,
            "recommendations": analysis["recommendations"]
        }
        
        self.optimization_history.append(result)
        
        return result
    
    async def start_auto_optimization(self, interval_hours: int = 6):
        """启动自动优化"""
        async def optimization_loop():
            while True:
                try:
                    await asyncio.sleep(interval_hours * 3600)
                    logger.info("开始自动优化...")
                    result = await self.auto_optimize()
                    logger.info(f"自动优化完成: {result}")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"自动优化异常: {e}", exc_info=True)
        
        asyncio.create_task(optimization_loop())
        logger.info(f"自动优化已启动，间隔: {interval_hours} 小时")


# 全局智能优化器实例
_smart_optimizer: Optional[SmartOptimizer] = None


def get_smart_optimizer() -> SmartOptimizer:
    """获取智能优化器实例"""
    global _smart_optimizer
    if _smart_optimizer is None:
        from app.core.config import get_settings
        settings = get_settings()
        auto_optimize = getattr(settings, "auto_optimize_enabled", True)
        _smart_optimizer = SmartOptimizer(auto_optimize_enabled=auto_optimize)
    return _smart_optimizer

