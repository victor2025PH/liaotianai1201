"""
數據庫操作測試（CRUD）
"""
import pytest
import uuid
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import SessionLocal, Base, engine
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.group_ai import (
    GroupAIAccount,
    GroupAIScript,
    GroupAIScriptVersion,
    GroupAIDialogueHistory,
    GroupAIRedpacketLog,
    GroupAIMetric
)
from app.core.security import get_password_hash
from app.crud.user import create_user, get_user_by_email, create_role, assign_role_to_user


@pytest.fixture
def db() -> Session:
    """創建數據庫會話"""
    # 在測試前創建表（如果不存在）
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db: Session) -> User:
    """創建測試用戶"""
    user = create_user(
        db,
        email="test@example.com",
        password="testpass123",
        full_name="Test User",
        is_superuser=False,
    )
    return user


@pytest.fixture
def test_role(db: Session) -> Role:
    """創建測試角色"""
    role = create_role(db, name="test_role", description="測試角色")
    return role


# ============ User CRUD 測試 ============

def test_create_user(db: Session):
    """測試創建用戶"""
    user = create_user(
        db,
        email="newuser@example.com",
        password="newpass123",
        full_name="New User",
        is_superuser=False,
    )
    
    assert user.id is not None
    assert user.email == "newuser@example.com"
    assert user.full_name == "New User"
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.hashed_password != "newpass123"  # 應該是加密後的密碼


def test_get_user_by_email(db: Session, test_user: User):
    """測試通過郵箱獲取用戶"""
    user = get_user_by_email(db, email=test_user.email)
    
    assert user is not None
    assert user.email == test_user.email
    assert user.id == test_user.id


def test_get_user_by_email_not_found(db: Session):
    """測試獲取不存在的用戶"""
    user = get_user_by_email(db, email="nonexistent@example.com")
    
    assert user is None


def test_user_password_hash(db: Session):
    """測試用戶密碼哈希"""
    user = create_user(
        db,
        email="hashuser@example.com",
        password="plainpass123",
        full_name="Hash User",
        is_superuser=False,
    )
    
    # 密碼應該是哈希後的，不等於原始密碼
    assert user.hashed_password != "plainpass123"
    # 哈希密碼應該以 bcrypt 格式開頭
    assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$")


# ============ Role CRUD 測試 ============

def test_create_role(db: Session):
    """測試創建角色"""
    role = create_role(db, name="admin_role", description="管理員角色")
    
    assert role.id is not None
    assert role.name == "admin_role"
    assert role.description == "管理員角色"


def test_assign_role_to_user(db: Session):
    """測試分配角色給用戶"""
    # 創建新的測試用戶和角色，避免與其他測試衝突
    test_user = create_user(
        db,
        email=f"assign-test-{uuid.uuid4().hex[:8]}@example.com",
        password="testpass123",
        full_name="Assign Test User",
        is_superuser=False,
    )
    test_role = create_role(
        db,
        name=f"assign_test_role_{uuid.uuid4().hex[:8]}",
        description="Assign Test Role"
    )
    
    # 確保用戶和角色都沒有任何關聯
    db.refresh(test_user)
    db.refresh(test_role)
    
    # 分配角色
    assign_role_to_user(db, user=test_user, role=test_role)
    
    # 刷新用戶對象以獲取關聯的角色
    db.refresh(test_user)
    db.refresh(test_role)
    
    assert test_role in test_user.roles
    assert test_user in test_role.users


# ============ GroupAIAccount CRUD 測試 ============

