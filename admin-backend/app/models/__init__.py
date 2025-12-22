from app.models.role import Role
from app.models.user import User
from app.models.permission import Permission
from app.models.user_role import user_role_table
from app.models.role_permission import role_permission_table
from app.models.audit_log import AuditLog
from app.models.notification import (
    NotificationConfig,
    Notification,
    NotificationType,
    NotificationStatus,
    NotificationTemplate,
)
from app.models.telegram_registration import (
    UserRegistration,
    SessionFile,
    AntiDetectionLog,
)
from app.models.group_ai import (
    GroupAIAccount,
    GroupAIScript,
    GroupAIScriptVersion,
    AllocationHistory,
    GroupAIDialogueHistory,
    GroupAIRedpacketLog,
    GroupAIMetric,
    GroupAIAlertRule,
    GroupAIRoleAssignmentScheme,
    GroupAIRoleAssignmentHistory,
    GroupAIAutomationTask,
    GroupAIAutomationTaskLog,
    RedPacketStrategy,
)
from app.models.theater import (
    TheaterScenario,
    TheaterExecution,
)
from app.models.unified_features import (
    KeywordTriggerRule,
    ScheduledMessageTask,
    ScheduledMessageLog,
    GroupJoinConfig,
    GroupJoinLog,
    UnifiedConfig,
    GroupActivityMetrics,
)

__all__ = [
    "Role",
    "User",
    "Permission",
    "user_role_table",
    "role_permission_table",
    "AuditLog",
    "NotificationConfig",
    "Notification",
    "NotificationType",
    "NotificationStatus",
    "NotificationTemplate",
    "UserRegistration",
    "SessionFile",
    "AntiDetectionLog",
    "GroupAIAccount",
    "GroupAIScript",
    "GroupAIScriptVersion",
    "AllocationHistory",
    "GroupAIDialogueHistory",
    "GroupAIRedpacketLog",
    "GroupAIMetric",
    "GroupAIAlertRule",
    "GroupAIRoleAssignmentScheme",
    "GroupAIRoleAssignmentHistory",
    "GroupAIAutomationTask",
    "GroupAIAutomationTaskLog",
    "RedPacketStrategy",
    "TheaterScenario",
    "TheaterExecution",
    "KeywordTriggerRule",
    "ScheduledMessageTask",
    "ScheduledMessageLog",
    "GroupJoinConfig",
    "GroupJoinLog",
    "UnifiedConfig",
    "GroupActivityMetrics",
]

