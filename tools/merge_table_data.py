#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据文件合并工具

该脚本用于根据匹配条件合并两个数据文件的数据，支持多种文件格式（Excel、CSV等）。
可以通过命令行参数灵活配置匹配列和合并方式，支持多列拼接。

使用示例:
    python merge_excel_data.py -s "源文件.xlsx" -t "目标文件.csv" -sd 1,2,3 -o "结果文件.xlsx"
    
    其中 -sd 1,2,3 表示拼接源文件的第2、3、4列(索引分别为1、2、3)
"""

import pandas as pd
import os
import sys
import argparse
import chardet
from pathlib import Path
import zipfile
import re

# 默认配置参数
DEFAULT_CONFIG = {
    "source_file": r"E:\Projects\leagle\inputData\tky\202504-品名申请信息.csv",     # 源文件路径 (包含要拼接的数据的文件)，支持Windows完整路径
    "target_file": r"E:\Projects\leagle\inputData\tky\新增品名.csv",     # 目标文件路径 (要合并到的文件)，支持Windows完整路径
    "output_file": None,     # 输出文件路径，默认为当前目录下以目标文件名为前缀的结果文件
    "source_key_column": 5,  # 源文件匹配键列索引（从0开始，0表示第1列）
    "target_key_column": 2,  # 目标文件匹配键列索引（从0开始，0表示第1列）
    "source_data_columns": [12,13],  # 源文件要拼接的数据列索引列表（从0开始，1表示第2列），多列用逗号分隔如 1,2,3
    "output_format": "csv", # 输出文件格式：xlsx, csv
    "encoding": None,        # 文件编码，None表示启用自动检测编码
}

def detect_encoding(file_path):
    """
    检测文件编码
    
    当未指定编码时，自动检测文件的编码格式
    """
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def read_file(file_path, encoding=None):
    """
    读取文件数据，自动检测格式并处理编码
    
    参数:
        file_path: 文件路径，支持Windows完整路径如 E:\\目录\\文件.xlsx
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
                df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else None)
                print(f"成功读取Excel文件: {file_path}")
                return df
            except Exception as e:
                print(f"作为Excel文件读取失败: {e}")
        
        # 尝试作为CSV文件读取
        if file_ext == '.csv' or True:  # 即使扩展名不是.csv也尝试
            # 尝试不同的编码和分隔符
            encodings = [encoding] if encoding else ['utf-8', 'gbk', 'latin1', 'gb18030', 'utf-16']
            delimiters = [',', '\t', ';', '|']
            
            # 移除None值
            encodings = [enc for enc in encodings if enc]
            
            for enc in encodings:
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(file_path, encoding=enc, sep=delimiter)
                        print(f"成功读取CSV文件: {file_path}，使用编码 {enc} 和分隔符 '{delimiter}'")
                        return df
                    except Exception:
                        continue
        
        # 如果以上方法都失败，尝试作为文本文件读取
        try:
            # 先检测编码
            detect_enc = detect_encoding(file_path)
            print(f"检测到文件编码: {detect_enc}")
            
            with open(file_path, 'r', encoding=detect_enc) as f:
                lines = f.readlines()
            
            if lines:
                # 尝试猜测分隔符
                for delimiter in delimiters:
                    if delimiter in lines[0]:
                        columns = lines[0].strip().split(delimiter)
                        data = []
                        for line in lines[1:]:
                            if line.strip():  # 跳过空行
                                data.append(line.strip().split(delimiter))
                        df = pd.DataFrame(data, columns=columns)
                        print(f"成功解析文本文件: {file_path}，使用分隔符 '{delimiter}'")
                        return df
        except Exception as e:
            print(f"作为文本文件读取失败: {e}")
        
        # 如果所有方法都失败
        raise ValueError(f"无法读取文件 {file_path}，请检查文件格式")
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        raise

def generate_default_output_path(target_file, output_format):
    """
    根据目标文件生成默认输出路径
    
    在当前工作目录创建输出文件，以目标文件名作为前缀
    """
    target_path = Path(target_file)
    file_name = target_path.stem  # 不带扩展名的文件名
    
    # 在当前目录创建输出文件，以目标文件名作为前缀
    output_path = Path(os.getcwd()) / f"{file_name}_merged.{output_format.lower()}"
    
    return str(output_path)

