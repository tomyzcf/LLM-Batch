#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import csv
import argparse
import logging
import codecs
import re
from pathlib import Path
from typing import Dict, List, Any, Generator, TextIO, Set, Union, Optional
import html
import chardet
from bs4 import BeautifulSoup
import ijson  # 用于流式解析JSON
from tqdm import tqdm  # 用于显示进度条
import os
import gc
import threading
from queue import Queue
import time
import sys
import psutil
import random
import pandas as pd  # 用于处理Excel和Parquet文件
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np

# 定义全局变量
MEMORY_CHECK_INTERVAL = 100 * 1024 * 1024  # 每处理100MB检查一次内存
MEMORY_THRESHOLD = 80  # 内存使用率警告阈值（百分数）
BATCH_SIZE = 10000  # 默认批处理大小
BUFFER_SIZE = 8192 * 1024  # 8MB文件缓冲区大小
GC_INTERVAL = 50 * 1024 * 1024  # 每处理50MB执行一次GC

# 支持的文件格式
SUPPORTED_FORMATS = {
    'json': ['.json'],
    'csv': ['.csv', '.tsv'],
    'excel': ['.xlsx', '.xls'],
    'parquet': ['.parquet']
}

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def detect_format(file_path: str) -> str:
    """
    根据文件扩展名检测文件格式
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    for format_name, extensions in SUPPORTED_FORMATS.items():
        if extension in extensions:
            return format_name
    
    raise ValueError(f"不支持的文件格式: {extension}。支持的格式: {', '.join([ext for exts in SUPPORTED_FORMATS.values() for ext in exts])}")

def detect_and_fix_encoding(content: str) -> str:
    """
    检测并修复编码问题
    """
    # 首先尝试UTF-8
    try:
        if isinstance(content, bytes):
            return content.decode('utf-8')
        return content
    except UnicodeDecodeError:
        # 尝试其他编码
        encodings = ['gb18030', 'gbk', 'gb2312', 'big5']
        for encoding in encodings:
            try:
                if isinstance(content, bytes):
                    return content.decode(encoding)
                return content
            except UnicodeDecodeError:
                continue
    
    # 如果所有编码都失败，使用errors='ignore'选项
    if isinstance(content, bytes):
        return content.decode('utf-8', errors='ignore')
    return content

def try_different_encodings(file_path: str) -> tuple:
    """
    尝试不同的编码方式读取文件
    """
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                return content, encoding
        except UnicodeDecodeError:
            continue
    
    # 如果所有编码都失败，尝试使用chardet检测
    with open(file_path, 'rb') as f:
        raw_data = f.read(1024 * 1024)  # 读取前1MB用于检测
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                return content, encoding
        except:
            raise UnicodeDecodeError(f"无法使用以下编码读取文件: {encodings + [encoding]}")

def get_memory_usage():
    """获取当前进程的内存使用情况"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    # 获取系统总内存
    total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
    # 计算内存使用率
    memory_percent = (memory_info.rss / (total_memory * 1024 * 1024)) * 100
    return memory_info.rss / (1024 * 1024), memory_percent  # 返回使用量(MB)和使用率

def check_memory_usage():
    """检查内存使用情况，如果超过阈值则发出警告"""
    memory_usage, memory_percent = get_memory_usage()
    if memory_percent > MEMORY_THRESHOLD:
        logger.warning(f"内存使用超过阈值: {memory_usage:.2f}MB ({memory_percent:.1f}%)")
    return memory_usage, memory_percent

