from pathlib import Path
import asyncio
from typing import Dict, Any, List, Optional
import json
from tqdm import tqdm
import datetime
import csv
import shutil
import pandas as pd
import re

from ..utils.logger import Logger, DEFAULT_LOG_CONFIG
from ..utils.config import Config
from ..utils.file_utils import FileProcessor
from ..utils.prompt_parser import PromptParser
from ..providers.base import BaseProvider

class BatchProcessor:
    """批处理器"""
    
    def __init__(self, config: Config, provider: BaseProvider):
        self.config = config
        self.provider = provider
        self.process_config = config.process_config
        self.output_dir = Path('outputData')  # 默认输出目录
        
    def set_output_dir(self, output_dir: str):
        """设置输出目录"""
        self.output_dir = Path(output_dir)
        Logger.info(f"设置输出目录为: {self.output_dir}")
        
    async def process_files(
        self,
        input_path: Path,
        prompt_file: Path,
        fields: List[int] = None,
        start_pos: int = 1,
        end_pos: Optional[int] = None
    ):
        """处理文件"""
        # 使用新的提示词解析器解析提示词文件
        try:
            prompt_data = PromptParser.parse_prompt_file(prompt_file)
            prompt_content = PromptParser.build_prompt_content(prompt_data, "combined")
            Logger.info(f"提示词格式：{prompt_file.suffix.upper()}")
            Logger.info(f"提示词文件：{prompt_file}")
        except Exception as e:
            Logger.error(f"解析提示词文件失败：{str(e)}")
            return
            
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
    
    async def retry_failed_records(
        self,
        input_path: Path,
        prompt_file: Path
    ):
        """重试失败的记录
        
        Args:
            input_path: 原始输入文件路径
            prompt_file: 提示词文件路径
        """
        # 解析提示词文件
        try:
            prompt_data = PromptParser.parse_prompt_file(prompt_file)
            prompt_content = PromptParser.build_prompt_content(prompt_data, "combined")
            Logger.info(f"提示词格式：{prompt_file.suffix.upper()}")
            Logger.info(f"提示词文件：{prompt_file}")
        except Exception as e:
            Logger.error(f"解析提示词文件失败：{str(e)}")
            return
        
        # 确定错误文件路径
        try:
            rel_path = input_path.relative_to(Path('inputData'))
        except ValueError:
            parts = input_path.parts
            if 'inputData' in parts:
                idx = parts.index('inputData')
                rel_path = Path(*parts[idx + 1:])
            else:
                rel_path = Path(input_path.name)
        
        base_name = rel_path.stem
        output_dir = self.output_dir
        if rel_path.parent != Path('.'):
            output_dir = output_dir / rel_path.parent
        
        error_file = output_dir / f"{base_name}_error{input_path.suffix}"
        
        if not error_file.exists():
            Logger.warning(f"未找到错误文件: {error_file}")
            Logger.info("没有需要重试的记录")
            return
        
        Logger.info(f"找到错误文件: {error_file}")
        
        # 读取错误记录
        failed_items = []
        try:
            if input_path.suffix.lower() == '.csv':
                # CSV格式
                with open(error_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'content' in row:
                            failed_items.append(row['content'])
            elif input_path.suffix.lower() in ['.xlsx', '.xls']:
                # Excel格式 - 需要读取原始数据
                df_error = pd.read_excel(error_file)
                # 假设第一列是content
                if len(df_error.columns) > 0:
                    for _, row in df_error.iterrows():
                        # 将整行转换为字符串
                        content = str(row.iloc[0]) if len(row) > 0 else ""
                        if content:
                            failed_items.append(content)
            else:
                # JSON格式
                with open(error_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            error_data = json.loads(line.strip())
                            if 'content' in error_data:
                                failed_items.append(error_data['content'])
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            Logger.error(f"读取错误文件失败: {str(e)}")
            return
        
        if not failed_items:
            Logger.info("错误文件中没有可重试的记录")
            return
        
        Logger.info(f"找到 {len(failed_items)} 条失败记录，开始重试...")
        
        # 备份错误文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = output_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_error_file = backup_dir / f"{error_file.stem}_{timestamp}{error_file.suffix}"
        shutil.copy2(error_file, backup_error_file)
        Logger.info(f"已备份错误文件: {backup_error_file}")
        
        # 清空错误文件，准备记录新的错误
        if input_path.suffix.lower() == '.csv':
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write("content,error_type\n")
        else:
            error_file.unlink()
        
        # 设置日志文件
        log_file = output_dir / f"{base_name}_retry.log"
        Logger.set_log_file(log_file)
        
        # 获取输出文件
        output_file = output_dir / f"{base_name}_output{input_path.suffix}"
        raw_file = output_dir / f"{base_name}_raw.json"
        
        # 统计信息
        stats = {
            'total': len(failed_items),
            'success': 0,
            'api_error': 0,
            'json_error': 0,
            'other_error': 0
        }
        
        # 创建API会话
        async with await self.provider.create_session() as session:
            batch_size = self.process_config.get('batch_size', 5)
            
            # 读取现有输出文件的表头
            output_headers = None
            if output_file.exists():
                if input_path.suffix.lower() == '.csv':
                    with open(output_file, 'r', encoding='utf-8-sig', newline='') as f:
                        reader = csv.reader(f)
                        output_headers = next(reader, None)
            
            # 创建进度条
            pbar = tqdm(total=len(failed_items), desc="重试进度", unit="条")
            
            try:
                # 分批处理
                for i in range(0, len(failed_items), batch_size):
                    batch_items = failed_items[i:i+batch_size]
                    
                    # 处理这一批
                    tasks = []
                    for content in batch_items:
                        task = self.provider.process_request(
                            session,
                            prompt_content,
                            content
                        )
                        tasks.append(task)
                    
                    # 等待所有任务完成
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 处理结果
                    for content, result in zip(batch_items, results):
                        item = {'content': content}
                        
                        try:
                            if isinstance(result, Exception):
                                # 错误处理
                                stats['api_error'] += 1
                                error_type = "API错误"
                                
                                Logger.error(f"重试失败 ({error_type}): {str(result)}")
                                
                                # 再次记录到错误文件
                                if input_path.suffix.lower() == '.csv':
                                    with open(error_file, 'a', encoding='utf-8') as f:
                                        f.write(f'"{content.replace(chr(34), chr(34)+chr(34))}",{error_type}\n')
                                else:
                                    with open(error_file, 'a', encoding='utf-8') as f:
                                        error_data = {
                                            "content": content,
                                            "error_type": error_type,
                                            "error_details": str(result)
                                        }
                                        json.dump(error_data, f, ensure_ascii=False)
                                        f.write('\n')
                            
                            elif isinstance(result, dict):
                                # 新格式：包含原始响应和解析结果
                                if '_raw_response' in result:
                                    # 先保存原始响应到raw.json
                                    raw_data = {
                                        "raw_response": result.get('_raw_response'),
                                        "raw_content": result.get('_raw_content'),
                                        "input": content
                                    }
                                    with open(raw_file, 'a', encoding='utf-8') as f:
                                        json.dump(raw_data, f, ensure_ascii=False)
                                        f.write('\n')
                                    
                                    # 检查是否解析成功
                                    if result.get('_parse_error') is None and result.get('_parsed_data') is not None:
                                        # 解析成功
                                        stats['success'] += 1
                                        parsed_data = result['_parsed_data']
                                        
                                        # 写入输出文件
                                        if output_headers is None and parsed_data:
                                            output_headers = list(parsed_data.keys())
                                            if not output_file.exists():
                                                with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                                                    writer = csv.DictWriter(f, fieldnames=output_headers)
                                                    writer.writeheader()
                                        
                                        with open(output_file, 'a', encoding='utf-8-sig', newline='') as f:
                                            writer = csv.DictWriter(f, fieldnames=output_headers)
                                            writer.writerow(parsed_data)
                                    else:
                                        # 解析失败
                                        stats['json_error'] += 1
                                        error_type = "JSON解析错误"
                                        error_details = result.get('_parse_error', '未知错误')
                                        Logger.error(f"重试解析失败: {error_details}")
                                        
                                        # 记录到错误文件
                                        if input_path.suffix.lower() == '.csv':
                                            with open(error_file, 'a', encoding='utf-8') as f:
                                                f.write(f'"{content.replace(chr(34), chr(34)+chr(34))}",{error_type}\n')
                                        else:
                                            with open(error_file, 'a', encoding='utf-8') as f:
                                                error_data = {
                                                    "content": content,
                                                    "error_type": error_type,
                                                    "error_details": error_details,
                                                    "raw_content": result.get('_raw_content', '')[:500]
                                                }
                                                json.dump(error_data, f, ensure_ascii=False)
                                                f.write('\n')
                                else:
                                    # 兼容旧格式
                                    stats['success'] += 1
                                    
                                    # 写入raw文件
                                    with open(raw_file, 'a', encoding='utf-8') as f:
                                        json.dump(result, f, ensure_ascii=False)
                                        f.write('\n')
                                    
                                    # 写入输出文件
                                    if output_headers is None and result:
                                        output_headers = list(result.keys())
                                        if not output_file.exists():
                                            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                                                writer = csv.DictWriter(f, fieldnames=output_headers)
                                                writer.writeheader()
                                    
                                    with open(output_file, 'a', encoding='utf-8-sig', newline='') as f:
                                        writer = csv.DictWriter(f, fieldnames=output_headers)
                                        writer.writerow(result)
                            
                            else:
                                stats['other_error'] += 1
                                Logger.error(f"重试返回了非预期的结果类型: {type(result)}")
                        
                        except Exception as e:
                            stats['other_error'] += 1
                            Logger.error(f"处理重试结果时出错: {str(e)}")
                        
                        pbar.update(1)
                    
                    # 短暂休息
                    await asyncio.sleep(0.1)
            
            finally:
                pbar.close()
        
        # 输出统计信息
        Logger.info(f"\n重试完成。统计信息:\n" + 
                  f"总记录: {stats['total']}\n" +
                  f"成功: {stats['success']}\n" +
                  f"API错误: {stats['api_error']}\n" +
                  f"JSON解析错误: {stats['json_error']}\n" +
                  f"其他错误: {stats['other_error']}")
        
        if stats['success'] == stats['total']:
            Logger.info("所有失败记录已成功重试！")
        elif stats['success'] > 0:
            Logger.info(f"成功重试 {stats['success']} 条记录，还有 {stats['total'] - stats['success']} 条记录仍然失败")
        else:
            Logger.warning("所有记录重试仍然失败")
    
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
        try:
            # 尝试获取相对于 inputData 的相对路径
            rel_path = file_path.relative_to(Path('inputData'))
        except ValueError:
            # 如果失败，尝试从绝对路径中提取相对路径部分
            parts = file_path.parts
            if 'inputData' in parts:
                idx = parts.index('inputData')
                rel_path = Path(*parts[idx + 1:])
            else:
                # 如果路径中没有 inputData，使用文件名作为相对路径
                rel_path = Path(file_path.name)
        
        base_name = rel_path.stem
        output_dir = self.output_dir
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
        try:
            # 根据文件类型选择不同的行数计算方法
            ext = file_path.suffix.lower()
            file_total_lines = None
            
            if ext == '.json':
                # JSON文件通常一行一条记录
                encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb18030', 'latin1']
                for encoding in encodings:
                    try:
                        file_total_lines = sum(1 for _ in open(file_path, 'r', encoding=encoding))
                        Logger.info(f"使用编码 {encoding} 成功读取JSON文件，总行数：{file_total_lines}")
                        break
                    except UnicodeDecodeError:
                        continue
            elif ext in ['.csv', '.xlsx', '.xls']:
                # CSV和Excel文件需要考虑表头
                if ext == '.csv':
                    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb18030', 'latin1']
                    for encoding in encodings:
                        try:
                            file_total_lines = sum(1 for _ in open(file_path, 'r', encoding=encoding)) - 1  # 减去表头
                            Logger.info(f"使用编码 {encoding} 成功读取CSV文件，总行数（不含表头）：{file_total_lines}")
                            break
                        except UnicodeDecodeError:
                            continue
                else:
                    # Excel文件使用pandas读取行数
                    try:
                        df = pd.read_excel(file_path)
                        file_total_lines = len(df)
                        Logger.info(f"成功读取Excel文件，总行数（不含表头）：{file_total_lines}")
                    except Exception as excel_e:
                        Logger.error(f"读取Excel文件出错: {str(excel_e)}")
                        raise
            
            if file_total_lines is None:
                raise ValueError(f"无法使用支持的编码读取文件: {encodings}")
        
            if end_pos:
                file_total_lines = min(file_total_lines, end_pos)
        except Exception as e:
            Logger.error(f"计算文件行数时出错: {str(e)}")
            raise
        
        # 加载处理进度
        current_pos = start_pos - 1
        stats = {
            'total': 0,
            'success': 0,
            'api_error': 0,
            'empty_result': 0,
            'json_error': 0,
            'other_error': 0
        }
        
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    current_pos = max(current_pos, progress_data.get('last_position', current_pos))
                    # 加载之前的统计数据
                    if 'stats' in progress_data:
                        stats = progress_data['stats']
                    Logger.info(f"从上次的进度继续处理: 第 {current_pos + 1} 行")
            except Exception as e:
                Logger.error(f"读取进度文件失败: {str(e)}")
        
        # 计算剩余需要处理的行数
        remaining_lines = file_total_lines - current_pos
        
        Logger.info(f"\n开始处理文件: {file_path}")
        Logger.info(f"处理范围: 第 {current_pos + 1} 行 到 {end_pos if end_pos else '文件末尾'}")
        Logger.info(f"剩余行数: {remaining_lines}")
        
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
            progress_config = DEFAULT_LOG_CONFIG.get('progress', {})
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
                    
                    # 逐条处理结果
                    for item, result in zip(items, results):
                        try:
                            if isinstance(result, Exception):
                                # 判断错误类型（API调用失败等）
                                stats['api_error'] += 1
                                error_type = "API错误"
                                
                                Logger.error(f"处理失败 ({error_type}): {str(result)}")
                                
                                # 记录错误
                                if file_path.suffix.lower() == '.csv':
                                    with open(error_file, 'a', encoding='utf-8') as f:
                                        f.write(f'"{item["content"].replace(chr(34), chr(34)+chr(34))}",{error_type}\n')
                                else:
                                    try:
                                        # 尝试解析原始内容
                                        try:
                                            error_data = json.loads(item['content'])
                                        except:
                                            # 如果不是JSON，创建一个包含原始内容的字典
                                            error_data = {"content": item['content']}
                                        
                                        error_data['error_type'] = error_type
                                        error_data['error_details'] = str(result)
                                        with open(error_file, 'a', encoding='utf-8') as f:
                                            json.dump(error_data, f, ensure_ascii=False)
                                            f.write('\n')
                                    except Exception as e:
                                        Logger.error(f"写入错误记录失败: {str(e)}")
                                        Logger.error(f"原始内容: {item['content'][:100]}...")
                                
                            elif isinstance(result, dict):
                                # 新格式：包含原始响应和解析结果
                                if '_raw_response' in result:
                                    # 先保存原始响应到raw.json
                                    raw_data = {
                                        "raw_response": result.get('_raw_response'),
                                        "raw_content": result.get('_raw_content'),
                                        "input": item['content']
                                    }
                                    with open(raw_file, 'a', encoding='utf-8') as f:
                                        json.dump(raw_data, f, ensure_ascii=False)
                                        f.write('\n')
                                    
                                    # 检查是否解析成功
                                    if result.get('_parse_error') is None and result.get('_parsed_data') is not None:
                                        # 解析成功
                                        stats['success'] += 1
                                        parsed_data = result['_parsed_data']
                                        
                                        # 写入输出文件
                                        if output_headers is None and parsed_data:
                                            output_headers = list(parsed_data.keys())
                                            if not output_file.exists():
                                                with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                                                    writer = csv.DictWriter(f, fieldnames=output_headers)
                                                    writer.writeheader()
                                        
                                        with open(output_file, 'a', encoding='utf-8-sig', newline='') as f:
                                            writer = csv.DictWriter(f, fieldnames=output_headers)
                                            writer.writerow(parsed_data)
                                    else:
                                        # 解析失败
                                        stats['json_error'] += 1
                                        error_type = "JSON解析错误"
                                        error_details = result.get('_parse_error', '未知错误')
                                        Logger.error(f"JSON解析失败: {error_details}")
                                        
                                        # 记录到错误文件
                                        if file_path.suffix.lower() == '.csv':
                                            with open(error_file, 'a', encoding='utf-8') as f:
                                                f.write(f'"{item["content"].replace(chr(34), chr(34)+chr(34))}",{error_type}\n')
                                        else:
                                            try:
                                                try:
                                                    error_data = json.loads(item['content'])
                                                except:
                                                    error_data = {"content": item['content']}
                                                
                                                error_data['error_type'] = error_type
                                                error_data['error_details'] = error_details
                                                error_data['raw_content'] = result.get('_raw_content', '')[:500]  # 保存部分原始内容用于调试
                                                with open(error_file, 'a', encoding='utf-8') as f:
                                                    json.dump(error_data, f, ensure_ascii=False)
                                                    f.write('\n')
                                            except Exception as e:
                                                Logger.error(f"写入错误记录失败: {str(e)}")
                                    
                                    continue
                                
                                # 兼容旧格式处理
                                try:
                                    # 检查是否是特殊格式：包含content和usage字段
                                    if 'content' in result and 'usage' in result:
                                        content = result['content']
                                        # 尝试解析content字段中的Markdown代码块
                                        json_pattern = r'```(?:json)?\s*(.*?)\s*```'
                                        md_json_match = re.search(json_pattern, content, re.DOTALL)
                                        if md_json_match:
                                            json_content = md_json_match.group(1).strip()
                                            try:
                                                result_dict = json.loads(json_content)
                                                stats['success'] += 1
                                                with open(raw_file, 'a', encoding='utf-8') as f:
                                                    json.dump(result_dict, f, ensure_ascii=False)
                                                    f.write('\n')
                                                
                                                if output_headers is None and result_dict:
                                                    output_headers = list(result_dict.keys())
                                                    if not output_file.exists():
                                                        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                                                            writer = csv.DictWriter(f, fieldnames=output_headers)
                                                            writer.writeheader()
                                                
                                                with open(output_file, 'a', encoding='utf-8-sig', newline='') as f:
                                                    writer = csv.DictWriter(f, fieldnames=output_headers)
                                                    writer.writerow(result_dict)
                                                continue
                                            except json.JSONDecodeError as je:
                                                Logger.error(f"解析特殊格式content字段中的JSON失败: {str(je)}")
                                                Logger.error(f"代码块内容: {json_content[:200]}...")
                                                stats['json_error'] += 1
                                                
                                                # 记录解析错误
                                                try:
                                                    error_data = {
                                                        "content": item['content'],
                                                        "error_type": "JSON解析错误",
                                                        "error_details": f"特殊格式content字段JSON解析错误: {str(je)}"
                                                    }
                                                    with open(error_file, 'a', encoding='utf-8') as f:
                                                        if file_path.suffix.lower() == '.csv':
                                                            f.write(f"{item['content']},JSON解析错误\n")
                                                        else:
                                                            json.dump(error_data, f, ensure_ascii=False)
                                                            f.write('\n')
                                                except Exception as e:
                                                    Logger.error(f"写入错误记录失败: {str(e)}")
                                                
                                                continue
                                        else:
                                            # 如果content不包含Markdown代码块，记录为错误
                                            Logger.error(f"特殊格式content字段不包含JSON代码块: {content[:100]}...")
                                            stats['json_error'] += 1
                                            
                                            # 记录解析错误
                                            try:
                                                error_data = {
                                                    "content": item['content'],
                                                    "error_type": "格式错误",
                                                    "error_details": "特殊格式content字段不包含JSON代码块"
                                                }
                                                with open(error_file, 'a', encoding='utf-8') as f:
                                                    if file_path.suffix.lower() == '.csv':
                                                        f.write(f"{item['content']},格式错误\n")
                                                    else:
                                                        json.dump(error_data, f, ensure_ascii=False)
                                                        f.write('\n')
                                            except Exception as e:
                                                Logger.error(f"写入错误记录失败: {str(e)}")
                                            
                                            continue
                                    
                                    # 正常字典处理流程
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
                                except Exception as e:
                                    stats['other_error'] += 1
                                    Logger.error(f"处理结果时出错: {str(e)}")
                                    
                                    # 记录处理错误
                                    try:
                                        error_data = {
                                            "content": item['content'],
                                            "error_type": "处理错误",
                                            "error_details": str(e)
                                        }
                                        with open(error_file, 'a', encoding='utf-8') as f:
                                            if file_path.suffix.lower() == '.csv':
                                                f.write(f"{item['content']},处理错误\n")
                                            else:
                                                json.dump(error_data, f, ensure_ascii=False)
                                                f.write('\n')
                                    except Exception as write_e:
                                        Logger.error(f"写入错误记录失败: {str(write_e)}")
                                    
                                    continue
                            else:  # 处理非字典类型的结果
                                try:
                                    # 尝试解析JSON字符串
                                    if isinstance(result, str):
                                        try:
                                            # 检查是否为Markdown代码块格式的JSON
                                            json_pattern = r'```(?:json)?\s*(.*?)\s*```'
                                            md_json_match = re.search(json_pattern, result, re.DOTALL)
                                            if md_json_match:
                                                # 如果匹配到Markdown代码块，提取其中的JSON内容
                                                json_content = md_json_match.group(1).strip()
                                                try:
                                                    result_dict = json.loads(json_content)
                                                    stats['success'] += 1
                                                    with open(raw_file, 'a', encoding='utf-8') as f:
                                                        json.dump(result_dict, f, ensure_ascii=False)
                                                        f.write('\n')
                                                    
                                                    if output_headers is None and result_dict:
                                                        output_headers = list(result_dict.keys())
                                                        if not output_file.exists():
                                                            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                                                                writer = csv.DictWriter(f, fieldnames=output_headers)
                                                                writer.writeheader()
                                                        
                                                    with open(output_file, 'a', encoding='utf-8-sig', newline='') as f:
                                                        writer = csv.DictWriter(f, fieldnames=output_headers)
                                                        writer.writerow(result_dict)
                                                    continue
                                                except json.JSONDecodeError as je:
                                                    Logger.error(f"解析Markdown代码块中的JSON失败: {str(je)}")
                                                    Logger.error(f"代码块内容: {json_content[:200]}...")
                                                    
                                                    # 记录错误
                                                    try:
                                                        error_data = {
                                                            "content": item['content'],
                                                            "error_type": "JSON解析错误",
                                                            "error_details": f"Markdown代码块中的JSON解析错误: {str(je)}"
                                                        }
                                                        with open(error_file, 'a', encoding='utf-8') as f:
                                                            if file_path.suffix.lower() == '.csv':
                                                                f.write(f"{item['content']},JSON解析错误\n")
                                                            else:
                                                                json.dump(error_data, f, ensure_ascii=False)
                                                                f.write('\n')
                                                    except Exception as e:
                                                        Logger.error(f"写入错误记录失败: {str(e)}")
                                                    
                                                    continue
                                            
                                            # 标准JSON解析
                                            try:
                                                result_dict = json.loads(result)
                                                if isinstance(result_dict, list):
                                                    result_dict = result_dict[0] if result_dict else {}
                                                
                                                if isinstance(result_dict, dict):
                                                    stats['success'] += 1
                                                    with open(raw_file, 'a', encoding='utf-8') as f:
                                                        json.dump(result_dict, f, ensure_ascii=False)
                                                        f.write('\n')
                                                    
                                                    if output_headers is None and result_dict:
                                                        output_headers = list(result_dict.keys())
                                                        if not output_file.exists():
                                                            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                                                                writer = csv.DictWriter(f, fieldnames=output_headers)
                                                                writer.writeheader()
                                                        
                                                    with open(output_file, 'a', encoding='utf-8-sig', newline='') as f:
                                                        writer = csv.DictWriter(f, fieldnames=output_headers)
                                                        writer.writerow(result_dict)
                                                    continue
                                            except json.JSONDecodeError as je:
                                                # JSON解析失败
                                                stats['json_error'] += 1
                                                Logger.error(f"JSON解析失败: {str(je)}")
                                                Logger.error(f"原始内容: {result[:200]}...")
                                                
                                                # 记录JSON解析错误
                                                try:
                                                    error_data = {
                                                        "content": item['content'],
                                                        "error_type": "JSON解析错误",
                                                        "error_details": f"标准JSON解析错误: {str(je)}"
                                                    }
                                                    with open(error_file, 'a', encoding='utf-8') as f:
                                                        if file_path.suffix.lower() == '.csv':
                                                            f.write(f"{item['content']},JSON解析错误\n")
                                                        else:
                                                            json.dump(error_data, f, ensure_ascii=False)
                                                            f.write('\n')
                                                except Exception as e:
                                                    Logger.error(f"写入错误记录失败: {str(e)}")
                                                
                                                continue
                                        except Exception as e:
                                            stats['other_error'] += 1
                                            Logger.error(f"处理结果时出错: {str(e)}")
                                            continue
                                except Exception as e:
                                    stats['other_error'] += 1
                                    Logger.error(f"处理结果时出错: {str(e)}")
                                    
                                    # 记录处理错误
                                    try:
                                        error_data = {
                                            "content": item['content'],
                                            "error_type": "处理错误",
                                            "error_details": str(e)
                                        }
                                        with open(error_file, 'a', encoding='utf-8') as f:
                                            if file_path.suffix.lower() == '.csv':
                                                f.write(f"{item['content']},处理错误\n")
                                            else:
                                                json.dump(error_data, f, ensure_ascii=False)
                                                f.write('\n')
                                    except Exception as write_e:
                                        Logger.error(f"写入错误记录失败: {str(write_e)}")
                                    
                                    continue
                        except Exception as outer_e:
                            # 添加外层异常捕获，确保单条记录处理失败不会影响整体
                            stats['other_error'] += 1
                            Logger.error(f"处理记录时发生未捕获的异常: {str(outer_e)}")
                            
                            # 记录未捕获的异常
                            try:
                                error_data = {
                                    "content": item['content'],
                                    "error_type": "未捕获异常",
                                    "error_details": str(outer_e)
                                }
                                with open(error_file, 'a', encoding='utf-8') as f:
                                    if file_path.suffix.lower() == '.csv':
                                        f.write(f"{item['content']},未捕获异常\n")
                                    else:
                                        json.dump(error_data, f, ensure_ascii=False)
                                        f.write('\n')
                            except Exception as write_e:
                                Logger.error(f"写入错误记录失败: {str(write_e)}")
                            
                            continue
                    
                    # 更新进度
                    current_pos += len(items)
                    if pbar:
                        pbar.update(len(items))
                    
                    # 每批次处理完成后更新进度文件
                    progress_data = {
                        'last_position': current_pos,
                        'last_update': datetime.datetime.now().isoformat(),
                        'stats': stats
                    }
                    with open(progress_file, 'w', encoding='utf-8') as f:
                        json.dump(progress_data, f, ensure_ascii=False, indent=2)
                    
                    # 每处理1000条记录输出一次统计信息
                    batch_count += len(items)
                    if batch_count >= 1000:
                        batch_count = 0
                        Logger.info(f"\n当前处理统计:\n总处理: {stats['total']}\n成功: {stats['success']}\nAPI错误: {stats['api_error']}\n空结果: {stats['empty_result']}\nJSON解析错误: {stats['json_error']}\n其他错误: {stats['other_error']}")
            finally:
                if pbar:
                    pbar.close()
        except Exception as e:
            stats['other_error'] += 1
            Logger.error(f"处理文件时出错: {str(e)}")
            # 添加返回，使得单个文件处理失败不会导致程序退出
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