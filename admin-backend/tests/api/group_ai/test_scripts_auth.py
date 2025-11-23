"""
测试 group-ai scripts 接口的认证功能
确保认证逻辑正确，防止 401 问题回归
"""
import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.core.security import create_access_token


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """创建数据库会话"""
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """创建测试用户"""
    from app.crud.user import get_user_by_email
    from app.models.user import User
    from app.core.security import get_password_hash
    
    # 检查用户是否已存在
    existing_user = get_user_by_email(db_session, email="test@example.com")
    if existing_user:
        return existing_user
    
    # 创建新用户
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """生成认证 token"""
    return create_access_token(data={"sub": test_user.email})


class TestScriptsAuth:
    """测试 scripts 接口的认证"""
    
    def test_get_scripts_without_auth(self, client: TestClient):
        """测试不带 Authorization 头时返回 401"""
        response = client.get("/api/v1/group-ai/scripts")
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_get_scripts_with_valid_token(self, client: TestClient, auth_token: str):
        """测试带合法 token 时返回 200"""
        response = client.get(
            "/api/v1/group-ai/scripts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_post_scripts_without_auth(self, client: TestClient):
        """测试不带 Authorization 头时返回 401"""
        script_data = {
            "script_id": "test-script-001",
            "name": "Test Script",
            "version": "1.0",
            "description": "Test description",
            "yaml_content": "script_id: test-script-001\nversion: '1.0'\nscenes: []"
        }
        response = client.post("/api/v1/group-ai/scripts", json=script_data)
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_post_scripts_with_valid_token(self, client: TestClient, auth_token: str):
        """测试带合法 token 和最小合法请求体时返回 201"""
        script_data = {
            "script_id": f"test-script-{int(time.time())}",
            "name": "Test Script",
            "version": "1.0",
            "description": "Test description",
            "yaml_content": "script_id: test\nversion: '1.0'\nscenes: []"
        }
        response = client.post(
            "/api/v1/group-ai/scripts",
            json=script_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 201]
        assert "script_id" in response.json()
    
    def test_post_scripts_with_invalid_token(self, client: TestClient):
        """测试带无效 token 时返回 401"""
        script_data = {
            "script_id": "test-script-002",
            "name": "Test Script",
            "version": "1.0",
            "description": "Test description",
            "yaml_content": "script_id: test\nversion: '1.0'\nscenes: []"
        }
        response = client.post(
            "/api/v1/group-ai/scripts",
            json=script_data,
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401

