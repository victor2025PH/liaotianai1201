"""
權限定義 - 系統所有權限的集中定義
"""
from enum import Enum


class PermissionCode(str, Enum):
    """權限代碼枚舉"""
    
    # ============ 賬號管理 ============
    ACCOUNT_VIEW = "account:view"
    ACCOUNT_CREATE = "account:create"
    ACCOUNT_UPDATE = "account:update"
    ACCOUNT_DELETE = "account:delete"
    ACCOUNT_START = "account:start"
    ACCOUNT_STOP = "account:stop"
    ACCOUNT_BATCH_OPERATE = "account:batch_operate"
    
    # ============ Session 文件管理 ============
    SESSION_VIEW = "session:view"
    SESSION_UPLOAD = "session:upload"
    SESSION_DOWNLOAD = "session:download"
    SESSION_DELETE = "session:delete"
    SESSION_ENCRYPT = "session:encrypt"
    
    # ============ 劇本管理 ============
    SCRIPT_VIEW = "script:view"
    SCRIPT_CREATE = "script:create"
    SCRIPT_UPDATE = "script:update"
    SCRIPT_DELETE = "script:delete"
    SCRIPT_TEST = "script:test"
    SCRIPT_VERSION_VIEW = "script:version:view"
    SCRIPT_VERSION_COMPARE = "script:version:compare"
    SCRIPT_VERSION_RESTORE = "script:version:restore"
    SCRIPT_REVIEW = "script:review"
    SCRIPT_PUBLISH = "script:publish"
    SCRIPT_DISABLE = "script:disable"
    
    # ============ 角色分配 ============
    ROLE_ASSIGNMENT_VIEW = "role_assignment:view"
    ROLE_ASSIGNMENT_CREATE = "role_assignment:create"
    ROLE_ASSIGNMENT_UPDATE = "role_assignment:update"
    ROLE_ASSIGNMENT_DELETE = "role_assignment:delete"
    ROLE_ASSIGNMENT_SCHEME_VIEW = "role_assignment_scheme:view"
    ROLE_ASSIGNMENT_SCHEME_CREATE = "role_assignment_scheme:create"
    ROLE_ASSIGNMENT_SCHEME_UPDATE = "role_assignment_scheme:update"
    ROLE_ASSIGNMENT_SCHEME_DELETE = "role_assignment_scheme:delete"
    ROLE_ASSIGNMENT_SCHEME_APPLY = "role_assignment_scheme:apply"
    
    # ============ 監控管理 ============
    MONITOR_VIEW = "monitor:view"
    MONITOR_HISTORY_VIEW = "monitor:history:view"
    MONITOR_STATISTICS_VIEW = "monitor:statistics:view"
    
    # ============ 告警管理 ============
    ALERT_RULE_VIEW = "alert_rule:view"
    ALERT_RULE_CREATE = "alert_rule:create"
    ALERT_RULE_UPDATE = "alert_rule:update"
    ALERT_RULE_DELETE = "alert_rule:delete"
    ALERT_RULE_ENABLE = "alert_rule:enable"
    ALERT_RULE_DISABLE = "alert_rule:disable"
    
    # ============ 自動化任務 ============
    AUTOMATION_TASK_VIEW = "automation_task:view"
    AUTOMATION_TASK_CREATE = "automation_task:create"
    AUTOMATION_TASK_UPDATE = "automation_task:update"
    AUTOMATION_TASK_DELETE = "automation_task:delete"
    AUTOMATION_TASK_RUN = "automation_task:run"
    AUTOMATION_TASK_LOG_VIEW = "automation_task:log:view"
    
    # ============ 數據導出 ============
    EXPORT_ACCOUNT = "export:account"
    EXPORT_SCRIPT = "export:script"
    EXPORT_ROLE_ASSIGNMENT_SCHEME = "export:role_assignment_scheme"
    
    # ============ 服務器管理 ============
    SERVER_VIEW = "server:view"
    SERVER_UPDATE = "server:update"
    SERVER_CONTROL = "server:control"
    
    # ============ 用戶管理 ============
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ROLE_ASSIGN = "user:role:assign"
    
    # ============ 角色管理 ============
    ROLE_VIEW = "role:view"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    
    # ============ 權限管理 ============
    PERMISSION_VIEW = "permission:view"
    PERMISSION_CREATE = "permission:create"
    PERMISSION_UPDATE = "permission:update"
    PERMISSION_DELETE = "permission:delete"
    PERMISSION_ASSIGN = "permission:assign"
    
    # ============ 審計日誌 ============
    AUDIT_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"
    
    # ============ 系統管理 ============
    SYSTEM_VIEW = "system:view"
    SYSTEM_MANAGE = "system:manage"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_RESTORE = "system:restore"


