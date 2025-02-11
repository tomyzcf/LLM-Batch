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

def collect_all_fields(data: Dict[str, Any], fieldnames: Set[str], prefix: str = '') -> None:
    """递归收集所有字段名"""
    if not isinstance(data, dict):
        return
        
    for key, value in data.items():
        field_name = f"{prefix}{key}" if prefix else key
        
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
                        collect_all_fields({sub_key: sub_value}, fieldnames, f"{field_name}_")
        elif isinstance(value, list):
            # 处理列表
            fieldnames.add(field_name)
        else:
            # 处理基本类型
            fieldnames.add(field_name)

def process_document(doc: Dict[str, Any], fieldnames: Set[str]) -> Dict[str, Any]:
    """处理单个文档，提取和清理字段"""
    processed_doc = {}
    
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
                    if all(isinstance(x, dict) for x in value):
                        # 如果列表中都是字典,转换为JSON字符串
                        processed_doc[field] = json.dumps(value, ensure_ascii=False)
                    else:
                        # 否则用分号连接,并确保每个元素都是字符串
                        processed_doc[field] = ';'.join(clean_text(str(x)) for x in value)
                elif isinstance(value, str):
                    # 处理字符串
                    # 1. 清理HTML内容
                    if field == 'qwContent':
                        value = clean_html(value)
                    # 2. 清理文本
                    value = clean_text(value)
                    # 3. 处理JSON字符串
                    if field in ['s47', 'wenshuAy'] and value.startswith('['):
                        try:
                            data = json.loads(value)
                            value = json.dumps(data, ensure_ascii=False)
                        except:
                            pass
                    processed_doc[field] = value
                else:
                    # 处理其他类型(数字、布尔等)
                    processed_doc[field] = str(value) if value is not None else ''
            else:
                processed_doc[field] = ''
        
        # 处理文书正文部分
        for field in ['s22', 's23', 's25', 's26', 's27', 's28']:
            if field in doc and doc[field] is not None:
                processed_doc[field] = clean_text(str(doc[field]))
        
    except Exception as e:
        logger.error(f"处理文档时出错: {str(e)}")
        logger.debug(f"问题文档: {json.dumps(doc, ensure_ascii=False)}")
        # 返回尽可能多的已处理字段
        return processed_doc
    
    return processed_doc

def process_input_file(input_file: str) -> List[Dict]:
    """处理输入文件，包括编码修复和JSON解析"""
    logger = logging.getLogger(__name__)
    processed_docs = []
    
    try:
        # 1. 获取文件大小用于进度显示
        file_size = os.path.getsize(input_file)
        logger.info(f"开始处理文件，总大小: {file_size / (1024*1024):.2f} MB")
        
        # 2. 检测和修复文件编码
        logger.info("开始检测文件编码...")
        with open(input_file, 'rb') as f:
            sample = f.read(32768)  # 读取32KB
            result = chardet.detect(sample)
            encoding = result['encoding'] or 'utf-8'
            confidence = result['confidence']
            logger.info(f"检测到编码: {encoding}, 置信度: {confidence}")
            
        # 3. 使用更健壮的方式解析JSON
        logger.info("开始解析JSON文件...")
        with open(input_file, 'r', encoding=encoding) as f:
            content = f.read().strip()
            
            # 显示读取进度
            with tqdm(total=len(content), desc="读取进度", unit='B', unit_scale=True) as pbar:
                # 尝试直接解析
                try:
                    data = json.loads(content)
                    pbar.update(len(content))
                    # 如果是单个对象，转换为列表
                    if isinstance(data, dict):
                        processed_docs = [data]
                        logger.info("成功解析单个JSON对象")
                    else:
                        processed_docs = data
                        logger.info(f"成功解析JSON数组，包含 {len(processed_docs)} 个文档")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败，尝试修复格式: {str(e)}")
                    # 如果解析失败，尝试修复格式
                    if not content.startswith('['):
                        content = '[' + content
                    if not content.endswith(']'):
                        content = content + ']'
                    # 修复对象之间缺少逗号的问题
                    content = re.sub(r'}\s*{', '},{', content)
                    
                    try:
                        data = json.loads(content)
                        pbar.update(len(content))
                        processed_docs = data if isinstance(data, list) else [data]
                        logger.info(f"通过格式修复成功解析 {len(processed_docs)} 个文档")
                    except json.JSONDecodeError as e:
                        logger.error(f"格式修复后仍然解析失败，尝试逐行解析: {str(e)}")
                        # 如果整体解析失败，尝试逐行解析
                        lines = re.split(r'}\s*{', content.strip('[]'))
                        for i, line in enumerate(lines):
                            line = line.strip()
                            if not line:
                                continue
                            if not line.startswith('{'):
                                line = '{' + line
                            if not line.endswith('}'):
                                line = line + '}'
                            try:
                                doc = json.loads(line)
                                if isinstance(doc, dict):
                                    processed_docs.append(doc)
                            except json.JSONDecodeError:
                                logger.warning(f"无法解析第 {i + 1} 行")
                                continue
                            
                            # 更新进度
                            pbar.update(len(line) + 1)
                            
                            # 定期清理内存
                            if len(processed_docs) % 1000 == 0:
                                gc.collect()
                        
                        if processed_docs:
                            logger.info(f"通过逐行解析成功解析 {len(processed_docs)} 个文档")
                        else:
                            logger.error("所有解析方法都失败")
            
    except Exception as e:
        logger.error(f"处理文件时出错: {str(e)}")
    
    return processed_docs

