# -*- coding: utf-8 -*-
import os
import json
import asyncio
from aiohttp import ClientSession
from tqdm import tqdm
import csv
import pandas as pd
from pathlib import Path
import argparse
import psutil
import datetime
import logging
import sys
from typing import Optional

class Logger:
    """日志工具类"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """设置日志配置"""
        self.logger = logging.getLogger('BatchProcessor')
        self.logger.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '\n%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # 文件处理器
        file_handler = logging.FileHandler('batch_process.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    @staticmethod
    def info(msg: str):
        Logger().logger.info(msg)
    
    @staticmethod
    def error(msg: str):
        Logger().logger.error(msg)
    
    @staticmethod
    def warning(msg: str):
        Logger().logger.warning(msg)
    
    @staticmethod
    def debug(msg: str):
        Logger().logger.debug(msg)

class Config:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.input_dir = self.root_dir / 'inputData'
        self.output_dir = self.root_dir / 'outputData'
        self.prompts_dir = self.root_dir / 'prompts'
        
        # 确保必要目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        # API配置
        self.deepseek_api_url = 'https://api.deepseek.com'
        self.deepseek_model = 'deepseek-chat'
        self.deepseek_api_key = "sk-4c5fa5086965449bbce91f3a0cd94d03"
        
        # 模型配置
        self.max_input_tokens = 64000  # DeepSeek模型的最大输入token限制
        
        # 失败记录相关配置
        self.failed_output_suffix = "_failed"  # 失败数据文件后缀

        # 性能配置
        self.batch_size = 5  # 每批处理5条数据
        self.max_retries = 5
        self.concurrent_tasks = 10  # 同时处理n个请求
        self.sleep_time = 0.5
        self.max_memory_percent = 80
        self.temperature = 0.7

def estimate_tokens(text: str) -> int:
    """简单估算token数量，使用字符数/3作为近似值"""
    return len(text) // 3

def check_input_length(system_prompt: str, user_input: str) -> tuple[bool, int]:
    """使用简单方法检查输入是否可能超出token限制"""
    # 使用字符数/3作为token数的粗略估计
    estimated_tokens = estimate_tokens(system_prompt) + estimate_tokens(user_input)
    return estimated_tokens <= Config().max_input_tokens, estimated_tokens

class OutputManager:
    """处理不同格式的输出"""
    
    def __init__(self, input_path: Path, output_dir: Path, output_name: str = None):
        # 构建输出路径，保持与输入路径相同的目录结构
        if input_path.is_dir():
            # 如果输入是目录，在输出目录中创建相同的目录结构
            rel_path = input_path.relative_to(Config().input_dir) if input_path.is_relative_to(Config().input_dir) else input_path.name
            self.output_subdir = output_dir / rel_path
        else:
            # 如果是单个文件，使用原来的逻辑
            rel_path = input_path.relative_to(Config().input_dir) if input_path.is_relative_to(Config().input_dir) else input_path.name
            self.output_subdir = output_dir / rel_path.parent
        
        self.output_subdir.mkdir(parents=True, exist_ok=True)
        self.input_path = input_path
        
        # 更新字段定义
        self.fields = [
            "判决书编号",
            "法院所在地区",
            "法院类型",
            "原告名称",
            "原告注册地",
            "被告名称",
            "被告注册地",
            "判决结果",
            "胜诉方",
            "判决依据条款数目",
            "判断案件受理费金额",
            "处理状态",
            "失败原因"
        ]
        
        # 初始化计数器
        self.processed_count = 0
        self.failed_count = 0
        self.current_file = None
        self.progress_data = {}
        
        # 初始化锁
        self.write_lock = asyncio.Lock()
        
        self.load_progress()
    
    def get_file_output_paths(self, file_path: Path):
        """获取单个文件的输出路径"""
        base_name = file_path.stem
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 查找该文件的最新进度文件
        existing_progress_files = list(self.output_subdir.glob(f"{base_name}_output_*_progress.json"))
        
        if existing_progress_files:
            latest_progress_file = max(existing_progress_files, key=lambda x: x.stat().st_mtime)
            timestamp = latest_progress_file.stem.split('_output_')[1].rsplit('_', 1)[0]
        
        file_prefix = f"{base_name}_output_{timestamp}"
        failed_prefix = f"{base_name}_output_{timestamp}{Config().failed_output_suffix}"
        
        return {
            'output': self.output_subdir / f"{file_prefix}.csv",
            'raw': self.output_subdir / f"{file_prefix}_raw.jsonl",
            'progress': self.output_subdir / f"{file_prefix}_progress.json",
            'failed': self.output_subdir / f"{failed_prefix}.csv",
            'failed_raw': self.output_subdir / f"{failed_prefix}_raw.jsonl"
        }
    
    def initialize_file(self, file_path: Path):
        """初始化单个文件的输出"""
        paths = self.get_file_output_paths(file_path)
        
        # 如果文件已存在且有进度，则不需要初始化
        if paths['progress'].exists():
            return paths
        
        # 初始化输出文件
        with open(paths['output'], 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            writer.writeheader()
        
        # 初始化原始输出文件
        with open(paths['raw'], 'w', encoding='utf-8') as f:
            pass
            
        # 初始化失败数据文件
        with open(paths['failed'], 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            writer.writeheader()
            
        with open(paths['failed_raw'], 'w', encoding='utf-8') as f:
            pass
        
        # 初始化进度文件
        self.save_file_progress(paths['progress'], 0)
        
        return paths
    
    def load_progress(self):
        """加载总体进度"""
        if self.input_path.is_dir():
            progress_file = self.output_subdir / "directory_progress.json"
            if progress_file.exists():
                try:
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        self.progress_data = json.load(f)
                except Exception as e:
                    print(f"加载目录进度文件失败: {e}")
                    self.progress_data = {}
    
    def save_progress(self):
        """保存总体进度"""
        if self.input_path.is_dir():
            progress_file = self.output_subdir / "directory_progress.json"
            try:
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存目录进度文件失败: {e}")
    
    def get_file_progress(self, file_path: Path) -> int:
        """获取单个文件的处理进度"""
        paths = self.get_file_output_paths(file_path)
        if paths['progress'].exists():
            try:
                with open(paths['progress'], 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                return progress.get('processed_count', 0)
            except Exception as e:
                print(f"加载文件进度失败: {e}")
        return 0
    
    def save_file_progress(self, progress_path: Path, count: int):
        """保存单个文件的处理进度"""
        try:
            with open(progress_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'processed_count': count,
                    'last_update': datetime.datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存文件进度失败: {e}")
    
    async def write_failed_result(self, result: dict, raw_response: str, error_type: str, error_message: str, lock: asyncio.Lock = None):
        """写入失败的处理结果"""
        if not self.current_file:
            return
            
        paths = self.get_file_output_paths(self.current_file)
        
        async with self.write_lock:
            try:
                # 准备写入的数据
                failed_result = {}
                
                # 保存原始输入数据
                if isinstance(result, dict):
                    if 'content' in result:
                        content = result['content']
                        failed_result = {
                            "原始内容": content,
                            "处理状态": "失败",
                            "失败原因": f"{error_type}: {error_message}"
                        }
                    else:
                        failed_result = result.copy()
                        failed_result["处理状态"] = "失败"
                        failed_result["失败原因"] = f"{error_type}: {error_message}"
                else:
                    failed_result = {
                        "原始内容": str(result),
                        "处理状态": "失败", 
                        "失败原因": f"{error_type}: {error_message}"
                    }
                
                # 写入失败数据CSV
                with open(paths['failed'], 'a', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=self.fields + ["原始内容"])
                    writer.writerow(failed_result)
                
                # 写入原始响应
                with open(paths['failed_raw'], 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.datetime.now().isoformat(),
                        'raw_response': raw_response,
                        'error_type': error_type,
                        'error_message': error_message,
                        'input_content': result.get('content', '') if isinstance(result, dict) else str(result)
                    }, ensure_ascii=False) + '\n')
                
                self.failed_count += 1
                
                # 添加错误日志
                Logger.error(f"处理失败 [{error_type}] - {error_message}")
                
            except Exception as e:
                Logger.error(f"写入失败数据时出错: {str(e)}")
                Logger.debug(f"原始结果: {result}")
    
    async def write_result(self, result: dict, raw_response: str, lock: asyncio.Lock = None):
        """写入处理结果"""
        if not self.current_file:
            return
        
        paths = self.get_file_output_paths(self.current_file)
        
        async with self.write_lock:  # 使用类的锁而不是传入的锁
            try:
                # 写入处理后的结果
                result["处理状态"] = "成功"
                result["失败原因"] = ""
                
                # 确保所有字段都存在
                for field in self.fields:
                    if field not in result:
                        result[field] = 'NA'
                
                # 追加模式写入
                with open(paths['output'], 'a', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=self.fields)
                    writer.writerow(result)
                
                # 追加模式写入原始响应
                with open(paths['raw'], 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.datetime.now().isoformat(),
                        'raw_response': raw_response,
                        'processed_result': result,
                        'input_content': result.get('content', '')
                    }, ensure_ascii=False) + '\n')
                
                # 更新进度
                self.processed_count += 1
                if self.processed_count % 10 == 0:  # 每处理10条保存一次进度
                    self.save_file_progress(paths['progress'], self.processed_count)
                    
                # 更新目录进度
                if self.input_path.is_dir():
                    self.progress_data[str(self.current_file)] = self.processed_count
                    if self.processed_count % 10 == 0:
                        self.save_progress()
            
            except Exception as e:
                print(f"写入结果时出错: {str(e)}")
                print(f"原始结果: {result}")

class FileProcessor:
    """处理不同类型的输入文件"""
    
    @staticmethod
    def get_input_files(input_path: Path) -> list:
        """获取输入目录下的所有支持的文件"""
        if input_path.is_dir():
            files = []
            for ext in ['.csv', '.json', '.xlsx', '.xls']:
                files.extend(input_path.glob(f'*{ext}'))
            return sorted(files)
        else:
            return [input_path] if input_path.suffix.lower() in ['.csv', '.json', '.xlsx', '.xls'] else []
    
    @staticmethod
    def read_file_batch(file_path: Path, start_pos: int, batch_size: int, selected_fields: list = None):
        """读取文件的一个批次数据"""
        ext = file_path.suffix.lower()
        if ext == '.json':
            return FileProcessor._read_json_batch(file_path, start_pos, batch_size, selected_fields)
        elif ext == '.csv':
            return FileProcessor._read_csv_batch(file_path, start_pos, batch_size, selected_fields)
        elif ext in ['.xlsx', '.xls']:
            return FileProcessor._read_excel_batch(file_path, start_pos, batch_size, selected_fields)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    @staticmethod
    def get_file_total_rows(file_path: Path) -> int:
        """获取文件的总行数"""
        ext = file_path.suffix.lower()
        try:
            if ext == '.json':
                count = 0
                with open(file_path, 'r', encoding='utf-8') as f:
                    for _ in f:
                        count += 1
                return count
            elif ext == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return sum(1 for _ in f) - 1  # 减去标题行
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                return len(df)
        except Exception as e:
            print(f"获取文件行数失败: {str(e)}")
            return 0
        return 0
    
    @staticmethod
    def _read_json_batch(file_path: Path, start_pos: int, batch_size: int, fields=None):
        """分批读取JSON文件"""
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            # 跳过之前的行
            for _ in range(start_pos):
                next(f, None)
            
            # 读取指定数量的行
            count = 0
            for line in f:
                if count >= batch_size:
                    break
                try:
                    item = json.loads(line.strip())
                    items.append(FileProcessor._process_row(item, fields))
                    count += 1
                except json.JSONDecodeError:
                    continue
        return items
    
    @staticmethod
    def _read_csv_batch(file_path: Path, start_pos: int, batch_size: int, fields=None):
        """分批读取CSV文件"""
        try:
            # 尝试不同的编码方式
            encodings = ['utf-8-sig', 'gbk', 'gb18030']
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, skiprows=range(1, start_pos + 1), nrows=batch_size)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("无法使用支持的编码读取文件")
            
            # 如果指定了字段，只选择这些字段
            if fields is not None:
                valid_fields = [i for i in fields if i < len(df.columns)]
                if len(valid_fields) != len(fields):
                    print("警告: 部分字段索引超出范围，将被忽略")
                selected_columns = df.iloc[:, valid_fields]
                return [FileProcessor._process_row(row) for _, row in selected_columns.iterrows()]
            
            return [FileProcessor._process_row(row) for _, row in df.iterrows()]
        except Exception as e:
            print(f"读取CSV文件失败: {str(e)}")
            return []
    
    @staticmethod
    def _read_excel_batch(file_path: Path, start_pos: int, batch_size: int, fields=None):
        """分批读取Excel文件"""
        try:
            df = pd.read_excel(file_path, skiprows=range(1, start_pos + 1), nrows=batch_size)
            if fields is not None:
                valid_fields = [i for i in fields if i < len(df.columns)]
                if len(valid_fields) != len(fields):
                    print("警告: 部分字段索引超出范围，将被忽略")
                selected_columns = df.iloc[:, valid_fields]
                return [FileProcessor._process_row(row) for _, row in selected_columns.iterrows()]
            
            return [FileProcessor._process_row(row) for _, row in df.iterrows()]
        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")
            return []
    
    @staticmethod
    def _process_row(row, field_indices=None):
        """处理单行数据，将所有字段组合成文本"""
        if isinstance(row, pd.Series):
            values = row.values.tolist()
        elif isinstance(row, dict):
            values = list(row.values())
        elif isinstance(row, (list, tuple)):
            values = row
        else:
            values = [row]
        
        # 将所有非空字段值组合成一个文本字符串，处理可能的编码问题
        text = ' '.join(str(v).strip() for v in values if pd.notna(v) and str(v).strip())
        return {"content": text}

async def create_session():
    return ClientSession(
        headers={
            "Authorization": f"Bearer {Config().deepseek_api_key}",
            "Content-Type": "application/json"
        }
    )

async def deepseek_request_async(session, content, item, semaphore, config):
    """处理单个请求，包含完整的错误处理"""
    async with semaphore:
        # 检查输入token长度
        is_within_limit, total_tokens = check_input_length(content, item["content"])
        if not is_within_limit:
            Logger.warning(f"Token超限 ({total_tokens} > {config.max_input_tokens})")
            return None, {
                "error_type": "TokenLimitExceeded",
                "error_message": f"输入token数({total_tokens})超出限制({config.max_input_tokens})"
            }
        
        for attempt in range(config.max_retries):
            try:
                data = {
                    "model": config.deepseek_model,
                    "messages": [
                        {"role": "system", "content": content},
                        {"role": "user", "content": item["content"]}
                    ],
                    "temperature": config.temperature,
                    "stream": False
                }
                
                if attempt > 0:
                    Logger.info(f"第{attempt + 1}次重试请求API...")
                
                async with session.post(f"{config.deepseek_api_url}/v1/chat/completions", json=data) as response:
                    try:
                        if response.status != 200:
                            error_body = await response.text()
                            Logger.error(f"API请求失败 [状态码:{response.status}] - {error_body}")
                            if attempt < config.max_retries - 1:
                                await asyncio.sleep(min(2 ** attempt * config.sleep_time, 10))
                                continue
                            return None, {
                                "error_type": "APIError",
                                "error_message": f"状态码: {response.status}, 响应: {error_body}"
                            }
                        
                        response_json = await response.json()
                        if not response_json:
                            Logger.error("API返回空响应")
                            if attempt < config.max_retries - 1:
                                await asyncio.sleep(min(2 ** attempt * config.sleep_time, 10))
                                continue
                            return None, {
                                "error_type": "EmptyResponse",
                                "error_message": "API返回空响应"
                            }
                            
                        parsed_result, raw_response = await parse_llm_response(response_json)
                        
                        if parsed_result is None:
                            Logger.error(f"解析响应失败: {raw_response}")
                            if attempt < config.max_retries - 1:
                                await asyncio.sleep(min(2 ** attempt * config.sleep_time, 10))
                                continue
                            return None, {
                                "error_type": "ParseError",
                                "error_message": f"解析响应失败: {raw_response}"
                            }
                        
                        Logger.info("请求处理成功")
                        return parsed_result, raw_response
                        
                    except json.JSONDecodeError as e:
                        Logger.error(f"JSON解析错误: {str(e)}")
                        if attempt < config.max_retries - 1:
                            await asyncio.sleep(min(2 ** attempt * config.sleep_time, 10))
                            continue
                        return None, {
                            "error_type": "JSONDecodeError",
                            "error_message": f"响应解析失败: {await response.text()}"
                        }
                        
            except Exception as e:
                Logger.error(f"请求异常: {str(e)}")
                if attempt < config.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt * config.sleep_time, 10))
                    continue
                return None, {
                    "error_type": "RequestError",
                    "error_message": str(e)
                }

async def parse_llm_response(response):
    """解析LLM响应，确保返回正确的JSON格式"""
    try:
        if not response or 'choices' not in response:
            return None, {
                "error_type": "InvalidResponse",
                "error_message": f"无效的响应: {str(response)}"
            }
            
        content = response['choices'][0]['message']['content']
        if not content:
            return None, {
                "error_type": "EmptyContent",
                "error_message": "响应内容为空"
            }
            
        # 尝试直接解析JSON
        try:
            result = json.loads(content)
            # 验证必要字段
            required_fields = [
                "法院所在地区", "法院类型", "原告名称", "原告注册地",
                "被告名称", "被告注册地", "判决结果", "胜诉方",
                "判决依据条款数目", "判断案件受理费金额"
            ]
            
            if not all(field in result for field in required_fields):
                missing_fields = [f for f in required_fields if f not in result]
                return None, {
                    "error_type": "MissingFields",
                    "error_message": f"缺少必要字段: {missing_fields}"
                }
                
            # 验证判决结果的值
            valid_results = ["支持", "驳回", "部分支持", "调解结案", "中止审理"]
            if result["判决结果"] not in valid_results:
                return None, {
                    "error_type": "InvalidJudgmentResult",
                    "error_message": f"判决结果'{result['判决结果']}'不在允许的值列表中"
                }
                
            return result, content
            
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}')
            if json_start != -1 and json_end != -1:
                try:
                    json_str = content[json_start:json_end + 1]
                    result = json.loads(json_str)
                    return result, content
                except:
                    return None, {
                        "error_type": "JSONParseError",
                        "error_message": f"JSON解析失败: {content}"
                    }
            else:
                return None, {
                    "error_type": "NoJSONFound",
                    "error_message": f"响应中未找到JSON: {content}"
                }
                
    except Exception as e:
        return None, {
            "error_type": "UnexpectedError",
            "error_message": f"解析响应时发生错误: {str(e)}"
        }

async def process_batch_async(session, items, output_manager, prompt_content, pbar, semaphore, config):
    """处理一批数据"""
    tasks = []
    for item in items:
        task = deepseek_request_async(session, prompt_content, item, semaphore, config)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for item, result in zip(items, results):
        if isinstance(result, Exception):
            print(f"处理项目失败: {str(result)}")
            await output_manager.write_failed_result(
                item, str(result), 
                "UnexpectedError", str(result), 
                None  # 不再传入锁
            )
            pbar.update(1)
            continue
            
        if result:
            parsed_result, response_info = result
            if parsed_result is None:
                if isinstance(response_info, dict):
                    await output_manager.write_failed_result(
                        item, str(response_info),
                        response_info["error_type"],
                        response_info["error_message"],
                        None  # 不再传入锁
                    )
                else:
                    await output_manager.write_failed_result(
                        item, str(response_info),
                        "UnknownError", str(response_info),
                        None  # 不再传入锁
                    )
            else:
                await output_manager.write_result(parsed_result, response_info, None)  # 不再传入锁
        pbar.update(1)

def print_usage_guide():
    """打印详细的使用指南"""
    guide = """
