#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path
import logging
from typing import Dict, Any, List
import mmap
import os

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
            items.update(flatten_json(v, new_key))
        elif isinstance(v, list):
            if all(isinstance(x, (str, int, float, bool)) for x in v):
                items[new_key] = '|'.join(str(x) for x in v)
            elif all(isinstance(x, dict) for x in v):
                for i, item in enumerate(v):
                    items.update(flatten_json(item, f"{new_key}_{i}"))
            else:
                items[new_key] = json.dumps(v, ensure_ascii=False)
        else:
            items[new_key] = v
    return items

def find_json_objects(mm: mmap.mmap, sample_size: int) -> List[Dict[str, Any]]:
    """使用内存映射快速查找JSON对象"""
    objects = []
    start = 0
    
    while len(objects) < sample_size:
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
            
        start = pos + 1
        
    return objects

def create_sample(input_file: str, output_file: str, sample_size: int = 1):
    """从大文件中提取指定数量的JSON对象创建样本文件"""
    logger = setup_logging()
    logger.info(f"开始从 {input_file} 创建样本文件")
    
    # 使用内存映射读取文件
    with open(input_file, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        
        try:
            # 查找JSON对象
            sample_objects = find_json_objects(mm, sample_size)
            
            if not sample_objects:
                logger.error("未能找到有效的JSON对象")
                return
                
            # 拉平JSON对象
            flattened_objects = [flatten_json(obj) for obj in sample_objects]
            
            # 写入结果
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
        print("用法: python create_sample.py <input_file> <output_file> [sample_size]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    sample_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    create_sample(input_file, output_file, sample_size)