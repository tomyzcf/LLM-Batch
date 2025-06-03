import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union
from .logger import Logger

class PromptParser:
    """提示词解析器 - 支持JSON和TXT格式"""
    
    @staticmethod
    def parse_prompt_file(prompt_file: Union[str, Path]) -> Dict[str, str]:
        """
        解析提示词文件，支持JSON和TXT格式
        
        Args:
            prompt_file: 提示词文件路径
            
        Returns:
            Dict[str, str]: 包含system, task, output等字段的字典
        """
        prompt_file = Path(prompt_file)
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"提示词文件不存在: {prompt_file}")
        
        # 根据文件扩展名选择解析方法
        if prompt_file.suffix.lower() == '.json':
            return PromptParser._parse_json_format(prompt_file)
        else:
            # 默认使用TXT格式解析
            return PromptParser._parse_txt_format(prompt_file)
    
    @staticmethod
    def _parse_json_format(prompt_file: Path) -> Dict[str, str]:
        """解析JSON格式的提示词文件"""
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证必需字段
            required_fields = ['system', 'task', 'output']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"JSON提示词文件缺少必需字段: {field}")
            
            # 构建完整的提示词内容
            result = {
                'system': data['system'],
                'task': data['task'],
                'output': json.dumps(data['output'], ensure_ascii=False, indent=2) if isinstance(data['output'], dict) else str(data['output'])
            }
            
            # 处理可选字段
            if 'variables' in data and data['variables']:
                # 在system和task中进行变量替换
                for key, value in data['variables'].items():
                    result['system'] = result['system'].replace(f"{{{key}}}", str(value))
                    result['task'] = result['task'].replace(f"{{{key}}}", str(value))
            
            # 如果有examples字段，添加到task中
            if 'examples' in data and data['examples']:
                examples_text = "\n\n示例：\n"
                for i, example in enumerate(data['examples'], 1):
                    examples_text += f"{i}. {example}\n"
                result['task'] += examples_text
            
            Logger.info(f"成功解析JSON格式提示词文件: {prompt_file}")
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON格式错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"解析JSON提示词文件失败: {str(e)}")
    
    @staticmethod
    def _parse_txt_format(prompt_file: Path) -> Dict[str, str]:
        """解析传统TXT格式的提示词文件"""
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析分节格式 [System], [Task], [Output Format]
            sections = {}
            
            # 匹配不同的节名称格式
            section_patterns = [
                (r'\[系统\](.*?)(?=\[|$)', 'system'),
                (r'\[System\](.*?)(?=\[|$)', 'system'),
                (r'\[任务\](.*?)(?=\[|$)', 'task'),
                (r'\[Task\](.*?)(?=\[|$)', 'task'),
                (r'\[输出格式\](.*?)(?=\[|$)', 'output'),
                (r'\[Output Format\](.*?)(?=\[|$)', 'output'),
                (r'\[Output\](.*?)(?=\[|$)', 'output')
            ]
            
            for pattern, section_name in section_patterns:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match and section_name not in sections:
                    sections[section_name] = match.group(1).strip()
            
            # 验证必需字段
            required_fields = ['system', 'task', 'output']
            missing_fields = [field for field in required_fields if field not in sections]
            
            if missing_fields:
                raise ValueError(f"TXT提示词文件缺少必需节: {missing_fields}")
            
            Logger.info(f"成功解析TXT格式提示词文件: {prompt_file}")
            return sections
            
        except Exception as e:
            raise ValueError(f"解析TXT提示词文件失败: {str(e)}")
    
    @staticmethod
    def build_prompt_content(prompt_data: Dict[str, str], format_style: str = "combined") -> str:
        """
        根据解析的数据构建提示词内容
        
        Args:
            prompt_data: 解析后的提示词数据
            format_style: 构建格式 ("combined", "system_only", "structured")
            
        Returns:
            str: 构建后的提示词内容
        """
        if format_style == "system_only":
            # 只返回system内容，适用于某些API
            return prompt_data['system']
        
        elif format_style == "structured":
            # 结构化格式，明确分离各部分
            return f"""[系统]
{prompt_data['system']}

[任务]
{prompt_data['task']}

[输出格式]
{prompt_data['output']}"""
        
        else:  # combined格式（默认）
            # 组合格式，将所有内容合并为一个连贯的提示词
            return f"""{prompt_data['system']}

{prompt_data['task']}

输出格式：
{prompt_data['output']}"""
    
    @staticmethod
    def get_output_template(prompt_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        从提示词数据中提取输出模板
        
        Args:
            prompt_data: 解析后的提示词数据
            
        Returns:
            Dict[str, Any]: 输出模板字典，如果解析失败返回None
        """
        try:
            output_str = prompt_data.get('output', '')
            
            # 尝试解析为JSON
            if output_str.strip().startswith('{') and output_str.strip().endswith('}'):
                return json.loads(output_str)
            
            return None
            
        except json.JSONDecodeError:
            Logger.warning("无法解析输出格式为JSON模板")
            return None 