def merge_data_files(source_file, target_file, source_key_col=0, target_key_col=0, 
                    source_data_cols=None, output_file=None, output_format='xlsx', encoding=None):
    """
    根据匹配条件合并两个数据文件的数据
    
    参数:
        source_file: 源文件路径 (包含要拼接的数据的文件)
        target_file: 目标文件路径 (要合并到的文件)
        source_key_col: 源文件匹配键列索引 (从0开始，0表示第1列)
        target_key_col: 目标文件匹配键列索引 (从0开始，0表示第1列)
        source_data_cols: 源文件要拼接的数据列索引列表 (从0开始)，支持多列
                         可以是单个数字如1，或列表如[1,2,3]
        output_file: 输出文件路径
        output_format: 输出文件格式 (xlsx, csv)
        encoding: 文件编码，如果为None则自动检测
    """
    # 设置默认值
    if source_data_cols is None:
        source_data_cols = [1]  # 默认拼接第二列
    elif isinstance(source_data_cols, int):
        source_data_cols = [source_data_cols]  # 将单个索引转换为列表
    
    # 设置默认输出文件路径
    if output_file is None:
        output_file = generate_default_output_path(target_file, output_format)
    
    source_file = Path(source_file)
    target_file = Path(target_file)
    output_file = Path(output_file)
    
    # 读取源文件
    print(f"读取源文件: {source_file}")
    try:
        df_source = read_file(source_file, encoding)
        print(f"成功读取源文件，共 {len(df_source)} 行, {len(df_source.columns)} 列")
    except Exception as e:
        print(f"读取源文件失败: {e}")
        raise
    
    # 读取目标文件
    print(f"读取目标文件: {target_file}")
    try:
        df_target = read_file(target_file, encoding)
        print(f"成功读取目标文件，共 {len(df_target)} 行, {len(df_target.columns)} 列")
    except Exception as e:
        print(f"读取目标文件失败: {e}")
        raise
    
    # 确保列索引在有效范围内
    if source_key_col >= len(df_source.columns):
        raise ValueError(f"源文件匹配键列索引 {source_key_col} 超出范围，文件只有 {len(df_source.columns)} 列")
    
    for col_idx in source_data_cols:
        if col_idx >= len(df_source.columns):
            raise ValueError(f"源文件数据列索引 {col_idx} 超出范围，文件只有 {len(df_source.columns)} 列")
    
    if target_key_col >= len(df_target.columns):
        raise ValueError(f"目标文件匹配键列索引 {target_key_col} 超出范围，文件只有 {len(df_target.columns)} 列")
    
    # 获取列名（数值索引转为实际列名）
    source_columns = df_source.columns.tolist()
    target_columns = df_target.columns.tolist()
    
    source_key_column = source_columns[source_key_col]
    source_data_column_names = [source_columns[col_idx] for col_idx in source_data_cols]
    target_key_column = target_columns[target_key_col]
    
    print(f"匹配键 - 源文件: {source_key_column}(索引:{source_key_col})，目标文件: {target_key_column}(索引:{target_key_col})")
    print(f"数据列 - 源文件: {source_data_column_names}(索引:{source_data_cols})")
    
    # 创建结果DataFrame
    df_result = df_target.copy()
    
    # 创建源文件匹配键到要拼接列的映射字典
    source_data_dict = {}
    for _, row in df_source.iterrows():
        key = row[source_key_column]
        if pd.notna(key):  # 只处理非空键
            # 转换为字符串以便于比较
            str_key = str(key).strip()
            if str_key not in source_data_dict:
                source_data_dict[str_key] = {}
            
            # 收集每个要拼接的数据列的值
            for col_idx, col_name in zip(source_data_cols, source_data_column_names):
                if col_name not in source_data_dict[str_key]:
                    source_data_dict[str_key][col_name] = []
                value = row[col_name]
                source_data_dict[str_key][col_name].append(value)
    
    # 计数器
    total_matches = 0
    multiple_matches = 0
    
    # 为每个拼接列创建新列
    for col_name in source_data_column_names:
        new_column_name = f"{col_name}"
        df_result[new_column_name] = None
    
    # 对每一行进行匹配和拼接
    for idx, row in df_result.iterrows():
        target_key = row[target_key_column]
        
        if pd.notna(target_key):
            # 转换为字符串以便于比较
            str_target_key = str(target_key).strip()
            if str_target_key and str_target_key in source_data_dict:
                total_matches += 1
                has_multiple = False
                
                # 拼接每一个数据列
                for col_name in source_data_column_names:
                    new_column_name = f"{col_name}"
                    
                    # 处理多个匹配的情况
                    if len(source_data_dict[str_target_key][col_name]) > 1:
                        has_multiple = True
                    
                    # 拼接数据（使用第一个匹配项）
                    value = source_data_dict[str_target_key][col_name][0]
                    df_result.at[idx, new_column_name] = value
                
                if has_multiple:
                    multiple_matches += 1
    
    print(f"总共匹配数: {total_matches}")
    print(f"多重匹配数: {multiple_matches}")
    
    # 保存结果
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"保存结果到: {output_file}")
    try:
        if output_format.lower() in ['xlsx', 'xls']:
            df_result.to_excel(output_file, index=False, engine='openpyxl')
            print("Excel格式保存成功！")
        elif output_format.lower() == 'csv':
            # 保存为UTF-8带BOM的CSV，确保Excel正确识别中文
            df_result.to_csv(output_file, index=False, encoding='utf-8-sig')
            print("CSV格式保存成功！")
        else:
            print(f"不支持的输出格式 {output_format}，使用Excel格式保存")
            excel_output = str(output_file).rsplit('.', 1)[0] + '.xlsx'
            df_result.to_excel(excel_output, index=False, engine='openpyxl')
            print(f"已保存结果到: {excel_output}")
    except Exception as e:
        print(f"保存为 {output_format} 失败: {e}，尝试保存为CSV")
        csv_output = str(output_file).rsplit('.', 1)[0] + '.csv'
        df_result.to_csv(csv_output, index=False, encoding='utf-8-sig')
        print(f"已保存结果到: {csv_output}")
    
    print("处理完成！")
    return total_matches, multiple_matches

