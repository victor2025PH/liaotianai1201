"""
角色分配管理器 - 自動分配劇本角色到帳號
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from group_ai_service.script_parser import Script, Scene, Response

logger = logging.getLogger(__name__)


@dataclass
class Role:
    """角色定義"""
    role_id: str
    role_name: str
    dialogue_count: int = 0  # 台詞數量
    dialogue_weight: float = 1.0  # 台詞權重（用於負載均衡）
    metadata: Dict = field(default_factory=dict)


@dataclass
class RoleAssignment:
    """角色分配"""
    role_id: str
    account_id: str
    assigned_dialogues: List[str] = field(default_factory=list)  # 分配的台詞ID列表
    weight: float = 0.0  # 分配的負載權重


@dataclass
class AssignmentPlan:
    """分配方案"""
    script_id: str
    roles: Dict[str, Role] = field(default_factory=dict)
    assignments: List[RoleAssignment] = field(default_factory=list)
    total_roles: int = 0
    total_accounts: int = 0
    assignment_mode: str = "auto"  # auto 或 manual
    metadata: Dict = field(default_factory=dict)


class RoleExtractor:
    """角色提取器 - 從劇本中提取角色信息"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_roles_from_script(self, script: Script) -> Dict[str, Role]:
        """從劇本中提取角色列表"""
        roles: Dict[str, Role] = {}
        
        # 方法1: 從 metadata 中讀取角色定義
        if "roles" in script.metadata:
            roles_data = script.metadata["roles"]
            if isinstance(roles_data, list):
                for role_data in roles_data:
                    if isinstance(role_data, dict):
                        role_id = role_data.get("id") or role_data.get("role_id")
                        # 優先使用metadata中定義的名稱，如果沒有則自動生成友好的名稱
                        role_name = role_data.get("name") or role_data.get("role_name")
                        if not role_name and role_id:
                            role_name = self._generate_role_name(role_id)
                        elif not role_name:
                            role_name = "未知角色"
                        if role_id:
                            roles[role_id] = Role(
                                role_id=role_id,
                                role_name=role_name,
                                metadata=role_data
                            )
        
        # 方法2: 從場景的 metadata 中提取角色
        for scene_id, scene in script.scenes.items():
            if "role" in scene.metadata:
                role_id = scene.metadata["role"]
                if role_id not in roles:
                    # 嘗試從場景metadata中獲取角色名稱
                    role_name = scene.metadata.get("role_name") or self._generate_role_name(role_id)
                    roles[role_id] = Role(
                        role_id=role_id,
                        role_name=role_name,
                        metadata={"source": "scene_metadata"}
                    )
            
            # 從回復的 metadata 中提取角色
            for response in scene.responses:
                if "role" in response.metadata:
                    role_id = response.metadata["role"]
                    if role_id not in roles:
                        # 嘗試從回復metadata中獲取角色名稱
                        role_name = response.metadata.get("role_name") or self._generate_role_name(role_id)
                        roles[role_id] = Role(
                            role_id=role_id,
                            role_name=role_name,
                            metadata={"source": "response_metadata"}
                        )
        
        # 方法3: 如果沒有找到角色，創建默認角色
        if not roles:
            roles["default"] = Role(
                role_id="default",
                role_name="默認角色",
                metadata={"source": "auto_generated"}
            )
        
        # 統計每個角色的台詞數量
        self._count_dialogues(script, roles)
        
        return roles
    
    def _generate_role_name(self, role_id: str) -> str:
        """根據角色ID生成友好的角色名稱"""
        # 如果role_id是"default"，返回"默認角色"
        if role_id == "default":
            return "默認角色"
        
        # 如果role_id包含數字，嘗試生成友好的名稱
        # 例如: "role_1" -> "角色1", "actor_2" -> "演員2"
        import re
        # 匹配 role_數字 或 actor_數字 等模式
        match = re.match(r'^(role|actor|character|角色|演員|人物)_?(\d+)$', role_id, re.IGNORECASE)
        if match:
            number = match.group(2)
            # 根據前綴選擇合適的中文名稱
            prefix = match.group(1).lower()
            if prefix in ['role', '角色']:
                return f"角色{number}"
            elif prefix in ['actor', '演員']:
                return f"演員{number}"
            elif prefix in ['character', '人物']:
                return f"人物{number}"
            else:
                return f"角色{number}"
        
        # 如果role_id是純數字，返回"角色{數字}"
        if role_id.isdigit():
            return f"角色{role_id}"
        
        # 如果role_id包含下劃線或連字符，嘗試提取關鍵部分
        if '_' in role_id or '-' in role_id:
            parts = re.split(r'[_-]', role_id)
            # 取最後一個部分作為名稱
            last_part = parts[-1]
            if last_part.isdigit():
                return f"角色{last_part}"
            # 如果最後一部分是"default"，返回"默認角色"
            if last_part.lower() == 'default':
                return "默認角色"
        
        # 默認情況下，將role_id的首字母大寫並返回
        # 如果role_id是英文，嘗試轉換為中文
        role_name_mapping = {
            "default": "默認角色",
            "main": "主要角色",
            "support": "配角",
            "npc": "NPC角色",
        }
        if role_id.lower() in role_name_mapping:
            return role_name_mapping[role_id.lower()]
        
        # 如果都不匹配，返回格式化的role_id（首字母大寫）
        return role_id.replace('_', ' ').title()
    
    def _count_dialogues(self, script: Script, roles: Dict[str, Role]):
        """統計每個角色的台詞數量"""
        for scene_id, scene in script.scenes.items():
            for response in scene.responses:
                # 確定這個回復屬於哪個角色
                role_id = response.metadata.get("role") or scene.metadata.get("role") or "default"
                
                if role_id in roles:
                    roles[role_id].dialogue_count += 1
                    # 計算權重（AI生成的回復權重更高）
                    if response.ai_generate:
                        roles[role_id].dialogue_weight += 1.5
                    else:
                        roles[role_id].dialogue_weight += 1.0


