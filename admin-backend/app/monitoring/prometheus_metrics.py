"""
Prometheus 指标定义和收集
"""
import time
import logging
from typing import Optional
from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY
)
from prometheus_client.multiprocess import MultiProcessCollector

logger = logging.getLogger(__name__)

# 创建自定义注册表（可选，用于多进程环境）
registry = CollectorRegistry()

# ============ HTTP 请求指标 ============

# HTTP 请求总数（按方法和状态码）
http_requests_total = Counter(
    'http_requests_total',
    'HTTP 请求总数',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

# HTTP 请求持续时间（按端点）
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP 请求持续时间（秒）',
    ['method', 'endpoint', 'status_code'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=registry
)

# HTTP 请求大小（字节）
http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP 请求大小（字节）',
    ['method', 'endpoint'],
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000],
    registry=registry
)

# HTTP 响应大小（字节）
http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP 响应大小（字节）',
    ['method', 'endpoint', 'status_code'],
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000, 500000],
    registry=registry
)

# ============ 账号管理指标 ============

# 账号总数
accounts_total = Gauge(
    'accounts_total',
    '账号总数',
    ['status'],  # online, offline, error
    registry=registry
)

# 账号在线数
accounts_online = Gauge(
    'accounts_online',
    '在线账号数',
    registry=registry
)

# 账号离线数
accounts_offline = Gauge(
    'accounts_offline',
    '离线账号数',
    registry=registry
)

# 账号错误数
accounts_error = Gauge(
    'accounts_error',
    '错误账号数',
    registry=registry
)

# 账号消息总数
account_messages_total = Counter(
    'account_messages_total',
    '账号消息总数',
    ['account_id', 'type'],  # type: sent, received
    registry=registry
)

# 账号回复总数
account_replies_total = Counter(
    'account_replies_total',
    '账号回复总数',
    ['account_id'],
    registry=registry
)

# 账号红包参与总数
account_redpackets_total = Counter(
    'account_redpackets_total',
    '账号红包参与总数',
    ['account_id', 'status'],  # status: success, failure
    registry=registry
)

# 账号错误总数
account_errors_total = Counter(
    'account_errors_total',
    '账号错误总数',
    ['account_id', 'error_type'],
    registry=registry
)

# 账号响应时间
account_response_time_seconds = Histogram(
    'account_response_time_seconds',
    '账号响应时间（秒）',
    ['account_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=registry
)

# ============ Session 文件指标 ============

# Session 文件总数
session_files_total = Gauge(
    'session_files_total',
    'Session 文件总数',
    ['type'],  # plain, encrypted
    registry=registry
)

# Session 文件上传总数
session_uploads_total = Counter(
    'session_uploads_total',
    'Session 文件上传总数',
    ['status'],  # success, failure
    registry=registry
)

# Session 文件访问总数
session_access_total = Counter(
    'session_access_total',
    'Session 文件访问总数',
    ['action'],  # upload, download, view, delete
    registry=registry
)

# ============ 数据库指标 ============

# 数据库连接数
database_connections = Gauge(
    'database_connections',
    '数据库连接数',
    ['state'],  # active, idle
    registry=registry
)

# 数据库查询总数
database_queries_total = Counter(
    'database_queries_total',
    '数据库查询总数',
    ['operation', 'status'],  # operation: select, insert, update, delete
    registry=registry
)

# 数据库查询持续时间
database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    '数据库查询持续时间（秒）',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry
)

# ============ Redis 指标（如果启用）============

# Redis 连接状态
redis_connected = Gauge(
    'redis_connected',
    'Redis 连接状态（1=已连接，0=未连接）',
    registry=registry
)

# Redis 操作总数
redis_operations_total = Counter(
    'redis_operations_total',
    'Redis 操作总数',
    ['operation', 'status'],  # operation: get, set, delete
    registry=registry
)

# Redis 操作持续时间
redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Redis 操作持续时间（秒）',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
    registry=registry
)

# ============ 系统资源指标 ============

# 系统 CPU 使用率
system_cpu_usage_percent = Gauge(
    'system_cpu_usage_percent',
    '系统 CPU 使用率（百分比）',
    registry=registry
)