def flatten_json(data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """将嵌套的JSON结构展平为单层字典"""
    items: List = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            # 处理嵌套字典
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if len(v) > 0:
                if isinstance(v[0], dict):
                    # 如果是字典列表，展平每个字典
                    flattened_list = []
                    for item in v:
                        flattened_list.append(flatten_json(item, new_key, sep=sep))
                    # 合并所有展平后的字典
                    merged_dict = {}
                    for d in flattened_list:
                        merged_dict.update(d)
                    items.extend(merged_dict.items())
                else:
                    items.append((new_key, ';'.join(str(x) for x in v)))
        else:
            items.append((new_key, v))
    return dict(items)

def clean_text(text: str) -> str:
    """清理文本内容"""
    if not text or not isinstance(text, str):
        return ''
    # 1. 替换换行符和多余空白
    text = re.sub(r'\s+', ' ', text.strip())
    # 2. 处理特殊字符
    text = text.replace('"', '"').replace('"', '"')  # 统一引号
    text = text.replace('，', ',')  # 统一逗号
    text = text.replace('、', ';')  # 统一分隔符
    text = text.replace('；', ';')  # 统一分号
    text = text.replace('：', ':')  # 统一冒号
    text = text.replace('．', '.')  # 统一点号
    # 3. 移除零宽字符和其他不可见字符
    text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\ufeff]', '', text)
    # 4. 移除重复的标点符号
    text = re.sub(r'[;,]{2,}', ';', text)
    text = re.sub(r'[:]{2,}', ':', text)
    return text

def clean_html(content):
    """清理HTML标签和实体"""
    try:
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(content, 'html.parser')
        # 获取纯文本内容
        text = soup.get_text(separator=' ', strip=True)
        # 解码HTML实体
        text = html.unescape(text)
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        logger.error(f"清理HTML时出错: {str(e)}")
        return content

# 数据读取函数
def read_json(file_path: str, batch_size: int = BATCH_SIZE) -> pd.DataFrame:
    """
    读取JSON文件并返回DataFrame
    支持流式处理大文件
    """
    try:
        logger.info(f"正在读取JSON文件: {file_path}")
        
        # 对于小文件，直接读取
        file_size = os.path.getsize(file_path)
        if file_size < 100 * 1024 * 1024:  # 小于100MB的文件直接读取
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]
                return pd.json_normalize(data)
        
        # 对于大文件，使用ijson流式解析
        all_data = []
        with open(file_path, 'rb') as f:
            objects = ijson.items(f, 'item')
            batch = []
            
            for obj in tqdm(objects, desc="读取JSON数据"):
                batch.append(obj)
                
                if len(batch) >= batch_size:
                    all_data.append(pd.json_normalize(batch))
                    batch = []
                    gc.collect()  # 回收内存
            
            # 处理剩余数据
            if batch:
                all_data.append(pd.json_normalize(batch))
        
        # 合并所有批次的数据
        if not all_data:
            return pd.DataFrame()
        
        result = pd.concat(all_data, ignore_index=True)
        logger.info(f"成功读取JSON文件: {file_path}, 共 {len(result)} 行数据")
        return result
    
    except Exception as e:
        logger.error(f"读取JSON文件时出错: {str(e)}")
        raise

def read_csv(file_path: str, **kwargs) -> pd.DataFrame:
    """
    读取CSV文件并返回DataFrame
    支持自动检测编码和分隔符
    """
    try:
        logger.info(f"正在读取CSV文件: {file_path}")
        
        # 检测文件编码
        with open(file_path, 'rb') as f:
            raw_data = f.read(1024 * 1024)  # 读取前1MB用于检测
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
        
        # 检测分隔符
        try:
            # 尝试读取前10行检测分隔符
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                sample = ''.join([f.readline() for _ in range(10)])
            
            # 检测常见分隔符
            separators = [',', '\t', ';', '|']
            counts = {sep: sample.count(sep) for sep in separators}
            separator = max(counts, key=counts.get)
            
            # 如果是TSV文件但检测到的不是制表符，强制使用制表符
            if file_path.lower().endswith('.tsv') and separator != '\t':
                separator = '\t'
        except:
            # 默认使用逗号
            separator = ','
        
        # 读取CSV文件 - 使用新版pandas参数
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            sep=separator,
            on_bad_lines='skip',  # 跳过错误行 (新版pandas参数)
            low_memory=False,  # 避免混合类型警告
            **kwargs
        )
        
        logger.info(f"成功读取CSV文件: {file_path}, 共 {len(df)} 行数据")
        return df
    
    except Exception as e:
        logger.error(f"读取CSV文件时出错: {str(e)}")
        raise

