from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import aiohttp
import asyncio
import json

class BaseProvider(ABC):
    """API提供商基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config['api_key']
        self.base_url = config['base_url']
        self.model = config['model']
        self.concurrent_limit = config['concurrent_limit']
        self.semaphore = asyncio.Semaphore(self.concurrent_limit)
        
    @abstractmethod
    async def create_session(self) -> aiohttp.ClientSession:
        """创建API会话"""
        pass
        
    @abstractmethod
    async def process_request(
        self,
        session: aiohttp.ClientSession,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """处理单个请求"""
        pass 