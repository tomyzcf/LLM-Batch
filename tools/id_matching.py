import os
import csv
import glob
import argparse
from pathlib import Path
import logging
from contextlib import contextmanager
import sys

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 增加CSV字段大小限制
maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)

@contextmanager
def safe_open_file(file_path, mode='r', encoding='utf-8'):
    """安全地打开和关闭文件"""
    file = None
    try:
        file = open(file_path, mode, encoding=encoding, errors='replace')
        yield file
    finally:
        if file:
            file.close()

def process_csv_file(file_path, reference_ids, output_dir, check_key_column, output_type):
    """处理单个CSV文件
    output_type: 'unmatched' - 只输出未匹配的数据
                'matched' - 只输出匹配的数据
                'both' - 同时输出匹配和未匹配的数据
    """
    file_name = os.path.basename(file_path)
    file_name_without_ext, file_ext = os.path.splitext(file_name)
    
    # 根据输出类型设置输出文件路径
    output_files = {}
    if output_type in ['unmatched', 'both']:
        output_files['unmatched'] = os.path.join(output_dir, f"{file_name_without_ext}_unmatched{file_ext}")
    if output_type in ['matched', 'both']:
        output_files['matched'] = os.path.join(output_dir, f"{file_name_without_ext}_matched{file_ext}")
    
    unmatched_count = 0
    matched_count = 0
    skipped_stats = {
        'empty_row': 0,      # 空行
        'insufficient_cols': 0,  # 列数不足
        'empty_id': 0,       # 空ID
        'processing_error': 0    # 处理错误
    }
    
    try:
        # 打开输入文件和输出文件
        with safe_open_file(file_path, 'r', 'utf-8') as f_in:
            csv_reader = csv.reader(f_in)
            
            # 打开所有需要的输出文件
            output_handles = {}
            csv_writers = {}
            for output_type, file_path in output_files.items():
                output_handles[output_type] = open(file_path, 'w', encoding='utf-8', newline='')
                csv_writers[output_type] = csv.writer(output_handles[output_type])
            
            # 读取并写入表头
            header = next(csv_reader, None)
            if header:
                for writer in csv_writers.values():
                    writer.writerow(header)
            
            # 处理每一行
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    if not row:  # 跳过空行
                        skipped_stats['empty_row'] += 1
                        continue
                        
                    if len(row) <= check_key_column:
                        logger.warning(f"文件 {file_name} 第 {row_num} 行数据列数不足")
                        skipped_stats['insufficient_cols'] += 1
                        continue
                    
                    row_id = row[check_key_column].strip()
                    if not row_id:  # 跳过空ID
                        skipped_stats['empty_id'] += 1
                        continue
                    
                    # 根据ID匹配情况写入相应的输出文件
                    if row_id not in reference_ids:
                        if 'unmatched' in csv_writers:
                            csv_writers['unmatched'].writerow(row)
                            unmatched_count += 1
                    else:
                        if 'matched' in csv_writers:
                            csv_writers['matched'].writerow(row)
                            matched_count += 1
                except Exception as e:
                    logger.error(f"处理文件 {file_name} 第 {row_num} 行时出错: {e}")
                    skipped_stats['processing_error'] += 1
                    continue
            
            # 关闭所有输出文件
            for handle in output_handles.values():
                handle.close()
            
            # 删除空文件
            for output_type, file_path in output_files.items():
                if output_type == 'unmatched' and unmatched_count == 0:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"删除空文件 {file_path}")
                elif output_type == 'matched' and matched_count == 0:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"删除空文件 {file_path}")
            
            return unmatched_count, matched_count, skipped_stats
                
    except Exception as e:
        logger.error(f"处理文件 {file_path} 时出错: {e}")
        raise

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='比较两个目录中CSV文件的ID，输出匹配和未匹配的数据')
    parser.add_argument('-r', '--reference-dir', type=str, 
                        default=r"E:\Projects\leagle\inputData\leagle\6-final-output",
                        help='参考目录路径，包含基准ID的CSV文件')
    parser.add_argument('-c', '--check-dir', type=str, 
                        default=r"E:\Projects\leagle\inputData\leagle\5-model-output",
                        help='待检查目录路径，包含需要比对的CSV文件')
    parser.add_argument('-o', '--output-dir', type=str, 
                        default=r"E:\Projects\leagle\inputData\leagle\results",
                        help='结果保存目录')
    parser.add_argument('-rk', '--reference-key-column', type=int, default=0,
                        help='参考目录CSV文件中用于匹配的列索引（从0开始）')
    parser.add_argument('-ck', '--check-key-column', type=int, default=0,
                        help='待检查目录CSV文件中用于匹配的列索引（从0开始）')
    parser.add_argument('-t', '--output-type', type=str, choices=['unmatched', 'matched', 'both'],
                        default='unmatched',
                        help='输出类型：unmatched-只输出未匹配的数据，matched-只输出匹配的数据，both-同时输出匹配和未匹配的数据')
    
    args = parser.parse_args()
    
    # 定义目录路径
    reference_dir = args.reference_dir
    check_dir = args.check_dir
    output_dir = args.output_dir
    reference_key_column = args.reference_key_column
    check_key_column = args.check_key_column
    output_type = args.output_type
    
    # 确保结果目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"正在从参考目录 {reference_dir} 中收集ID...")
    # 收集参考目录中所有文件指定列的ID
    reference_ids = set()
    for file_path in glob.glob(os.path.join(reference_dir, "*.csv")):
        try:
            with safe_open_file(file_path, 'r', 'utf-8') as f:
                csv_reader = csv.reader(f)
                # 跳过头行（如果有）
                next(csv_reader, None)
                
                for row in csv_reader:
                    if row and len(row) > reference_key_column and row[reference_key_column].strip():
                        reference_ids.add(row[reference_key_column].strip())
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
    
    logger.info(f"从参考数据中收集到 {len(reference_ids)} 个唯一ID")
    
    # 创建字典，用于跟踪每个文件中匹配和未匹配的行计数
    unmatched_counts = {}
    matched_counts = {}
    skipped_stats = {}
    
    # 处理待检查目录中的文件，查找匹配和未匹配的ID
    logger.info(f"正在处理待检查目录 {check_dir} 中的文件...")
    for file_path in glob.glob(os.path.join(check_dir, "*.csv")):
        file_name = os.path.basename(file_path)
        try:
            unmatched_count, matched_count, file_skipped_stats = process_csv_file(
                file_path, reference_ids, output_dir, check_key_column, output_type
            )
            
            unmatched_counts[file_name] = unmatched_count
            matched_counts[file_name] = matched_count
            skipped_stats[file_name] = file_skipped_stats
            
            total_skipped = sum(file_skipped_stats.values())
            logger.info(f"文件 {file_name} 处理完成: {unmatched_count} 行未匹配，{matched_count} 行匹配，{total_skipped} 行被跳过")
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时发生错误: {e}")
    
    # 创建一个摘要文件
    summary_file_path = os.path.join(output_dir, "matching_summary.txt")
    with safe_open_file(summary_file_path, 'w', 'utf-8') as f:
        f.write("ID匹配统计摘要:\n")
        f.write("-" * 50 + "\n")
        f.write(f"参考目录 ({reference_dir}) 中共有 {len(reference_ids)} 个唯一ID\n")
        f.write(f"参考数据使用列索引 {reference_key_column} 进行匹配\n")
        f.write(f"待检查目录 ({check_dir}) 使用列索引 {check_key_column} 进行匹配\n")
        f.write(f"输出类型: {output_type}\n")
        f.write("-" * 50 + "\n")
        
        # 写入未匹配统计
        if output_type in ['unmatched', 'both']:
            f.write("每个文件中未匹配的行数:\n")
            total_unmatched = sum(unmatched_counts.values())
            for file_name, count in sorted(unmatched_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{file_name}: {count}\n")
            f.write(f"总计未匹配行数: {total_unmatched}\n")
        
        # 写入跳过的行数统计
        f.write("-" * 50 + "\n")
        f.write("跳过的行数统计:\n")
        
        # 统计所有类型的跳过行数
        total_skipped_by_type = {
            'empty_row': 0,
            'insufficient_cols': 0,
            'empty_id': 0,
            'processing_error': 0
        }
        
        for file_name, stats in skipped_stats.items():
            f.write(f"\n文件 {file_name}:\n")
            for error_type, count in stats.items():
                total_skipped_by_type[error_type] += count
                error_desc = {
                    'empty_row': '空行',
                    'insufficient_cols': '列数不足',
                    'empty_id': '空ID',
                    'processing_error': '处理错误'
                }
                f.write(f"  {error_desc[error_type]}: {count}\n")
        
        f.write("\n总计:\n")
        for error_type, count in total_skipped_by_type.items():
            error_desc = {
                'empty_row': '空行',
                'insufficient_cols': '列数不足',
                'empty_id': '空ID',
                'processing_error': '处理错误'
            }
            f.write(f"{error_desc[error_type]}: {count}\n")
        f.write(f"总计跳过的行数: {sum(total_skipped_by_type.values())}\n")
        
        # 写入匹配统计
        if output_type in ['matched', 'both']:
            f.write("-" * 50 + "\n")
            f.write("每个文件中匹配的行数:\n")
            total_matched = sum(matched_counts.values())
            for file_name, count in sorted(matched_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{file_name}: {count}\n")
            f.write(f"总计匹配行数: {total_matched}\n")
    
    logger.info(f"处理完成！结果已保存到 {output_dir} 目录")
    logger.info(f"摘要信息已保存到 {summary_file_path}")

if __name__ == "__main__":
    main() 