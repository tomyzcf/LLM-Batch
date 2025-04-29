from typing import Any, Dict, Optional
import aiohttp
import asyncio
import json
import time
import uuid
from .base import BaseProvider
from ..utils.logger import Logger

class AliyunAgentProvider(BaseProvider):
    """阿里云百炼Agent API提供商实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化阿里云百炼Agent API提供商
        
        Args:
            config: API提供商配置
        """
        super().__init__(config)
        self.api_key = config['api_key']
        self.base_url = config['base_url']
        self.app_id = config['app_id']
        # 为了兼容性，添加model属性
        self.model = f"bailian-app-{self.app_id}"
        self.concurrent_limit = config.get('concurrent_limit', 5)
    
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
            # 构造请求数据
            data = {
                "input": {
                    "prompt": user_content
                },
                "parameters": {
                    "system_prompt": system_content
                }
            }
            
            # 发起异步请求
            url = f"{self.base_url}/api/v1/apps/{self.app_id}/completion"
            Logger.debug(f"请求URL: {url}")
            
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    Logger.debug(f"收到百炼Agent响应: {result}")
                    return self._parse_response(result)
                
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
    
    def _parse_response(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析API响应
        
        Args:
            response: API响应对象
            
        Returns:
            处理结果或None（如果处理失败）
        """
        try:
            # 检查是否出错
            if 'code' in response and response['code'] != 200:
                Logger.error(f"API请求失败：{response.get('message', '未知错误')}")
                return None
            
            # 解析output内容
            output = response.get('output', {})
            text = output.get('text', '')
            
            # 尝试从文本中提取JSON
            try:
                # 如果文本看起来是JSON格式，尝试解析
                if text.strip().startswith('{') and text.strip().endswith('}'):
                    json_obj = json.loads(text)
                    return json_obj
            except json.JSONDecodeError:
                # 如果不是有效的JSON，直接返回文本内容
                pass
            
            # 构建结果
            result = {"content": text}
            
            # 添加usage信息（如果有）
            usage = response.get('usage', {})
            if usage:
                result["usage"] = {
                    "input_tokens": usage.get('input_tokens', 0),
                    "output_tokens": usage.get('output_tokens', 0),
                    "total_tokens": usage.get('total_tokens', 0)
                }
            
            return result
            
        except Exception as e:
            Logger.error(f"解析响应异常: {str(e)}")
            return None 