def test_create_group_ai_account(db: Session):
    """測試創建群組 AI 賬號"""
    account = GroupAIAccount(
        id="test-account-1",
        account_id="test_account_1",
        session_file="test_session.session",
        script_id="test_script",
        group_ids=[123456, 789012],
        active=True,
        reply_rate=0.5,
        redpacket_enabled=True,
        redpacket_probability=0.6,
        max_replies_per_hour=100,
        min_reply_interval=5,
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    assert account.id == "test-account-1"
    assert account.account_id == "test_account_1"
    assert account.session_file == "test_session.session"
    assert account.script_id == "test_script"
    assert account.group_ids == [123456, 789012]
    assert account.active is True
    assert account.reply_rate == 0.5


def test_get_group_ai_account(db: Session):
    """測試獲取群組 AI 賬號"""
    account = GroupAIAccount(
        id="test-account-2",
        account_id="test_account_2",
        session_file="test_session2.session",
        script_id="test_script",
        group_ids=[],
        active=True,
    )
    
    db.add(account)
    db.commit()
    
    retrieved = db.query(GroupAIAccount).filter(GroupAIAccount.account_id == "test_account_2").first()
    
    assert retrieved is not None
    assert retrieved.account_id == "test_account_2"
    assert retrieved.id == "test-account-2"


def test_update_group_ai_account(db: Session):
    """測試更新群組 AI 賬號"""
    account = GroupAIAccount(
        id="test-account-3",
        account_id="test_account_3",
        session_file="test_session3.session",
        script_id="test_script",
        group_ids=[],
        active=True,
        reply_rate=0.3,
    )
    
    db.add(account)
    db.commit()
    
    # 更新賬號
    account.reply_rate = 0.7
    account.active = False
    db.commit()
    db.refresh(account)
    
    assert account.reply_rate == 0.7
    assert account.active is False


def test_delete_group_ai_account(db: Session):
    """測試刪除群組 AI 賬號"""
    account = GroupAIAccount(
        id="test-account-4",
        account_id="test_account_4",
        session_file="test_session4.session",
        script_id="test_script",
        group_ids=[],
        active=True,
    )
    
    db.add(account)
    db.commit()
    
    account_id = account.id
    
    # 刪除賬號
    db.delete(account)
    db.commit()
    
    # 驗證已刪除
    deleted = db.query(GroupAIAccount).filter(GroupAIAccount.id == account_id).first()
    assert deleted is None


# ============ GroupAIScript CRUD 測試 ============

def test_create_group_ai_script(db: Session):
    """測試創建群組 AI 劇本"""
    script = GroupAIScript(
        id="test-script-1",
        script_id="test_script_1",
        name="測試劇本",
        version="1.0",
        yaml_content="script_id: test_script_1\nversion: 1.0\nscenes: []",
        description="這是一個測試劇本",
    )
    
    db.add(script)
    db.commit()
    db.refresh(script)
    
    assert script.id == "test-script-1"
    assert script.script_id == "test_script_1"
    assert script.name == "測試劇本"
    assert script.version == "1.0"
    assert script.yaml_content is not None


def test_get_group_ai_script(db: Session):
    """測試獲取群組 AI 劇本"""
    script = GroupAIScript(
        id="test-script-2",
        script_id="test_script_2",
        name="測試劇本 2",
        version="1.0",
        yaml_content="script_id: test_script_2\nversion: 1.0\nscenes: []",
    )
    
    db.add(script)
    db.commit()
    
    retrieved = db.query(GroupAIScript).filter(GroupAIScript.script_id == "test_script_2").first()
    
    assert retrieved is not None
    assert retrieved.script_id == "test_script_2"
    assert retrieved.name == "測試劇本 2"


def test_update_group_ai_script(db: Session):
    """測試更新群組 AI 劇本"""
    script = GroupAIScript(
        id="test-script-3",
        script_id="test_script_3",
        name="測試劇本 3",
        version="1.0",
        yaml_content="script_id: test_script_3\nversion: 1.0\nscenes: []",
    )
    
    db.add(script)
    db.commit()
    
    # 更新劇本
    script.version = "1.1"
    script.name = "更新的劇本名稱"
    db.commit()
    db.refresh(script)
    
    assert script.version == "1.1"
    assert script.name == "更新的劇本名稱"


def test_delete_group_ai_script(db: Session):
    """測試刪除群組 AI 劇本"""
    script = GroupAIScript(
        id="test-script-4",
        script_id="test_script_4",
        name="測試劇本 4",
        version="1.0",
        yaml_content="script_id: test_script_4\nversion: 1.0\nscenes: []",
    )
    
    db.add(script)
    db.commit()
    
    script_id = script.id
    
    # 刪除劇本
    db.delete(script)
    db.commit()
    
    # 驗證已刪除
    deleted = db.query(GroupAIScript).filter(GroupAIScript.id == script_id).first()
    assert deleted is None


# ============ GroupAIScriptVersion CRUD 測試 ============

def test_create_group_ai_script_version(db: Session):
    """測試創建劇本版本"""
    # 先創建劇本
    script = GroupAIScript(
        id="test-script-5",
        script_id="test_script_5",
        name="測試劇本 5",
        version="1.0",
        yaml_content="script_id: test_script_5\nversion: 1.0\nscenes: []",
    )
    db.add(script)
    db.commit()
    
    # 創建版本
    version = GroupAIScriptVersion(
        id="test-version-1",
        script_id="test_script_5",
        version="1.1",
        yaml_content="script_id: test_script_5\nversion: 1.1\nscenes: []",
        description="版本 1.1",
    )
    
    db.add(version)
    db.commit()
    db.refresh(version)
    
    assert version.id == "test-version-1"
    assert version.script_id == "test_script_5"
    assert version.version == "1.1"


def test_get_script_versions(db: Session):
    """測試獲取劇本版本列表"""
    # 先創建劇本
    script = GroupAIScript(
        id="test-script-6",
        script_id="test_script_6",
        name="測試劇本 6",
        version="1.0",
        yaml_content="script_id: test_script_6\nversion: 1.0\nscenes: []",
    )
    db.add(script)
    db.commit()
    
    # 創建多個版本
    version1 = GroupAIScriptVersion(
        id="test-version-2",
        script_id="test_script_6",
        version="1.1",
        yaml_content="script_id: test_script_6\nversion: 1.1\nscenes: []",
    )
    version2 = GroupAIScriptVersion(
        id="test-version-3",
        script_id="test_script_6",
        version="1.2",
        yaml_content="script_id: test_script_6\nversion: 1.2\nscenes: []",
    )
    
    db.add(version1)
    db.add(version2)
    db.commit()
    
    # 查詢版本列表
    versions = db.query(GroupAIScriptVersion).filter(
        GroupAIScriptVersion.script_id == "test_script_6"
    ).all()
    
    assert len(versions) == 2
    version_ids = {v.version for v in versions}
    assert "1.1" in version_ids
    assert "1.2" in version_ids


# ============ GroupAIDialogueHistory CRUD 測試 ============

def test_create_dialogue_history(db: Session):
    """測試創建對話歷史"""
    history = GroupAIDialogueHistory(
        id="test-history-1",
        account_id="test_account_1",
        group_id=123456,
        message_id=789012,
        user_id=345678,
        message_text="測試消息",
        reply_text="測試回復",
        timestamp=datetime.utcnow(),
    )
    
    db.add(history)
    db.commit()
    db.refresh(history)
    
    assert history.id == "test-history-1"
    assert history.account_id == "test_account_1"
    assert history.group_id == 123456
    assert history.message_text == "測試消息"
    assert history.reply_text == "測試回復"


def test_query_dialogue_history_by_account(db: Session):
    """測試通過賬號查詢對話歷史"""
    # 創建多條對話歷史
    history1 = GroupAIDialogueHistory(
        id="test-history-2",
        account_id="test_account_2",
        group_id=123456,
        message_id=1,
        user_id=1,
        message_text="消息1",
        timestamp=datetime.utcnow(),
    )
    history2 = GroupAIDialogueHistory(
        id="test-history-3",
        account_id="test_account_2",
        group_id=123456,
        message_id=2,
        user_id=2,
        message_text="消息2",
        timestamp=datetime.utcnow(),
    )
    
    db.add(history1)
    db.add(history2)
    db.commit()
    
    # 查詢特定賬號的對話歷史
    histories = db.query(GroupAIDialogueHistory).filter(
        GroupAIDialogueHistory.account_id == "test_account_2"
    ).all()
    
    assert len(histories) == 2
    assert all(h.account_id == "test_account_2" for h in histories)


# ============ GroupAIRedpacketLog CRUD 測試 ============

def test_create_redpacket_log(db: Session):
    """測試創建紅包日誌"""
    log = GroupAIRedpacketLog(
        id="test-redpacket-1",
        account_id="test_account_1",
        group_id=123456,
        redpacket_id="redpacket_123",
        amount=10.5,
        success=True,
        timestamp=datetime.utcnow(),
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    assert log.id == "test-redpacket-1"
    assert log.account_id == "test_account_1"
    assert log.redpacket_id == "redpacket_123"
    assert log.amount == 10.5
    assert log.success is True


def test_query_redpacket_logs_by_account(db: Session):
    """測試通過賬號查詢紅包日誌"""
    # 創建多條紅包日誌
    log1 = GroupAIRedpacketLog(
        id="test-redpacket-2",
        account_id="test_account_3",
        group_id=123456,
        redpacket_id="redpacket_1",
        amount=10.0,
        success=True,
        timestamp=datetime.utcnow(),
    )
    log2 = GroupAIRedpacketLog(
        id="test-redpacket-3",
        account_id="test_account_3",
        group_id=123456,
        redpacket_id="redpacket_2",
        amount=20.0,
        success=False,
        timestamp=datetime.utcnow(),
    )
    
    db.add(log1)
    db.add(log2)
    db.commit()
    
    # 查詢特定賬號的紅包日誌
    logs = db.query(GroupAIRedpacketLog).filter(
        GroupAIRedpacketLog.account_id == "test_account_3"
    ).all()
    
    assert len(logs) == 2
    assert all(l.account_id == "test_account_3" for l in logs)
    
    # 查詢成功的紅包日誌
    success_logs = db.query(GroupAIRedpacketLog).filter(
        GroupAIRedpacketLog.account_id == "test_account_3",
        GroupAIRedpacketLog.success == True
    ).all()
    
    assert len(success_logs) == 1
    assert success_logs[0].redpacket_id == "redpacket_1"


# ============ GroupAIMetric CRUD 測試 ============

def test_create_metric(db: Session):
    """測試創建指標"""
    metric = GroupAIMetric(
        id="test-metric-1",
        account_id="test_account_1",
        metric_type="reply_count",
        metric_value=100.0,
        timestamp=datetime.utcnow(),
    )
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    
    assert metric.id == "test-metric-1"
    assert metric.account_id == "test_account_1"
    assert metric.metric_type == "reply_count"
    assert metric.metric_value == 100.0


def test_query_metrics_by_type(db: Session):
    """測試通過類型查詢指標"""
    # 先清理可能存在的測試數據，避免與其他測試衝突
    db.query(GroupAIMetric).filter(
        GroupAIMetric.id.in_(["test-metric-2", "test-metric-3", "test-metric-4"])
    ).delete(synchronize_session=False)
    db.commit()
    
    # 創建多個指標（使用唯一的ID）
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    metric1 = GroupAIMetric(
        id=f"test-metric-{unique_id}-1",
        account_id="test_account_4",
        metric_type="reply_count",
        metric_value=100.0,
        timestamp=datetime.utcnow(),
    )
    metric2 = GroupAIMetric(
        id=f"test-metric-{unique_id}-2",
        account_id="test_account_4",
        metric_type="message_count",
        metric_value=200.0,
        timestamp=datetime.utcnow(),
    )
    metric3 = GroupAIMetric(
        id=f"test-metric-{unique_id}-3",
        account_id="test_account_5",
        metric_type="reply_count",
        metric_value=150.0,
        timestamp=datetime.utcnow(),
    )
    
    db.add(metric1)
    db.add(metric2)
    db.add(metric3)
    db.commit()
    
    # 查詢特定類型的指標（只查詢剛剛創建的）
    reply_metrics = db.query(GroupAIMetric).filter(
        GroupAIMetric.metric_type == "reply_count",
        GroupAIMetric.id.like(f"test-metric-{unique_id}%")
    ).all()
    
    assert len(reply_metrics) == 2
    assert all(m.metric_type == "reply_count" for m in reply_metrics)
    
    # 查詢特定賬號和類型的指標
    account_metrics = db.query(GroupAIMetric).filter(
        GroupAIMetric.account_id == "test_account_4",
        GroupAIMetric.metric_type == "reply_count"
    ).all()
    
    assert len(account_metrics) == 1
    assert account_metrics[0].metric_value == 100.0

