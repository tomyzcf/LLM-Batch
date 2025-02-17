#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path
import logging
from typing import Dict, Any, List, Generator
import mmap
import os
from tqdm import tqdm
import psutil
import gc

# 性能优化配置
MEMORY_CHECK_INTERVAL = 100 * 1024 * 1024  # 每处理100MB检查一次内存
MEMORY_THRESHOLD = 80  # 内存使用率警告阈值（百分数）
BATCH_SIZE = 10000  # 默认批处理大小
BUFFER_SIZE = 8192 * 1024  # 8MB文件缓冲区大小
GC_INTERVAL = 50 * 1024 * 1024  # 每处理50MB执行一次GC

def get_memory_usage():
    """获取当前进程的内存使用情况"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    # 获取系统总内存
    total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
    # 计算内存使用率
    memory_percent = (memory_info.rss / (total_memory * 1024 * 1024)) * 100
    return memory_info.rss / (1024 * 1024), memory_percent  # 返回使用量(MB)和使用率

def check_memory_usage(logger):
    """检查内存使用情况，如果超过阈值则发出警告"""
    memory_usage, memory_percent = get_memory_usage()
    if memory_percent > MEMORY_THRESHOLD:
        logger.warning(f"内存使用超过阈值: {memory_usage:.2f}MB ({memory_percent:.1f}%)")
    return memory_usage, memory_percent

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def flatten_json(obj: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """将嵌套的JSON对象拉平为单层结构"""
    items = {}
    
    for k, v in obj.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            # 检查是否是数字序列键的字典
            is_numbered_keys = all(k[-1].isdigit() for k in v.keys() if k)
            if is_numbered_keys:
                array_values = []
                # 按数字排序键
                sorted_keys = sorted(v.keys(), key=lambda x: int(''.join(filter(str.isdigit, x))))
                for sub_k in sorted_keys:
                    full_key = f"{new_key}.{sub_k}"
                    array_values.append(f'{full_key}-"{str(v[sub_k])}"')
                items[new_key] = ','.join(array_values)
            else:
                items.update(flatten_json(v, new_key))
        elif isinstance(v, list):
            if v:  # 只在列表非空时处理
                if all(isinstance(x, dict) for x in v):
                    array_values = []
                    for i, item in enumerate(v):
                        temp_dict = {f"{new_key}_{i}.{sub_k}": sub_v 
                                   for sub_k, sub_v in item.items()}
                        flattened = flatten_json(temp_dict)
                        item_str = ','.join(f'{k}-"{str(v)}"' for k, v in flattened.items())
                        array_values.append(item_str)
                    items[new_key] = '|'.join(array_values)
                elif all(isinstance(x, (str, int, float, bool)) for x in v):
                    items[new_key] = '|'.join(str(x) for x in v)
                else:
                    items[new_key] = json.dumps(v, ensure_ascii=False)
        else:
            items[new_key] = v
            
    return items

def find_json_objects(mm: mmap.mmap, file_size: int) -> Generator[Dict[str, Any], None, None]:
    """使用生成器模式逐个产出JSON对象"""
    start = 0
    logger = logging.getLogger(__name__)
    processed_bytes = 0
    
    with tqdm(total=file_size, desc="处理进度", unit='B', unit_scale=True) as pbar:
        while start < len(mm):
            try:
                # 查找下一个对象开始
                while start < len(mm):
                    if chr(mm[start]) == '{':
                        break
                    start += 1
                    
                if start >= len(mm):
                    break
                    
                # 解析JSON对象
                brace_count = 0
                pos = start
                in_string = False
                escape = False
                
                while pos < len(mm):
                    char = chr(mm[pos])
                    
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                try:
                                    json_str = mm[start:pos+1].decode('utf-8', errors='ignore')
                                    json_obj = json.loads(json_str)
                                    yield json_obj
                                    break
                                except json.JSONDecodeError:
                                    logger.warning(f"JSON解析错误，位置: {start}-{pos+1}")
                                except Exception as e:
                                    logger.warning(f"处理错误: {str(e)}")
                        elif char == '"':
                            in_string = True
                    else:
                        if char == '\\':
                            escape = not escape
                        elif char == '"' and not escape:
                            in_string = False
                        else:
                            escape = False
                            
                    pos += 1
                
                processed_bytes = pos - start
                pbar.update(processed_bytes)
                start = pos + 1
                
                # 定期检查内存使用情况
                if processed_bytes >= MEMORY_CHECK_INTERVAL:
                    check_memory_usage(logger)
                    processed_bytes = 0
                
                # 定期进行垃圾回收
                if processed_bytes >= GC_INTERVAL:
                    gc.collect()
                    processed_bytes = 0
                    
            except Exception as e:
                logger.error(f"处理过程中出错: {str(e)}")
                start += 1

def create_sample(input_file: str, output_file: str, sample_size: int = 1, batch_size: int = BATCH_SIZE):
    """分批处理JSON对象并创建样本文件"""
    logger = setup_logging()
    logger.info(f"开始从 {input_file} 创建样本文件")
    
    file_size = os.path.getsize(input_file)
    
    # 使用内存映射读取文件
    with open(input_file, 'rb', buffering=BUFFER_SIZE) as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        
        try:
            # 创建输出文件
            with open(output_file, 'w', encoding='utf-8', buffering=BUFFER_SIZE) as out:
                out.write('[\n')  # 开始JSON数组
                
                # 使用生成器逐个处理对象
                processed_count = 0
                for obj in find_json_objects(mm, file_size):
                    if processed_count >= sample_size:
                        break
                        
                    flattened_obj = flatten_json(obj)
                    
                    # 写入对象
                    if processed_count > 0:
                        out.write(',\n')
                    json.dump(flattened_obj, out, ensure_ascii=False, indent=2)
                    
                    processed_count += 1
                    
                    # 定期清理内存并检查使用情况
                    if processed_count % batch_size == 0:
                        gc.collect()
                        memory_usage, memory_percent = check_memory_usage(logger)
                        logger.info(f"已处理 {processed_count} 个对象，当前内存使用: {memory_usage:.2f}MB ({memory_percent:.1f}%)")
                
                out.write('\n]')  # 结束JSON数组
                    
            logger.info(f"成功创建样本文件: {output_file}，包含 {processed_count} 个对象")
            
        finally:
            mm.close()

def process_directory(input_path: str, output_path: str, sample_size: int = 1, batch_size: int = BATCH_SIZE):
    """处理目录下的所有JSON文件"""
    logger = setup_logging()
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # 确保输出目录存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    if input_path.is_file():
        # 如果输入是文件，直接处理
        if output_path.is_dir():
            output_file = output_path / f"{input_path.stem}_formatted.json"
        else:
            output_file = output_path
        create_sample(str(input_path), str(output_file), sample_size, batch_size)
    elif input_path.is_dir():
        # 如果输入是目录，处理所有JSON文件
        json_files = list(input_path.glob("*.json"))
        logger.info(f"在目录 {input_path} 中找到 {len(json_files)} 个JSON文件")
        
        for json_file in json_files:
            output_file = output_path / f"{json_file.stem}_formatted.json"
            logger.info(f"处理文件: {json_file}")
            create_sample(str(json_file), str(output_file), sample_size, batch_size)
    else:
        logger.error(f"输入路径 {input_path} 不存在")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python json_format.py <input_path> <output_path> [sample_size] [batch_size]")
        print("input_path 可以是单个JSON文件或包含JSON文件的目录")
        print("output_path 可以是输出文件或输出目录")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    sample_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    batch_size = int(sys.argv[4]) if len(sys.argv) > 4 else BATCH_SIZE
    
    process_directory(input_path, output_path, sample_size, batch_size)