批量数据处理脚本使用指南
======================

功能描述：
--------
本脚本用于批量处理法律文书数据，支持JSON、CSV、Excel格式的输入和输出。
可以选择性处理指定字段，支持断点续处理。

基本用法：
--------
python llm_batch_call.py <input_path> <prompt_file> [options]

参数说明：
--------
必选参数：
  input_path    输入文件或目录的路径
  prompt_file   提示词文件的路径

可选参数：
  --output-format {json,csv,excel}  
                输出文件格式，默认为csv
  --fields SELECTION               
                要处理的输入字段，支持以下格式：
                - all: 所有字段（默认）
                - 1-5: 第1到第5个字段
                - 1,2,3,6: 指定的字段位置
                注意：字段位置从1开始计数
  --output-name NAME                
                输出文件名（不含扩展名），默认为'output'
  --start-pos N                     
                开始处理的位置（从1开始），默认为1
  --end-pos N                       
                结束处理的位置（包含），默认处理到末尾
  --help                            
                显示此使用指南

使用示例：
--------
1. 基本使用：
   python llm_batch_call.py input.csv prompt.txt

2. 处理特定字段：
   # 处理第1、2、5个字段
   python llm_batch_call.py input.csv prompt.txt --fields 1,2,5

   # 处理第1到第5个字段
   python llm_batch_call.py input.csv prompt.txt --fields 1-5