class RoleAssigner:
    """角色分配器 - 自動或手動分配角色到帳號"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.extractor = RoleExtractor()
    
    def create_assignment_plan(
        self,
        script: Script,
        available_accounts: List[str],
        mode: str = "auto",
        manual_assignments: Optional[Dict[str, str]] = None
    ) -> AssignmentPlan:
        """創建分配方案"""
        # 1. 提取角色
        roles = self.extractor.extract_roles_from_script(script)
        
        # 2. 創建分配方案
        plan = AssignmentPlan(
            script_id=script.script_id,
            roles=roles,
            total_roles=len(roles),
            total_accounts=len(available_accounts),
            assignment_mode=mode
        )
        
        # 3. 執行分配
        if mode == "auto":
            assignments = self._auto_assign(roles, available_accounts)
        else:
            assignments = self._manual_assign(roles, available_accounts, manual_assignments or {})
        
        plan.assignments = assignments
        
        return plan
    
    def _auto_assign(
        self,
        roles: Dict[str, Role],
        accounts: List[str]
    ) -> List[RoleAssignment]:
        """自動分配算法"""
        assignments: List[RoleAssignment] = []
        role_list = list(roles.values())
        account_list = accounts.copy()
        
        # 按台詞權重排序角色（權重大的優先分配）
        role_list.sort(key=lambda r: r.dialogue_weight, reverse=True)
        
        if len(role_list) <= len(account_list):
            # 情況1: 角色數 ≤ 帳號數，一對一分配
            for i, role in enumerate(role_list):
                if i < len(account_list):
                    assignment = RoleAssignment(
                        role_id=role.role_id,
                        account_id=account_list[i],
                        weight=role.dialogue_weight
                    )
                    assignments.append(assignment)
                    self.logger.info(f"自動分配: 角色 {role.role_name} ({role.role_id}) -> 帳號 {account_list[i]}")
        else:
            # 情況2: 角色數 > 帳號數，按負載均衡分配
            # 計算總權重
            total_weight = sum(r.dialogue_weight for r in role_list)
            weight_per_account = total_weight / len(account_list)
            
            # 為每個帳號分配角色
            current_account_index = 0
            current_account_weight = 0.0
            
            for role in role_list:
                # 如果當前帳號負載已滿，切換到下一個帳號
                if current_account_weight >= weight_per_account and current_account_index < len(account_list) - 1:
                    current_account_index += 1
                    current_account_weight = 0.0
                
                account_id = account_list[current_account_index]
                assignment = RoleAssignment(
                    role_id=role.role_id,
                    account_id=account_id,
                    weight=role.dialogue_weight
                )
                assignments.append(assignment)
                current_account_weight += role.dialogue_weight
                
                self.logger.info(
                    f"自動分配: 角色 {role.role_name} ({role.role_id}) -> 帳號 {account_id} "
                    f"(負載: {current_account_weight:.2f}/{weight_per_account:.2f})"
                )
        
        return assignments
    
    def _manual_assign(
        self,
        roles: Dict[str, Role],
        accounts: List[str],
        manual_assignments: Dict[str, str]
    ) -> List[RoleAssignment]:
        """手動分配"""
        assignments: List[RoleAssignment] = []
        
        for role_id, account_id in manual_assignments.items():
            if role_id in roles and account_id in accounts:
                role = roles[role_id]
                assignment = RoleAssignment(
                    role_id=role_id,
                    account_id=account_id,
                    weight=role.dialogue_weight
                )
                assignments.append(assignment)
                self.logger.info(f"手動分配: 角色 {role.role_name} ({role_id}) -> 帳號 {account_id}")
            else:
                self.logger.warning(f"手動分配失敗: 角色 {role_id} 或帳號 {account_id} 不存在")
        
        # 為未分配的角色使用自動分配
        assigned_role_ids = set(manual_assignments.keys())
        unassigned_roles = {r_id: r for r_id, r in roles.items() if r_id not in assigned_role_ids}
        unassigned_accounts = [acc for acc in accounts if acc not in manual_assignments.values()]
        
        if unassigned_roles and unassigned_accounts:
            auto_assignments = self._auto_assign(unassigned_roles, unassigned_accounts)
            assignments.extend(auto_assignments)
        
        return assignments
    
    def validate_assignment(self, plan: AssignmentPlan) -> Tuple[bool, List[str]]:
        """驗證分配方案"""
        errors = []
        
        # 檢查是否有角色未分配
        assigned_role_ids = {a.role_id for a in plan.assignments}
        all_role_ids = set(plan.roles.keys())
        unassigned_roles = all_role_ids - assigned_role_ids
        
        if unassigned_roles:
            errors.append(f"以下角色未分配: {', '.join(unassigned_roles)}")
        
        # 檢查是否有帳號被重複分配過多角色（負載不均衡）
        account_loads: Dict[str, float] = defaultdict(float)
        for assignment in plan.assignments:
            account_loads[assignment.account_id] += assignment.weight
        
        if account_loads:
            max_load = max(account_loads.values())
            min_load = min(account_loads.values())
            load_imbalance = max_load - min_load
            
            if load_imbalance > max_load * 0.5:  # 負載差異超過50%
                errors.append(
                    f"負載不均衡: 最大負載 {max_load:.2f}, 最小負載 {min_load:.2f}, "
                    f"差異 {load_imbalance:.2f}"
                )
        
        return len(errors) == 0, errors
    
    def get_assignment_summary(self, plan: AssignmentPlan) -> Dict:
        """獲取分配方案摘要"""
        account_loads: Dict[str, Dict] = defaultdict(lambda: {"roles": [], "total_weight": 0.0})
        
        for assignment in plan.assignments:
            role = plan.roles.get(assignment.role_id)
            account_loads[assignment.account_id]["roles"].append({
                "role_id": assignment.role_id,
                "role_name": role.role_name if role else assignment.role_id,
                "weight": assignment.weight
            })
            account_loads[assignment.account_id]["total_weight"] += assignment.weight
        
        return {
            "script_id": plan.script_id,
            "total_roles": plan.total_roles,
            "total_accounts": plan.total_accounts,
            "assignment_mode": plan.assignment_mode,
            "account_assignments": dict(account_loads),
            "role_statistics": {
                role_id: {
                    "name": role.role_name,
                    "dialogue_count": role.dialogue_count,
                    "weight": role.dialogue_weight
                }
                for role_id, role in plan.roles.items()
            }
        }

