from typing import Dict, Any
from .base import BaseProvider
from .aliyun import AliyunProvider
try:
    from .deepseek import DeepseekProvider
except ImportError:
    DeepseekProvider = None
try:
    from .openai import OpenAIProvider
except ImportError:
    OpenAIProvider = None
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
        providers = {
            'aliyun': AliyunProvider,
            'deepseek': DeepseekProvider,
            'openai': OpenAIProvider
        }
        
        provider_class = providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"不支持的API提供商类型: {provider_type}")
            
        if provider_class is None:
            raise ValueError(f"API提供商 {provider_type} 的实现未找到")
            
        if 'api_providers' not in config or provider_type not in config['api_providers']:
            raise ValueError(f"配置文件中缺少 {provider_type} 的API配置")
            
        provider_config = config['api_providers'][provider_type]
        Logger.info(f"使用API提供商: {provider_type}")
        return provider_class(provider_config) 