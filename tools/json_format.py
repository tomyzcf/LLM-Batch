#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path
import logging
from typing import Dict, Any, List
import mmap
import os
from tqdm import tqdm

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
            # 处理列表中的字典对象
            if all(isinstance(x, dict) for x in v):
                array_values = []
                for i, item in enumerate(v):
                    # 为每个字典创建一个临时键
                    temp_dict = {}
                    for sub_k, sub_v in item.items():
                        temp_key = f"{new_key}_{i}.{sub_k}"
                        temp_dict[temp_key] = sub_v
                    # 递归处理字典
                    flattened = flatten_json(temp_dict)
                    # 将展平后的键值对转换为字符串
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

def find_json_objects(mm: mmap.mmap, sample_size: int, file_size: int) -> List[Dict[str, Any]]:
    """使用内存映射快速查找JSON对象"""
    objects = []
    start = 0
    
    with tqdm(total=file_size, desc="处理进度", unit='B', unit_scale=True) as pbar:
        while len(objects) < sample_size:
            last_pos = start
            # 查找下一个对象开始
            while start < len(mm):
                if chr(mm[start]) == '{':
                    break
                start += 1
                
            if start >= len(mm):
                pbar.update(start - last_pos)
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
                            # 找到完整的JSON对象
                            try:
                                json_str = mm[start:pos+1].decode('utf-8', errors='ignore')
                                json_obj = json.loads(json_str)
                                objects.append(json_obj)
                                break
                            except:
                                pass
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
            
            pbar.update(pos - last_pos)
            start = pos + 1
        
    return objects

def create_sample(input_file: str, output_file: str, sample_size: int = 1):
    """从大文件中提取指定数量的JSON对象创建样本文件"""
    logger = setup_logging()
    logger.info(f"开始从 {input_file} 创建样本文件")
    
    file_size = os.path.getsize(input_file)
    
    # 使用内存映射读取文件
    with open(input_file, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        
        try:
            # 查找JSON对象
            sample_objects = find_json_objects(mm, sample_size, file_size)
            
            if not sample_objects:
                logger.error("未能找到有效的JSON对象")
                return
            
            logger.info("开始拉平JSON对象...")
            # 拉平JSON对象
            flattened_objects = []
            for obj in tqdm(sample_objects, desc="拉平进度"):
                flattened_objects.append(flatten_json(obj))
            
            # 写入结果
            logger.info("写入结果文件...")
            with open(output_file, 'w', encoding='utf-8') as out:
                if len(flattened_objects) == 1:
                    json.dump(flattened_objects[0], out, ensure_ascii=False, indent=2)
                else:
                    json.dump(flattened_objects, out, ensure_ascii=False, indent=2)
                    
            logger.info(f"成功创建样本文件: {output_file}，包含 {len(flattened_objects)} 个对象")
            
        finally:
            mm.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python json_format.py <input_file> <output_file> [sample_size]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    sample_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    create_sample(input_file, output_file, sample_size)