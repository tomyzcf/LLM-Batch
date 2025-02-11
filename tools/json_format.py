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

def get_memory_usage():
    """获取当前进程的内存使用情况"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # 转换为MB

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
                
                pbar.update(pos - start)
                start = pos + 1
                
                # 定期进行垃圾回收
                if start % (10 * 1024 * 1024) == 0:  # 每10MB检查一次
                    gc.collect()
                    current_memory = get_memory_usage()
                    logger.debug(f"当前内存使用: {current_memory:.2f}MB")
                    
            except Exception as e:
                logger.error(f"处理过程中出错: {str(e)}")
                start += 1

def create_sample(input_file: str, output_file: str, sample_size: int = 1, batch_size: int = 100):
    """分批处理JSON对象并创建样本文件"""
    logger = setup_logging()
    logger.info(f"开始从 {input_file} 创建样本文件")
    
    file_size = os.path.getsize(input_file)
    
    # 使用内存映射读取文件
    with open(input_file, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        
        try:
            # 创建输出文件
            with open(output_file, 'w', encoding='utf-8') as out:
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
                    
                    # 定期清理内存
                    if processed_count % batch_size == 0:
                        gc.collect()
                        current_memory = get_memory_usage()
                        logger.info(f"已处理 {processed_count} 个对象，当前内存使用: {current_memory:.2f}MB")
                
                out.write('\n]')  # 结束JSON数组
                    
            logger.info(f"成功创建样本文件: {output_file}，包含 {processed_count} 个对象")
            
        finally:
            mm.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python json_format.py <input_file> <output_file> [sample_size] [batch_size]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    sample_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    batch_size = int(sys.argv[4]) if len(sys.argv) > 4 else 5000
    
    create_sample(input_file, output_file, sample_size, batch_size)