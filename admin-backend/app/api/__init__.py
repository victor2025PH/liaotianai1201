from fastapi import APIRouter

from app.api import routes
from app.api import auth, users
from app.api import group_ai, permissions, roles, user_roles, audit_logs, notifications, performance
from app.api.system import optimization
from app.api import telegram_registration
from app.api import workers
from app.api import redpacket
from app.api import agents

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(routes.router)
router.include_router(group_ai.router)
router.include_router(permissions.router)
router.include_router(roles.router)
router.include_router(user_roles.router)
router.include_router(audit_logs.router)
router.include_router(notifications.router)
router.include_router(performance.router)
router.include_router(optimization.router)
router.include_router(telegram_registration.router)
router.include_router(workers.router)
router.include_router(redpacket.router)
router.include_router(agents.router)

