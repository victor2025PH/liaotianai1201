"""
RoleAssigner 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock

from group_ai_service.role_assigner import (
    Role,
    RoleAssignment,
    AssignmentPlan,
    RoleExtractor,
    RoleAssigner
)
from group_ai_service.script_parser import Script, Scene, Trigger, Response


@pytest.fixture
def sample_script():
    """創建示例劇本"""
    return Script(
        script_id="test_script",
        version="1.0.0",
        description="測試劇本",
        scenes={
            "scene1": Scene(
                id="scene1",
                triggers=[Trigger(type="keyword", keywords=["觸發詞1"])],
                responses=[Response(template="回復1", metadata={"role": "role1"})]
            )
        },
        metadata={
            "roles": [
                {"id": "role1", "name": "角色1"},
                {"id": "role2", "name": "角色2"}
            ]
        }
    )


@pytest.fixture
def role_extractor():
    """創建 RoleExtractor 實例"""
    return RoleExtractor()


@pytest.fixture
def role_assigner():
    """創建 RoleAssigner 實例"""
    return RoleAssigner()


class TestRole:
    """Role 數據類測試"""
    
    def test_role_creation(self):
        """測試角色創建"""
        role = Role(
            role_id="role1",
            role_name="角色1"
        )
        
        assert role.role_id == "role1"
        assert role.role_name == "角色1"
        assert role.dialogue_count == 0
        assert role.dialogue_weight == 1.0
    
    def test_role_with_metadata(self):
        """測試帶元數據的角色創建"""
        metadata = {"source": "test"}
        role = Role(
            role_id="role1",
            role_name="角色1",
            metadata=metadata
        )
        
        assert role.metadata == metadata


class TestRoleAssignment:
    """RoleAssignment 數據類測試"""
    
    def test_role_assignment_creation(self):
        """測試角色分配創建"""
        assignment = RoleAssignment(
            role_id="role1",
            account_id="account1"
        )
        
        assert assignment.role_id == "role1"
        assert assignment.account_id == "account1"
        assert isinstance(assignment.assigned_dialogues, list)
        assert assignment.weight == 0.0


class TestAssignmentPlan:
    """AssignmentPlan 數據類測試"""
    
    def test_assignment_plan_creation(self):
        """測試分配方案創建"""
        plan = AssignmentPlan(
            script_id="test_script"
        )
        
        assert plan.script_id == "test_script"
        assert isinstance(plan.roles, dict)
        assert isinstance(plan.assignments, list)
        assert plan.total_roles == 0
        assert plan.total_accounts == 0
        assert plan.assignment_mode == "auto"


class TestRoleExtractor:
    """RoleExtractor 測試"""
    
    def test_extractor_initialization(self, role_extractor):
        """測試提取器初始化"""
        assert role_extractor is not None
    
    def test_extract_roles_from_script_metadata(self, role_extractor, sample_script):
        """測試從劇本 metadata 提取角色"""
        roles = role_extractor.extract_roles_from_script(sample_script)
        
        assert isinstance(roles, dict)
        assert "role1" in roles
        assert "role2" in roles
        assert roles["role1"].role_name == "角色1"
    
    def test_extract_roles_from_scene_metadata(self, role_extractor):
        """測試從場景 metadata 提取角色"""
        script = Script(
            script_id="test_script",
            version="1.0.0",
            scenes={
                "scene1": Scene(
                    id="scene1",
                    triggers=[Trigger(type="keyword", keywords=["觸發詞1"])],
                    responses=[Response(template="回復1")],
                    metadata={"role": "scene_role"}
                )
            }
        )
        
        roles = role_extractor.extract_roles_from_script(script)
        
        assert isinstance(roles, dict)
        assert "scene_role" in roles
    
    def test_generate_role_name_default(self, role_extractor):
        """測試生成角色名稱（默認）"""
        name = role_extractor._generate_role_name("default")
        assert name == "默認角色"
    
    def test_generate_role_name_with_number(self, role_extractor):
        """測試生成角色名稱（帶數字）"""
        name = role_extractor._generate_role_name("role_1")
        assert name == "角色1"
    
    def test_generate_role_name_pure_number(self, role_extractor):
        """測試生成角色名稱（純數字）"""
        name = role_extractor._generate_role_name("123")
        assert name == "角色123"


class TestRoleAssigner:
    """RoleAssigner 測試"""
    
    def test_assigner_initialization(self, role_assigner):
        """測試分配器初始化"""
        assert role_assigner is not None
    
    def test_create_assignment_plan_auto(self, role_assigner, sample_script):
        """測試創建分配方案（自動模式）"""
        accounts = ["account1", "account2"]
        
        plan = role_assigner.create_assignment_plan(
            script=sample_script,
            available_accounts=accounts
        )
        
        assert plan is not None
        assert plan.script_id == "test_script"
        assert plan.assignment_mode == "auto"
        assert len(plan.roles) > 0
    
    def test_create_assignment_plan_manual(self, role_assigner, sample_script):
        """測試創建分配方案（手動模式）"""
        accounts = ["account1", "account2"]
        manual_assignments = {"role1": "account1"}
        
        plan = role_assigner.create_assignment_plan(
            script=sample_script,
            available_accounts=accounts,
            mode="manual",
            manual_assignments=manual_assignments
        )
        
        assert plan is not None
        assert plan.assignment_mode == "manual"
    
    def test_auto_assign_equal_roles_accounts(self, role_assigner):
        """測試自動分配（角色數 = 賬號數）"""
        roles = {
            "role1": Role(role_id="role1", role_name="角色1"),
            "role2": Role(role_id="role2", role_name="角色2")
        }
        accounts = ["account1", "account2"]
        
        assignments = role_assigner._auto_assign(roles, accounts)
        
        assert len(assignments) == 2
        assert assignments[0].role_id == "role1"
        assert assignments[1].role_id == "role2"
    
    def test_auto_assign_more_roles(self, role_assigner):
        """測試自動分配（角色數 > 賬號數）"""
        roles = {
            "role1": Role(role_id="role1", role_name="角色1", dialogue_weight=1.0),
            "role2": Role(role_id="role2", role_name="角色2", dialogue_weight=2.0),
            "role3": Role(role_id="role3", role_name="角色3", dialogue_weight=1.0)
        }
        accounts = ["account1", "account2"]
        
        assignments = role_assigner._auto_assign(roles, accounts)
        
        assert len(assignments) == 3
        # 應該按負載均衡分配
        assert all(a.account_id in accounts for a in assignments)
    
    def test_auto_assign_more_accounts(self, role_assigner):
        """測試自動分配（角色數 < 賬號數）"""
        roles = {
            "role1": Role(role_id="role1", role_name="角色1")
        }
        accounts = ["account1", "account2", "account3"]
        
        assignments = role_assigner._auto_assign(roles, accounts)
        
        assert len(assignments) == 1
        assert assignments[0].role_id == "role1"
        assert assignments[0].account_id in accounts

