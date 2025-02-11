#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import os
from tqdm import tqdm
import sys
import argparse

def get_csv_columns(file_path):
    """读取CSV文件的列名"""
    try:
        # 只读取第一行来获取列名
        df = pd.read_csv(file_path, nrows=0)
        return list(df.columns)
    except Exception as e:
        print(f"读取文件出错: {str(e)}")
        sys.exit(1)

def process_csv_file(input_file, output_file, columns_to_drop, chunksize=10000):
    """处理CSV文件，删除指定的列"""
    try:
        # 获取文件总行数（用于进度条）
        total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8')) - 1
        
        # 创建进度条
        pbar = tqdm(total=total_rows, desc="处理进度")
        
        # 分块读取和处理文件
        first_chunk = True
        for chunk in pd.read_csv(input_file, chunksize=chunksize):
            # 删除选定的列
            chunk = chunk.drop(columns=columns_to_drop)
            
            # 写入模式：第一个块用'w'，后续块用'a'
            mode = 'w' if first_chunk else 'a'
            # 只在第一个块写入表头
            header = first_chunk
            
            # 写入处理后的数据
            chunk.to_csv(output_file, mode=mode, index=False, header=header)
            
            # 更新进度条
            pbar.update(len(chunk))
            first_chunk = False
            
        pbar.close()
        print(f"\n处理完成！输出文件已保存为: {output_file}")
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='CSV文件列管理工具')
    parser.add_argument('input_file', help='输入CSV文件路径')
    parser.add_argument('--output_file', help='输出CSV文件路径（可选）')
    args = parser.parse_args()

    # 检查输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"错误：找不到输入文件 {args.input_file}")
        sys.exit(1)

    # 如果未指定输出文件，创建默认输出文件名
    if not args.output_file:
        file_name, file_ext = os.path.splitext(args.input_file)
        args.output_file = f"{file_name}_processed{file_ext}"

    # 获取并显示所有列名
    columns = get_csv_columns(args.input_file)
    print("\n可用的列名：")
    for i, col in enumerate(columns, 1):
        print(f"{i}. {col}")

    # 让用户选择要删除的列
    print("\n请输入要删除的列的编号（多个编号用空格分隔，直接回车跳过）：")
    user_input = input().strip()
    
    if user_input:
        # 将用户输入转换为列名列表
        try:
            selected_indices = [int(x) - 1 for x in user_input.split()]
            columns_to_drop = [columns[i] for i in selected_indices if 0 <= i < len(columns)]
            
            # 确认要删除的列
            print("\n将要删除以下列：")
            for col in columns_to_drop:
                print(f"- {col}")
            
            # 询问用户是否继续
            confirm = input("\n是否继续？(y/n): ").lower()
            if confirm != 'y':
                print("操作已取消")
                sys.exit(0)
                
            # 处理文件
            process_csv_file(args.input_file, args.output_file, columns_to_drop)
        except ValueError:
            print("输入格式错误，请输入有效的数字")
            sys.exit(1)
    else:
        print("未选择要删除的列，操作已取消")

if __name__ == "__main__":
    main() 