3. 处理指定范围的数据：
   python llm_batch_call.py input.csv prompt.txt --start-pos 1 --end-pos 100

4. 完整示例：
   python llm_batch_call.py input.csv prompt.txt --fields 1,2,3 --output-name result --start-pos 1 --end-pos 100

注意事项：
--------
1. 支持的输入格式：json, csv, xlsx, xls
2. 所有的位置计数（包括字段位置和数据位置）都从1开始
3. 大数据量处理时建议使用断点续处理功能
4. 输出文件默认保存在outputData目录下
"""
    print(guide)

async def main():
    parser = argparse.ArgumentParser(description='批量处理数据脚本', add_help=False)
    
    # 添加help参数
    parser.add_argument('--help', '-h', action='store_true', 
                       help='显示详细使用指南')
    
    # 必选参数
    parser.add_argument('input_path', type=str, nargs='?',
                       help='输入文件或目录的路径')
    parser.add_argument('prompt_file', type=str, nargs='?',
                       help='提示词文件路径')
    
    # 可选参数
    parser.add_argument('--output-format', type=str, 
                       choices=['json', 'csv', 'excel'], 
                       default='csv', help='输出格式')
    parser.add_argument('--fields', type=str, default='all',
                       help='要处理的输入字段，支持以下格式：\n- all: 所有字段（默认）\n- 1-5: 第1到第5个字段\n- 1,2,3,6: 指定的字段位置\n注意：字段位置从1开始计数')
    parser.add_argument('--output-name', type=str,
                       default='output', help='输出文件名（不含扩展名）')
    parser.add_argument('--start-pos', type=int,
                       default=1, help='开始处理的位置（从1开始）')
    parser.add_argument('--end-pos', type=int,
                       default=None, help='结束处理的位置（包含）')
    
    args = parser.parse_args()
    
    # 如果指定了help，显示使用指南并退出
    if args.help:
        print_usage_guide()
        return
    
    # 检查必要参数
    if not args.input_path or not args.prompt_file:
        parser.print_help()
        return
    
    config = Config()
    input_path = Path(args.input_path)
    prompt_path = Path(args.prompt_file)
    
    if not prompt_path.exists():
        print(f"提示词文件不存在: {prompt_path}")
        return
        
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    # 获取需要处理的文件列表
    input_files = FileProcessor.get_input_files(input_path)
    if not input_files:
        print("未找到支持的输入文件")
        return
    
    # 设置输出管理器
    output_manager = OutputManager(input_path, config.output_dir, args.output_name)
    
    try:
        async with await create_session() as session:
            semaphore = asyncio.Semaphore(config.concurrent_tasks)
            
            # 逐个处理文件
            for file_path in input_files:
                Logger.info(f"\n开始处理文件: {file_path}")
                
                # 获取文件总行数
                total_rows = FileProcessor.get_file_total_rows(file_path)
                if total_rows == 0:
                    Logger.warning(f"文件 {file_path} 为空或无法读取，跳过处理")
                    continue
                
                # 初始化文件输出
                output_manager.initialize_file(file_path)
                output_manager.current_file = file_path
                
                # 获取文件的处理进度
                processed_count = output_manager.get_file_progress(file_path)
                start_pos = processed_count if processed_count > 0 else max(0, args.start_pos - 1)
                end_pos = min(total_rows, args.end_pos) if args.end_pos is not None else total_rows
                
                if start_pos >= end_pos:
                    Logger.info(f"文件 {file_path} 已处理完成，跳过")
                    continue
                
                output_manager.processed_count = processed_count
                total_items = end_pos - start_pos
                
                Logger.info(f"将处理从第 {start_pos + 1} 到第 {end_pos} 行，共 {total_items} 行")
                
                with tqdm(total=total_items, desc="处理进度", ncols=100) as pbar:
                    current_pos = start_pos
                    while current_pos < end_pos:
                        # 检查内存使用情况
                        if psutil.virtual_memory().percent > config.max_memory_percent:
                            Logger.warning("内存使用率过高，等待1秒...")
                            await asyncio.sleep(1)
                            continue
                        
                        # 计算本批次要处理的数量
                        batch_size = min(config.batch_size, end_pos - current_pos)
                        
                        # 读取一批数据
                        if args.fields and args.fields != 'all':
                            try:
                                field_indices = [int(f) - 1 for f in args.fields.split(',')]
                                items = FileProcessor.read_file_batch(file_path, current_pos, batch_size, field_indices)
                            except ValueError:
                                print("字段参数格式错误，应为逗号分隔的数字")
                                return
                        else:
                            items = FileProcessor.read_file_batch(file_path, current_pos, batch_size, None)
                        
                        if not items:
                            break
                        
                        # 处理这一批数据
                        await process_batch_async(session, items, output_manager, 
                                               prompt_content, pbar, semaphore, config)
                        
                        current_pos += len(items)
                
                # 保存最终进度
                output_manager.save_file_progress(output_manager.get_file_output_paths(file_path)['progress'], 
                                               output_manager.processed_count)
            
            # 保存总体进度
            output_manager.save_progress()
            Logger.info("\n所有文件处理完成！")
    
    except KeyboardInterrupt:
        Logger.warning("\n检测到中断，保存进度...")
        if output_manager.current_file:
            output_manager.save_file_progress(
                output_manager.get_file_output_paths(output_manager.current_file)['progress'],
                output_manager.processed_count
            )
        output_manager.save_progress()
        Logger.info(f"已处理到文件 {output_manager.current_file}，行数：{output_manager.processed_count}")
        return

if __name__ == '__main__':
    asyncio.run(main())