# 系统内存使用量（字节）
system_memory_usage_bytes = Gauge(
    'system_memory_usage_bytes',
    '系统内存使用量（字节）',
    registry=registry
)

# 系统内存使用率（百分比）
system_memory_usage_percent = Gauge(
    'system_memory_usage_percent',
    '系统内存使用率（百分比）',
    registry=registry
)

# 系统磁盘使用量（字节）
system_disk_usage_bytes = Gauge(
    'system_disk_usage_bytes',
    '系统磁盘使用量（字节）',
    registry=registry
)

# 系统磁盘使用率（百分比）
system_disk_usage_percent = Gauge(
    'system_disk_usage_percent',
    '系统磁盘使用率（百分比）',
    registry=registry
)

# ============ 业务指标 ============

# 剧本总数
scripts_total = Gauge(
    'scripts_total',
    '剧本总数',
    ['status'],  # active, inactive
    registry=registry
)

# 角色分配方案总数
role_assignment_schemes_total = Gauge(
    'role_assignment_schemes_total',
    '角色分配方案总数',
    registry=registry
)

# 自动化任务总数
automation_tasks_total = Gauge(
    'automation_tasks_total',
    '自动化任务总数',
    ['status'],  # enabled, disabled
    registry=registry
)

# 自动化任务执行总数
automation_task_executions_total = Counter(
    'automation_task_executions_total',
    '自动化任务执行总数',
    ['task_id', 'status'],  # status: success, failure
    registry=registry
)

# ============ 错误和告警指标 ============

# 系统错误总数
system_errors_total = Counter(
    'system_errors_total',
    '系统错误总数',
    ['error_type', 'severity'],  # severity: warning, error, critical
    registry=registry
)

# 告警总数
alerts_total = Counter(
    'alerts_total',
    '告警总数',
    ['level', 'type'],  # level: warning, critical, type: account, system, etc.
    registry=registry
)

# 活跃告警数
alerts_active = Gauge(
    'alerts_active',
    '活跃告警数',
    ['level', 'type'],
    registry=registry
)

# ============ 工具函数 ============

def update_account_metrics(account_id: str, status: str, metrics: Optional[dict] = None):
    """
    更新账号指标
    
    Args:
        account_id: 账号 ID
        status: 账号状态（online, offline, error）
        metrics: 账号指标字典（可选）
    """
    try:
        # 更新账号状态计数
        if status == "online":
            accounts_online.inc()
        elif status == "offline":
            accounts_offline.inc()
        elif status == "error":
            accounts_error.inc()
        
        # 更新账号总数（按状态）
        accounts_total.labels(status=status).inc()
        
        if metrics:
            # 更新消息计数
            if "messages_sent" in metrics:
                account_messages_total.labels(account_id=account_id, type="sent").inc(metrics["messages_sent"])
            if "messages_received" in metrics:
                account_messages_total.labels(account_id=account_id, type="received").inc(metrics["messages_received"])
            
            # 更新回复计数
            if "replies" in metrics:
                account_replies_total.labels(account_id=account_id).inc(metrics["replies"])
            
            # 更新红包计数
            if "redpackets_success" in metrics:
                account_redpackets_total.labels(account_id=account_id, status="success").inc(metrics["redpackets_success"])
            if "redpackets_failure" in metrics:
                account_redpackets_total.labels(account_id=account_id, status="failure").inc(metrics["redpackets_failure"])
            
            # 更新错误计数
            if "errors" in metrics:
                for error_type, count in metrics["errors"].items():
                    account_errors_total.labels(account_id=account_id, error_type=error_type).inc(count)
            
            # 更新响应时间
            if "response_time" in metrics:
                account_response_time_seconds.labels(account_id=account_id).observe(metrics["response_time"])
    except Exception as e:
        logger.error(f"更新账号指标失败: {e}")


def update_session_metrics(action: str, status: str = "success", file_type: Optional[str] = None):
    """
    更新 Session 文件指标
    
    Args:
        action: 操作类型（upload, download, view, delete）
        status: 操作状态（success, failure）
        file_type: 文件类型（plain, encrypted）
    """
    try:
        session_access_total.labels(action=action).inc()
        
        if action == "upload":
            session_uploads_total.labels(status=status).inc()
        
        if file_type:
            session_files_total.labels(type=file_type).inc()
    except Exception as e:
        logger.error(f"更新 Session 指标失败: {e}")


