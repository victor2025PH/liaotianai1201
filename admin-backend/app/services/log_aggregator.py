"""
日志聚合服务
集中收集、过滤和分析来自多个源的日志
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


class LogAggregator:
    """日志聚合器"""
    
    def __init__(self, max_buffer_size: int = 10000):
        """
        初始化日志聚合器
        
        Args:
            max_buffer_size: 最大缓冲区大小
        """
        self.max_buffer_size = max_buffer_size
        self.log_buffer: List[Dict[str, Any]] = []
        self.log_sources: Dict[str, Dict[str, Any]] = {}
        self.aggregation_stats = {
            "total_logs": 0,
            "logs_by_level": defaultdict(int),
            "logs_by_source": defaultdict(int),
            "logs_by_type": defaultdict(int),
            "error_patterns": Counter(),
            "recent_errors": []
        }
    
    def add_log(self, log_entry: Dict[str, Any]):
        """
        添加日志条目到缓冲区
        
        Args:
            log_entry: 日志条目字典，应包含：
                - timestamp: 时间戳
                - level: 日志级别 (error, warning, info)
                - message: 日志消息
                - source: 日志来源
                - type: 日志类型
        """
        # 确保时间戳是datetime对象
        if isinstance(log_entry.get("timestamp"), str):
            try:
                log_entry["timestamp"] = datetime.fromisoformat(log_entry["timestamp"].replace("Z", "+00:00"))
            except Exception:
                log_entry["timestamp"] = datetime.now()
        
        # 添加到缓冲区
        self.log_buffer.append(log_entry)
        
        # 如果缓冲区超过最大大小，移除最旧的条目
        if len(self.log_buffer) > self.max_buffer_size:
            self.log_buffer = self.log_buffer[-self.max_buffer_size:]
        
        # 更新统计信息
        self._update_stats(log_entry)
    
    def _update_stats(self, log_entry: Dict[str, Any]):
        """更新统计信息"""
        self.aggregation_stats["total_logs"] += 1
        
        level = log_entry.get("level", "info").lower()
        source = log_entry.get("source", "unknown")
        log_type = log_entry.get("type", "unknown")
        
        self.aggregation_stats["logs_by_level"][level] += 1
        self.aggregation_stats["logs_by_source"][source] += 1
        self.aggregation_stats["logs_by_type"][log_type] += 1
        
        # 如果是错误，提取错误模式并添加到最近错误列表
        if level == "error":
            message = log_entry.get("message", "")
            # 提取错误模式（例如：数据库连接错误、API错误等）
            error_pattern = self._extract_error_pattern(message)
            self.aggregation_stats["error_patterns"][error_pattern] += 1
            
            # 添加到最近错误列表（最多保留50个）
            self.aggregation_stats["recent_errors"].append(log_entry)
            if len(self.aggregation_stats["recent_errors"]) > 50:
                self.aggregation_stats["recent_errors"] = self.aggregation_stats["recent_errors"][-50:]
    
    def _extract_error_pattern(self, message: str) -> str:
        """
        从错误消息中提取错误模式
        
        Args:
            message: 错误消息
        
        Returns:
            错误模式字符串
        """
        # 常见的错误模式
        patterns = [
            (r"database.*connection.*failed", "数据库连接失败"),
            (r"timeout", "超时错误"),
            (r"permission.*denied", "权限拒绝"),
            (r"not.*found", "资源未找到"),
            (r"validation.*error", "验证错误"),
            (r"authentication.*failed", "认证失败"),
            (r"rate.*limit", "速率限制"),
            (r"internal.*error", "内部错误"),
        ]
        
        message_lower = message.lower()
        for pattern, label in patterns:
            if re.search(pattern, message_lower):
                return label
        
        # 如果没有匹配的模式，返回消息的前50个字符
        return message[:50] + "..." if len(message) > 50 else message
    
    def get_logs(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取过滤后的日志
        
        Args:
            level: 日志级别过滤
            source: 日志来源过滤
            start_time: 开始时间
            end_time: 结束时间
            search: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            过滤后的日志列表
        """
        filtered_logs = self.log_buffer.copy()
        
        # 按时间过滤
        if start_time:
            filtered_logs = [
                log for log in filtered_logs
                if isinstance(log.get("timestamp"), datetime) and log["timestamp"] >= start_time
            ]
        
        if end_time:
            filtered_logs = [
                log for log in filtered_logs
                if isinstance(log.get("timestamp"), datetime) and log["timestamp"] <= end_time
            ]
        
        # 按级别过滤
        if level:
            filtered_logs = [
                log for log in filtered_logs
                if log.get("level", "").lower() == level.lower()
            ]
        
        # 按来源过滤
        if source:
            filtered_logs = [
                log for log in filtered_logs
                if log.get("source", "") == source
            ]
        
        # 搜索关键词
        if search:
            search_lower = search.lower()
            filtered_logs = [
                log for log in filtered_logs
                if search_lower in log.get("message", "").lower()
            ]
        
        # 按时间排序（最新的在前）
        filtered_logs.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        # 限制数量
        return filtered_logs[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "total_logs": self.aggregation_stats["total_logs"],
            "logs_by_level": dict(self.aggregation_stats["logs_by_level"]),
            "logs_by_source": dict(self.aggregation_stats["logs_by_source"]),
            "logs_by_type": dict(self.aggregation_stats["logs_by_type"]),
            "error_count": self.aggregation_stats["logs_by_level"].get("error", 0),
            "warning_count": self.aggregation_stats["logs_by_level"].get("warning", 0),
            "info_count": self.aggregation_stats["logs_by_level"].get("info", 0),
            "top_error_patterns": dict(self.aggregation_stats["error_patterns"].most_common(10)),
            "recent_errors": self.aggregation_stats["recent_errors"][-10:],  # 最近10个错误
            "buffer_size": len(self.log_buffer)
        }
    
    def clear_buffer(self):
        """清空日志缓冲区"""
        self.log_buffer.clear()
        self.aggregation_stats = {
            "total_logs": 0,
            "logs_by_level": defaultdict(int),
            "logs_by_source": defaultdict(int),
            "logs_by_type": defaultdict(int),
            "error_patterns": Counter(),
            "recent_errors": []
        }
        logger.info("日志缓冲区已清空")
    
    def register_source(self, source_id: str, source_info: Dict[str, Any]):
        """
        注册日志来源
        
        Args:
            source_id: 来源ID
            source_info: 来源信息（名称、类型等）
        """
        self.log_sources[source_id] = source_info
        logger.info(f"注册日志来源: {source_id}")
    
    def get_sources(self) -> Dict[str, Dict[str, Any]]:
        """获取所有注册的日志来源"""
        return self.log_sources.copy()


# 全局日志聚合器实例
_log_aggregator: Optional[LogAggregator] = None


def get_log_aggregator() -> LogAggregator:
    """获取日志聚合器实例"""
    global _log_aggregator
    if _log_aggregator is None:
        _log_aggregator = LogAggregator()
    return _log_aggregator

