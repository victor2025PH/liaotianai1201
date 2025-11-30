"""
群組 AI 系統 API 路由
"""
import logging
from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user

logger = logging.getLogger(__name__)

# 导入基础模块（logs 延迟导入以避免循环导入）
from app.api.group_ai import accounts, scripts, monitor, control, role_assignments, script_versions, servers, dashboard, alert_rules, dialogue, redpacket, script_review, role_assignment_schemes, export, automation_tasks, telegram_alerts, session_export, account_allocation, allocation, account_management, statistics

# 延迟导入 logs 以避免循环导入（logs 导入 servers，而 __init__ 同时导入两者）
try:
    from app.api.group_ai import logs
except ImportError as e:
    logger.warning(f"Logs模块导入失败: {e}，将跳过logs路由注册")
    logs = None

# 显式导入groups模块，添加错误处理
try:
    from app.api.group_ai import groups
    logger.info("Groups模块导入成功")
except Exception as e:
    logger.error(f"Groups模块导入失败: {e}", exc_info=True)
    # 创建一个空的router作为占位符，避免服务启动失败
    from fastapi import APIRouter as EmptyRouter
    groups = type('GroupsModule', (), {'router': EmptyRouter()})()

# 路由級別的認證依賴
router = APIRouter(
    prefix="/group-ai",
    tags=["group-ai"],
)

protected_dependency = [Depends(get_current_active_user)]

# 注意：accounts 路由的认证依赖在端点级别处理
router.include_router(
    accounts.router,
    prefix="/accounts",
    tags=["group-ai-accounts"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
# script_versions 必須在 scripts 之前註冊，確保 /compare 路由優先匹配
router.include_router(
    script_versions.router,
    prefix="/scripts",
    tags=["script-versions"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    script_review.router,
    prefix="/scripts",
    tags=["script-review"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)  # 審核流程路由必須在 scripts 之前
# 注意：scripts 路由的认证依赖在端点级别处理，避免路由级别和端点级别冲突
router.include_router(
    scripts.router,
    prefix="/scripts",
    tags=["group-ai-scripts"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    monitor.router,
    prefix="/monitor",
    tags=["group-ai-monitor"],
)
router.include_router(
    control.router,
    prefix="/control",
    tags=["group-ai-control"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    role_assignments.router,
    prefix="/role-assignments",
    tags=["role-assignments"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    role_assignment_schemes.router,
    prefix="/role-assignment-schemes",
    tags=["role-assignment-schemes"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    export.router,
    prefix="/export",
    tags=["data-export"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    automation_tasks.router,
    prefix="/automation-tasks",
    tags=["automation-tasks"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
# 注意：servers 路由的认证依赖在端点级别处理
router.include_router(
    servers.router,
    prefix="/servers",
    tags=["servers"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
# 注册 logs 路由（如果成功导入）
if logs is not None:
    router.include_router(
        logs.router,
        prefix="/logs",
        tags=["logs"],
        # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
    )
router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    alert_rules.router,
    prefix="/alert-rules",
    tags=["alert-rules"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    dialogue.router,
    prefix="/dialogue",
    tags=["group-ai-dialogue"],
)
router.include_router(
    redpacket.router,
    prefix="/redpacket",
    tags=["group-ai-redpacket"],
)
router.include_router(
    telegram_alerts.router,
    prefix="",
    tags=["telegram-alerts"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    session_export.router,
    prefix="/sessions",
    tags=["session-export"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    account_allocation.router,
    prefix="/account-allocation",
    tags=["account-allocation"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    allocation.router,
    prefix="/allocation",
    tags=["allocation"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
router.include_router(
    account_management.router,
    prefix="/account-management",
    tags=["account-management"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)

# 包含groups路由，添加错误处理
try:
    if hasattr(groups, 'router') and groups.router:
        router.include_router(groups.router, prefix="/groups", tags=["groups"])
        logger.info("Groups路由已成功注册")
    else:
        logger.warning("Groups router不存在或为空，跳过注册")
except Exception as e:
    logger.error(f"注册Groups路由失败: {e}", exc_info=True)