# 權限組定義（用於批量分配和檢查）
PERMISSION_GROUPS = {
    "account_management": [
        PermissionCode.ACCOUNT_VIEW,
        PermissionCode.ACCOUNT_CREATE,
        PermissionCode.ACCOUNT_UPDATE,
        PermissionCode.ACCOUNT_DELETE,
        PermissionCode.ACCOUNT_START,
        PermissionCode.ACCOUNT_STOP,
        PermissionCode.ACCOUNT_BATCH_OPERATE,
        PermissionCode.SESSION_VIEW,
        PermissionCode.SESSION_UPLOAD,
        PermissionCode.SESSION_DOWNLOAD,
        PermissionCode.SESSION_DELETE,
        PermissionCode.SESSION_ENCRYPT,
    ],
    "script_management": [
        PermissionCode.SCRIPT_VIEW,
        PermissionCode.SCRIPT_CREATE,
        PermissionCode.SCRIPT_UPDATE,
        PermissionCode.SCRIPT_DELETE,
        PermissionCode.SCRIPT_TEST,
        PermissionCode.SCRIPT_VERSION_VIEW,
        PermissionCode.SCRIPT_VERSION_COMPARE,
        PermissionCode.SCRIPT_VERSION_RESTORE,
        PermissionCode.SCRIPT_REVIEW,
        PermissionCode.SCRIPT_PUBLISH,
        PermissionCode.SCRIPT_DISABLE,
    ],
    "role_assignment": [
        PermissionCode.ROLE_ASSIGNMENT_VIEW,
        PermissionCode.ROLE_ASSIGNMENT_CREATE,
        PermissionCode.ROLE_ASSIGNMENT_UPDATE,
        PermissionCode.ROLE_ASSIGNMENT_DELETE,
        PermissionCode.ROLE_ASSIGNMENT_SCHEME_VIEW,
        PermissionCode.ROLE_ASSIGNMENT_SCHEME_CREATE,
        PermissionCode.ROLE_ASSIGNMENT_SCHEME_UPDATE,
        PermissionCode.ROLE_ASSIGNMENT_SCHEME_DELETE,
        PermissionCode.ROLE_ASSIGNMENT_SCHEME_APPLY,
    ],
    "monitor_management": [
        PermissionCode.MONITOR_VIEW,
        PermissionCode.MONITOR_HISTORY_VIEW,
        PermissionCode.MONITOR_STATISTICS_VIEW,
        PermissionCode.ALERT_RULE_VIEW,
        PermissionCode.ALERT_RULE_CREATE,
        PermissionCode.ALERT_RULE_UPDATE,
        PermissionCode.ALERT_RULE_DELETE,
        PermissionCode.ALERT_RULE_ENABLE,
        PermissionCode.ALERT_RULE_DISABLE,
    ],
    "automation_management": [
        PermissionCode.AUTOMATION_TASK_VIEW,
        PermissionCode.AUTOMATION_TASK_CREATE,
        PermissionCode.AUTOMATION_TASK_UPDATE,
        PermissionCode.AUTOMATION_TASK_DELETE,
        PermissionCode.AUTOMATION_TASK_RUN,
        PermissionCode.AUTOMATION_TASK_LOG_VIEW,
    ],
    "export_management": [
        PermissionCode.EXPORT_ACCOUNT,
        PermissionCode.EXPORT_SCRIPT,
        PermissionCode.EXPORT_ROLE_ASSIGNMENT_SCHEME,
    ],
    "server_management": [
        PermissionCode.SERVER_VIEW,
        PermissionCode.SERVER_UPDATE,
        PermissionCode.SERVER_CONTROL,
    ],
    "user_management": [
        PermissionCode.USER_VIEW,
        PermissionCode.USER_CREATE,
        PermissionCode.USER_UPDATE,
        PermissionCode.USER_DELETE,
        PermissionCode.USER_ROLE_ASSIGN,
        PermissionCode.ROLE_VIEW,
        PermissionCode.ROLE_CREATE,
        PermissionCode.ROLE_UPDATE,
        PermissionCode.ROLE_DELETE,
        PermissionCode.PERMISSION_VIEW,
        PermissionCode.PERMISSION_CREATE,
        PermissionCode.PERMISSION_UPDATE,
        PermissionCode.PERMISSION_DELETE,
        PermissionCode.PERMISSION_ASSIGN,
    ],
    "audit_management": [
        PermissionCode.AUDIT_VIEW,
        PermissionCode.AUDIT_EXPORT,
    ],
    "system_management": [
        PermissionCode.SYSTEM_VIEW,
        PermissionCode.SYSTEM_MANAGE,
        PermissionCode.SYSTEM_BACKUP,
        PermissionCode.SYSTEM_RESTORE,
    ],
}