def read_excel(file_path: str, **kwargs) -> pd.DataFrame:
    """
    读取Excel文件并返回DataFrame
    支持.xlsx和.xls格式
    """
    try:
        logger.info(f"正在读取Excel文件: {file_path}")
        
        # 读取Excel文件
        df = pd.read_excel(file_path, **kwargs)
        
        logger.info(f"成功读取Excel文件: {file_path}, 共 {len(df)} 行数据")
        return df
    
    except Exception as e:
        logger.error(f"读取Excel文件时出错: {str(e)}")
        raise

def read_parquet(file_path: str) -> pd.DataFrame:
    """
    读取Parquet文件并返回DataFrame
    """
    try:
        logger.info(f"正在读取Parquet文件: {file_path}")
        
        # 读取Parquet文件
        df = pd.read_parquet(file_path)
        
        # 修复可能存在的编码问题
        for col in df.select_dtypes(include=['object']).columns:
            try:
                # 尝试检测并修复编码问题
                if df[col].dtype == 'object':
                    df[col] = df[col].apply(lambda x: detect_and_fix_encoding(x) if isinstance(x, (str, bytes)) else x)
            except:
                pass
        
        logger.info(f"成功读取Parquet文件: {file_path}, 共 {len(df)} 行数据")
        return df
    
    except Exception as e:
        logger.error(f"读取Parquet文件时出错: {str(e)}")
        raise

# 数据写入函数
def write_json(df: pd.DataFrame, file_path: str, orient: str = 'records', lines: bool = False):
    """
    将DataFrame写入JSON文件
    
    参数:
        df: 数据框
        file_path: 输出文件路径
        orient: JSON格式方向，默认为'records'
        lines: 是否每行一个JSON对象，适合大数据集
    """
    try:
        logger.info(f"正在写入JSON文件: {file_path}")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # 对于大数据集，使用lines模式
        if len(df) > 100000 or df.memory_usage(deep=True).sum() > 1024*1024*100:  # 超过10万行或100MB
            logger.info("检测到大数据集，使用lines模式写入JSON")
            df.to_json(file_path, orient='records', lines=True, force_ascii=False)
        else:
            df.to_json(file_path, orient=orient, force_ascii=False)
        
        logger.info(f"成功写入JSON文件: {file_path}")
    
    except Exception as e:
        logger.error(f"写入JSON文件时出错: {str(e)}")
        raise

def write_csv(df: pd.DataFrame, file_path: str, **kwargs):
    """
    将DataFrame写入CSV文件
    
    参数:
        df: 数据框
        file_path: 输出文件路径
        **kwargs: 传递给pd.to_csv的其他参数
    """
    try:
        logger.info(f"正在写入CSV文件: {file_path}")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # 决定分隔符
        sep = kwargs.pop('sep', ',')
        if file_path.lower().endswith('.tsv'):
            sep = '\t'
        
        # 写入CSV文件
        df.to_csv(
            file_path,
            sep=sep,
            index=False,
            encoding='utf-8-sig',  # 使用带BOM的UTF-8编码，兼容Excel
            quoting=csv.QUOTE_MINIMAL,
            **kwargs
        )
        
        logger.info(f"成功写入CSV文件: {file_path}")
    
    except Exception as e:
        logger.error(f"写入CSV文件时出错: {str(e)}")
        raise

def write_excel(df: pd.DataFrame, file_path: str, **kwargs):
    """
    将DataFrame写入Excel文件
    
    参数:
        df: 数据框
        file_path: 输出文件路径
        **kwargs: 传递给pd.to_excel的其他参数
    """
    try:
        logger.info(f"正在写入Excel文件: {file_path}")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # 写入Excel文件
        sheet_name = kwargs.pop('sheet_name', 'Sheet1')
        
        # 对于大数据集，进行批量写入
        if len(df) > 100000:
            logger.info("检测到大数据集，使用批量方式写入Excel")
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 每次写入5万行
                chunk_size = 50000
                for i in range(0, len(df), chunk_size):
                    chunk_df = df.iloc[i:i+chunk_size]
                    if i == 0:
                        chunk_df.to_excel(writer, sheet_name=sheet_name, index=False, **kwargs)
                    else:
                        # 追加到已有的工作表
                        chunk_df.to_excel(writer, sheet_name=sheet_name, startrow=i+1, header=False, index=False, **kwargs)
                    
                    # 释放内存
                    del chunk_df
                    gc.collect()
        else:
            df.to_excel(file_path, sheet_name=sheet_name, index=False, **kwargs)
        
        logger.info(f"成功写入Excel文件: {file_path}")
    
    except Exception as e:
        logger.error(f"写入Excel文件时出错: {str(e)}")
        raise