def parse_column_list(column_str):
    """
    解析列索引字符串为列表，支持逗号分隔的多个值
    
    例如:
        "1" -> [1]
        "1,2,3" -> [1, 2, 3]
    """
    if not column_str:
        return [1]  # 默认值
    
    try:
        # 处理逗号分隔的值
        if ',' in column_str:
            return [int(x.strip()) for x in column_str.split(',')]
        # 处理单个值
        return [int(column_str.strip())]
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的列索引: {column_str}，必须是整数或逗号分隔的整数列表")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='''
    数据文件合并工具 - 根据匹配条件合并两个数据文件
    
    此脚本用于：
    1. 从源文件和目标文件中读取数据
    2. 根据指定的匹配列进行数据匹配
    3. 将源文件的指定数据列合并到目标文件中
    4. 生成合并后的新文件
    
    支持Excel、CSV等多种文件格式，自动检测文件编码。
    
    使用示例:
        python merge_excel_data.py -s "源文件.xlsx" -t "目标文件.csv" -sd 1,2,3
        
        上述命令将合并源文件的第2列、第3列和第4列(索引分别为1,2,3)到目标文件中
    ''', formatter_class=argparse.RawTextHelpFormatter)
    
    parser.add_argument('-s', '--source', type=str, default=DEFAULT_CONFIG['source_file'],
                        help='源文件路径 (包含要拼接的数据的文件)，支持Windows完整路径')
    parser.add_argument('-t', '--target', type=str, default=DEFAULT_CONFIG['target_file'],
                        help='目标文件路径 (要合并到的文件)，支持Windows完整路径')
    parser.add_argument('-o', '--output', type=str, default=DEFAULT_CONFIG['output_file'],
                        help='输出文件路径，默认为当前目录下以目标文件名为前缀的结果文件')
    parser.add_argument('-sk', '--source-key-column', type=int, default=DEFAULT_CONFIG['source_key_column'],
                        help='源文件匹配键列索引 (从0开始，0表示第1列)，默认为0')
    parser.add_argument('-tk', '--target-key-column', type=int, default=DEFAULT_CONFIG['target_key_column'],
                        help='目标文件匹配键列索引 (从0开始，0表示第1列)，默认为0')
    parser.add_argument('-sd', '--source-data-columns', type=parse_column_list, default=DEFAULT_CONFIG['source_data_columns'],
                        help='源文件要拼接的数据列索引 (从0开始)，可以是单个索引(如1)或逗号分隔的多个索引(如1,2,3)，默认为1')
    parser.add_argument('-f', '--format', type=str, default=DEFAULT_CONFIG['output_format'],
                        help='输出文件格式 (xlsx, csv)，默认为xlsx')
    parser.add_argument('-e', '--encoding', type=str, default=DEFAULT_CONFIG['encoding'],
                        help='文件编码，不指定时自动检测')
    
    # 解析参数
    if len(sys.argv) == 1:
        print("使用默认配置进行处理...")
        
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.source):
        print(f"错误: 源文件不存在 - {args.source}")
        sys.exit(1)
    if not os.path.exists(args.target):
        print(f"错误: 目标文件不存在 - {args.target}")
        sys.exit(1)
    
    try:
        # 调用合并函数
        total_matches, multiple_matches = merge_data_files(
            source_file=args.source,
            target_file=args.target,
            source_key_col=args.source_key_column,
            target_key_col=args.target_key_column,
            source_data_cols=args.source_data_columns,
            output_file=args.output,
            output_format=args.format,
            encoding=args.encoding
        )
        
        print(f"合并完成！共匹配 {total_matches} 条记录，其中 {multiple_matches} 条为多重匹配。")
        if args.output:
            print(f"结果已保存到：{args.output}")
        return 0
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 