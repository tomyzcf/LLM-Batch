#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from pathlib import Path
import pandas as pd
import tiktoken
from typing import List, Dict, Tuple
from tqdm import tqdm
import psutil
import gc
import time
import chardet

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 性能优化配置
MEMORY_CHECK_INTERVAL = 100 * 1024 * 1024  # 每处理100MB检查一次内存
MEMORY_THRESHOLD = 80  # 内存使用率警告阈值（百分数）
BATCH_SIZE = 10000  # 默认批处理大小
BUFFER_SIZE = 8192 * 1024  # 8MB文件缓冲区大小

DISCLAIMER = """
免责声明：
1. 本工具提供的token数量和费用估算仅供参考，实际数值可能与API供应商的计算结果有所差异
2. token计算基于tiktoken库，可能与不同API供应商的计算方法存在差异
3. 输出token的预估基于经验值，实际输出token数可能因模型、任务类型等因素而变化
4. 建议在正式使用前，先使用小批量数据测试计算结果的准确性
"""

def get_memory_usage():
    """获取当前进程的内存使用情况"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    total_memory = psutil.virtual_memory().total
    memory_percent = (memory_info.rss / total_memory) * 100
    return memory_info.rss / (1024 * 1024), memory_percent

def check_memory_usage():
    """检查内存使用情况，如果超过阈值则发出警告"""
    memory_usage, memory_percent = get_memory_usage()
    if memory_percent > MEMORY_THRESHOLD:
        logger.warning(f"内存使用超过阈值: {memory_usage:.2f}MB ({memory_percent:.1f}%)")
        gc.collect()
    return memory_usage, memory_percent

def detect_file_encoding(file_path: str) -> str:
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read(10000)
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
    except Exception as e:
        logger.error(f"检测文件编码时出错: {str(e)}")
        return 'utf-8'

def count_file_lines(file_path: str, encoding: str) -> int:
    """快速计算文件行数"""
    with open(file_path, 'rb') as f:
        return sum(1 for _ in f)

def get_csv_info(file_path: str, sample_rows: int = 1000) -> Tuple[List[str], int, float]:
    """获取CSV文件的基本信息"""
    encoding = detect_file_encoding(file_path)
    df_sample = pd.read_csv(file_path, nrows=sample_rows, encoding=encoding)
    total_rows = count_file_lines(file_path, encoding) - 1  # 减去标题行
    return list(df_sample.columns), total_rows, 0

def collect_csv_files(path: str) -> List[str]:
    """递归收集所有CSV文件"""
    csv_files = []
    if os.path.isfile(path) and path.lower().endswith('.csv'):
        csv_files.append(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.lower().endswith('.csv'):
                    csv_files.append(os.path.join(root, file))
    return sorted(csv_files)

def calculate_tokens(text: str, encoding_name: str = "cl100k_base") -> Tuple[int, int]:
    """计算文本的token数量和字符数
    返回：(token数, 字符数)
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        char_count = len(str(text))
        token_count = len(encoding.encode(str(text)))
        return token_count, char_count
    except Exception as e:
        logger.warning(f"计算token时出错: {str(e)}")
        return 0, 0

def estimate_output_tokens(input_tokens: int, task_type: str = "summary") -> int:
    """估算输出token数量
    
    不同任务类型的输出token比例：
    - summary: 输入的0.3倍（总结任务，默认）
    - general: 输入的1.5倍
    - qa: 输入的0.5倍（问答任务）
    - chat: 输入的2.0倍（聊天任务）
    """
    ratios = {
        "summary": 0.3,
        "general": 1.5,
        "qa": 0.5,
        "chat": 2.0
    }
    ratio = ratios.get(task_type, 0.3)
    return int(input_tokens * ratio)

def process_csv_file(
    file_path: str,
    selected_columns: List[str],
    prompt_tokens: int,
    batch_size: int = BATCH_SIZE
) -> Dict:
    """处理单个CSV文件"""
    encoding = detect_file_encoding(file_path)
    total_rows = count_file_lines(file_path, encoding) - 1
    processed_bytes = 0
    
    results = {
        'total_rows': 0,
        'input_tokens': 0,
        'input_chars': 0,
        'estimated_output_tokens': 0,
        'errors': []
    }
    
    try:
        with tqdm(total=total_rows, desc=f"处理 {os.path.basename(file_path)}", unit='行') as pbar:
            for chunk in pd.read_csv(file_path, 
                                   usecols=selected_columns,
                                   chunksize=batch_size,
                                   encoding=encoding,
                                   on_bad_lines='skip'):
                
                chunk_size = len(chunk)
                results['total_rows'] += chunk_size
                
                chunk_text = chunk[selected_columns].fillna('').astype(str).agg(' '.join, axis=1)
                for text in chunk_text:
                    tokens, chars = calculate_tokens(text)
                    results['input_tokens'] += tokens + prompt_tokens
                    results['input_chars'] += chars
                
                processed_bytes += chunk.memory_usage(deep=True).sum()
                pbar.update(chunk_size)
                
                # 检查内存使用
                if processed_bytes >= MEMORY_CHECK_INTERVAL:
                    memory_usage, memory_percent = check_memory_usage()
                    pbar.set_postfix({
                        '内存': f'{memory_usage:.1f}MB',
                        '字符/token比': f'{results["input_chars"]/(results["input_tokens"] or 1):.1f}'
                    })
                    processed_bytes = 0
                
                del chunk
                gc.collect()
        
        results['estimated_output_tokens'] = estimate_output_tokens(results['input_tokens'])
        return results
        
    except Exception as e:
        error_msg = f"处理文件时出错: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        return results

