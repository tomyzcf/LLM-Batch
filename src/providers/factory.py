from typing import Dict, Any
from .base import BaseProvider
from .universal_llm import UniversalLLMProvider
from .aliyun_agent import AliyunAgentProvider
from ..utils.logger import Logger

class ProviderFactory:
    """API提供商工厂类"""
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any]) -> BaseProvider:
        """创建API提供商实例
        
        Args:
            provider_type: 提供商类型
            config: 提供商配置
            
        Returns:
            API提供商实例
            
        Raises:
            ValueError: 不支持的提供商类型
        """
        # 通用LLM提供商（支持所有OpenAI兼容API）
        universal_llm_providers = {
            'aliyun': UniversalLLMProvider,
            'deepseek': UniversalLLMProvider, 
            'openai': UniversalLLMProvider,
            'volcengine': UniversalLLMProvider
        }
        
        # 特殊提供商
        special_providers = {
            'aliyun-agent': AliyunAgentProvider,
        }
        
        # 合并所有提供商映射
        providers = {**universal_llm_providers, **special_providers}
        
        provider_class = providers.get(provider_type.lower())
        if provider_class is None:
            raise ValueError(f"不支持的API提供商类型: {provider_type}")
            
        if 'api_providers' not in config or provider_type not in config['api_providers']:
            raise ValueError(f"配置文件中缺少 {provider_type} 的API配置")
            
        provider_config = config['api_providers'][provider_type]
        
        if provider_class == UniversalLLMProvider:
            Logger.info(f"使用通用LLM提供商处理: {provider_type}")
        else:
            Logger.info(f"使用特殊提供商: {provider_type}")
            
        return provider_class(provider_config) 