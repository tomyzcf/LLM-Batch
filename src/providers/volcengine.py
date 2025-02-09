from typing import Dict, Any, Optional
import aiohttp
import json
import asyncio
from .base import BaseProvider
from ..utils.logger import Logger

class VolcengineProvider(BaseProvider):
    """火山引擎API提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化火山引擎API提供商"""
        super().__init__(config)
        self.api_key = config['api_key']
        self.base_url = config['base_url']
        self.model = config['model']
        self.semaphore = asyncio.Semaphore(config.get('concurrent_limit', 10))
    
    async def create_session(self) -> aiohttp.ClientSession:
        """创建API会话"""
        return aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def process_request(
        self,
        session: aiohttp.ClientSession,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """处理单个请求"""
        async with self.semaphore:
            try:
                data = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature
                }
                
                async with session.post(
                    f"{self.base_url}/api/v3/chat/completions",
                    json=data
                ) as response:
                    if response.status != 200:
                        error_body = await response.text()
                        Logger.error(f"API请求失败 [状态码:{response.status}] - {error_body}")
                        return None
                        
                    response_json = await response.json()
                    if not response_json or 'choices' not in response_json:
                        Logger.error("API返回无效响应")
                        return None
                        
                    content = response_json['choices'][0]['message']['content']
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        Logger.error(f"JSON解析失败: {content}")
                        return None
                        
            except Exception as e:
                Logger.error(f"请求处理异常: {str(e)}")
                return None 