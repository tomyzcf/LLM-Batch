from typing import Any, Dict, Optional
import aiohttp
import asyncio
import json
from .base import BaseProvider
from ..utils.logger import Logger

class UniversalLLMProvider(BaseProvider):
    """通用 LLM API 提供商实现 - 支持所有 OpenAI 兼容的 API"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化通用 LLM API 提供商
        
        Args:
            config: API提供商配置
        """
        super().__init__(config)
        self.api_key = config['api_key']
        self.base_url = config['base_url'].rstrip('/')  # 移除末尾斜杠
        self.model = config['model']
        self.model_params = config.get('model_params', {})
        
        # 配置API端点路径 - 支持不同提供商的路径格式
        self.endpoint_path = config.get('endpoint_path', self._detect_endpoint_path())
        
        # 并发控制
        concurrent_limit = config.get('concurrent_limit', 10)
        self.semaphore = asyncio.Semaphore(concurrent_limit)
    
    def _detect_endpoint_path(self) -> str:
        """根据 base_url 自动检测API端点路径"""
        base_url_lower = self.base_url.lower()
        
        if 'dashscope.aliyuncs.com' in base_url_lower:
            return '/chat/completions'
        elif 'volces.com' in base_url_lower:
            return '/api/v3/chat/completions'  
        else:
            # DeepSeek, OpenAI 等标准格式
            return '/v1/chat/completions'
    
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
        async with self.semaphore:
            try:
                # 构建请求数据
                data = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content}
                    ],
                    **self.model_params
                }
                
                # 发送请求
                url = f"{self.base_url}{self.endpoint_path}"
                Logger.debug(f"请求URL: {url}")
                
                async with session.post(url, json=data) as response:
                    return await self._handle_response(
                        response, 
                        session, 
                        system_content, 
                        user_content, 
                        retry_count
                    )
                    
            except Exception as e:
                Logger.error(f"请求处理异常: {str(e)}")
                return await self._handle_retry(
                    session, 
                    system_content, 
                    user_content, 
                    retry_count,
                    str(e)
                )
    
    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        session: aiohttp.ClientSession,
        system_content: str,
        user_content: str,
        retry_count: int
    ) -> Optional[Dict[str, Any]]:
        """处理API响应"""
        if response.status == 200:
            result = await response.json()
            return self._parse_success_response(result)
        
        elif response.status in [429, 503, 502, 504]:
            # 可重试的错误
            error_text = await response.text()
            Logger.warning(f"API请求失败 [状态码:{response.status}] - {error_text}")
            return await self._handle_retry(
                session,
                system_content,
                user_content,
                retry_count,
                f"HTTP {response.status}"
            )
        
        else:
            # 不可重试的错误
            error_text = await response.text()
            Logger.error(f"API请求失败 [状态码:{response.status}] - {error_text}")
            return None
    
    def _parse_success_response(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析成功的API响应"""
        try:
            # 检查响应格式
            if 'choices' not in result or not result['choices']:
                Logger.error("API返回无效响应：缺少choices字段")
                return None
            
            # 提取LLM返回的内容
            content = result['choices'][0]['message']['content']
            
            # 首先尝试检查是否是Markdown代码块格式
            import re
            json_pattern = r'```(?:json)?\s*(.*?)\s*```'
            md_json_match = re.search(json_pattern, content, re.DOTALL)
            
            if md_json_match:
                # 如果是Markdown代码块，提取其中的JSON内容
                json_content = md_json_match.group(1).strip()
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError as e:
                    Logger.error(f"Markdown代码块中的JSON解析失败: {str(e)}")
                    Logger.error(f"代码块内容: {json_content[:200]}...")
                    return None
            
            # 然后尝试直接解析为JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                Logger.error(f"JSON解析失败: {str(e)}")
                # 记录原始内容以便调试
                Logger.debug(f"原始响应内容: {content[:200]}...")
                return None
                
        except Exception as e:
            Logger.error(f"处理返回内容时出错: {str(e)}")
            return None
    
    async def _handle_retry(
        self,
        session: aiohttp.ClientSession,
        system_content: str,
        user_content: str,
        retry_count: int,
        error_msg: str
    ) -> Optional[Dict[str, Any]]:
        """处理重试逻辑"""
        if retry_count < self.max_retries:
            retry_delay = min(2 ** retry_count * self.retry_interval, 10)
            Logger.warning(f"请求失败：{error_msg}，{retry_delay}秒后重试第{retry_count + 1}次")
            await asyncio.sleep(retry_delay)
            return await self.process_request(
                session,
                system_content,
                user_content,
                retry_count + 1
            )
        else:
            Logger.error(f"达到最大重试次数，请求失败：{error_msg}")
            return None 