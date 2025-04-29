#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件比较工具

该脚本用于比较两个文件（支持Excel、CSV等格式）中指定列的数据，
找出第二个文件中缺失的记录，并输出到新文件中。

使用示例:
    python compare_files.py -f1 "完整文件.xlsx" -f2 "可能缺失记录的文件.csv" -c 0 -f xlsx
    
    其中 -c 0 表示比较两个文件的第1列(索引为0)
"""

import os
import sys
import argparse
import pandas as pd
import chardet
from pathlib import Path
import zipfile

# 默认配置参数
DEFAULT_CONFIG = {
    "input_file1": r"E:\Projects\leagle\inputData\tky\品名申请列表（已去重）--铁路命名规范化.xlsx",  # 第一个文件路径（完整文件），支持Windows完整路径
    "input_file2": r"E:\Projects\leagle\outputData\tky\品名申请列表（已去重）--铁路命名规范化_output.csv",  # 第二个文件路径（可能缺失记录的文件），支持Windows完整路径
    "output_file": None,  # 输出文件路径，默认为当前目录下以第二个文件名为前缀的结果文件
    "column_index": 0,    # 默认比较第一列（索引为0）
    "output_format": "xlsx", # 输出文件格式：xlsx, csv
    "encoding": None,     # 文件编码，None表示启用自动检测编码
}

def detect_encoding(file_path):
    """
    检测文件编码
    
    当未指定编码时，自动检测文件的编码格式
    """
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def read_file(file_path, column_index=0, encoding=None):
    """
    读取文件数据
    
    参数:
        file_path: 文件路径，支持Windows完整路径如 E:\\目录\\文件.xlsx
        column_index: 要比较的列索引（从0开始，0表示第1列）
        encoding: 文件编码，如不指定则自动检测
    """
    file_path = Path(file_path)
    file_ext = file_path.suffix.lower()
    
    try:
        # 尝试作为Excel文件读取
        if file_ext in ['.xlsx', '.xls']:
            try:
                # 检查是否是有效的Excel文件
                if file_ext == '.xlsx':
                    try:
                        with zipfile.ZipFile(file_path, 'r') as _:
                            pass  # 只检查是否是有效的zip文件
                    except zipfile.BadZipFile:
                        print(f"警告: 文件 {file_path} 命名为Excel但不是有效的Excel格式，尝试其他方式读取...")
                        raise ValueError("无效的Excel文件")
                
                # 作为Excel读取
                df = pd.read_excel(file_path)
                print(f"成功读取Excel文件: {file_path}")
                return df
            except Exception as e:
                print(f"作为Excel文件读取失败: {e}")
        elif file_ext == '.csv':
            # 如果未指定编码，尝试检测
            if encoding is None:
                encoding = detect_encoding(file_path)
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"成功读取CSV文件: {file_path}")
            return df
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
            
        # 确保列索引有效
        if column_index >= len(df.columns):
            raise ValueError(f"列索引 {column_index} 超出范围，文件只有 {len(df.columns)} 列")
            
        return df
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        sys.exit(1)

def generate_default_output_path(file2, output_format):
    """
    根据第二个文件生成默认输出路径
    
    在当前工作目录创建输出文件，以第二个文件名为前缀
    """
    file_path = Path(file2)
    file_name = file_path.stem  # 不带扩展名的文件名
    
    # 在当前目录创建输出文件，以第二个文件名作为前缀
    output_path = Path(os.getcwd()) / f"{file_name}_missing.{output_format.lower()}"
    
    return str(output_path)

def compare_files(file1, file2, column_index=0, encoding=None):
    """
    比较两个文件，找出第二个文件中缺失的记录
    
    参数:
        file1: 第一个文件路径（完整文件）
        file2: 第二个文件路径（可能缺失记录的文件）
        column_index: 要比较的列索引（从0开始，0表示第1列）
        encoding: 文件编码，如不指定则自动检测
    
    返回:
        包含缺失记录的DataFrame
    """
    df1 = read_file(file1, column_index, encoding)
    df2 = read_file(file2, column_index, encoding)
    
    # 获取指定列
    col_name1 = df1.columns[column_index]
    col_name2 = df2.columns[column_index]
    
    print(f"比较列 - 文件1: {col_name1}(索引:{column_index})，文件2: {col_name2}(索引:{column_index})")
    
    # 获取两个文件中的值
    values1 = set(df1[col_name1].astype(str))
    values2 = set(df2[col_name2].astype(str))
    
    # 找出缺失的记录
    missing_values = values1 - values2
    
    # 从原始DataFrame中筛选出缺失的记录
    missing_records = df1[df1[col_name1].astype(str).isin(missing_values)]
    
    print(f"文件1中共有 {len(df1)} 条记录")
    print(f"文件2中共有 {len(df2)} 条记录")
    print(f"文件2中缺失的记录数: {len(missing_records)}")
    
    return missing_records

def save_output(df, output_file, output_format='xlsx'):
    """
    保存输出结果
    
    参数:
        df: 要保存的DataFrame
        output_file: 输出文件路径
        output_format: 输出文件格式 (xlsx, csv)
    """
    try:
        # 创建输出目录（如果不存在）
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 根据指定格式保存文件
        if output_format.lower() == 'csv':
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"CSV格式保存成功: {output_file}")
        elif output_format.lower() in ['xlsx', 'xls']:
            df.to_excel(output_file, index=False, engine='openpyxl')
            print(f"Excel格式保存成功: {output_file}")
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
            
        print(f"缺失记录已保存到: {output_file}")
        print(f"共找到 {len(df)} 条缺失记录")
    except Exception as e:
        print(f"保存输出文件时出错: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='''
    文件比较工具 - 比较两个文件并找出缺失的记录
    
    此脚本用于：
    1. 从两个文件中读取数据
    2. 比较指定列的数据
    3. 找出第二个文件中缺失的记录
    4. 将缺失的记录保存到新文件中
    
    支持Excel、CSV等多种文件格式，自动检测文件编码。
    
    使用示例:
        python compare_files.py -f1 "完整文件.xlsx" -f2 "可能缺失记录的文件.csv" -c 0
        
        上述命令将比较两个文件的第1列(索引为0)，找出第二个文件中缺失的记录
    ''', formatter_class=argparse.RawTextHelpFormatter)
    
    parser.add_argument('-f1', '--file1', type=str, default=DEFAULT_CONFIG['input_file1'],
                        help='第一个文件路径（完整文件），支持Windows完整路径')
    parser.add_argument('-f2', '--file2', type=str, default=DEFAULT_CONFIG['input_file2'],
                        help='第二个文件路径（可能缺失记录的文件），支持Windows完整路径')
    parser.add_argument('-o', '--output', type=str, default=DEFAULT_CONFIG['output_file'],
                        help='输出文件路径，默认为当前目录下以第二个文件名为前缀的结果文件')
    parser.add_argument('-c', '--column', type=int, default=DEFAULT_CONFIG['column_index'],
                        help='要比较的列索引（从0开始，0表示第1列），默认为0')
    parser.add_argument('-f', '--format', type=str, default=DEFAULT_CONFIG['output_format'],
                        help='输出文件格式 (xlsx, csv)，默认为xlsx')
    parser.add_argument('-e', '--encoding', type=str, default=DEFAULT_CONFIG['encoding'],
                        help='文件编码，不指定时自动检测')
    
    # 解析参数
    if len(sys.argv) == 1:
        print("使用默认配置进行处理...")
        
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.file1):
        print(f"错误: 文件不存在 - {args.file1}")
        sys.exit(1)
    if not os.path.exists(args.file2):
        print(f"错误: 文件不存在 - {args.file2}")
        sys.exit(1)
        
    # 设置输出文件格式
    output_format = args.format
    if not output_format:
        output_format = DEFAULT_CONFIG['output_format']
    
    # 设置输出文件路径
    output_file = args.output
    if not output_file:
        output_file = generate_default_output_path(args.file2, output_format)
    elif not os.path.splitext(output_file)[1]:
        # 如果输出文件没有扩展名，根据格式添加
        output_file = f"{output_file}.{output_format}"
    
    try:
        # 比较文件并找出缺失记录
        missing_records = compare_files(args.file1, args.file2, args.column, args.encoding)
        
        # 保存结果
        save_output(missing_records, output_file, output_format)
        
        print(f"比较完成！找到 {len(missing_records)} 条缺失记录。")
        print(f"结果已保存到：{output_file}")
        return 0
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 