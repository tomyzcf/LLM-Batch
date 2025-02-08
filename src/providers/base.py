from typing import Any, Dict, Optional
import aiohttp
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """API提供商基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化基类
        
        Args:
            config: API提供商配置
        """
        self.config = config
        self.max_retries = config.get('max_retries', 5)
        self.retry_interval = config.get('retry_interval', 0.5)
    
    @abstractmethod
    async def create_session(self) -> aiohttp.ClientSession:
        """创建API会话"""
        pass
    
    @abstractmethod
    async def process_request(
        self,
        session: aiohttp.ClientSession,
        system_content: str,
        user_content: str,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """处理单个请求
        
        Args:
            session: API会话
            system_content: 系统提示词
            user_content: 用户输入内容
            retry_count: 当前重试次数
            
        Returns:
            处理结果或None（如果处理失败）
        """
        pass 