def update_database_metrics(operation: str, duration: float, status: str = "success"):
    """
    更新数据库指标
    
    Args:
        operation: 操作类型（select, insert, update, delete）
        duration: 操作持续时间（秒）
        status: 操作状态（success, failure）
    """
    try:
        database_queries_total.labels(operation=operation, status=status).inc()
        if status == "success":
            database_query_duration_seconds.labels(operation=operation).observe(duration)
    except Exception as e:
        logger.error(f"更新数据库指标失败: {e}")


def update_redis_metrics(operation: str, duration: float, status: str = "success"):
    """
    更新 Redis 指标
    
    Args:
        operation: 操作类型（get, set, delete）
        duration: 操作持续时间（秒）
        status: 操作状态（success, failure）
    """
    try:
        redis_operations_total.labels(operation=operation, status=status).inc()
        if status == "success":
            redis_operation_duration_seconds.labels(operation=operation).observe(duration)
        
        # 更新连接状态
        if status == "success":
            redis_connected.set(1)
        else:
            redis_connected.set(0)
    except Exception as e:
        logger.error(f"更新 Redis 指标失败: {e}")


def update_system_resource_metrics(cpu_percent: float, memory_bytes: int, memory_percent: float,
                                   disk_bytes: int, disk_percent: float):
    """
    更新系统资源指标
    
    Args:
        cpu_percent: CPU 使用率（百分比）
        memory_bytes: 内存使用量（字节）
        memory_percent: 内存使用率（百分比）
        disk_bytes: 磁盘使用量（字节）
        disk_percent: 磁盘使用率（百分比）
    """
    try:
        system_cpu_usage_percent.set(cpu_percent)
        system_memory_usage_bytes.set(memory_bytes)
        system_memory_usage_percent.set(memory_percent)
        system_disk_usage_bytes.set(disk_bytes)
        system_disk_usage_percent.set(disk_percent)
    except Exception as e:
        logger.error(f"更新系统资源指标失败: {e}")


def get_metrics_output() -> bytes:
    """
    获取 Prometheus 格式的指标输出
    
    Returns:
        Prometheus 格式的指标数据（字节）
    """
    try:
        # 尝试使用多进程收集器（如果启用）
        try:
            collector = MultiProcessCollector(registry)
            return generate_latest(registry)
        except (ValueError, ImportError):
            # 单进程模式，使用默认注册表
            return generate_latest(REGISTRY)
    except Exception as e:
        logger.error(f"生成 Prometheus 指标失败: {e}")
        return b"# Error generating metrics\n"


# 导出所有指标（用于在其他模块中使用）
__all__ = [
    # HTTP 指标
    'http_requests_total',
    'http_request_duration_seconds',
    'http_request_size_bytes',
    'http_response_size_bytes',
    # 账号指标
    'accounts_total',
    'accounts_online',
    'accounts_offline',
    'accounts_error',
    'account_messages_total',
    'account_replies_total',
    'account_redpackets_total',
    'account_errors_total',
    'account_response_time_seconds',
    # Session 指标
    'session_files_total',
    'session_uploads_total',
    'session_access_total',
    # 数据库指标
    'database_connections',
    'database_queries_total',
    'database_query_duration_seconds',
    # Redis 指标
    'redis_connected',
    'redis_operations_total',
    'redis_operation_duration_seconds',
    # 系统资源指标
    'system_cpu_usage_percent',
    'system_memory_usage_bytes',
    'system_memory_usage_percent',
    'system_disk_usage_bytes',
    'system_disk_usage_percent',
    # 业务指标
    'scripts_total',
    'role_assignment_schemes_total',
    'automation_tasks_total',
    'automation_task_executions_total',
    # 错误和告警指标
    'system_errors_total',
    'alerts_total',
    'alerts_active',
    # 工具函数
    'update_account_metrics',
    'update_session_metrics',
    'update_database_metrics',
    'update_redis_metrics',
    'update_system_resource_metrics',
    'get_metrics_output',
    'CONTENT_TYPE_LATEST',
]

