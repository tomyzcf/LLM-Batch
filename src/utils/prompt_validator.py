import json
import re
from typing import Dict, Any, Optional
from .logger import Logger

class PromptValidator:
    """提示词验证器"""
    
    @staticmethod
    def validate_prompt(content: str) -> tuple[bool, Optional[str]]:
        """
        验证提示词格式，只检查输出格式部分
        
        Args:
            content: 提示词内容
            
        Returns:
            (bool, str): (是否有效, 错误信息)
        """
        try:
            # 提取输出格式部分
            output_format_match = re.search(r'\[输出格式\](.*?)$', content, re.DOTALL)
            if not output_format_match:
                return False, '未找到[输出格式]部分，请检查提示词格式'
                
            # 验证JSON格式
            output_format = output_format_match.group(1).strip()
            try:
                json_obj = json.loads(output_format)
            except json.JSONDecodeError:
                return False, '输出格式JSON语法错误，请检查格式'
            
            # 验证字段类型说明
            for field, value in json_obj.items():
                if not isinstance(value, str):
                    return False, f'字段 "{field}" 的类型说明必须是字符串'
                if value.lower() not in ['string', 'number']:
                    return False, f'字段 "{field}" 的类型必须是 "string" 或 "number"'
                    
            return True, None
            
        except Exception as e:
            return False, f'验证提示词时出错: {str(e)}'
    
    @staticmethod
    def validate_output(output: Dict[str, Any], template: Dict[str, str]) -> tuple[bool, Optional[str]]:
        """
        验证输出是否符合模板要求
        
        Args:
            output: 实际输出
            template: 输出模板
            
        Returns:
            (bool, str): (是否有效, 错误信息)
        """
        try:
            # 检查必需字段
            missing_fields = set(template.keys()) - set(output.keys())
            if missing_fields:
                return False, f'输出缺少必需的字段: {", ".join(missing_fields)}'
            
            # 检查字段类型
            for field, value in output.items():
                if field not in template:
                    continue  # 允许额外字段
                    
                expected_type = template[field].lower()
                if expected_type == 'string':
                    if not isinstance(value, str):
                        return False, f'字段 "{field}" 必须是字符串类型'
                elif expected_type == 'number':
                    if not isinstance(value, (int, float)):
                        return False, f'字段 "{field}" 必须是数字类型'
                        
            return True, None
            
        except Exception as e:
            return False, f'验证输出时出错: {str(e)}' 