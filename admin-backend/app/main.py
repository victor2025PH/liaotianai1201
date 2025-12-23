from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.api import router as api_router
from app.core.auto_backup import get_backup_manager
from app.core.performance_monitor import get_performance_monitor
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db import Base, engine, SessionLocal
from app.crud.user import assign_role_to_user, create_role, create_user, get_user_by_email
from app.core.errors import UserFriendlyError, create_error_response
from app.middleware.performance import PerformanceMonitoringMiddleware
from fastapi.exceptions import RequestValidationError, ResponseValidationError

# 導入限流（可選，如果未安裝則跳過）
try:
    from app.core.limiter import limiter, RateLimitExceeded
    from slowapi.errors import _rate_limit_exceeded_handler
    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False
    limiter = None

logger = logging.getLogger(__name__)

# 配置日志：同时输出到控制台和文件
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 创建logs目录
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 清除现有的处理器
root_logger.handlers.clear()

# 控制台处理器（输出到stdout）
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(console_formatter)

# 文件处理器（输出到文件）
file_handler = RotatingFileHandler(
    log_dir / "backend.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

# 添加处理器
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

logger.info(f"日志配置完成：控制台输出 + 文件输出 ({log_dir / 'backend.log'})")

app = FastAPI(
    title="Smart TG Admin API",
    version="0.1.0",
    description="后台管理系统 API 服务",
)

# 自定义OpenAPI生成函数，确保包含所有路由
def custom_openapi():
    """自定义OpenAPI生成函数，确保包含所有路由"""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# 使用自定义OpenAPI生成函数
app.openapi = custom_openapi

settings = get_settings()

# 添加限流（如果可用）
if RATE_LIMITING_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置 CORS - 當 allow_credentials=True 時，不能使用 "*"，必須指定具體的來源
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else []
# 如果未配置，使用默認開發環境的前端地址
if not cors_origins:
    cors_origins = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加性能監控中間件
app.add_middleware(
    PerformanceMonitoringMiddleware,
    slow_request_threshold_ms=1000.0  # 超過 1000ms 的請求視為慢請求
)

# 添加请求日志中间件，记录所有 PUT 请求到 /accounts
@app.middleware("http")
async def log_accounts_requests(request: Request, call_next):
    import logging
    import json
    logger = logging.getLogger(__name__)
    
    # 记录 PUT 请求到 /accounts
    if request.method == "PUT" and "/accounts/" in str(request.url.path):
        client_host = request.client.host if request.client else 'unknown'
        logger.info(f"[MIDDLEWARE] PUT 请求到达: {request.url.path}, client={client_host}, headers={dict(request.headers)}")
        
        # 读取请求体并记录（需要恢复请求体以便后续处理）
        body_bytes = await request.body()
        if body_bytes:
            try:
                body_dict = json.loads(body_bytes)
                logger.info(f"[MIDDLEWARE] 请求体: {json.dumps(body_dict, ensure_ascii=False)[:500]}")
            except Exception as e:
                logger.warning(f"[MIDDLEWARE] 无法解析请求体: {e}")
        
        # 恢复请求体（FastAPI 需要可迭代的 body）
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive
    
    response = await call_next(request)
    
    if request.method == "PUT" and "/accounts/" in str(request.url.path):
        logger.info(f"[MIDDLEWARE] PUT 响应状态: {response.status_code}, path={request.url.path}")
    
    return response

app.include_router(api_router, prefix="/api/v1")


# 添加 ResponseValidationError 异常处理器
@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    """处理响应验证错误"""
    import json
    import traceback
    
    error_details = exc.errors()
    logger.error(f"响应验证错误: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
    logger.error(f"请求路径: {request.url.path}")
    logger.error(f"请求方法: {request.method}")
    
    # 尝试解析响应体
    try:
        if hasattr(exc, 'body') and exc.body:
            if isinstance(exc.body, bytes):
                body_str = exc.body.decode('utf-8', errors='ignore')
            else:
                body_str = str(exc.body)
            logger.error(f"响应内容（前500字符）: {body_str[:500]}")
    except Exception as e:
        logger.error(f"无法解析响应体: {e}")
    
    # 记录完整的堆栈跟踪
    logger.error(f"响应验证错误堆栈跟踪:\n{traceback.format_exc()}")
    
    # 返回详细的错误信息（开发环境）
    import os
    is_dev = os.getenv("ENVIRONMENT", "production") == "development"
    
    return create_error_response(
        error_code="INTERNAL_ERROR",
        message="服务器内部错误：响应验证失败",
        status_code=500,
        technical_detail=f"响应验证失败: {json.dumps(error_details, indent=2, ensure_ascii=False)}" if is_dev else "响应验证失败"
    )


@app.on_event("startup")
async def on_startup() -> None:
    # 驗證數據庫連接和數據持久化
    try:
        from app.db import SessionLocal
        from app.models.group_ai import GroupAIScript, GroupAIAutomationTask
        db = SessionLocal()
        try:
            script_count = db.query(GroupAIScript).count()
            task_count = db.query(GroupAIAutomationTask).count()
            logger.info(f"數據庫連接成功 - 劇本數量: {script_count}, 任務數量: {task_count}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"數據庫驗證失敗: {e}", exc_info=True)
    
    # 啟動任務調度器（會自動從數據庫加載啟用的定時任務）
    try:
        from app.services.task_scheduler import get_task_scheduler
        scheduler = get_task_scheduler()
        scheduler.start()
        logger.info("任務調度器已啟動，已從數據庫加載所有啟用的定時任務")
    except Exception as e:
        logger.error(f"啟動任務調度器失敗: {e}", exc_info=True)
    
    # 啟動自動備份服務
    try:
        backup_manager = get_backup_manager()
        if backup_manager.auto_backup_enabled:
            settings = get_settings()
            await backup_manager.start_auto_backup(
                database_url=getattr(settings, "database_url", None),
                sessions_dir="sessions",
                config_files=[".env", "admin-backend/.env"]
            )
            logger.info("自動備份服務已啟動")
    except Exception as e:
        logger.warning(f"啟動自動備份失敗: {e}")
    
    # 啟動性能監控服務
    try:
        monitor = get_performance_monitor()
        await monitor.start_monitoring()
        logger.info("性能監控服務已啟動")
    except Exception as e:
        logger.warning(f"啟動性能監控失敗: {e}")
    
    # 啟動 WebSocket Manager（Agent 通信）
    try:
        from app.websocket import get_websocket_manager
        ws_manager = get_websocket_manager()
        await ws_manager.start()
        logger.info("WebSocket Manager 已啟動（Agent 通信）")
    except Exception as e:
        logger.error(f"啟動 WebSocket Manager 失敗: {e}", exc_info=True)
    
    # 初始化日誌聚合器並註冊日誌來源
    try:
        from app.services.log_aggregator import get_log_aggregator
        aggregator = get_log_aggregator()
        aggregator.register_source("local", {"name": "本地服務", "type": "application"})
        aggregator.register_source("remote", {"name": "遠程服務器", "type": "system"})
        logger.info("日誌聚合服務已初始化")
    except Exception as e:
        logger.warning(f"初始化日誌聚合服務失敗: {e}", exc_info=True)
    
    # 啟動故障恢復服務
    try:
        from app.core.intelligent_allocator import IntelligentAllocator
        from app.core.fault_recovery import FaultRecoveryService
        from app.db import SessionLocal
        
        allocator = IntelligentAllocator()
        fault_recovery = FaultRecoveryService(allocator)
        
        # 從配置文件讀取故障恢復設置
        import json
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "data" / "master_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                fault_recovery_config = config.get("allocation", {}).get("fault_recovery", {})
                fault_recovery.recovery_enabled = fault_recovery_config.get("enabled", True)
                fault_recovery.check_interval = fault_recovery_config.get("check_interval", 300)
                fault_recovery.failure_threshold = fault_recovery_config.get("failure_threshold", 3)
        
        if fault_recovery.recovery_enabled:
            await fault_recovery.start()
            logger.info("故障恢復服務已啟動")
        else:
            logger.info("故障恢復服務已禁用")
    except Exception as e:
        logger.warning(f"啟動故障恢復服務失敗: {e}")
    
    # 啟動智能優化服務
    try:
        from app.services.smart_optimizer import get_smart_optimizer
        optimizer = get_smart_optimizer()
        if optimizer.auto_optimize_enabled:
            settings = get_settings()
            interval = getattr(settings, "auto_optimize_interval_hours", 6)
            await optimizer.start_auto_optimization(interval_hours=interval)
            logger.info("智能優化服務已啟動")
    except Exception as e:
        logger.warning(f"啟動智能優化失敗: {e}")
    
    # 啟動時驗證環境變量（fail-fast）
    settings = get_settings()
    try:
        # 驗證必填環境變量
        if settings.jwt_secret == "change_me":
            logger.warning(
                "⚠️  JWT_SECRET 使用默認值 'change_me'，生產環境必須修改！"
            )
        if settings.admin_default_password == "changeme123":
            logger.warning(
                "⚠️  ADMIN_DEFAULT_PASSWORD 使用默認值 'changeme123'，生產環境必須修改！"
            )
        logger.info("環境變量驗證通過")
    except Exception as e:
        logger.error(f"環境變量驗證失敗: {e}")
        # 注意：這裡不 raise，允許應用啟動（某些配置可能可選）
    # 確保導入所有模型，包括 Group AI 模型（用於 Alembic 自動生成）
    from app.models import group_ai  # 確保導入模型
    from app.models.group_ai import (  # 明確導入所有模型類
        GroupAIScript,
        GroupAIAccount,
        GroupAIScriptVersion,
        GroupAIDialogueHistory,
        GroupAIRedpacketLog,
        GroupAIAutomationTask,
        GroupAIAutomationTaskLog,
        AllocationHistory,
        AIProviderConfig,
        AIProviderSettings  # 新增的分配历史模型
    )
    
    # 確保所有表已創建（開發環境後備方案）
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("數據庫表已確保創建（後備方案）")
    except Exception as create_error:
        logger.warning(f"創建數據庫表失敗（可能已存在）: {create_error}")
    
    # 檢查 Alembic 版本（不自動運行遷移，僅檢查和警告）
    try:
        from alembic.config import Config
        from alembic import script
        from alembic.runtime.migration import MigrationContext
        
        alembic_cfg = Config("alembic.ini")
        script_dir = script.ScriptDirectory.from_config(alembic_cfg)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            head_rev = script_dir.get_current_head()
            
            if current_rev != head_rev:
                logger.warning(
                    f"數據庫版本 ({current_rev}) 與代碼版本 ({head_rev}) 不一致。"
                    f"請運行 'poetry run alembic upgrade head' 或 'python -m scripts.run_migrations' 進行遷移。"
                )
            else:
                logger.info(f"數據庫版本已是最新 ({current_rev})")
    except Exception as e:
        logger.warning(f"檢查 Alembic 版本失敗: {e}，將嘗試使用 create_all() 作為後備")
        # 後備方案：如果 Alembic 檢查失敗，使用 create_all()（僅用於開發環境）
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("使用 create_all() 創建數據庫表（後備方案）")
        except Exception as create_error:
            logger.error(f"創建數據庫表失敗: {create_error}", exc_info=True)
    settings = get_settings()
    with SessionLocal() as db:
        admin = get_user_by_email(db, email=settings.admin_default_email)
        if not admin:
            admin = create_user(
                db,
                email=settings.admin_default_email,
                password=settings.admin_default_password,
                full_name="超级管理员",
                is_superuser=True,
            )
        admin_role = create_role(db, name="admin", description="系统管理员")
        assign_role_to_user(db, user=admin, role=admin_role)
    
    # 显式导入groups模块，确保路由注册
    try:
        from app.api.group_ai import groups
        logger.info(f"Groups模块已显式导入，路由数: {len(groups.router.routes)}")
        
        # 检查groups路由是否已注册到主应用
        groups_routes = [r for r in app.routes if hasattr(r, 'path') and 'groups' in str(r.path)]
        logger.info(f"主应用中的Groups路由数: {len(groups_routes)}")
        
        if not groups_routes:
            logger.warning("Groups路由未注册到主应用，尝试重新注册...")
            # 如果路由未注册，尝试重新包含
            from app.api import group_ai
            if hasattr(group_ai, 'router'):
                # 路由应该已经通过api_router包含，这里只是验证
                logger.info("Group-AI router已包含在API router中")
    except Exception as e:
        logger.error(f"显式导入Groups模块失败: {e}", exc_info=True)
    
    # 强制重新生成OpenAPI schema，确保包含所有路由
    try:
        app.openapi_schema = None  # 清除缓存
        _ = app.openapi()  # 触发重新生成
        logger.info("OpenAPI schema已重新生成")
    except Exception as e:
        logger.warning(f"重新生成OpenAPI schema失败: {e}", exc_info=True)
    
    # 啟動定時告警檢查服務（如果啟用）
    if settings.alert_check_enabled:
        try:
            from app.services.scheduled_alert_checker import get_scheduled_checker
            checker = get_scheduled_checker()
            checker.start()
            logger.info(f"定時告警檢查服務已啟動，檢查間隔: {checker.interval_seconds} 秒")
        except Exception as e:
            logger.warning(f"啟動定時告警檢查服務失敗: {e}", exc_info=True)
    
    # 啟動緩存預熱服務
    try:
        from app.core.cache_optimization import CacheOptimizer
        optimizer = CacheOptimizer()
        # 在后台任务中执行缓存预热（不阻塞启动）
        import asyncio
        asyncio.create_task(optimizer.warmup_cache())
        logger.info("緩存預熱服務已啟動（後台執行）")
    except Exception as e:
        logger.warning(f"啟動緩存預熱服務失敗: {e}", exc_info=True)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """應用關閉時停止定時任務"""
    # 停止性能監控
    try:
        monitor = get_performance_monitor()
        monitor.stop_monitoring()
        logger.info("性能監控服務已停止")
    except Exception as e:
        logger.warning(f"停止性能監控失敗: {e}")
    
    # 停止自動備份
    try:
        backup_manager = get_backup_manager()
        backup_manager.stop_auto_backup()
        logger.info("自動備份服務已停止")
    except Exception as e:
        logger.warning(f"停止自動備份失敗: {e}")
    
    # 停止 WebSocket Manager
    try:
        from app.websocket import get_websocket_manager
        ws_manager = get_websocket_manager()
        await ws_manager.stop()
        logger.info("WebSocket Manager 已停止")
    except Exception as e:
        logger.warning(f"停止 WebSocket Manager 失敗: {e}")
    # 停止任務調度器
    try:
        from app.services.task_scheduler import get_task_scheduler
        scheduler = get_task_scheduler()
        if scheduler.is_running:
            scheduler.stop()
            logger.info("任務調度器已停止")
    except Exception as e:
        logger.warning(f"停止任務調度器失敗: {e}", exc_info=True)
    
    # 停止定時告警檢查服務
    try:
        from app.services.scheduled_alert_checker import get_scheduled_checker
        checker = get_scheduled_checker()
        if checker.is_running:
            checker.stop()
            logger.info("定時告警檢查服務已停止")
    except Exception as e:
        logger.warning(f"停止定時告警檢查服務失敗: {e}", exc_info=True)


@app.get("/health", tags=["health"])
async def health_check(detailed: bool = Query(False, description="是否返回详细健康信息")):
    """
    基礎健康檢查端點
    
    Args:
        detailed: 是否返回详细健康信息（默认 False，快速检查）
    
    Returns:
        健康状态信息
    """
    if not detailed:
        # 快速检查：只检查数据库
        try:
            from app.db import SessionLocal
            from sqlalchemy import text
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                return {"status": "ok"}
            finally:
                db.close()
        except Exception:
            return {"status": "error"}, 503
    
    # 详细检查：检查所有组件
    from app.core.health_check import get_health_checker
    checker = get_health_checker()
    result = await checker.check_all(include_optional=True)
    
    # 根据整体状态返回相应的 HTTP 状态码
    status_code = 200
    if result["status"] == "unhealthy":
        status_code = 503
    elif result["status"] == "degraded":
        status_code = 200  # 降级但仍可用
    
    return result, status_code


@app.get("/healthz", tags=["health"])
async def health_check_k8s():
    """
    Kubernetes 健康檢查端點
    
    用于 Kubernetes liveness 和 readiness 探针
    只进行快速检查，不包含详细组件信息
    """
    try:
        from app.db import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ok"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {"status": "error", "message": str(e)}, 503


@app.get("/metrics", tags=["metrics"])
async def prometheus_metrics():
    """
    Prometheus 指标端点
    
    返回 Prometheus 格式的指标数据
    用于 Prometheus 服务器抓取
    """
    from app.monitoring.prometheus_metrics import get_metrics_output, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    try:
        output = get_metrics_output()
        return Response(content=output, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"获取 Prometheus 指标失败: {e}")
        return Response(content=b"# Error generating metrics\n", media_type=CONTENT_TYPE_LATEST)


@app.get("/", tags=["root"])
def root():
    """根路徑，返回API信息"""
    return {
        "message": "Smart TG Admin API",
        "version": "0.1.0",
        "docs": "/docs",
        "api_prefix": "/api/v1"
    }


# 全局錯誤處理
@app.exception_handler(UserFriendlyError)
async def user_friendly_error_handler(request: Request, exc: UserFriendlyError):
    """用戶友好錯誤處理"""
    response = JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {"error_code": "UNKNOWN", "message": str(exc.detail)}
    )
    # 確保 CORS 頭被添加
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用異常處理"""
    import traceback
    error_traceback = traceback.format_exc()
    logger.exception(f"未處理的異常: {exc}", exc_info=True)
    
    # 生產環境返回通用錯誤，開發環境返回詳細錯誤
    import os
    environment = os.getenv("ENVIRONMENT", "development")  # 默認開發環境
    
    if environment == "development":
        detail = {
            "error_code": "INTERNAL_ERROR",
            "message": "服務器內部錯誤",
            "technical_detail": str(exc),
            "error_type": type(exc).__name__,
            "traceback": error_traceback.split('\n')[-10:]  # 最後10行堆棧
        }
    else:
        detail = {
            "error_code": "INTERNAL_ERROR",
            "message": "服務器內部錯誤，請聯繫管理員"
        }
    
    response = JSONResponse(
        status_code=500,
        content=detail
    )
    # 確保 CORS 頭被添加
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response


