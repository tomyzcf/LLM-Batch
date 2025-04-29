from typing import Any, Dict, Optional
import aiohttp
import asyncio
from .base import BaseProvider
from ..utils.logger import Logger

class AliyunProvider(BaseProvider):
    """阿里云API提供商实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化阿里云API提供商
        
        Args:
            config: API提供商配置
        """
        super().__init__(config)
        self.api_key = config['api_key']
        self.base_url = config['base_url']
        self.model = config['model']
        self.model_params = config.get('model_params', {})
    
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
        system_content: str,
        user_content: str,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """处理单个请求"""
        try:
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                **self.model_params
            }
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # 从API响应中提取LLM返回的内容
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        # 提取JSON字符串并解析
                        try:
                            import json
                            
                            # 尝试直接解析整个内容
                            try:
                                return json.loads(content)
                            except json.JSONDecodeError as e:
                                # 记录错误但不中断流程
                                Logger.error(f"JSON解析失败: {str(e)}")
                                # 返回原始内容，让处理器决定如何处理
                                return content
                        except Exception as e:
                            Logger.error(f"处理返回内容时出错: {str(e)}")
                            # 在出错时仍然返回原始内容，避免中断流程
                            return content
                    return None
                elif response.status in [429, 503]:
                    if retry_count < self.max_retries:
                        retry_delay = min(2 ** retry_count * self.retry_interval, 10)
                        Logger.warning(f"请求限流或服务暂时不可用，{retry_delay}秒后重试第{retry_count + 1}次")
                        await asyncio.sleep(retry_delay)
                        return await self.process_request(
                            session,
                            system_content,
                            user_content,
                            retry_count + 1
                        )
                    else:
                        Logger.error("达到最大重试次数，请求失败")
                        return None
                else:
                    error_text = await response.text()
                    Logger.error(f"API请求失败，状态码：{response.status}，响应：{error_text}")
                    return None
                    
        except Exception as e:
            Logger.error(f"请求处理异常: {str(e)}")
            if retry_count < self.max_retries:
                retry_delay = min(2 ** retry_count * self.retry_interval, 10)
                Logger.warning(f"发生异常，{retry_delay}秒后重试第{retry_count + 1}次")
                await asyncio.sleep(retry_delay)
                return await self.process_request(
                    session,
                    system_content,
                    user_content,
                    retry_count + 1
                )
            return None 