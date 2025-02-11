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

def get_csv_columns(file_path):
    """读取CSV文件的列名"""
    try:
        df = pd.read_csv(file_path, nrows=0)
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

def split_by_percentage(input_file, output_prefix, percentage, columns_to_drop=None):
    """按百分比分割CSV文件"""
    try:
        # 读取总行数
        total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8')) - 1
        first_part_rows = int(total_rows * (percentage / 100))
        
        print(f"总行数: {total_rows}, 将分割成 {percentage}% ({first_part_rows}行) 和 {100-percentage}% ({total_rows-first_part_rows}行)")
        pbar = tqdm(total=total_rows, desc="分割进度")
        
        # 分两部分读取和保存
        current_row = 0
        for i, chunk in enumerate(pd.read_csv(input_file, chunksize=10000)):
            if columns_to_drop:
                chunk = chunk.drop(columns=columns_to_drop)
            
            # 处理第一个文件
            if current_row < first_part_rows:
                rows_for_first = min(len(chunk), first_part_rows - current_row)
                first_part = chunk.iloc[:rows_for_first]
                mode = 'a' if current_row > 0 else 'w'
                first_part.to_csv(f"{output_prefix}_part1.csv", mode=mode, index=False, header=(mode=='w'))
            
            # 处理第二个文件
            if current_row + len(chunk) > first_part_rows:
                start_idx = max(0, first_part_rows - current_row)
                second_part = chunk.iloc[start_idx:]
                mode = 'a' if current_row > first_part_rows else 'w'
                second_part.to_csv(f"{output_prefix}_part2.csv", mode=mode, index=False, header=(mode=='w'))
            
            current_row += len(chunk)
            pbar.update(len(chunk))
        
        pbar.close()
        print(f"\n分割完成！文件已保存为 {output_prefix}_part1.csv 和 {output_prefix}_part2.csv")
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def split_by_date(input_file, output_prefix, date_column, date_format, columns_to_drop=None):
    """按日期列分割CSV文件"""
    try:
        # 验证日期列是否存在
        all_columns = get_csv_columns(input_file)
        if date_column not in all_columns:
            print(f"错误：日期列 '{date_column}' 不存在")
            sys.exit(1)
        
        # 读取数据并转换日期
        print("读取数据并处理日期...")
        df = pd.read_csv(input_file)
        df[date_column] = pd.to_datetime(df[date_column], format=date_format)
        
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)
        
        # 按年月分组
        groups = df.groupby(df[date_column].dt.to_period('M'))
        total_groups = len(groups)
        
        print(f"将按月份分割成 {total_groups} 个文件")
        
        # 保存每个月的数据
        for period, group in tqdm(groups, desc="分割进度"):
            output_file = f"{output_prefix}_{period}.csv"
            group.to_csv(output_file, index=False)
        
        print(f"\n分割完成！文件已保存在输出目录中")
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def split_random(input_file, output_prefix, num_parts, columns_to_drop=None):
    """随机分割CSV文件"""
    try:
        # 读取总行数
        total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8')) - 1
        
        # 生成随机分配方案
        assignments = list(range(num_parts)) * (total_rows // num_parts + 1)
        random.shuffle(assignments)
        assignments = assignments[:total_rows]
        
        # 创建输出文件的句柄
        output_files = {i: open(f"{output_prefix}_part{i+1}.csv", 'w', encoding='utf-8') 
                       for i in range(num_parts)}
        
        print(f"总行数: {total_rows}, 将随机分割成 {num_parts} 个文件")
        pbar = tqdm(total=total_rows, desc="分割进度")
        
        # 写入表头
        header = pd.read_csv(input_file, nrows=0)
        if columns_to_drop:
            header = header.drop(columns=columns_to_drop)
        for f in output_files.values():
            f.write(header.to_csv(index=False))
        
        # 逐行读取并分配
        current_row = 0
        for chunk in pd.read_csv(input_file, chunksize=10000):
            if columns_to_drop:
                chunk = chunk.drop(columns=columns_to_drop)
            
            for _, row in chunk.iterrows():
                file_idx = assignments[current_row]
                output_files[file_idx].write(row.to_csv(index=False, header=False))
                current_row += 1
                pbar.update(1)
        
        # 关闭所有文件
        for f in output_files.values():
            f.close()
        
        pbar.close()
        print(f"\n分割完成！文件已保存在输出目录中")
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def split_by_column_value(input_file, output_prefix, split_column, columns_to_drop=None):
    """按列值分割CSV文件"""
    try:
        # 验证分割列是否存在
        all_columns = get_csv_columns(input_file)
        if split_column not in all_columns:
            print(f"错误：分割列 '{split_column}' 不存在")
            sys.exit(1)
        
        # 读取并按列值分组
        print("读取数据并进行分组...")
        df = pd.read_csv(input_file)
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)
        
        groups = df.groupby(split_column)
        total_groups = len(groups)
        
        print(f"将按列值分割成 {total_groups} 个文件")
        
        # 保存每个分组的数据
        for value, group in tqdm(groups, desc="分割进度"):
            # 处理文件名中的特殊字符
            safe_value = str(value).replace('/', '_').replace('\\', '_')
            output_file = f"{output_prefix}_{safe_value}.csv"
            group.to_csv(output_file, index=False)
        
        print(f"\n分割完成！文件已保存在输出目录中")
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def split_by_rows(input_file, output_prefix, rows_per_file, columns_to_drop=None):
    """按行数分割CSV文件"""
    try:
        # 获取文件总行数
        total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8')) - 1
        num_chunks = math.ceil(total_rows / rows_per_file)
        
        print(f"总行数: {total_rows}, 将分割成 {num_chunks} 个文件")
        pbar = tqdm(total=total_rows, desc="分割进度")
        
        for i, chunk in enumerate(pd.read_csv(input_file, chunksize=rows_per_file)):
            if columns_to_drop:
                chunk = chunk.drop(columns=columns_to_drop)
            
            output_file = f"{output_prefix}_part_{i+1}.csv"
            chunk.to_csv(output_file, index=False)
            pbar.update(len(chunk))
        
        pbar.close()
        print(f"\n分割完成！文件已保存在输出目录中")
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def split_by_size(input_file, output_prefix, size_per_file_mb, columns_to_drop=None):
    """按文件大小分割CSV文件"""
    try:
        total_size = get_file_size(input_file)
        # 估算每行大小来计算chunksize
        sample_df = pd.read_csv(input_file, nrows=1000)
        if columns_to_drop:
            sample_df = sample_df.drop(columns=columns_to_drop)
        avg_row_size = len(sample_df.to_csv(index=False).encode('utf-8')) / len(sample_df)
        rows_per_chunk = int((size_per_file_mb * 1024 * 1024) / avg_row_size)
        
        print(f"总大小: {total_size:.2f}MB, 每个文件大小: {size_per_file_mb}MB")
        return split_by_rows(input_file, output_prefix, rows_per_chunk, columns_to_drop)
        
    except Exception as e:
        print(f"分割文件时出错: {str(e)}")
        sys.exit(1)

