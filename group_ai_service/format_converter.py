"""
智能格式转换器 - 使用AI将旧格式转换为新格式
"""
import logging
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import openai
import os

logger = logging.getLogger(__name__)


class FormatConverter:
    """格式转换器"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY 未设置，格式转换功能可能不可用")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    def convert_old_format_to_new(
        self, 
        old_yaml_content: str,
        script_id: Optional[str] = None,
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        将旧格式YAML或纯文本转换为新格式
        
        Args:
            old_yaml_content: 旧格式YAML内容或纯文本内容
            script_id: 剧本ID（如果未提供，将从内容中提取或生成）
            script_name: 剧本名称（可选）
        
        Returns:
            转换后的新格式字典
        """
        try:
            # 尝试解析为YAML
            old_data = None
            is_plain_text = False
            
            try:
                old_data = yaml.safe_load(old_yaml_content)
                # 如果解析结果为None或空，可能是纯文本
                if old_data is None:
                    is_plain_text = True
            except yaml.YAMLError:
                # YAML解析失败，可能是纯文本
                is_plain_text = True
            
            # 如果是纯文本，使用文本解析器
            if is_plain_text:
                try:
                    from group_ai_service.text_parser import TextParser
                    text_parser = TextParser()
                    
                    # 创建临时文件
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                        f.write(old_yaml_content)
                        temp_path = f.name
                    
                    try:
                        result = text_parser.parse_text_file(
                            temp_path,
                            script_id=script_id,
                            script_name=script_name
                        )
                        logger.info("纯文本解析成功")
                        return result
                    finally:
                        import os
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"文本解析失败，尝试使用AI转换: {e}")
                    # 降级到AI转换，将文本作为字符串传递
                    old_data = old_yaml_content
            
            # 如果已经是新格式，直接返回
            if isinstance(old_data, dict) and self._is_new_format(old_data):
                logger.info("内容已经是新格式，无需转换")
                return old_data
            
            # 使用AI进行转换
            if self.openai_api_key:
                try:
                    converted = self._convert_with_ai(old_data, script_id, script_name)
                    # 验证转换结果
                    if not converted.get("script_id"):
                        logger.warning("AI转换结果缺少script_id，使用规则转换")
                        converted = self._convert_with_rules(old_data, script_id, script_name)
                    return converted
                except Exception as e:
                    logger.warning(f"AI转换失败，使用规则转换: {e}")
                    # 降级到规则转换
                    return self._convert_with_rules(old_data, script_id, script_name)
            else:
                # 降级方案：使用规则转换
                return self._convert_with_rules(old_data, script_id, script_name)
        
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析失败: {e}")
        except Exception as e:
            raise ValueError(f"格式转换失败: {e}")
    
    def _is_new_format(self, data: Dict[str, Any]) -> bool:
        """检查是否是新格式"""
        return "script_id" in data and "scenes" in data
    
    def _convert_with_ai(
        self, 
        old_data: Dict[str, Any],
        script_id: Optional[str] = None,
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用AI进行转换"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            # 构建提示词
            prompt = self._build_conversion_prompt(old_data, script_id, script_name)
            
            # 调用OpenAI API
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个专业的YAML格式转换专家。你的任务是将旧格式的剧本YAML或纯文本对话转换为新格式。

旧格式特点：
- 使用 step, actor, action, lines 等字段
- 结构是步骤列表
- 或纯文本对话格式（如"角色: 内容"）

新格式要求：
- 必须有 script_id, version, description 字段
- scenes 是场景列表，每个场景必须包含：
  - id: 场景ID（必填）
  - triggers: 触发条件列表（必填，至少一个）
    - 每个trigger必须包含 type 字段（必填，如"message"）
  - responses: 回复模板列表（必填，至少一个）
    - 每个response必须包含 template 字段（必填）

重要：每个场景的triggers必须至少包含一个trigger，且每个trigger必须有type字段。如果无法确定触发条件，使用默认值：{"type": "message"}

请确保：
1. 保持原有语义和逻辑
2. 合理生成场景ID和触发条件
3. 将 lines 或对话内容转换为 responses 中的 template
4. 生成合适的描述和元数据
5. 输出必须是有效的YAML格式
6. 每个场景都必须有完整的triggers和responses结构"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # 解析响应
            result_text = response.choices[0].message.content.strip()
            
            # 提取YAML内容（可能包含markdown代码块）
            if "```yaml" in result_text:
                result_text = result_text.split("```yaml")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # 解析YAML
            new_data = yaml.safe_load(result_text)
            
            # 如果解析失败，尝试规则转换
            if not new_data or not isinstance(new_data, dict):
                logger.warning("AI转换结果解析失败，使用规则转换")
                return self._convert_with_rules(old_data, script_id, script_name)
            
            # 验证和优化
            new_data = self._validate_and_optimize(new_data, script_id, script_name)
            
            # 再次验证必要字段
            if not new_data.get("script_id") or not new_data.get("scenes"):
                logger.warning("AI转换结果缺少必要字段，使用规则转换")
                return self._convert_with_rules(old_data, script_id, script_name)
            
            logger.info("AI格式转换成功")
            return new_data
        
        except Exception as e:
            logger.error(f"AI转换失败: {e}，尝试使用规则转换")
            return self._convert_with_rules(old_data, script_id, script_name)
    
    def _build_conversion_prompt(
        self, 
        old_data: Any,  # 可能是dict、list或str
        script_id: Optional[str] = None,
        script_name: Optional[str] = None
    ) -> str:
        """构建转换提示词"""
        # 判断数据类型
        if isinstance(old_data, str):
            # 纯文本
            old_yaml = old_data
        else:
            # YAML数据
            old_yaml = yaml.dump(old_data, allow_unicode=True, default_flow_style=False)
        
        prompt = f"""请将以下旧格式的剧本YAML转换为新格式：

旧格式内容：
```yaml
{old_yaml}
```

"""
        
        if script_id:
            prompt += f"剧本ID: {script_id}\n"
        if script_name:
            prompt += f"剧本名称: {script_name}\n"
        
        prompt += """
请按照新格式要求进行转换，确保：
1. 生成完整的 script_id, version, description
2. 将步骤转换为场景（scenes）
3. 为每个场景生成合适的触发条件（triggers）
4. 将 lines 转换为 responses 中的 template
5. 保持原有的对话逻辑和顺序

只输出转换后的YAML内容，不要包含其他说明。"""
        
        return prompt
    
    def _convert_with_rules(
        self, 
        old_data: Any,  # 可能是dict、list或str
        script_id: Optional[str] = None,
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用规则进行转换（降级方案）"""
        # 如果 old_data 是字符串，无法使用规则转换，返回默认格式
        if isinstance(old_data, str):
            logger.warning("无法使用规则转换纯文本，返回默认格式")
            return {
                "script_id": script_id or "converted_script",
                "version": "1.0",
                "description": script_name or "转换自纯文本",
                "scenes": [
                    {
                        "id": "default",
                        "triggers": [{"type": "message"}],
                        "responses": [{"template": "已收到您的消息"}]
                    }
                ]
            }
        
        # 确保 old_data 是字典或列表
        if not isinstance(old_data, (dict, list)):
            logger.warning(f"无法识别的格式类型: {type(old_data)}")
            raise ValueError(f"格式转换失败: 无法识别的格式类型 {type(old_data)}")
        
        # 提取script_id，確保是字符串
        if not script_id:
            if isinstance(old_data, dict):
                script_id_value = old_data.get("script_id", "converted_script")
                script_id = str(script_id_value) if script_id_value is not None else "converted_script"
            else:
                script_id = "converted_script"
        else:
            script_id = str(script_id)
        
        # 提取version，確保是字符串
        if isinstance(old_data, dict):
            version_value = old_data.get("version", "1.0")
            version = str(version_value) if version_value is not None else "1.0"
            description = script_name or old_data.get("description", "转换自旧格式")
        else:
            version = "1.0"
            description = script_name or "转换自旧格式"
        
        # 构建新格式
        new_data = {
            "script_id": script_id,
            "version": version,
            "description": description,
            "scenes": []
        }
        
        # 转换步骤为场景
        if isinstance(old_data, list):
            # 如果是步骤列表（旧格式）
            for idx, step in enumerate(old_data):
                # 检查是否是旧格式步骤
                if not isinstance(step, dict):
                    continue
                    
                step_num = step.get("step", idx + 1)
                scene_id = f"scene_{step_num}"
                scene = {
                    "id": scene_id,
                    "triggers": [
                        {
                            "type": "message"
                        }
                    ],
                    "responses": []
                }
                
                # 转换lines为responses
                lines = step.get("lines", [])
                if isinstance(lines, list):
                    for line in lines:
                        if line:  # 跳过空行
                            scene["responses"].append({
                                "template": str(line).strip()
                            })
                elif isinstance(lines, str):
                    # 如果lines是字符串，直接添加
                    scene["responses"].append({
                        "template": lines.strip()
                    })
                
                # 只有当有responses时才添加场景
                if scene["responses"]:
                    new_data["scenes"].append(scene)
        elif isinstance(old_data, dict):
            # 检查是否是旧格式（包含steps字段）
            if "steps" in old_data:
                steps = old_data.get("steps", [])
                for idx, step in enumerate(steps):
                    if not isinstance(step, dict):
                        continue
                        
                    step_num = step.get("step", idx + 1)
                    scene_id = f"scene_{step_num}"
                    scene = {
                        "id": scene_id,
                        "triggers": [
                            {
                                "type": "message"
                            }
                        ],
                        "responses": []
                    }
                    
                    lines = step.get("lines", [])
                    if isinstance(lines, list):
                        for line in lines:
                            if line:
                                scene["responses"].append({
                                    "template": str(line).strip()
                                })
                    elif isinstance(lines, str):
                        scene["responses"].append({
                            "template": lines.strip()
                        })
                    
                    if scene["responses"]:
                        new_data["scenes"].append(scene)
            else:
                # 可能是其他格式，尝试直接使用
                # 检查是否是新格式（但缺少 scenes）
                if "script_id" in old_data:
                    # 可能是新格式但结构不完整，尝试修复
                    if "scenes" not in old_data:
                        old_data["scenes"] = []
                    return old_data
                else:
                    raise ValueError("格式转换失败: 无法识别的格式。请确保是旧格式（包含step和lines字段）或新格式（包含script_id和scenes字段）")
        
        # 验证转换结果
        if not new_data.get("scenes"):
            raise ValueError("转换后没有生成任何场景，请检查输入格式")
        
        return new_data
    
    def _validate_and_optimize(
        self, 
        data: Dict[str, Any],
        script_id: Optional[str] = None,
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """验证和优化转换结果"""
        if not isinstance(data, dict):
            raise ValueError("转换结果必须是字典格式")
        
        # 确保必要字段存在，並確保類型正確
        script_id_value = data.get("script_id") or script_id or "converted_script"
        data["script_id"] = str(script_id_value)  # 確保是字符串
        
        version_value = data.get("version") or "1.0"
        data["version"] = str(version_value)  # 確保是字符串
        
        if script_name and not data.get("description"):
            data["description"] = script_name
        elif not data.get("description"):
            data["description"] = "转换自旧格式"
        
        # 确保scenes是列表
        if "scenes" not in data:
            data["scenes"] = []
        elif not isinstance(data["scenes"], list):
            # 如果scenes不是列表，尝试转换
            if isinstance(data["scenes"], dict):
                # 如果是字典，转换为列表
                data["scenes"] = [data["scenes"]]
            else:
                data["scenes"] = []
        
        # 验证每个场景
        valid_scenes = []
        for idx, scene in enumerate(data["scenes"]):
            if not isinstance(scene, dict):
                continue
                
            if "id" not in scene:
                scene["id"] = f"scene_{idx + 1}"
            if "triggers" not in scene:
                scene["triggers"] = [{"type": "message"}]
            elif not isinstance(scene["triggers"], list):
                scene["triggers"] = [{"type": "message"}]
            if "responses" not in scene:
                scene["responses"] = []
            elif not isinstance(scene["responses"], list):
                # 如果responses不是列表，尝试转换
                if isinstance(scene["responses"], dict):
                    scene["responses"] = [scene["responses"]]
                else:
                    scene["responses"] = []
            
            valid_scenes.append(scene)
        
        data["scenes"] = valid_scenes
        
        # 最终验证
        if not data.get("script_id"):
            raise ValueError("转换结果缺少script_id字段")
        if not data.get("scenes"):
            raise ValueError("转换结果没有生成任何场景")
        
        return data
    
    def optimize_content(
        self, 
        yaml_content: str,
        optimize_type: str = "all"
    ) -> str:
        """
        优化YAML内容
        
        Args:
            yaml_content: YAML内容
            optimize_type: 优化类型 (all, grammar, expression, structure)
        
        Returns:
            优化后的YAML内容
        """
        if not self.openai_api_key:
            logger.warning("OpenAI API密钥未设置，跳过内容优化")
            return yaml_content
        
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            optimize_prompts = {
                "all": "请对以下YAML内容进行全面优化，包括语法纠正、表达润色和结构调整：",
                "grammar": "请纠正以下YAML内容中的语法错误：",
                "expression": "请优化以下YAML内容的表达方式，使其更自然流畅：",
                "structure": "请优化以下YAML内容的结构，使其更清晰合理："
            }
            
            prompt = f"""{optimize_prompts.get(optimize_type, optimize_prompts["all"])}

```yaml
{yaml_content}
```

请保持YAML格式不变，只优化内容。输出优化后的完整YAML。"""
            
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的YAML内容优化专家。你的任务是优化YAML内容，但保持格式和结构不变。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content.strip()
            
            # 提取YAML内容
            if "```yaml" in result:
                result = result.split("```yaml")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            
            return result
        
        except Exception as e:
            logger.error(f"内容优化失败: {e}")
            return yaml_content

