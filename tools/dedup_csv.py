#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
from collections import defaultdict

def normalize_term_set(term_string):
    """将竖线分隔的字符串转换为集合，去除顺序因素"""
    return set(term.strip() for term in term_string.split('|') if term.strip())

def process_csv(input_file='./inputData/tky/0426社会品名近似识别_原始模型输出+人工处理（进行中）.csv', 
                output_file='./deduped_output.csv'):
    """
    处理CSV文件并执行去重逻辑
    - 相同集合保留第一条
    - 子集被超集覆盖
    """
    print(f"开始处理文件: {input_file}")
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        return
    
    # 创建输出目录（如果不存在）
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 首先读取所有记录，构建词集映射
    term_sets = []  # 存储所有的词集
    second_columns = []  # 存储第二列的值
    
    try:
        # 读取文件
        with open(input_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            next(csv_reader, None)  # 跳过标题行
            
            for row in csv_reader:
                if len(row) >= 2:
                    term_string = row[0]
                    second_column = row[1] if len(row) > 1 else ""
                    
                    term_set = normalize_term_set(term_string)
                    term_sets.append(term_set)
                    second_columns.append(second_column)
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        return
    
    # 记录要保留的索引
    keep_indices = set()
    
    # 第一步：处理完全相同的集合（只保留第一个）
    unique_sets = {}  # 用于去除完全相同的集合
    
    for i, term_set in enumerate(term_sets):
        # 将集合转换为可哈希的frozenset
        frozen_set = frozenset(term_set)
        
        if frozen_set not in unique_sets:
            unique_sets[frozen_set] = i
            keep_indices.add(i)
    
    # 第二步：处理超集关系
    # 首先对集合按大小排序，从大到小
    sorted_indices = sorted(keep_indices, key=lambda i: len(term_sets[i]), reverse=True)
    
    final_keep_indices = set()
    for i in sorted_indices:
        # 检查这个集合是否已经被其他集合覆盖
        is_covered = False
        for j in final_keep_indices:
            if term_sets[i].issubset(term_sets[j]):
                is_covered = True
                break
        
        if not is_covered:
            final_keep_indices.add(i)
    
    # 写入结果
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            csv_writer = csv.writer(f)
            
            # 写入标题行
            csv_writer.writerow(["去重后的名词集合", "保留的内容"])
            
            # 写入保留的记录
            for i in sorted(final_keep_indices):
                original_terms = '|'.join(sorted(term_sets[i]))
                csv_writer.writerow([original_terms, second_columns[i]])
        
        print(f"去重完成! 原始记录数: {len(term_sets)}, 去重后记录数: {len(final_keep_indices)}")
        print(f"去重结果已保存到: {output_file}")
    
    except Exception as e:
        print(f"写入结果时出错: {str(e)}")

if __name__ == "__main__":
    print("CSV文件去重处理程序")
    print("该程序将处理具有相同名词集合和超集关系的记录")
    
    try:
        process_csv()
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
    
    print("处理完成!") 