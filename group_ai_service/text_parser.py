"""
纯文本解析器 - 将纯文本对话转换为结构化数据
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class TextParser:
    """纯文本对话解析器"""
    
    # 对话模式识别
    DIALOGUE_PATTERNS = [
        # 中文模式：角色: 内容
        re.compile(r'^([^:：]+)[:：]\s*(.+)$'),
        # 英文模式：Role: Content
        re.compile(r'^([A-Za-z\s]+):\s*(.+)$'),
        # 带编号：1. 角色: 内容
        re.compile(r'^\d+[\.、]\s*([^:：]+)[:：]\s*(.+)$'),
        # 带标记：[角色] 内容
        re.compile(r'^\[([^\]]+)\]\s*(.+)$'),
        # 带标记：【角色】内容
        re.compile(r'^【([^】]+)】\s*(.+)$'),
    ]
    
    # 角色识别关键词（与enhanced_format_converter保持一致）
    ROLE_KEYWORDS = {
        "管理员": ["管理员", "admin", "administrator", "管理"],
        "审核员": ["审核员", "reviewer", "审核", "审核人员"],
        "接待员": ["接待员", "receptionist", "接待", "客服"],
        "siya": ["siya", "Siya", "SIYA"],
        "huge": ["huge", "Huge", "HUGE"],
        "用户": ["用户", "user", "成员", "member"]
    }
    
    def parse_text_to_dialogue(self, text: str) -> List[Dict[str, Any]]:
        """
        将纯文本解析为对话列表
        
        Returns:
            List of dialogue dicts with keys: role, content, line_number
        """
        dialogues = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # 尝试匹配对话模式
            matched = False
            for pattern in self.DIALOGUE_PATTERNS:
                match = pattern.match(line)
                if match:
                    role = match.group(1).strip()
                    content = match.group(2).strip()
                    
                    # 规范化角色名称
                    normalized_role = self._normalize_role(role)
                    
                    dialogues.append({
                        "role": normalized_role,
                        "content": content,
                        "line_number": line_num,
                        "original_role": role
                    })
                    matched = True
                    break
            
            # 如果没有匹配到模式，可能是连续对话内容
            if not matched and dialogues:
                # 追加到上一个对话的内容
                last_dialogue = dialogues[-1]
                last_dialogue["content"] += "\n" + line
            elif not matched:
                # 无法识别的行，作为独立对话
                dialogues.append({
                    "role": "未知",
                    "content": line,
                    "line_number": line_num,
                    "original_role": ""
                })
        
        return dialogues
    
    def _normalize_role(self, role: str) -> str:
        """规范化角色名称"""
        role_lower = role.lower()
        
        for normalized_role, keywords in self.ROLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in role_lower or role_lower in keyword.lower():
                    return normalized_role
        
        return role
    
    def convert_dialogues_to_scenes(
        self,
        dialogues: List[Dict[str, Any]],
        script_id: Optional[str] = None,
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        将对话列表转换为场景结构
        
        Returns:
            新格式的剧本字典
        """
        script_id = script_id or "converted_script"
        
        # 按角色分组对话
        scenes = []
        current_scene = None
        current_role = None
        
        for dialogue in dialogues:
            role = dialogue["role"]
            content = dialogue["content"]
            
            # 如果角色改变，创建新场景
            if role != current_role or current_scene is None:
                if current_scene and current_scene["responses"]:
                    scenes.append(current_scene)
                
                scene_id = f"scene_{len(scenes) + 1}"
                current_scene = {
                    "id": scene_id,
                    "triggers": [
                        {
                            "type": "message"
                        }
                    ],
                    "responses": []
                }
                current_role = role
            
            # 添加响应
            if content:
                current_scene["responses"].append({
                    "template": content
                })
        
        # 添加最后一个场景
        if current_scene and current_scene["responses"]:
            scenes.append(current_scene)
        
        # 构建完整结构
        result = {
            "script_id": str(script_id),
            "version": "1.0",
            "description": script_name or "转换自纯文本",
            "scenes": scenes
        }
        
        # 添加元数据
        roles_found = {}
        for dialogue in dialogues:
            role = dialogue["role"]
            roles_found[role] = roles_found.get(role, 0) + 1
        
        if roles_found:
            result["metadata"] = {
                "detected_roles": [
                    {"name": role, "count": count}
                    for role, count in roles_found.items()
                ]
            }
        
        return result
    
    def detect_encoding(self, file_path: str) -> str:
        """
        检测文件编码
        
        Returns:
            编码名称（如 'utf-8', 'gbk'）
        """
        encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        # 默认返回utf-8
        return 'utf-8'
    
    def parse_text_file(
        self,
        file_path: str,
        script_id: Optional[str] = None,
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        解析文本文件并转换为剧本格式
        
        Returns:
            新格式的剧本字典
        """
        # 检测编码
        encoding = self.detect_encoding(file_path)
        logger.info(f"检测到文件编码: {encoding}")
        
        # 读取文件
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"无法读取文件: {str(e)}")
        
        # 清理内容
        content = self._clean_content(content)
        
        # 解析对话
        dialogues = self.parse_text_to_dialogue(content)
        
        if not dialogues:
            raise ValueError("无法从文本中提取对话内容，请确保文本包含对话格式（如'角色: 内容'）")
        
        # 转换为场景
        result = self.convert_dialogues_to_scenes(dialogues, script_id, script_name)
        
        logger.info(f"从文本文件解析出 {len(dialogues)} 条对话，生成 {len(result['scenes'])} 个场景")
        
        return result
    
    def _clean_content(self, content: str) -> str:
        """清理文本内容"""
        # 移除BOM标记
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # 规范化换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除多余空行（保留单个空行）
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            if not (is_empty and prev_empty):
                cleaned_lines.append(line)
            prev_empty = is_empty
        
        return '\n'.join(cleaned_lines)