def process_csv_file(input_file, output_file, columns_to_drop, chunksize=10000):
    """处理CSV文件，删除指定的列"""
    try:
        total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8')) - 1
        pbar = tqdm(total=total_rows, desc="处理进度")
        
        first_chunk = True
        for chunk in pd.read_csv(input_file, chunksize=chunksize):
            chunk = chunk.drop(columns=columns_to_drop)
            mode = 'w' if first_chunk else 'a'
            header = first_chunk
            chunk.to_csv(output_file, mode=mode, index=False, header=header)
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
  
  # 按行数分割文件（每1000行一个文件）
  %(prog)s input.csv --split-rows 1000 --output output_prefix
  
  # 按大小分割文件（每个文件10MB）
  %(prog)s input.csv --split-size 10 --output output_prefix
  
  # 按百分比分割（分成60%%和40%%两部分）
  %(prog)s input.csv --split-percent 60 --output output_prefix
  
  # 按日期列分割（按月份分割）
  %(prog)s input.csv --split-date "date_column" --date-format "%%Y-%%m-%%d" --output output_prefix
  
  # 随机分割成N份
  %(prog)s input.csv --split-random 5 --output output_prefix
  
  # 按列值分割（根据某列的不同值分割成多个文件）
  %(prog)s input.csv --split-column "category" --output output_prefix
  
  # 删除指定列（可以指定多个列名）
  %(prog)s input.csv --drop-columns "列名1,列名2" --output output.csv
  
  # 组合使用（分割同时删除列）
  %(prog)s input.csv --split-rows 1000 --drop-columns "列名1,列名2" --output output_prefix
