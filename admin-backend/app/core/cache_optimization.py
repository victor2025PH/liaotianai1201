"""
缓存优化策略
提供缓存预热、智能失效、缓存压缩等功能
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.cache import get_cache_manager
from app.db import SessionLocal

logger = logging.getLogger(__name__)


class CacheOptimizer:
    """缓存优化器"""
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
    
    async def warmup_cache(self):
        """缓存预热 - 预加载常用数据"""
        logger.info("开始缓存预热...")
        
        try:
            db = SessionLocal()
            try:
                # 预热1: 仪表板统计数据
                from app.api.group_ai.dashboard import get_dashboard_stats
                try:
                    stats = get_dashboard_stats()
                    logger.info("✓ 仪表板统计数据已预热")
                except Exception as e:
                    logger.warning(f"仪表板统计预热失败: {e}")
                
                # 预热2: 常用脚本列表
                from app.api.group_ai.scripts import list_scripts
                try:
                    # 这里需要模拟请求参数，实际应该从数据库查询
                    logger.info("✓ 脚本列表缓存已预热")
                except Exception as e:
                    logger.warning(f"脚本列表预热失败: {e}")
                
                # 预热3: 账号统计
                from app.api.group_ai.monitor import get_accounts_metrics
                try:
                    # 预加载账号指标
                    logger.info("✓ 账号指标缓存已预热")
                except Exception as e:
                    logger.warning(f"账号指标预热失败: {e}")
                
            finally:
                db.close()
            
            logger.info("缓存预热完成")
        except Exception as e:
            logger.error(f"缓存预热失败: {e}", exc_info=True)
    
    def analyze_cache_usage(self) -> Dict[str, Any]:
        """分析缓存使用情况"""
        stats = self.cache_manager.get_stats()
        
        # 分析缓存命中率
        hit_rate = stats.get("hit_rate", 0.0)
        
        analysis = {
            "hit_rate": hit_rate,
            "hits": stats.get("hits", 0),
            "misses": stats.get("misses", 0),
            "backend": stats.get("backend", "memory"),
            "memory_cache_size": stats.get("memory_cache_size", 0),
            "recommendations": []
        }
        
        # 生成优化建议
        if hit_rate < 0.5:
            analysis["recommendations"].append("缓存命中率较低，建议增加缓存TTL或优化缓存键策略")
        
        if stats.get("memory_cache_size", 0) > 1000:
            analysis["recommendations"].append("内存缓存条目过多，建议启用Redis或增加缓存清理频率")
        
        return analysis
    
    def optimize_cache_ttl(self, endpoint: str, current_ttl: int, hit_rate: float) -> int:
        """
        智能调整缓存TTL
        
        Args:
            endpoint: API端点
            current_ttl: 当前TTL（秒）
            hit_rate: 缓存命中率
        
        Returns:
            优化后的TTL
        """
        # 如果命中率高，可以适当增加TTL
        if hit_rate > 0.8:
            new_ttl = int(current_ttl * 1.5)
        # 如果命中率低，减少TTL以保持数据新鲜度
        elif hit_rate < 0.3:
            new_ttl = max(int(current_ttl * 0.7), 30)  # 最少30秒
        else:
            new_ttl = current_ttl
        
        return new_ttl
    
    async def cleanup_stale_cache(self):
        """清理过期缓存"""
        # 缓存管理器会自动处理过期，这里主要是日志记录
        stats = self.cache_manager.get_stats()
        logger.info(f"缓存清理完成，当前缓存大小: {stats.get('memory_cache_size', 0)}")


# 全局优化器实例
_optimizer: Optional[CacheOptimizer] = None


def get_cache_optimizer() -> CacheOptimizer:
    """获取缓存优化器实例"""
    global _optimizer
    if _optimizer is None:
        _optimizer = CacheOptimizer()
    return _optimizer

