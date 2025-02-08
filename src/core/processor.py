from pathlib import Path
import asyncio
from typing import Dict, Any, List, Optional
import json
from tqdm import tqdm

from ..utils.logger import Logger
from ..utils.config import Config
from ..utils.file_utils import FileProcessor
from ..providers.base import BaseProvider

class BatchProcessor:
    """批处理器"""
    
    def __init__(self, config: Config, provider: BaseProvider):
        self.config = config
        self.provider = provider
        self.process_config = config.process_config
        
    async def process_files(
        self,
        input_path: Path,
        prompt_file: Path,
        fields: List[int] = None,
        start_pos: int = 1,
        end_pos: Optional[int] = None
    ):
        """处理文件"""
        # 读取prompt文件
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
            
        # 获取输入文件列表
        input_files = FileProcessor.get_input_files(input_path)
        if not input_files:
            Logger.error("未找到支持的输入文件")
            return
            
        # 创建API会话
        async with await self.provider.create_session() as session:
            # 处理每个文件
            for file_path in input_files:
                await self._process_single_file(
                    file_path,
                    prompt_content,
                    session,
                    fields,
                    start_pos,
                    end_pos
                )
    
    async def _process_single_file(
        self,
        file_path: Path,
        prompt_content: str,
        session: Any,
        fields: List[int],
        start_pos: int,
        end_pos: Optional[int]
    ):
        """处理单个文件"""
        Logger.info(f"\n开始处理文件: {file_path}")
        
        try:
            current_pos = start_pos - 1
            batch_size = self.process_config.get('batch_size', 5)
            
            while True:
                # 读取一批数据
                items = FileProcessor.read_file_batch(
                    file_path,
                    current_pos,
                    batch_size,
                    fields
                )
                
                if not items or (end_pos and current_pos >= end_pos):
                    break
                    
                # 处理这一批数据
                tasks = []
                for item in items:
                    task = self.provider.process_request(
                        session,
                        prompt_content,
                        item['content']
                    )
                    tasks.append(task)
                
                # 等待所有任务完成
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                for item, result in zip(items, results):
                    if isinstance(result, Exception):
                        Logger.error(f"处理失败: {str(result)}")
                    elif result is None:
                        Logger.error("处理返回空结果")
                    else:
                        Logger.info("处理成功")
                        
                current_pos += len(items)
                
        except Exception as e:
            Logger.error(f"处理文件时出错: {str(e)}")
            return 