"""
增强的智能格式转换器 - 支持多种文档格式和角色识别
"""
import logging
import yaml
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import openai
import os

logger = logging.getLogger(__name__)


class EnhancedFormatConverter:
    """增强的格式转换器，支持多种格式和角色识别"""
    
    # 支持的格式模式
    FORMAT_PATTERNS = {
        "old_yaml_list": {
            "indicators": ["step:", "actor:", "action:", "lines:"],
            "structure": "list"
        },
        "old_yaml_dict": {
            "indicators": ["steps:", "script_id:"],
            "structure": "dict"
        },
        "new_yaml": {
            "indicators": ["script_id:", "scenes:", "triggers:", "responses:"],
            "structure": "dict"
        },
        "plain_text": {
            "indicators": [],
            "structure": "text"
        },
        "markdown": {
            "indicators": ["#", "##", "```"],
            "structure": "text"
        }
    }
    
    # 角色识别关键词
    ROLE_KEYWORDS = {
        "管理员": ["管理员", "admin", "administrator", "管理"],
        "审核员": ["审核员", "reviewer", "审核", "审核人员"],
        "接待员": ["接待员", "receptionist", "接待", "客服"],
        "siya": ["siya", "Siya", "SIYA"],
        "huge": ["huge", "Huge", "HUGE"],
        "用户": ["用户", "user", "成员", "member"]
    }
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY 未设置，AI功能可能不可用")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.base_converter = None  # 延迟导入避免循环依赖
    
    def detect_format(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """
        检测文档格式
        
        Returns:
            (format_type, format_info)
        """
        content_lower = content.lower()
        
        # 检查新格式
        if "script_id:" in content and "scenes:" in content:
            return "new_yaml", {"structure": "dict", "needs_conversion": False}
        
        # 检查旧格式列表
        if any(indicator in content for indicator in ["step:", "actor:", "action:", "lines:"]):
            return "old_yaml_list", {"structure": "list", "needs_conversion": True}
        
        # 检查旧格式字典
        if "steps:" in content or ("script_id:" in content and "steps:" in content):
            return "old_yaml_dict", {"structure": "dict", "needs_conversion": True}
        
        # 检查Markdown
        if content.strip().startswith("#") or "```" in content:
            return "markdown", {"structure": "text", "needs_conversion": True}
        
        # 检查纯文本
        try:
            yaml.safe_load(content)
            return "yaml_unknown", {"structure": "unknown", "needs_conversion": True}
        except:
            # 检查是否是对话格式的纯文本
            if self._is_dialogue_text(content):
                return "plain_text_dialogue", {"structure": "text", "needs_conversion": True}
            return "plain_text", {"structure": "text", "needs_conversion": True}
    
    def _is_dialogue_text(self, content: str) -> bool:
        """检查是否是对话格式的文本"""
        import re
        lines = content.split('\n')[:10]  # 检查前10行
        dialogue_patterns = [
            re.compile(r'^[^:：]+[:：]\s*.+$'),  # 角色: 内容
            re.compile(r'^\[[^\]]+\]\s*.+$'),   # [角色] 内容
            re.compile(r'^【[^】]+】\s*.+$'),   # 【角色】内容
        ]
        
        dialogue_count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            for pattern in dialogue_patterns:
                if pattern.match(line):
                    dialogue_count += 1
                    break
        
        # 如果前10行中有至少3行匹配对话模式，认为是对话文本
        return dialogue_count >= 3
    
    def extract_roles(self, content: str) -> List[Dict[str, Any]]:
        """
        从内容中提取角色信息
        
        Returns:
            List of role info dicts with keys: name, occurrences, context
        """
        roles_found = []
        content_lines = content.split('\n')
        
        for role_name, keywords in self.ROLE_KEYWORDS.items():
            occurrences = []
            for line_num, line in enumerate(content_lines, 1):
                for keyword in keywords:
                    if keyword in line:
                        # 提取上下文
                        context_start = max(0, line_num - 2)
                        context_end = min(len(content_lines), line_num + 2)
                        context = '\n'.join(content_lines[context_start:context_end])
                        
                        occurrences.append({
                            "line": line_num,
                            "keyword": keyword,
                            "context": context
                        })
                        break
            
            if occurrences:
                roles_found.append({
                    "name": role_name,
                    "keywords": keywords,
                    "occurrences": occurrences,
                    "count": len(occurrences)
                })
        
        return roles_found
    
    def match_roles_to_actors(self, roles: List[Dict[str, Any]], actors: List[str]) -> Dict[str, str]:
        """
        将识别的角色匹配到actor字段
        
        Returns:
            Mapping of role_name -> actor_name
        """
        role_mapping = {}
        
        for role in roles:
            role_name = role["name"]
            # 尝试匹配到已知的actor
            for actor in actors:
                if role_name.lower() == actor.lower():
                    role_mapping[role_name] = actor
                    break
                # 检查关键词匹配
                for keyword in role["keywords"]:
                    if keyword.lower() in actor.lower() or actor.lower() in keyword.lower():
                        role_mapping[role_name] = actor
                        break
        
        return role_mapping
    
    def convert_with_enhanced_detection(
        self,
        content: str,
        script_id: Optional[str] = None,
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用增强检测进行转换
        """
        # 检测格式
        format_type, format_info = self.detect_format(content)
        
        logger.info(f"检测到格式类型: {format_type}, 信息: {format_info}")
        
        # 提取角色信息
        roles = self.extract_roles(content)
        logger.info(f"识别到 {len(roles)} 个角色: {[r['name'] for r in roles]}")
        
        # 如果已经是新格式，直接返回
        if not format_info.get("needs_conversion", True):
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict) and "script_id" in data and "scenes" in data:
                    # 确保类型正确
                    warnings = []
                    if data.get("script_id"):
                        if not isinstance(data["script_id"], str):
                            warnings.append("script_id 类型已转换为字符串")
                        data["script_id"] = str(data["script_id"])
                    if data.get("version"):
                        if not isinstance(data["version"], str):
                            warnings.append("version 类型已转换为字符串")
                        data["version"] = str(data["version"])
                    
                    # 添加角色信息
                    if roles:
                        if "metadata" not in data:
                            data["metadata"] = {}
                        data["metadata"]["detected_roles"] = [
                            {
                                "name": r["name"],
                                "count": r["count"]
                            }
                            for r in roles
                        ]
                        warnings.append(f"識別到 {len(roles)} 個角色: {', '.join([r['name'] for r in roles])}")
                    
                    return data, warnings
            except Exception as e:
                logger.warning(f"解析新格式失败: {e}")
        
        # 如果是纯文本对话格式，使用文本解析器
        if format_type == "plain_text_dialogue":
            try:
                from group_ai_service.text_parser import TextParser
                text_parser = TextParser()
                
                # 创建临时文件进行解析
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(content)
                    temp_path = f.name
                
                try:
                    converted = text_parser.parse_text_file(
                        temp_path,
                        script_id=script_id,
                        script_name=script_name
                    )
                finally:
                    import os
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                
                # 添加角色信息到元数据
                warnings = []
                if roles:
                    if "metadata" not in converted:
                        converted["metadata"] = {}
                    converted["metadata"]["detected_roles"] = [
                        {
                            "name": r["name"],
                            "count": r["count"]
                        }
                        for r in roles
                    ]
                    warnings.append(f"識別到 {len(roles)} 個角色: {', '.join([r['name'] for r in roles])}")
                
                return converted, warnings
            except Exception as e:
                logger.warning(f"文本解析失败，尝试使用AI转换: {e}")
                # 降级到AI转换
        
        # 使用基础转换器
        if self.base_converter is None:
            from group_ai_service.format_converter import FormatConverter
            self.base_converter = FormatConverter()
        
        # 转换
        try:
            converted = self.base_converter.convert_old_format_to_new(
                old_yaml_content=content,
                script_id=script_id,
                script_name=script_name
            )
            
            # 添加角色信息到元数据
            warnings = []
            if roles:
                if "metadata" not in converted:
                    converted["metadata"] = {}
                converted["metadata"]["detected_roles"] = [
                    {
                        "name": r["name"],
                        "count": r["count"]
                    }
                    for r in roles
                ]
                warnings.append(f"識別到 {len(roles)} 個角色: {', '.join([r['name'] for r in roles])}")
            
            return converted, warnings
            
        except Exception as e:
            logger.error(f"转换失败: {e}", exc_info=True)
            suggestions = self.get_conversion_suggestions(e)
            error_msg = f"格式转换失败: {str(e)}"
            if suggestions:
                error_msg += "\n\n建议：\n" + "\n".join(f"  • {s}" for s in suggestions)
            raise ValueError(error_msg)
    
    def validate_and_fix(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        验证并修复转换结果
        
        Returns:
            (fixed_data, warnings)
        """
        warnings = []
        
        # 确保script_id是字符串
        if "script_id" in data:
            if not isinstance(data["script_id"], str):
                warnings.append(f"script_id 类型错误 ({type(data['script_id']).__name__})，已转换为字符串")
                data["script_id"] = str(data["script_id"])
        
        # 确保version是字符串
        if "version" in data:
            if not isinstance(data["version"], str):
                warnings.append(f"version 类型错误 ({type(data['version']).__name__})，已转换为字符串")
                data["version"] = str(data["version"])
        
        # 验证scenes
        if "scenes" not in data:
            warnings.append("缺少 scenes 字段，已添加空列表")
            data["scenes"] = []
        elif not isinstance(data["scenes"], list):
            warnings.append("scenes 不是列表类型，已转换")
            if isinstance(data["scenes"], dict):
                data["scenes"] = [data["scenes"]]
            else:
                data["scenes"] = []
        
        # 验证每个场景
        for idx, scene in enumerate(data["scenes"]):
            if not isinstance(scene, dict):
                warnings.append(f"场景 {idx} 不是字典类型，已跳过")
                continue
            
            # 确保有id
            if "id" not in scene:
                scene["id"] = f"scene_{idx + 1}"
                warnings.append(f"场景 {idx} 缺少 id，已自动生成: {scene['id']}")
            
            # 确保有triggers（必填，且必须包含type）
            if "triggers" not in scene:
                scene["triggers"] = [{"type": "message"}]
                warnings.append(f"场景 {idx} 缺少 triggers，已添加默认值")
            elif not isinstance(scene["triggers"], list):
                scene["triggers"] = [{"type": "message"}]
                warnings.append(f"场景 {idx} triggers 不是列表，已修复")
            elif len(scene["triggers"]) == 0:
                # triggers列表为空，添加默认trigger
                scene["triggers"] = [{"type": "message"}]
                warnings.append(f"场景 {idx} triggers 列表为空，已添加默认trigger")
            else:
                # 验证每个trigger都有type字段
                valid_triggers = []
                for trigger_idx, trigger in enumerate(scene["triggers"]):
                    if not isinstance(trigger, dict):
                        warnings.append(f"场景 {idx} 的trigger {trigger_idx} 不是字典类型，已跳过")
                        continue
                    if "type" not in trigger:
                        # 自动添加type字段
                        trigger["type"] = "message"
                        warnings.append(f"场景 {idx} 的trigger {trigger_idx} 缺少 type 字段，已添加默认值")
                    valid_triggers.append(trigger)
                scene["triggers"] = valid_triggers
                if len(scene["triggers"]) == 0:
                    # 如果所有trigger都无效，添加默认trigger
                    scene["triggers"] = [{"type": "message"}]
                    warnings.append(f"场景 {idx} 所有trigger无效，已添加默认trigger")
            
            # 确保有responses（必填，至少一个）
            if "responses" not in scene:
                scene["responses"] = []
                warnings.append(f"场景 {idx} 缺少 responses，已添加空列表")
            elif not isinstance(scene["responses"], list):
                if isinstance(scene["responses"], dict):
                    scene["responses"] = [scene["responses"]]
                else:
                    scene["responses"] = []
                warnings.append(f"场景 {idx} responses 不是列表，已修复")
            
            # 验证每个response都有template字段
            if len(scene["responses"]) > 0:
                valid_responses = []
                for response_idx, response in enumerate(scene["responses"]):
                    if not isinstance(response, dict):
                        warnings.append(f"场景 {idx} 的response {response_idx} 不是字典类型，已跳过")
                        continue
                    if "template" not in response:
                        # 尝试从其他字段提取或使用空字符串
                        if "text" in response:
                            response["template"] = response.pop("text")
                        elif "content" in response:
                            response["template"] = response.pop("content")
                        else:
                            response["template"] = ""
                            warnings.append(f"场景 {idx} 的response {response_idx} 缺少 template 字段，已添加空值")
                    valid_responses.append(response)
                scene["responses"] = valid_responses
        
        return data, warnings
    
    def get_conversion_suggestions(self, error: Exception) -> List[str]:
        """
        根据错误提供转换建议
        """
        suggestions = []
        error_msg = str(error).lower()
        
        if "yaml" in error_msg or "parse" in error_msg:
            suggestions.append("检查YAML格式是否正确，确保缩进使用空格而非Tab")
            suggestions.append("确保所有键值对格式正确（key: value）")
            suggestions.append("检查是否有未闭合的引号或括号")
        
        if "script_id" in error_msg:
            suggestions.append("确保YAML中包含 script_id 字段（新格式）或 step/actor 字段（旧格式）")
            suggestions.append("如果是旧格式，请先使用「智能转换」功能")
        
        if "scenes" in error_msg or "scene" in error_msg:
            suggestions.append("确保包含 scenes 字段（新格式）或 steps 字段（旧格式）")
            suggestions.append("检查场景结构是否正确")
        
        if "type" in error_msg or "validation" in error_msg:
            suggestions.append("检查字段类型是否正确（script_id 和 version 应为字符串）")
            suggestions.append("确保数值字段格式正确")
        
        if not suggestions:
            suggestions.append("请检查文档格式是否符合要求")
            suggestions.append("如果问题持续，请尝试使用「智能转换」功能")
        
        return suggestions

