from typing import Dict, Any
from .base import BaseProvider
from .universal_llm import UniversalLLMProvider
from .aliyun_agent import AliyunAgentProvider
from ..utils.logger import Logger

class ProviderFactory:
    """API提供商工厂类"""
    
    # API类型到Provider类的映射
    API_TYPE_MAPPING = {
        'llm_compatible': UniversalLLMProvider,
        'aliyun_agent': AliyunAgentProvider,
    }
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any]) -> BaseProvider:
        """创建API提供商实例
        
        Args:
            provider_type: 提供商类型（配置文件中的key）
            config: 完整配置
            
        Returns:
            API提供商实例
            
        Raises:
            ValueError: 不支持的提供商类型或配置错误
        """
        if 'api_providers' not in config or provider_type not in config['api_providers']:
            raise ValueError(f"配置文件中缺少 {provider_type} 的API配置")
            
        provider_config = config['api_providers'][provider_type]
        
        # 检查是否指定了api_type
        if 'api_type' in provider_config:
            api_type = provider_config['api_type']
        else:
            # 如果没有指定api_type，根据配置字段自动检测
            api_type = ProviderFactory._detect_api_type(provider_config)
            Logger.info(f"未指定api_type，自动检测为: {api_type}")
        
        # 获取对应的Provider类
        provider_class = ProviderFactory.API_TYPE_MAPPING.get(api_type)
        if provider_class is None:
            supported_types = list(ProviderFactory.API_TYPE_MAPPING.keys())
            raise ValueError(f"不支持的API类型: {api_type}，支持的类型: {supported_types}")
        
        Logger.info(f"使用API提供商: {provider_type} (类型: {api_type})")
        return provider_class(provider_config)
    
    @staticmethod
    def _detect_api_type(provider_config: Dict[str, Any]) -> str:
        """根据配置字段自动检测API类型
        
        Args:
            provider_config: 提供商配置
            
        Returns:
            检测到的API类型
        """
        # 如果有app_id字段，判断为阿里云Agent
        if 'app_id' in provider_config:
            return 'aliyun_agent'
        
        # 如果有model字段，判断为LLM兼容
        if 'model' in provider_config:
            return 'llm_compatible'
        
        # 默认为LLM兼容类型
        return 'llm_compatible'
    
    @staticmethod
    def get_supported_api_types() -> list:
        """获取支持的API类型列表"""
        return list(ProviderFactory.API_TYPE_MAPPING.keys())
    
    @staticmethod
    def add_api_type(api_type: str, provider_class: type):
        """动态添加新的API类型支持
        
        Args:
            api_type: API类型名称
            provider_class: Provider类
        """
        ProviderFactory.API_TYPE_MAPPING[api_type] = provider_class
        Logger.info(f"添加新的API类型支持: {api_type}") 