def format_number(num: int) -> str:
    """格式化数字，添加千位分隔符"""
    return f"{num:,}"

def main():
    """主函数"""
    start_time = time.time()
    
    try:
        print("\n=== Token成本计算器 ===")
        print(DISCLAIMER)
        
        target_path = input("请输入目标CSV文件或目录路径：").strip()
        prompt_file = input("请输入提示词文件路径：").strip()
        input_price = float(input("请输入模型输入价格（每千token）："))
        output_price = float(input("请输入模型输出价格（每千token）："))
        task_type = input("请输入任务类型（summary/general/qa/chat）[默认summary]：").strip().lower() or "summary"
        
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"目标路径不存在：{target_path}")
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"提示词文件不存在：{prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        prompt_tokens, prompt_chars = calculate_tokens(prompt)
        print(f"\n提示词统计：")
        print(f"- Token数：{format_number(prompt_tokens)}")
        print(f"- 字符数：{format_number(prompt_chars)}")
        print(f"- 字符/Token比：{prompt_chars/(prompt_tokens or 1):.1f}")
        
        csv_files = collect_csv_files(target_path)
        if not csv_files:
            logger.error("未找到CSV文件！")
            return
        
        print(f"\n找到 {len(csv_files)} 个CSV文件：")
        for file in csv_files:
            print(f"- {file}")
        
        columns, total_rows, _ = get_csv_info(csv_files[0])
        print("\n可用的列：")
        for i, col in enumerate(columns):
            print(f"{i+1}. {col}")
        
        selected_indices = input("\n请选择需要处理的列（输入序号，用逗号分隔）：").strip()
        selected_columns = [columns[int(i)-1] for i in selected_indices.split(",")]
        print(f"\n已选择列：{', '.join(selected_columns)}")
        
        total_results = {
            'total_files': len(csv_files),
            'total_rows': 0,
            'total_input_tokens': 0,
            'total_input_chars': 0,
            'total_output_tokens': 0
        }
        
        print("\n=== 开始处理 ===")
        for file_path in csv_files:
            results = process_csv_file(file_path, selected_columns, prompt_tokens)
            
            total_results['total_rows'] += results['total_rows']
            total_results['total_input_tokens'] += results['input_tokens']
            total_results['total_input_chars'] += results['input_chars']
            total_results['total_output_tokens'] += results['estimated_output_tokens']
            
            print(f"\n文件：{file_path}")
            print(f"- 记录数：{format_number(results['total_rows'])}")
            print(f"- 输入字符数：{format_number(results['input_chars'])}")
            print(f"- 输入token数：{format_number(results['input_tokens'])}")
            print(f"- 字符/Token比：{results['input_chars']/(results['input_tokens'] or 1):.1f}")
            print(f"- 预估输出token：{format_number(results['estimated_output_tokens'])}")
            input_cost = results['input_tokens']/1000*input_price
            output_cost = results['estimated_output_tokens']/1000*output_price
            print(f"- 预估费用：¥{input_cost+output_cost:.2f} (输入：¥{input_cost:.2f}, 输出：¥{output_cost:.2f})")
        
        print(f"\n=== 总体统计 ===")
        print(f"处理文件数：{total_results['total_files']}")
        print(f"总记录数：{format_number(total_results['total_rows'])}")
        print(f"\nToken统计：")
        print(f"- 输入字符总数：{format_number(total_results['total_input_chars'])}")
        print(f"- 输入token总数：{format_number(total_results['total_input_tokens'])}")
        print(f"- 平均字符/Token比：{total_results['total_input_chars']/(total_results['total_input_tokens'] or 1):.1f}")
        print(f"- 预估输出token总数：{format_number(total_results['total_output_tokens'])}")
        print(f"- 任务类型：{task_type} (输出预估比例：{estimate_output_tokens(100, task_type)/100:.1f}x)")
        
        total_input_cost = total_results['total_input_tokens']/1000*input_price
        total_output_cost = total_results['total_output_tokens']/1000*output_price
        total_cost = total_input_cost + total_output_cost
        
        print(f"\n费用预估：")
        print(f"- 输入费用：¥{total_input_cost:.2f}")
        print(f"- 输出费用：¥{total_output_cost:.2f}")
        print(f"- 总费用：¥{total_cost:.2f}")
        
        end_time = time.time()
        print(f"\n总处理时间：{end_time - start_time:.1f}秒")
        
    except Exception as e:
        logger.error(f"处理过程中出错：{str(e)}")
        raise

if __name__ == '__main__':
    main() 