def write_parquet(df: pd.DataFrame, file_path: str, **kwargs):
    """
    将DataFrame写入Parquet文件
    
    参数:
        df: 数据框
        file_path: 输出文件路径
        **kwargs: 传递给pd.to_parquet的其他参数
    """
    try:
        logger.info(f"正在写入Parquet文件: {file_path}")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # 转换所有对象列为字符串，确保兼容性
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str)
        
        # 写入Parquet文件
        compression = kwargs.pop('compression', 'snappy')  # 默认使用snappy压缩
        df.to_parquet(file_path, compression=compression, **kwargs)
        
        logger.info(f"成功写入Parquet文件: {file_path}")
    
    except Exception as e:
        logger.error(f"写入Parquet文件时出错: {str(e)}")
        raise

# 主要转换函数
def convert_file(input_file: str, output_file: str, batch_size: int = BATCH_SIZE):
    """
    根据文件扩展名自动转换文件格式
    
    参数:
        input_file: 输入文件路径
        output_file: 输出文件路径
        batch_size: 批处理大小
    """
    try:
        # 检测输入和输出格式
        input_format = detect_format(input_file)
        output_format = detect_format(output_file)
        
        logger.info(f"正在转换文件: {input_file} ({input_format}) -> {output_file} ({output_format})")
        
        # 读取输入文件
        df = None
        if input_format == 'json':
            df = read_json(input_file, batch_size)
        elif input_format == 'csv':
            df = read_csv(input_file)
        elif input_format == 'excel':
            df = read_excel(input_file)
        elif input_format == 'parquet':
            df = read_parquet(input_file)
        
        if df is None or df.empty:
            logger.warning(f"输入文件 {input_file} 为空或读取失败")
            return
        
        # 写入输出文件
        if output_format == 'json':
            write_json(df, output_file)
        elif output_format == 'csv':
            write_csv(df, output_file)
        elif output_format == 'excel':
            write_excel(df, output_file)
        elif output_format == 'parquet':
            write_parquet(df, output_file)
        
        logger.info(f"文件转换完成: {input_file} -> {output_file}")
    
    except Exception as e:
        logger.error(f"转换文件时出错: {str(e)}")
        raise

def convert_directory(input_path: str, output_path: str, target_format: str, batch_size: int = BATCH_SIZE):
    """
    转换目录下的所有支持格式文件到目标格式
    
    参数:
        input_path: 输入目录路径
        output_path: 输出目录路径
        target_format: 目标格式 (json/csv/excel/parquet)
        batch_size: 批处理大小
    """
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # 确保输出目录存在
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 验证目标格式
        if target_format not in SUPPORTED_FORMATS:
            raise ValueError(f"不支持的目标格式: {target_format}。支持的格式: {', '.join(SUPPORTED_FORMATS.keys())}")
        
        if input_path.is_file():
            # 单个文件转换
            output_file = output_path / f"{input_path.stem}{SUPPORTED_FORMATS[target_format][0]}"
            convert_file(str(input_path), str(output_file), batch_size)
        elif input_path.is_dir():
            # 处理目录下的所有文件
            all_files = []
            for format_name, extensions in SUPPORTED_FORMATS.items():
                for ext in extensions:
                    all_files.extend(list(input_path.glob(f"*{ext}")))
            
            logger.info(f"在目录 {input_path} 中找到 {len(all_files)} 个可转换文件")
            
            for file_path in all_files:
                # 构建输出文件路径
                output_file = output_path / f"{file_path.stem}{SUPPORTED_FORMATS[target_format][0]}"
                convert_file(str(file_path), str(output_file), batch_size)
        else:
            logger.error(f"输入路径 {input_path} 不存在")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"转换目录时出错: {str(e)}")
        raise