def json_to_csv(input_file: str, output_file: str, batch_size: int = 1000) -> None:
    """将JSON文件转换为CSV文件"""
    logger = logging.getLogger(__name__)
    fieldnames: Set[str] = set()
    
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 处理输入文件
        logger.info("开始处理输入文件...")
        all_docs = process_input_file(input_file)
        
        if not all_docs:
            logger.error("未找到有效文档")
            return
            
        doc_count = len(all_docs)
        logger.info(f"成功读取 {doc_count} 个有效文档")
        
        # 收集字段名
        for doc in tqdm(all_docs, desc="收集字段名"):
            collect_all_fields(doc, fieldnames)
            # 定期清理内存
            if all_docs.index(doc) % 1000 == 0:
                gc.collect()
        
        logger.info(f"找到 {len(fieldnames)} 个字段")
        
        # 写入CSV
        logger.info("开始写入CSV...")
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.writer(
                csvfile,
                quoting=csv.QUOTE_ALL,
                escapechar='\\',
                doublequote=True
            )
            writer.writerow(list(fieldnames))
            
            # 写入数据
            for doc in tqdm(all_docs, desc="写入CSV"):
                processed_doc = process_document(doc, fieldnames)
                row = []
                for field in fieldnames:
                    value = processed_doc.get(field, '')
                    value = str(value).replace('\n', ' ').replace('\r', ' ')
                    row.append(value)
                
                writer.writerow(row)
                
                # 定期清理内存
                if all_docs.index(doc) % 1000 == 0:
                    gc.collect()
        
        logger.info(f"成功处理完成，共写入 {doc_count} 个文档")
    
    except Exception as e:
        logger.error(f"处理文件时出错: {str(e)}")
        raise

def stream_json_file(file_path: str, batch_size: int = 1000) -> Generator[List[Dict], None, None]:
    """流式读取JSON文件"""
    batch = []
    logger = logging.getLogger(__name__)
    
    try:
        with open(file_path, 'rb') as file:
            # 检测文件编码
            raw_data = file.read(4096)
            result = chardet.detect(raw_data)
            file.seek(0)
            
            # 使用检测到的编码读取文件
            encoding = result['encoding'] or 'utf-8'
            logger.info(f"检测到文件编码: {encoding}")
            
            # 读取文件内容
            content = file.read().decode(encoding)
            
            # 解析JSON
            data = json.loads(content)
            if not isinstance(data, list):
                data = [data]
            
            # 分批处理
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                yield batch
                
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"读取文件时出错: {str(e)}")
        if batch:  # 如果还有未处理的数据，尝试返回
            yield batch
        raise

def read_json_file(file_path):
    """读取JSON文件并处理编码问题"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("开始读取文件...")
        
        # 1. 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 2. 预处理内容
        content = content.strip()
        if content.startswith('\ufeff'):
            content = content[1:]  # 移除BOM
            
        # 3. 尝试解析JSON
        try:
            data = json.loads(content)
            # 如果是单个对象,转换为列表
            if isinstance(data, dict):
                data = [data]
                logger.info("成功解析单个JSON对象")
            else:
                logger.info(f"成功解析JSON数组,包含 {len(data)} 个对象")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {str(e)}")
            # 尝试修复JSON格式
            try:
                # 如果内容以{开头,说明是单个对象
                if content.strip().startswith('{'):
                    fixed_content = content.strip()
                    if not fixed_content.endswith('}'):
                        fixed_content += '}'
                    data = json.loads(fixed_content)
                    return [data]
                else:
                    # 否则尝试作为数组修复
                    fixed_content = fix_json_format(content)
                    data = json.loads(fixed_content)
                    if isinstance(data, dict):
                        return [data]
                    return data
            except Exception as fix_error:
                logger.error(f"修复JSON格式失败: {str(fix_error)}")
                return []
                
    except Exception as e:
        logger.error(f"读取文件时出错: {str(e)}")
        return []

def aggressive_fix_json(content):
    """更激进的JSON修复方法"""
    # 移除可能导致问题的控制字符
    content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
    
    # 修复引号问题
    content = re.sub(r'(?<!\\)"(?!,|\s*}|\s*]|\s*:)', '\\"', content)
    
    # 修复逗号问题
    content = re.sub(r',(\s*[}\]])', r'\1', content)  # 移除对象/数组末尾多余的逗号
    content = re.sub(r'([}\]])\s*([{\[])', r'\1,\2', content)  # 添加缺失的逗号
    
    # 修复花括号和方括号
    if not (content.startswith('{') or content.startswith('[')):
        content = '{' + content
    if not (content.endswith('}') or content.endswith(']')):
        content = content + '}'
    
    # 确保最外层是数组
    if content.startswith('{'):
        content = '[' + content + ']'
    
    return content

def main():
    parser = argparse.ArgumentParser(description='将JSON文件转换为CSV格式')
    parser.add_argument('input_file', help='输入的JSON文件路径')
    parser.add_argument('output_file', help='输出的CSV文件路径')
    parser.add_argument('--batch-size', type=int, default=1000, help='批处理大小')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        json_to_csv(args.input_file, args.output_file, args.batch_size)
    except Exception as e:
        logger.error(f"转换失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 