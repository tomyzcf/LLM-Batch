#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import csv
import argparse
import logging
import codecs
import re
from pathlib import Path
from typing import Dict, List, Any, Generator, TextIO, Set
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

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

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

def try_different_encodings(file_path: str) -> str:
    """
    尝试不同的编码方式读取文件
    """
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
    content = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                return content, encoding
        except UnicodeDecodeError:
            continue
    
    raise UnicodeDecodeError(f"无法使用以下编码读取文件: {encodings}")

def decode_html_entities(content: str) -> str:
    """
    解码HTML实体编码
    """
    try:
        # 解码HTML实体
        content = html.unescape(content)
        # 处理一些特殊的HTML实体
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&quot;', '"')
        content = content.replace('&amp;', '&')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        return content
    except Exception as e:
        logging.warning(f"解码HTML实体时出错: {str(e)}")
        return content

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
        logging.error(f"清理HTML时出错: {str(e)}")
        return content

def fix_garbled_text(text):
    if not isinstance(text, str):
        return text
        
    # 处理HTML实体编码
    text = html.unescape(text)
    
    # 处理特殊字符
    text = text.replace('锟?', '')
    text = text.replace('锟', '')
    text = text.replace('', '')  # 处理零宽字符
    
    # 处理其他可能的乱码字符
    text = re.sub(r'[\ufffd\u0000-\u0019]', '', text)
    
    return text

def fix_json_format(content):
    """修复JSON格式问题"""
    # 移除BOM标记
    if content.startswith('\ufeff'):
        content = content[1:]
    
    # 处理常见的JSON格式问题
    content = content.strip()
    
    # 如果内容以{开头，说明是单个对象
    if content.startswith('{'):
        # 检查是否有多个对象（用}{ 分隔）
        if re.search(r'}\s*{', content):
            # 有多个对象，需要添加逗号和数组括号
            content = '[' + re.sub(r'}\s*{', '},{', content) + ']'
        else:
            # 单个对象，直接包装成数组
            content = '[' + content + ']'
    
    # 处理其他格式问题
    content = re.sub(r',\s*}', '}', content)  # 移除对象末尾多余的逗号
    content = re.sub(r',\s*]', ']', content)  # 移除数组末尾多余的逗号
    
    return content

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

def collect_all_fields(data: Dict[str, Any], fieldnames: Set[str], parent_key: str = '', sep: str = '_') -> None:
    """递归收集所有字段名"""
    if not isinstance(data, dict):
        return
        
    for key, value in data.items():
        field_name = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            # 处理嵌套字典
            if key == '_id' and '$oid' in value:
                # MongoDB ObjectId的特殊处理
                fieldnames.add(field_name)
            else:
                # 处理其他嵌套字典
                for sub_key, sub_value in value.items():
                    sub_field = f"{field_name}_{sub_key}"
                    if isinstance(sub_value, (str, int, float, bool)) or sub_value is None:
                        fieldnames.add(sub_field)
                    else:
                        collect_all_fields({sub_key: sub_value}, fieldnames, field_name, sep=sep)
        elif isinstance(value, list):
            # 处理列表
            fieldnames.add(field_name)
        else:
            # 处理基本类型
            fieldnames.add(field_name)

def process_document(doc: Dict[str, Any], fieldnames: Set[str]) -> Dict[str, Any]:
    """处理单个文档，提取和清理字段"""
    processed_doc = {}
    error_fields = []  # 记录处理失败的字段
    
    def clean_text(text: str) -> str:
        """清理文本内容"""
        if not text:
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
    
    try:
        # 处理所有字段
        for field in fieldnames:
            try:
                if field in doc:
                    value = doc[field]
                    if isinstance(value, dict):
                        # 处理嵌套字典
                        if field == '_id' and '$oid' in value:
                            processed_doc[field] = value['$oid']
                        elif field == 'fyTree':
                            # 将法院层级合并为一个字符串
                            courts = []
                            for level in ['L1', 'L2', 'L3', 'L4']:
                                if level in value and value[level]:
                                    courts.append(clean_text(str(value[level])))
                            processed_doc[field] = ' > '.join(courts) if courts else ''
                        else:
                            processed_doc[field] = json.dumps(value, ensure_ascii=False)
                    elif isinstance(value, list):
                        # 处理列表
                        if value:  # 只处理非空列表
                            if all(isinstance(x, dict) for x in value):
                                # 如果是字典列表，展平每个字典
                                flattened_list = []
                                for item in value:
                                    flattened_item = flatten_json(item)
                                    flattened_list.append(json.dumps(flattened_item, ensure_ascii=False))
                                processed_doc[field] = '|'.join(flattened_list)
                            else:
                                # 其他类型的列表，直接连接
                                processed_doc[field] = '|'.join(str(x) for x in value)
                        else:
                            processed_doc[field] = ''
                    elif isinstance(value, str):
                        # 处理字符串
                        processed_doc[field] = clean_text(value)
                    else:
                        # 处理其他类型
                        processed_doc[field] = str(value)
                else:
                    processed_doc[field] = ''
            except Exception as e:
                error_fields.append(field)
                processed_doc[field] = ''
                logging.warning(f"处理字段 {field} 时出错: {str(e)}")
        
        if error_fields:
            logging.warning(f"以下字段处理失败: {', '.join(error_fields)}")
            
        return processed_doc
        
    except Exception as e:
        logging.error(f"处理文档时出错: {str(e)}")
        return {field: '' for field in fieldnames}

