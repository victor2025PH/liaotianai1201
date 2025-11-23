"""
YAML验证和修复工具 - 在解析前验证和修复YAML内容
"""
import yaml
import logging
from typing import Dict, Any, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


class YAMLValidator:
    """YAML内容验证和修复工具"""
    
    @staticmethod
    def validate_and_fix_yaml_file(file_path: str) -> Tuple[str, List[str]]:
        """
        验证和修复YAML文件
        
        Args:
            file_path: YAML文件路径
        
        Returns:
            (fixed_yaml_content, warnings)
        """
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析YAML
            data = yaml.safe_load(content)
            if not data or not isinstance(data, dict):
                return content, ["YAML内容为空或格式不正确"]
            
            # 使用增强转换器修复
            from group_ai_service.enhanced_format_converter import EnhancedFormatConverter
            enhanced_converter = EnhancedFormatConverter()
            fixed_data, warnings = enhanced_converter.validate_and_fix(data)
            
            # 转换为YAML字符串
            fixed_content = yaml.dump(fixed_data, allow_unicode=True, default_flow_style=False)
            
            return fixed_content, warnings
            
        except Exception as e:
            logger.error(f"YAML验证和修复失败: {e}", exc_info=True)
            return content, [f"验证失败: {str(e)}"]
    
    @staticmethod
    def validate_and_fix_yaml_content(yaml_content: str) -> Tuple[str, List[str]]:
        """
        验证和修复YAML内容字符串
        
        Args:
            yaml_content: YAML内容字符串
        
        Returns:
            (fixed_yaml_content, warnings)
        """
        try:
            # 解析YAML
            data = yaml.safe_load(yaml_content)
            if not data or not isinstance(data, dict):
                return yaml_content, ["YAML内容为空或格式不正确"]
            
            # 使用增强转换器修复
            from group_ai_service.enhanced_format_converter import EnhancedFormatConverter
            enhanced_converter = EnhancedFormatConverter()
            fixed_data, warnings = enhanced_converter.validate_and_fix(data)
            
            # 转换为YAML字符串
            fixed_content = yaml.dump(fixed_data, allow_unicode=True, default_flow_style=False)
            
            return fixed_content, warnings
            
        except Exception as e:
            logger.error(f"YAML验证和修复失败: {e}", exc_info=True)
            return yaml_content, [f"验证失败: {str(e)}"]

