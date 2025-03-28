import os
import csv
import glob
import argparse
from pathlib import Path

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
    parser.add_argument('--matched', action='store_true',
                        help='是否输出匹配的数据（默认只输出未匹配的数据）')
    
    args = parser.parse_args()
    
    # 定义目录路径
    reference_dir = args.reference_dir
    check_dir = args.check_dir
    output_dir = args.output_dir
    reference_key_column = args.reference_key_column
    check_key_column = args.check_key_column
    output_matched = args.matched
    
    # 确保结果目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"正在从参考目录 {reference_dir} 中收集ID...")
    # 收集参考目录中所有文件指定列的ID
    reference_ids = set()
    for file_path in glob.glob(os.path.join(reference_dir, "*.csv")):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                csv_reader = csv.reader(f)
                # 跳过头行（如果有）
                next(csv_reader, None)
                
                for row in csv_reader:
                    if row and len(row) > reference_key_column and row[reference_key_column].strip():
                        reference_ids.add(row[reference_key_column].strip())
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
    
    print(f"从参考数据中收集到 {len(reference_ids)} 个唯一ID")
    
    # 创建字典，用于跟踪每个文件中匹配和未匹配的行计数
    unmatched_counts = {}
    matched_counts = {}
    
    # 处理待检查目录中的文件，查找匹配和未匹配的ID
    print(f"正在处理待检查目录 {check_dir} 中的文件...")
    for file_path in glob.glob(os.path.join(check_dir, "*.csv")):
        file_name = os.path.basename(file_path)
        file_name_without_ext, file_ext = os.path.splitext(file_name)
        
        # 未匹配数据的输出文件路径
        unmatched_file_path = os.path.join(output_dir, f"{file_name_without_ext}_unmatched{file_ext}")
        # 匹配数据的输出文件路径（如果需要）
        matched_file_path = os.path.join(output_dir, f"{file_name_without_ext}_matched{file_ext}") if output_matched else None
        
        unmatched_count = 0
        matched_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_in, \
                 open(unmatched_file_path, 'w', encoding='utf-8', newline='') as f_unmatched:
                
                csv_reader = csv.reader(f_in)
                csv_unmatched_writer = csv.writer(f_unmatched)
                
                # 如果需要输出匹配数据，打开匹配文件
                f_matched = None
                csv_matched_writer = None
                if output_matched:
                    f_matched = open(matched_file_path, 'w', encoding='utf-8', newline='')
                    csv_matched_writer = csv.writer(f_matched)
                
                # 读取并写入表头
                header = next(csv_reader, None)
                if header:
                    csv_unmatched_writer.writerow(header)
                    if output_matched and csv_matched_writer:
                        csv_matched_writer.writerow(header)
                
                # 处理每一行
                for row in csv_reader:
                    if row and len(row) > check_key_column:
                        row_id = row[check_key_column].strip()
                        if row_id:
                            # 如果ID不在参考ID集合中，写入未匹配结果文件
                            if row_id not in reference_ids:
                                csv_unmatched_writer.writerow(row)
                                unmatched_count += 1
                            elif output_matched and csv_matched_writer:
                                # 如果ID在参考ID集合中且需要输出匹配数据，写入匹配结果文件
                                csv_matched_writer.writerow(row)
                                matched_count += 1
            
            # 关闭匹配文件（如果打开）
            if output_matched and f_matched:
                f_matched.close()
            
            unmatched_counts[file_name] = unmatched_count
            matched_counts[file_name] = matched_count
            
            print(f"文件 {file_name} 中有 {unmatched_count} 行未匹配，{matched_count} 行匹配")
            
            # 如果没有未匹配的行(只有表头)，删除未匹配文件
            if unmatched_count == 0:
                os.remove(unmatched_file_path)
                print(f"删除空文件 {unmatched_file_path}")
            
            # 如果没有匹配的行(只有表头)且需要输出匹配数据，删除匹配文件
            if output_matched and matched_count == 0 and matched_file_path:
                if os.path.exists(matched_file_path):
                    os.remove(matched_file_path)
                    print(f"删除空文件 {matched_file_path}")
                
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
    
    # 创建一个摘要文件
    summary_file_path = os.path.join(output_dir, "matching_summary.txt")
    with open(summary_file_path, 'w', encoding='utf-8') as f:
        f.write("ID匹配统计摘要:\n")
        f.write("-" * 50 + "\n")
        f.write(f"参考目录 ({reference_dir}) 中共有 {len(reference_ids)} 个唯一ID\n")
        f.write(f"参考数据使用列索引 {reference_key_column} 进行匹配\n")
        f.write(f"待检查目录 ({check_dir}) 使用列索引 {check_key_column} 进行匹配\n")
        f.write("-" * 50 + "\n")
        
        # 写入未匹配统计
        f.write("每个文件中未匹配的行数:\n")
        total_unmatched = sum(unmatched_counts.values())
        for file_name, count in sorted(unmatched_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{file_name}: {count}\n")
        f.write(f"总计未匹配行数: {total_unmatched}\n")
        
        # 如果输出匹配数据，写入匹配统计
        if output_matched:
            f.write("-" * 50 + "\n")
            f.write("每个文件中匹配的行数:\n")
            total_matched = sum(matched_counts.values())
            for file_name, count in sorted(matched_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{file_name}: {count}\n")
            f.write(f"总计匹配行数: {total_matched}\n")
    
    print(f"处理完成！结果已保存到 {output_dir} 目录")
    print(f"摘要信息已保存到 {summary_file_path}")

if __name__ == "__main__":
    main() 