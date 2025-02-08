from typing import Dict, Any
from .base import BaseProvider
from .deepseek import DeepSeekProvider
from .openai import OpenAIProvider
from ..utils.logger import Logger

class ProviderFactory:
    """API提供商工厂"""
    
    _providers = {
        "deepseek": DeepSeekProvider,
        "openai": OpenAIProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, config: Dict[str, Any]) -> BaseProvider:
        """创建API提供商实例"""
        if provider_name not in cls._providers:
            raise ValueError(f"不支持的API提供商: {provider_name}")
            
        if provider_name not in config['api_providers']:
            raise ValueError(f"未找到API提供商配置: {provider_name}")
            
        provider_class = cls._providers[provider_name]
        provider_config = config['api_providers'][provider_name]
        
        Logger.info(f"使用API提供商: {provider_name}")
        return provider_class(provider_config) 