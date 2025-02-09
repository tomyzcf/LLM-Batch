from pathlib import Path
import asyncio
from typing import Dict, Any, List, Optional
import json
from tqdm import tqdm
import datetime
import csv
import shutil

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
        progress_file = output_dir / f"{base_name}_progress.json"
        
        # 创建备份
        backup_dir = output_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 备份现有文件
        for f in [output_file, raw_file, error_file, progress_file]:
            if f.exists():
                backup_file = backup_dir / f"{f.stem}_{timestamp}{f.suffix}"
                shutil.copy2(f, backup_file)
                Logger.info(f"已创建文件备份: {backup_file}")
        
        # 设置日志文件
        Logger.set_log_file(log_file)
        
        # 打印配置信息
        Logger.info("批处理任务配置信息:")
        Logger.info(f"API提供商: {self.config.default_provider}")
        Logger.info(f"模型: {self.provider.model}")
        Logger.info(f"批处理大小: {self.process_config.get('batch_size', 5)}")
        Logger.info(f"最大重试次数: {self.process_config.get('max_retries', 5)}")
        Logger.info(f"重试间隔: {self.process_config.get('retry_interval', 0.5)}秒")
        Logger.info(f"输入文件: {file_path}")
        Logger.info(f"输出目录: {output_dir}")
        if fields:
            Logger.info(f"处理字段: {fields}")
        Logger.info("---" * 20)
        
        # 获取总行数和剩余行数
        file_total_lines = sum(1 for _ in open(file_path, 'r', encoding='utf-8')) - 1  # 减去表头
        if end_pos:
            file_total_lines = min(file_total_lines, end_pos)
        
        # 加载处理进度
        current_pos = start_pos - 1
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    current_pos = max(current_pos, progress_data.get('last_position', current_pos))
                    Logger.info(f"从上次的进度继续处理: 第 {current_pos + 1} 行")
            except Exception as e:
                Logger.error(f"读取进度文件失败: {str(e)}")
        
        # 计算剩余需要处理的行数
        remaining_lines = file_total_lines - current_pos
        
        Logger.info(f"\n开始处理文件: {file_path}")
        Logger.info(f"处理范围: 第 {current_pos + 1} 行 到 {end_pos if end_pos else '文件末尾'}")
        Logger.info(f"剩余行数: {remaining_lines}")
        
        # 统计信息
        stats = {
            'total': 0,
            'success': 0,
            'api_error': 0,
            'empty_result': 0,
            'json_error': 0,
            'other_error': 0
        }
        
        # 批次计数器
        batch_count = 0
        
        try:
            batch_size = self.process_config.get('batch_size', 5)
            
            # 如果是错误记录文件，只在文件不存在时添加表头
            if file_path.suffix.lower() == '.csv' and not error_file.exists():
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write("content,error_type\n")
            
            # 输出文件的表头会在第一次写入数据时创建
            output_headers = None
            
            # 创建进度条，使用剩余行数
            progress_config = self.config.logging_config.get('progress', {})
            if progress_config.get('show_progress_bar', True):
                pbar = tqdm(
                    total=remaining_lines,
                    desc="处理进度",
                    unit="条",
                    bar_format=progress_config.get('bar_format'),
                    mininterval=progress_config.get('update_interval', 0.1)
                )
            else:
                pbar = None
            
            try:
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
                    
                    stats['total'] += len(items)
                    
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
                            stats['api_error'] += 1
                            Logger.error(f"处理失败: {str(result)}")
                            
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
                            stats['empty_result'] += 1
                            Logger.error("处理返回空结果")
                            
                            if file_path.suffix.lower() == '.csv':
                                with open(error_file, 'a', encoding='utf-8') as f:
                                    f.write(f"{item['content']},空结果\n")
                            else:
                                error_data = json.loads(item['content'])
                                error_data['error_type'] = '空结果'
                                with open(error_file, 'a', encoding='utf-8') as f:
                                    json.dump(error_data, f, ensure_ascii=False)
                                    f.write('\n')
                            
                            with open(raw_file, 'a', encoding='utf-8') as f:
                                json.dump(result, f, ensure_ascii=False)
                                f.write('\n')
                        else:
                            try:
                                # 预处理JSON字符串，使用正则表达式处理未加引号的特殊值
                                if isinstance(result, str):
                                    import re
                                    # 1. 提取JSON内容（去除所有非JSON文本）
                                    result = re.sub(r'^[^{]*({.*})[^}]*$', r'\1', result.strip())
                                    
                                    # 2. 处理特殊值
                                    result = re.sub(r':\s*(无相关内容|NA)\s*(?=,|\n|\s*})', r': "\1"', result)
                                    
                                    # 3. 确保数字字段不带引号
                                    result = re.sub(r'"(判决依据条款数目|判断案件受理费金额)":\s*"(\d+)"', r'"\1": \2', result)
                                    
                                    # 尝试解析JSON
                                    result = json.loads(result)
                                
                                stats['success'] += 1
                                with open(raw_file, 'a', encoding='utf-8') as f:
                                    json.dump(result, f, ensure_ascii=False)
                                    f.write('\n')
                                    
                                if output_headers is None and result:
                                    output_headers = list(result.keys())
                                    if not output_file.exists():
                                        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                                            writer = csv.DictWriter(f, fieldnames=output_headers)
                                            writer.writeheader()
                                    else:
                                        with open(output_file, 'r', encoding='utf-8-sig', newline='') as f:
                                            reader = csv.reader(f)
                                            existing_headers = next(reader)
                                            if existing_headers != output_headers:
                                                Logger.warning(f"警告：现有文件的表头与当前结果的字段不匹配")
                                                Logger.warning(f"现有表头: {existing_headers}")
                                                Logger.warning(f"当前字段: {output_headers}")
                                        
                                with open(output_file, 'a', encoding='utf-8-sig', newline='') as f:
                                    writer = csv.DictWriter(f, fieldnames=output_headers)
                                    writer.writerow(result)
                            except json.JSONDecodeError as e:
                                stats['json_error'] += 1
                                Logger.error(f"JSON解析失败: {result}")
                                Logger.error(f"错误详情: {str(e)}")
                                
                                if file_path.suffix.lower() == '.csv':
                                    with open(error_file, 'a', encoding='utf-8') as f:
                                        f.write(f"{item['content']},JSON解析错误\n")
                                else:
                                    error_data = json.loads(item['content'])
                                    error_data['error_type'] = 'JSON解析错误'
                                    with open(error_file, 'a', encoding='utf-8') as f:
                                        json.dump(error_data, f, ensure_ascii=False)
                                        f.write('\n')
                    
                    # 更新进度条
                    if pbar:
                        pbar.update(len(items))
                    
                    # 更新批次计数
                    batch_count += 1
                    
                    # 保存进度
                    current_pos += len(items)
                    with open(progress_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'last_position': current_pos,
                            'last_update': datetime.datetime.now().isoformat(),
                            'stats': stats
                        }, f, ensure_ascii=False, indent=2)
                    
                    # 定期输出统计信息
                    if Logger.should_show_stats(batch_count):
                        Logger.info(f"\n当前处理统计:\n" + 
                                  f"总处理: {stats['total']}\n" +
                                  f"成功: {stats['success']}\n" +
                                  f"API错误: {stats['api_error']}\n" +
                                  f"空结果: {stats['empty_result']}\n" +
                                  f"JSON解析错误: {stats['json_error']}\n" +
                                  f"其他错误: {stats['other_error']}")
            finally:
                if pbar:
                    pbar.close()
        except Exception as e:
            stats['other_error'] += 1
            Logger.error(f"处理文件时出错: {str(e)}")
            return
        finally:
            # 输出最终统计信息
            Logger.info(f"\n处理完成。最终统计:\n" + 
                      f"总处理: {stats['total']}\n" +
                      f"成功: {stats['success']}\n" +
                      f"API错误: {stats['api_error']}\n" +
                      f"空结果: {stats['empty_result']}\n" +
                      f"JSON解析错误: {stats['json_error']}\n" +
                      f"其他错误: {stats['other_error']}") 