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

def split_by_percentage(input_file, output_prefix, percentage, columns_to_drop=None):
    """按百分比分割CSV文件"""
    try:
        # 读取总行数
        total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8-sig')) - 1
        first_part_rows = int(total_rows * (percentage / 100))
        
        print(f"总行数: {total_rows}, 将分割成 {percentage}% ({first_part_rows}行) 和 {100-percentage}% ({total_rows-first_part_rows}行)")
        pbar = tqdm(total=total_rows, desc="分割进度")
        
        # 分两部分读取和保存
        current_row = 0
        for i, chunk in enumerate(pd.read_csv(input_file, chunksize=10000, encoding='utf-8-sig')):
            if columns_to_drop:
                chunk = chunk.drop(columns=columns_to_drop)
            
            # 处理第一个文件
            if current_row < first_part_rows:
                rows_for_first = min(len(chunk), first_part_rows - current_row)
                first_part = chunk.iloc[:rows_for_first]
                mode = 'a' if current_row > 0 else 'w'
                first_part.to_csv(f"{output_prefix}_part1.csv", mode=mode, index=False, header=(mode=='w'), encoding='utf-8-sig')
            
            # 处理第二个文件
            if current_row + len(chunk) > first_part_rows:
                start_idx = max(0, first_part_rows - current_row)
                second_part = chunk.iloc[start_idx:]
                mode = 'a' if current_row > first_part_rows else 'w'
                second_part.to_csv(f"{output_prefix}_part2.csv", mode=mode, index=False, header=(mode=='w'), encoding='utf-8-sig')
            
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
        df = pd.read_csv(input_file, encoding='utf-8-sig')
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
            group.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n分割完成！文件已保存在输出目录中")
        
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
        first_chunk = True
        for chunk in pd.read_csv(input_file, chunksize=10000, encoding='utf-8-sig'):
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
            
            current_row += rows_to_save
            pbar.update(rows_to_save)
            first_chunk = False
            
            if current_row >= top_n:
                break
        
        pbar.close()
        print(f"\n处理完成！已截取前 {actual_rows} 条记录并保存为: {output_file}")
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
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
  
  # 删除指定列（可以指定多个列名）
  %(prog)s input.csv --drop-columns "列名1,列名2" --output output.csv
  
  # 组合使用（截取前N条同时删除列）
  %(prog)s input.csv --top-n 1000 --drop-columns "列名1,列名2" --output output.csv
'''

    parser = argparse.ArgumentParser(
        description='''CSV文件处理工具 - 支持以下功能：
  1. 显示CSV文件的列名
  2. 截取文件的前N条记录
  3. 按百分比分割文件
  4. 按日期列分割文件
  5. 删除指定的列
  6. 支持UTF-8编码，确保中文正常显示
  7. 支持大文件处理，自动分块读取''',
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
    
    # 其他选项
    parser.add_argument('--date-format', help='日期格式，例如：%%Y-%%m-%%d，仅在使用 --split-date 时需要')
    parser.add_argument('--drop-columns', help='要删除的列名，多个列名用逗号分隔，例如：列名1,列名2')
    
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"错误：找不到输入文件 {args.input_file}")
        sys.exit(1)

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
    elif columns_to_drop:
        process_csv_file(args.input_file, args.output, columns_to_drop)
    else:
        print("错误：必须指定一个操作类型（--top-n、--split-percent、--split-date 或 --drop-columns）")
        sys.exit(1)

if __name__ == '__main__':
    main() 