def show_format_guide():
    """Show format conversion guide"""
    guide = """
Format Conversion Guide:
======================

JSON Conversion:
  - JSON → CSV: Best for flat JSON data, nested structures will be flattened
  - JSON → Excel: Similar to CSV, but Excel has row limit (~1M rows)
  - JSON → Parquet: Best for large datasets, preserves data types

CSV Conversion:
  - CSV → JSON: Each row becomes a JSON object
  - CSV → Excel: Direct conversion, but Excel has row limit
  - CSV → Parquet: Good for large datasets, infers data types

Excel Conversion:
  - Excel → JSON: Each row becomes a JSON object
  - Excel → CSV: Direct conversion, good for sharing
  - Excel → Parquet: Good for data analysis, but has row limit

Parquet Conversion:
  - Parquet → JSON: Preserves type information
  - Parquet → CSV: Good for sharing, may lose type info
  - Parquet → Excel: Good for visualization, but has row limit

Notes:
  - For large files (>100MB), use batch mode and consider Parquet
  - Excel has row limit, not suitable for very large datasets
  - Nested JSON structures will be flattened in other formats
"""
    print(guide)

def main():
    """命令行入口函数"""
    global MEMORY_THRESHOLD, BUFFER_SIZE
    
    parser = argparse.ArgumentParser(
        description='Data Format Converter - Convert between JSON, CSV, Excel and Parquet formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Convert single file (auto-detect input format, default to CSV)
  python data_converter.py input.json
  python data_converter.py input.xlsx --output-format parquet
  
  # Convert directory (auto-detect input formats, default to CSV)
  python data_converter.py input_dir
  
  # Convert with custom batch size
  python data_converter.py large_data.json --output-format csv --batch-size 5000
  
  # Show format guide
  python data_converter.py --guide
  
Supported formats:
  - JSON (.json)
  - CSV (.csv, .tsv)
  - Excel (.xlsx, .xls)
  - Parquet (.parquet)
'''
    )
    
    # 主要参数
    parser.add_argument('input_path', help='Input file or directory path')
    parser.add_argument('--output-format', choices=SUPPORTED_FORMATS.keys(), default='csv',
                       help='Target format (default: csv): ' + ', '.join(SUPPORTED_FORMATS.keys()))
    parser.add_argument('--output-path', help='Output file or directory path (optional)')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, 
                       help='Batch size for large files (default: ' + str(BATCH_SIZE) + ')')
    parser.add_argument('--guide', action='store_true', help='Show format conversion guide')
    
    # 全局选项
    parser.add_argument('--memory-threshold', type=int, default=MEMORY_THRESHOLD, 
                       help='Memory usage warning threshold, default: ' + str(MEMORY_THRESHOLD) + '%')
    parser.add_argument('--buffer-size', type=int, default=BUFFER_SIZE, 
                       help='File buffer size, default: ' + str(BUFFER_SIZE//1024) + 'KB')
    parser.add_argument('-v', '--version', action='version', version='Data Converter v1.0.0',
                       help='Show version info')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 显示格式指南
    if args.guide:
        show_format_guide()
        return
    
    # 更新全局配置
    MEMORY_THRESHOLD = args.memory_threshold
    BUFFER_SIZE = args.buffer_size
    
    # 转换文件或目录
    input_path = Path(args.input_path)
    output_format = args.output_format
    
    # 确定输出路径
    if args.output_path:
        output_path = Path(args.output_path)
    else:
        if input_path.is_file():
            # 对于单个文件，在当前目录下创建同名目录
            output_dir = Path.cwd() / input_path.stem
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"{input_path.stem}{SUPPORTED_FORMATS[output_format][0]}"
        else:
            # 对于目录，在当前目录下创建同名目录
            output_dir = Path.cwd() / input_path.name
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir
    
    # 转换文件或目录
    if input_path.is_file():
        convert_file(str(input_path), str(output_path), args.batch_size)
    elif input_path.is_dir():
        convert_directory(str(input_path), str(output_path), output_format, args.batch_size)
    else:
        logger.error(f"输入路径 {input_path} 不存在")
        sys.exit(1)

if __name__ == '__main__':
    main() 