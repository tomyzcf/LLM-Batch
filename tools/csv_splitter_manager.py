#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import os
from tqdm import tqdm
import sys
import argparse
import math
import random
from datetime import datetime
import psutil
import gc
from typing import List

# 性能优化配置
MEMORY_CHECK_INTERVAL = 100 * 1024 * 1024  # 每处理100MB检查一次内存
MEMORY_THRESHOLD = 80  # 内存使用率警告阈值（百分数）
BATCH_SIZE = 10000  # 默认批处理大小
BUFFER_SIZE = 8192 * 1024  # 8MB文件缓冲区大小
ENCODING = 'utf-8-sig'  # 统一使用的编码

def get_memory_usage():
    """获取当前进程的内存使用情况"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
    memory_percent = (memory_info.rss / (total_memory * 1024 * 1024)) * 100
    return memory_info.rss / (1024 * 1024), memory_percent

def check_memory_usage():
    """检查内存使用情况，如果超过阈值则发出警告并执行垃圾回收"""
    memory_usage, memory_percent = get_memory_usage()
    if memory_percent > MEMORY_THRESHOLD:
        print(f"警告：内存使用超过阈值: {memory_usage:.2f}MB ({memory_percent:.1f}%)")
        gc.collect()
    return memory_usage, memory_percent

def get_total_rows(file_path: str) -> int:
    """获取CSV文件的总行数（不包括标题行）"""
    return sum(1 for _ in open(file_path, 'r', encoding=ENCODING)) - 1

def process_chunk(chunk: pd.DataFrame, columns_to_drop: List[str] = None) -> pd.DataFrame:
    """处理数据块的通用函数"""
    if columns_to_drop:
        chunk = chunk.drop(columns=columns_to_drop)
    return chunk

def write_chunk(chunk: pd.DataFrame, output_file: str, mode: str = 'w', header: bool = True):
    """写入数据块的通用函数"""
    chunk.to_csv(output_file, mode=mode, index=False, header=header, encoding=ENCODING)

def get_csv_columns(file_path):
    """读取CSV文件的列名"""
    try:
        df = pd.read_csv(file_path, nrows=0, encoding='utf-8-sig')
        return list(df.columns)
    except Exception as e:
        print(f"读取文件出错: {str(e)}")
        sys.exit(1)

def display_columns(file_path):
    """显示CSV文件的列名"""
    try:
        columns = get_csv_columns(file_path)
        print("\nCSV文件的列名:")
        for i, col in enumerate(columns, 1):
            print(f"{i}. {col}")
        print("\n列名总数:", len(columns))
    except Exception as e:
        print(f"显示列名时出错: {str(e)}")
        sys.exit(1)

def get_file_size(file_path):
    """获取文件大小（MB）"""
    return os.path.getsize(file_path) / (1024 * 1024)

def split_by_rows(input_file: str, output_prefix: str, rows_per_file: int, columns_to_drop=None):
    """按行数分割CSV文件"""
    try:
        total_rows = get_total_rows(input_file)
        total_files = (total_rows + rows_per_file - 1) // rows_per_file
        
        print(f"总行数: {total_rows}, 将分割成 {total_files} 个文件，每个文件 {rows_per_file} 行")
        pbar = tqdm(total=total_rows, desc="分割进度")
        
        current_file = 0
        processed_bytes = 0
        
        for chunk in pd.read_csv(input_file, chunksize=min(BATCH_SIZE, rows_per_file), encoding=ENCODING):
            chunk = process_chunk(chunk, columns_to_drop)
            output_file = f"{output_prefix}_{current_file+1}.csv"
            write_chunk(chunk, output_file)
            
            chunk_size = len(chunk)
            processed_bytes += chunk.memory_usage(deep=True).sum()
            pbar.update(chunk_size)
            current_file += 1
            
            if processed_bytes >= MEMORY_CHECK_INTERVAL:
                check_memory_usage()
                processed_bytes = 0
        
        pbar.close()
        print(f"\n分割完成！已生成 {current_file} 个文件")
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def split_by_percentage(input_file: str, output_prefix: str, percentage: float, columns_to_drop=None):
    """按百分比分割CSV文件"""
    try:
        total_rows = get_total_rows(input_file)
        first_part_rows = int(total_rows * (percentage / 100))
        
        print(f"总行数: {total_rows}, 将分割成 {percentage}% ({first_part_rows}行) 和 {100-percentage}% ({total_rows-first_part_rows}行)")
        pbar = tqdm(total=total_rows, desc="分割进度")
        
        current_row = 0
        processed_bytes = 0
        
        for chunk in pd.read_csv(input_file, chunksize=min(BATCH_SIZE, first_part_rows), encoding=ENCODING):
            chunk = process_chunk(chunk, columns_to_drop)
            chunk_size = len(chunk)
            
            # 处理第一个文件
            if current_row < first_part_rows:
                rows_for_first = min(chunk_size, first_part_rows - current_row)
                first_part = chunk.iloc[:rows_for_first]
                mode = 'a' if current_row > 0 else 'w'
                write_chunk(first_part, f"{output_prefix}_part1.csv", mode, header=(mode=='w'))
            
            # 处理第二个文件
            if current_row + chunk_size > first_part_rows:
                start_idx = max(0, first_part_rows - current_row)
                second_part = chunk.iloc[start_idx:]
                mode = 'a' if current_row > first_part_rows else 'w'
                write_chunk(second_part, f"{output_prefix}_part2.csv", mode, header=(mode=='w'))
            
            current_row += chunk_size
            processed_bytes += chunk.memory_usage(deep=True).sum()
            pbar.update(chunk_size)
            
            if processed_bytes >= MEMORY_CHECK_INTERVAL:
                check_memory_usage()
                processed_bytes = 0
        
        pbar.close()
        print(f"\n分割完成！文件已保存为 {output_prefix}_part1.csv 和 {output_prefix}_part2.csv")
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def split_by_date(input_file: str, output_prefix: str, date_column: str, date_format: str, columns_to_drop=None):
    """按日期列分割CSV文件"""
    try:
        # 验证日期列是否存在
        all_columns = pd.read_csv(input_file, nrows=0, encoding=ENCODING).columns
        if date_column not in all_columns:
            print(f"错误：日期列 '{date_column}' 不存在")
            sys.exit(1)
        
        print("读取数据并处理日期...")
        processed_bytes = 0
        total_rows = 0
        
        for chunk in pd.read_csv(input_file, chunksize=BATCH_SIZE, encoding=ENCODING):
            chunk[date_column] = pd.to_datetime(chunk[date_column], format=date_format)
            chunk = process_chunk(chunk, columns_to_drop)
            
            for period, group in chunk.groupby(chunk[date_column].dt.to_period('M')):
                output_file = f"{output_prefix}_{period}.csv"
                mode = 'a' if os.path.exists(output_file) else 'w'
                write_chunk(group, output_file, mode, header=(mode=='w'))
            
            chunk_size = len(chunk)
            total_rows += chunk_size
            processed_bytes += chunk.memory_usage(deep=True).sum()
            
            if processed_bytes >= MEMORY_CHECK_INTERVAL:
                check_memory_usage()
                processed_bytes = 0
                print(f"已处理 {total_rows} 条记录")
        
        print(f"\n分割完成！文件已保存在输出目录中，共处理 {total_rows} 条记录")
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def split_top_n(input_file, output_file, top_n, columns_to_drop=None):
    """截取CSV文件的前N条记录"""
    try:
        # 读取总行数
        total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8-sig')) - 1
        actual_rows = min(top_n, total_rows)
        
        print(f"总行数: {total_rows}, 将截取前 {actual_rows} 条记录")
        pbar = tqdm(total=actual_rows, desc="处理进度")
        
        # 分块读取并处理
        current_row = 0
        processed_bytes = 0
        first_chunk = True
        
        for chunk in pd.read_csv(input_file, chunksize=min(BATCH_SIZE, top_n), encoding='utf-8-sig'):
            if current_row >= top_n:
                break
                
            if columns_to_drop:
                chunk = chunk.drop(columns=columns_to_drop)
            
            # 计算本次需要保存的行数
            rows_to_save = min(len(chunk), top_n - current_row)
            chunk = chunk.iloc[:rows_to_save]
            
            # 保存数据
            mode = 'w' if first_chunk else 'a'
            header = first_chunk
            chunk.to_csv(output_file, mode=mode, index=False, header=header, encoding='utf-8-sig')
            
            chunk_size = len(chunk)
            current_row += chunk_size
            processed_bytes += chunk.memory_usage(deep=True).sum()
            pbar.update(chunk_size)
            first_chunk = False
            
            # 定期检查内存使用情况
            if processed_bytes >= MEMORY_CHECK_INTERVAL:
                check_memory_usage()
                processed_bytes = 0
            
            if current_row >= top_n:
                break
        
        pbar.close()
        print(f"\n处理完成！已截取前 {actual_rows} 条记录并保存为: {output_file}")
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        sys.exit(1)

def split_by_size(input_file: str, output_prefix: str, size_per_file_mb: float, columns_to_drop=None):
    """按文件大小分割CSV文件"""
    try:
        # 估算每行大小来计算chunksize
        sample_df = pd.read_csv(input_file, nrows=1000, encoding=ENCODING)
        if columns_to_drop:
            sample_df = sample_df.drop(columns=columns_to_drop)
        avg_row_size = len(sample_df.to_csv(index=False).encode(ENCODING)) / len(sample_df)
        rows_per_chunk = int((size_per_file_mb * 1024 * 1024) / avg_row_size)
        
        total_size = os.path.getsize(input_file) / (1024 * 1024)
        print(f"总大小: {total_size:.2f}MB, 每个文件大小: {size_per_file_mb}MB")
        
        return split_by_rows(input_file, output_prefix, rows_per_chunk, columns_to_drop)
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def process_csv_file(input_file, output_file, columns_to_drop, chunksize=10000):
    """处理CSV文件，删除指定的列"""
    try:
        total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8-sig')) - 1
        pbar = tqdm(total=total_rows, desc="处理进度")
        
        first_chunk = True
        for chunk in pd.read_csv(input_file, chunksize=chunksize, encoding='utf-8-sig'):
            chunk = chunk.drop(columns=columns_to_drop)
            mode = 'w' if first_chunk else 'a'
            header = first_chunk
            chunk.to_csv(output_file, mode=mode, index=False, header=header, encoding='utf-8-sig')
            pbar.update(len(chunk))
            first_chunk = False
            
        pbar.close()
        print(f"\n处理完成！输出文件已保存为: {output_file}")
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        sys.exit(1)

def main():
    example_text = '''示例:
  # 显示CSV文件的列名
  %(prog)s input.csv --show-columns
  
  # 截取前N条记录
  %(prog)s input.csv --top-n 1000 --output output.csv
  
  # 按百分比分割（分成60%%和40%%两部分）
  %(prog)s input.csv --split-percent 60 --output output_prefix
  
  # 按日期列分割（按月份分割）
  %(prog)s input.csv --split-date "date_column" --date-format "%%Y-%%m-%%d" --output output_prefix
  
  # 按行数分割（每个文件1000行）
  %(prog)s input.csv --split-rows 1000 --output output_prefix
  
  # 删除指定列（可以指定多个列名）
  %(prog)s input.csv --drop-columns "列名1,列名2" --output output.csv
  
  # 组合使用（截取前N条同时删除列）
  %(prog)s input.csv --top-n 1000 --drop-columns "列名1,列名2" --output output.csv
  
  # 性能调优
  %(prog)s input.csv --top-n 1000 --output output.csv --batch-size 5000 --memory-threshold 90 --buffer-size 16384
'''

    parser = argparse.ArgumentParser(
        description='''CSV文件处理工具 - 支持以下功能：
  1. 显示CSV文件的列名
  2. 截取文件的前N条记录
  3. 按百分比分割文件
  4. 按日期列分割文件
  5. 按行数分割文件
  6. 删除指定的列
  7. 支持UTF-8编码，确保中文正常显示
  8. 支持大文件处理，自动分块读取
  9. 内存使用优化，支持性能调优''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=example_text)
    
    parser.add_argument('input_file', help='输入CSV文件的路径')
    parser.add_argument('--output', help='输出文件的路径（对于分割操作则作为文件名前缀）')
    parser.add_argument('--show-columns', action='store_true', help='显示CSV文件的所有列名')
    
    # 分割方式选项组
    split_group = parser.add_mutually_exclusive_group()
    split_group.add_argument('--top-n', type=int, help='截取文件的前N条记录')
    split_group.add_argument('--split-percent', type=float, help='按百分比分割，指定第一个文件的百分比（1-99）')
    split_group.add_argument('--split-date', help='按日期列分割，指定用于分割的日期列名')
    split_group.add_argument('--split-rows', type=int, help='按行数分割，指定每个文件的行数')
    
    # 其他选项
    parser.add_argument('--date-format', help='日期格式，例如：%%Y-%%m-%%d，仅在使用 --split-date 时需要')
    parser.add_argument('--drop-columns', help='要删除的列名，多个列名用逗号分隔，例如：列名1,列名2')
    
    # 性能调优选项
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help=f'批处理大小（默认：{BATCH_SIZE}）')
    parser.add_argument('--memory-threshold', type=int, default=MEMORY_THRESHOLD, help=f'内存使用率警告阈值（默认：{MEMORY_THRESHOLD}%）')
    parser.add_argument('--buffer-size', type=int, default=BUFFER_SIZE, help=f'文件缓冲区大小（默认：{BUFFER_SIZE//1024}KB）')
    
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"错误：找不到输入文件 {args.input_file}")
        sys.exit(1)

    # 更新配置
    global MEMORY_THRESHOLD, BUFFER_SIZE, BATCH_SIZE
    MEMORY_THRESHOLD = args.memory_threshold
    BUFFER_SIZE = args.buffer_size
    BATCH_SIZE = args.batch_size

    # 如果只是显示列名
    if args.show_columns:
        display_columns(args.input_file)
        sys.exit(0)

    # 检查是否指定了输出路径
    if not args.output and not args.show_columns:
        print("错误：必须指定输出文件路径（使用 --output 参数）")
        sys.exit(1)

    # 处理要删除的列
    columns_to_drop = None
    if args.drop_columns:
        columns_to_drop = [col.strip() for col in args.drop_columns.split(',')]
        # 验证列名是否存在
        all_columns = get_csv_columns(args.input_file)
        invalid_columns = [col for col in columns_to_drop if col not in all_columns]
        if invalid_columns:
            print(f"错误：以下列名不存在：{', '.join(invalid_columns)}")
            sys.exit(1)

    # 根据不同的操作类型执行相应的功能
    if args.top_n:
        if args.top_n <= 0:
            print("错误：--top-n 参数必须大于0")
            sys.exit(1)
        split_top_n(args.input_file, args.output, args.top_n, columns_to_drop)
    elif args.split_percent:
        if not 1 <= args.split_percent <= 99:
            print("错误：--split-percent 参数必须在1到99之间")
            sys.exit(1)
        split_by_percentage(args.input_file, args.output, args.split_percent, columns_to_drop)
    elif args.split_date:
        if not args.date_format:
            print("错误：使用 --split-date 时必须指定 --date-format")
            sys.exit(1)
        split_by_date(args.input_file, args.output, args.split_date, args.date_format, columns_to_drop)
    elif args.split_rows:
        if args.split_rows <= 0:
            print("错误：--split-rows 参数必须大于0")
            sys.exit(1)
        split_by_rows(args.input_file, args.output, args.split_rows, columns_to_drop)
    elif columns_to_drop:
        process_csv_file(args.input_file, args.output, columns_to_drop)
    else:
        print("错误：必须指定一个操作类型（--top-n、--split-percent、--split-date、--split-rows 或 --drop-columns）")
        sys.exit(1)

if __name__ == '__main__':
    main() 