def process_input_file(input_file: str) -> List[Dict]:
    """处理输入文件，返回JSON对象列表"""
    try:
        # 读取文件内容
        content, encoding = try_different_encodings(input_file)
        logging.info(f"使用 {encoding} 编码读取文件")
        
        # 修复JSON格式
        content = fix_json_format(content)
        
        # 解析JSON
        try:
            data = json.loads(content)
            if not isinstance(data, list):
                data = [data]
            return data
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析错误: {str(e)}")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"处理输入文件时出错: {str(e)}")
        sys.exit(1)

def collect_fields_with_sampling(docs: List[Dict], sample_size: int = 1000) -> Set[str]:
    """从样本中收集字段名"""
    fieldnames = set()
    
    # 确定采样大小
    sample_size = min(sample_size, len(docs))
    sample_indices = random.sample(range(len(docs)), sample_size)
    
    # 从样本中收集字段
    for i in tqdm(sample_indices, desc="收集字段名"):
        collect_all_fields(docs[i], fieldnames)
    
    return fieldnames

def stream_process_json(input_file: str, output_file: str, batch_size: int = 1000) -> None:
    """流式处理JSON文件并输出为CSV"""
    logger = setup_logging()
    logger.info(f"开始处理文件: {input_file}")
    
    # 创建输出目录（如果不存在）
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 第一次扫描：收集所有字段名
        logger.info("第一次扫描：收集字段名...")
        fieldnames = set()
        
        with open(input_file, 'rb') as f:
            # 使用ijson流式解析JSON
            parser = ijson.parse(f)
            current_object = {}
            current_path = []
            
            for prefix, event, value in parser:
                if event == 'start_map':
                    current_path.append(prefix)
                elif event == 'end_map':
                    if len(current_path) == 1:  # 一个完整的对象
                        collect_all_fields(current_object, fieldnames)
                        current_object = {}
                    current_path.pop()
                elif event == 'map_key':
                    current_path.append(value)
                else:
                    if current_path:
                        # 构建当前字段的完整路径
                        field_path = '_'.join(filter(None, current_path))
                        # 更新当前对象
                        current_dict = current_object
                        for part in current_path[:-1]:
                            if part:
                                current_dict = current_dict.setdefault(part, {})
                        if current_path[-1]:
                            current_dict[current_path[-1]] = value
                    current_path.pop()
        
        logger.info(f"找到 {len(fieldnames)} 个字段")
        
        # 第二次扫描：处理数据并写入CSV
        logger.info("第二次扫描：处理数据并写入CSV...")
        
        # 创建CSV文件并写入表头
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(fieldnames))
            writer.writeheader()
            
            # 重新打开输入文件
            with open(input_file, 'rb') as f:
                # 使用ijson流式解析JSON
                objects = ijson.items(f, 'item')
                
                # 批量处理对象
                batch = []
                total_processed = 0
                
                for obj in objects:
                    # 处理单个对象
                    processed_obj = process_document(obj, fieldnames)
                    batch.append(processed_obj)
                    
                    # 当批次达到指定大小时写入文件
                    if len(batch) >= batch_size:
                        writer.writerows(batch)
                        total_processed += len(batch)
                        logger.info(f"已处理 {total_processed} 条记录")
                        batch = []
                        
                        # 强制刷新文件缓冲区
                        csvfile.flush()
                        
                        # 清理内存
                        gc.collect()
                
                # 写入剩余的对象
                if batch:
                    writer.writerows(batch)
                    total_processed += len(batch)
                    logger.info(f"已处理 {total_processed} 条记录")
        
        logger.info(f"处理完成！输出文件：{output_file}")
        
    except Exception as e:
        logger.error(f"处理文件时出错: {str(e)}")
        sys.exit(1)

def process_directory(input_path: str, output_path: str, batch_size: int = 1000) -> None:
    """处理目录下的所有JSON文件"""
    logger = setup_logging()
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # 确保输出目录存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    if input_path.is_file():
        # 如果输入是文件，直接处理
        if output_path.is_dir():
            output_file = output_path / f"{input_path.stem}.csv"
        else:
            output_file = output_path
        stream_process_json(str(input_path), str(output_file), batch_size)
    elif input_path.is_dir():
        # 如果输入是目录，处理所有JSON文件
        json_files = list(input_path.glob("*.json"))
        logger.info(f"在目录 {input_path} 中找到 {len(json_files)} 个JSON文件")
        
        for json_file in json_files:
            output_file = output_path / f"{json_file.stem}.csv"
            logger.info(f"处理文件: {json_file}")
            stream_process_json(str(json_file), str(output_file), batch_size)
    else:
        logger.error(f"输入路径 {input_path} 不存在")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='JSON转CSV工具 - 支持处理大文件和目录')
    parser.add_argument('input_path', help='输入JSON文件或目录的路径')
    parser.add_argument('output_path', help='输出CSV文件或目录的路径')
    parser.add_argument('--batch-size', type=int, default=1000, help='批处理大小（默认：1000）')
    
    args = parser.parse_args()
    
    process_directory(args.input_path, args.output_path, args.batch_size)

if __name__ == '__main__':
    main() 