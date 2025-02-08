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
        # 设置输出文件路径
        rel_path = file_path.relative_to(Path('inputData'))
        base_name = rel_path.stem
        output_dir = Path('outputData')
        if rel_path.parent != Path('.'):
            output_dir = output_dir / rel_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置所有输出文件路径
        log_file = output_dir / f"{base_name}_process.log"
        output_file = output_dir / f"{base_name}_output{file_path.suffix}"
        raw_file = output_dir / f"{base_name}_raw.json"
        error_file = output_dir / f"{base_name}_error{file_path.suffix}"
        
        # 设置日志文件
        Logger.set_log_file(log_file)
        
        Logger.info(f"\n开始处理文件: {file_path}")
        
        try:
            current_pos = start_pos - 1
            batch_size = self.process_config.get('batch_size', 5)
            
            # 如果是错误记录文件，添加错误类型字段的表头
            if file_path.suffix.lower() == '.csv':
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write(f"{item['content']},error_type\n")
            
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
                        # 保存错误信息到日志
                        Logger.error(f"处理失败: {str(result)}")
                        
                        # 保存原始数据和错误类型
                        if file_path.suffix.lower() == '.csv':
                            with open(error_file, 'a', encoding='utf-8') as f:
                                f.write(f"{item['content']},API错误\n")
                        else:
                            error_data = json.loads(item['content'])
                            error_data['error_type'] = 'API错误'
                            with open(error_file, 'a', encoding='utf-8') as f:
                                json.dump(error_data, f, ensure_ascii=False)
                                f.write('\n')
                                
                    elif result is None:
                        # 保存空结果错误到日志
                        Logger.error("处理返回空结果")
                        
                        # 保存原始数据和错误类型
                        if file_path.suffix.lower() == '.csv':
                            with open(error_file, 'a', encoding='utf-8') as f:
                                f.write(f"{item['content']},空结果\n")
                        else:
                            error_data = json.loads(item['content'])
                            error_data['error_type'] = '空结果'
                            with open(error_file, 'a', encoding='utf-8') as f:
                                json.dump(error_data, f, ensure_ascii=False)
                                f.write('\n')
                            
                        # 保存原始输出
                        with open(raw_file, 'a', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False)
                            f.write('\n')
                            
                        # 保存处理结果
                        with open(output_file, 'a', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False)
                            f.write('\n')
                            
                        Logger.info("处理成功")
                        
                current_pos += len(items)
                
        except Exception as e:
            Logger.error(f"处理文件时出错: {str(e)}")
            return 