# 預定義角色及其權限
PREDEFINED_ROLES = {
    "admin": {
        "description": "系統管理員",
        "permissions": [code.value for code in PermissionCode],  # 包含所有權限，包括審計日誌
    },
    "operator": {
        "description": "運營人員",
        "permissions": [
            # 賬號管理（讀取和操作，不能刪除）
            PermissionCode.ACCOUNT_VIEW.value,
            PermissionCode.ACCOUNT_UPDATE.value,
            PermissionCode.ACCOUNT_START.value,
            PermissionCode.ACCOUNT_STOP.value,
            PermissionCode.ACCOUNT_BATCH_OPERATE.value,
            # 劇本管理（讀取和測試，不能創建/刪除/發布）
            PermissionCode.SCRIPT_VIEW.value,
            PermissionCode.SCRIPT_TEST.value,
            PermissionCode.SCRIPT_VERSION_VIEW.value,
            # 角色分配（讀取和應用）
            PermissionCode.ROLE_ASSIGNMENT_VIEW.value,
            PermissionCode.ROLE_ASSIGNMENT_SCHEME_VIEW.value,
            PermissionCode.ROLE_ASSIGNMENT_SCHEME_APPLY.value,
            # 監控管理（完整權限）
            *[code.value for code in PERMISSION_GROUPS["monitor_management"]],
            # 自動化任務（查看和執行）
            PermissionCode.AUTOMATION_TASK_VIEW.value,
            PermissionCode.AUTOMATION_TASK_RUN.value,
            PermissionCode.AUTOMATION_TASK_LOG_VIEW.value,
            # 數據導出
            *[code.value for code in PERMISSION_GROUPS["export_management"]],
        ],
    },
    "viewer": {
        "description": "查看者",
        "permissions": [
            # 只讀權限
            PermissionCode.ACCOUNT_VIEW.value,
            PermissionCode.SCRIPT_VIEW.value,
            PermissionCode.SCRIPT_VERSION_VIEW.value,
            PermissionCode.ROLE_ASSIGNMENT_VIEW.value,
            PermissionCode.ROLE_ASSIGNMENT_SCHEME_VIEW.value,
            PermissionCode.MONITOR_VIEW.value,
            PermissionCode.MONITOR_HISTORY_VIEW.value,
            PermissionCode.MONITOR_STATISTICS_VIEW.value,
            PermissionCode.ALERT_RULE_VIEW.value,
            PermissionCode.AUTOMATION_TASK_VIEW.value,
            PermissionCode.AUTOMATION_TASK_LOG_VIEW.value,
        ],
    },
}