'''

    parser = argparse.ArgumentParser(
        description='CSV文件分割管理工具 - 支持多种分割方式和列的管理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=example_text)
    
    parser.add_argument('input_file', help='输入CSV文件路径')
    parser.add_argument('--output', help='输出文件路径或前缀')
    parser.add_argument('--show-columns', action='store_true', help='显示CSV文件的列名')
    
    # 分割方式选项组
    split_group = parser.add_mutually_exclusive_group()
    split_group.add_argument('--split-rows', type=int, help='按行数分割，指定每个文件的行数')
    split_group.add_argument('--split-size', type=float, help='按大小分割，指定每个文件的大小（MB）')
    split_group.add_argument('--split-percent', type=float, help='按百分比分割，指定第一个文件的百分比（1-99）')
    split_group.add_argument('--split-date', help='按日期列分割，指定日期列名')
    split_group.add_argument('--split-random', type=int, help='随机分割，指定分割成几份')
    split_group.add_argument('--split-column', help='按列值分割，指定用于分割的列名')
    
    # 其他选项
    parser.add_argument('--date-format', help='日期格式，例如 %%Y-%%m-%%d')
    parser.add_argument('--drop-columns', help='要删除的列名，多个列名用逗号分隔')
    
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"错误：找不到输入文件 {args.input_file}")
        sys.exit(1)

    # 如果只是显示列名
    if args.show_columns:
        display_columns(args.input_file)
        sys.exit(0)

    # 设置默认输出路径
    if not args.output:
        file_name, file_ext = os.path.splitext(args.input_file)
        args.output = f"{file_name}_processed{file_ext}"

    # 处理要删除的列
    columns_to_drop = []
    if args.drop_columns:
        columns_to_drop = [col.strip() for col in args.drop_columns.split(',')]
        all_columns = get_csv_columns(args.input_file)
        invalid_columns = [col for col in columns_to_drop if col not in all_columns]
        if invalid_columns:
            print(f"错误：以下列名不存在: {', '.join(invalid_columns)}")
            sys.exit(1)

    # 根据分割类型处理文件
    if args.split_rows:
        split_by_rows(args.input_file, args.output, args.split_rows, columns_to_drop)
    elif args.split_size:
        split_by_size(args.input_file, args.output, args.split_size, columns_to_drop)
    elif args.split_percent:
        if not 1 <= args.split_percent <= 99:
            print("错误：百分比必须在1到99之间")
            sys.exit(1)
        split_by_percentage(args.input_file, args.output, args.split_percent, columns_to_drop)
    elif args.split_date:
        if not args.date_format:
            print("错误：使用日期分割时必须指定 --date-format")
            sys.exit(1)
        split_by_date(args.input_file, args.output, args.split_date, args.date_format, columns_to_drop)
    elif args.split_random:
        if args.split_random < 2:
            print("错误：随机分割份数必须大于1")
            sys.exit(1)
        split_random(args.input_file, args.output, args.split_random, columns_to_drop)
    elif args.split_column:
        split_by_column_value(args.input_file, args.output, args.split_column, columns_to_drop)
    elif columns_to_drop:
        process_csv_file(args.input_file, args.output, columns_to_drop)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 