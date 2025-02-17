#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据质量检查脚本
支持检查CSV、JSON、Excel、Parquet等格式文件的数据质量
"""
import pandas as pd
import json
import argparse
from pathlib import Path
import logging
import numpy as np
from typing import Dict, List, Optional, Union
import pyarrow.parquet as pq
import psutil
import gc
import os

# 性能优化配置
MEMORY_CHECK_INTERVAL = 100 * 1024 * 1024  # 每处理100MB检查一次内存
MEMORY_THRESHOLD = 80  # 内存使用率警告阈值（百分数）
BATCH_SIZE = 10000  # 默认批处理大小
BUFFER_SIZE = 8192 * 1024  # 8MB文件缓冲区大小

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

class DataQualityChecker:
    """数据质量检查类"""
    
    SUPPORTED_FORMATS = {
        '.csv': '逗号分隔值文件',
        '.json': 'JSON文件',
        '.parquet': 'Parquet文件',
        '.xlsx': 'Excel文件',
        '.xls': 'Excel文件',
        '.txt': '文本文件'  # 新增支持
    }
    
    def __init__(self):
        self.data = None
        self.file_path = None
        self.file_type = None
        self.error_stats = {"errors": [], "error_count": 0}
        
    def record_error(self, error_type: str, message: str):
        """记录错误信息"""
        self.error_stats["errors"].append({
            "type": error_type,
            "message": message,
            "file": str(self.file_path)
        })
        self.error_stats["error_count"] += 1
        logger.error(f"{error_type}: {message}")
        
    def is_supported_format(self, file_path: Path) -> bool:
        """检查文件格式是否支持"""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS
        
    def load_file(self, file_path: Union[str, Path]) -> bool:
        """加载数据文件"""
        self.file_path = Path(file_path)
        self.file_type = self.file_path.suffix.lower()
        
        if not self.file_path.exists():
            self.record_error("FileNotFound", f"文件不存在: {self.file_path}")
            return False
            
        if not self.is_supported_format(self.file_path):
            self.record_error("UnsupportedFormat", f"不支持的文件格式: {self.file_type}")
            logger.info(f"支持的格式: {', '.join(self.SUPPORTED_FORMATS.keys())}")
            return False
        
        try:
            if self.file_type == '.csv':
                self.data = pd.read_csv(file_path, encoding='utf-8')
            elif self.file_type == '.txt':
                # 尝试不同的分隔符
                for sep in [',', '\t', '|', ';']:
                    try:
                        self.data = pd.read_csv(file_path, sep=sep, encoding='utf-8')
                        if len(self.data.columns) > 1:  # 如果成功解析出多列，说明找到了正确的分隔符
                            break
                    except:
                        continue
            elif self.file_type == '.json':
                self.data = pd.read_json(file_path, encoding='utf-8')
            elif self.file_type == '.parquet':
                self.data = pq.read_table(file_path).to_pandas()
            elif self.file_type in ['.xlsx', '.xls']:
                self.data = pd.read_excel(file_path)
                
            if self.data is None:
                self.record_error("LoadError", f"无法解析文件内容: {file_path}")
                return False
                
            # 检查内存使用
            check_memory_usage()
                
            logger.info(f"成功加载文件: {file_path}")
            logger.info(f"数据大小: {len(self.data)} 行, {len(self.data.columns)} 列")
            return True
            
        except Exception as e:
            self.record_error("LoadError", f"加载文件失败: {str(e)}")
            return False
    
    def check_basic_info(self) -> Dict:
        """检查基本信息"""
        return {
            "文件名": self.file_path.name,
            "文件类型": self.file_type,
            "行数": len(self.data),
            "列数": len(self.data.columns),
            "列名": self.data.columns.tolist(),
            "内存占用(MB)": round(self.data.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
    
    def check_null_values(self) -> Dict:
        """检查空值"""
        null_stats = {}
        for col in self.data.columns:
            null_count = self.data[col].isnull().sum()
            null_stats[col] = {
                "空值数量": int(null_count),
                "空值比例": round(float(null_count / len(self.data) * 100), 2)
            }
        return null_stats
    
    def check_duplicates(self) -> Dict:
        """检查重复值"""
        # 全行重复
        full_duplicates = self.data.duplicated().sum()
        # 单列重复
        column_duplicates = {}
        for col in self.data.columns:
            dup_count = self.data[col].duplicated().sum()
            column_duplicates[col] = {
                "重复值数量": int(dup_count),
                "重复值比例": round(float(dup_count / len(self.data) * 100), 2)
            }
            
        return {
            "全行重复数": int(full_duplicates),
            "全行重复比例": round(float(full_duplicates / len(self.data) * 100), 2),
            "单列重复统计": column_duplicates
        }
    
    def check_data_types(self) -> Dict:
        """检查数据类型"""
        type_stats = {}
        for col in self.data.columns:
            type_stats[col] = {
                "数据类型": str(self.data[col].dtype),
                "非空唯一值数量": int(self.data[col].nunique()),
                "示例值": str(self.data[col].iloc[0]) if len(self.data) > 0 else None
            }
        return type_stats
    
    def check_numeric_stats(self) -> Dict:
        """检查数值统计"""
        numeric_stats = {}
        numeric_columns = self.data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            stats = self.data[col].describe()
            numeric_stats[col] = {
                "最小值": float(stats['min']),
                "最大值": float(stats['max']),
                "平均值": float(stats['mean']),
                "中位数": float(stats['50%']),
                "标准差": float(stats['std'])
            }
        return numeric_stats
    
    def check_string_length(self) -> Dict:
        """检查字符串长度"""
        string_stats = {}
        string_columns = self.data.select_dtypes(include=['object']).columns
        
        for col in string_columns:
            lengths = self.data[col].astype(str).str.len()
            string_stats[col] = {
                "最短长度": int(lengths.min()),
                "最长长度": int(lengths.max()),
                "平均长度": round(float(lengths.mean()), 2)
            }
        return string_stats
    
    def run_all_checks(self) -> Dict:
        """运行所有检查"""
        if self.data is None:
            return {"error": "未加载数据文件"}
            
        try:
            results = {
                "基本信息": self.check_basic_info(),
                "空值检查": self.check_null_values(),
                "重复值检查": self.check_duplicates(),
                "数据类型检查": self.check_data_types(),
                "数值统计": self.check_numeric_stats(),
                "字符串长度统计": self.check_string_length(),
                "错误统计": self.error_stats
            }
            
            # 检查内存使用
            check_memory_usage()
            
            return results
            
        except Exception as e:
            self.record_error("CheckError", f"执行检查时出错: {str(e)}")
            return {"error": str(e), "错误统计": self.error_stats}

    def get_single_record(self, file_path: Union[str, Path]) -> Dict:
        """只读取一条记录样例（第二行数据）"""
        self.file_path = Path(file_path)
        self.file_type = self.file_path.suffix.lower()
        
        if not self.file_path.exists():
            return {"error": "文件不存在"}
            
        if not self.is_supported_format(self.file_path):
            return {"error": f"不支持的文件格式: {self.file_type}"}
        
        try:
            # 根据文件类型选择不同的读取方式
            if self.file_type == '.csv':
                # 读取前两行，取第二行
                sample = pd.read_csv(file_path, nrows=2).iloc[1]
            elif self.file_type == '.txt':
                # 尝试不同的分隔符
                for sep in [',', '\t', '|', ';']:
                    try:
                        sample = pd.read_csv(file_path, sep=sep, nrows=2)
                        if len(sample.columns) > 1:  # 如果成功解析出多列
                            sample = sample.iloc[1]
                            break
                    except:
                        continue
            elif self.file_type == '.json':
                # JSON文件特殊处理：读取第一个非空记录
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and line not in ['[', ']', '{', '}']:
                            try:
                                data = json.loads(line)
                                if isinstance(data, dict):
                                    sample = pd.Series(data)
                                elif isinstance(data, list):
                                    sample = pd.Series(data[0] if data else {})
                                break
                            except:
                                continue
            elif self.file_type == '.parquet':
                sample = pq.read_table(file_path, num_rows=2).to_pandas().iloc[1]
            elif self.file_type in ['.xlsx', '.xls']:
                sample = pd.read_excel(file_path, nrows=2).iloc[1]
                
            if sample is None or len(sample) == 0:
                return {"error": "文件为空或无法读取数据"}
                
            # 转换成值的列表
            values = []
            for value in sample:
                if pd.isna(value):
                    values.append(None)
                elif isinstance(value, (np.int64, np.int32)):
                    values.append(int(value))
                elif isinstance(value, (np.float64, np.float32)):
                    values.append(float(value))
                else:
                    values.append(str(value))
                    
            return {"样例记录": values}
            
        except Exception as e:
            return {"error": f"读取文件失败: {str(e)}"}

    def get_summary_stats(self) -> Dict:
        """获取数据质量摘要统计"""
        if self.data is None:
            return {"error": "未加载数据文件"}
            
        # 基本信息
        total_rows = len(self.data)
        total_cols = len(self.data.columns)
        
        # 空值统计
        null_counts = self.data.isnull().sum()
        cols_with_nulls = sum(null_counts > 0)
        total_nulls = null_counts.sum()
        
        # 重复值统计
        full_duplicates = self.data.duplicated().sum()
        
        # 数据类型统计
        dtype_counts = self.data.dtypes.value_counts().to_dict()
        dtype_counts = {str(k): int(v) for k, v in dtype_counts.items()}
        
        # 异常值检测（针对数值列）
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        outlier_stats = {}
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                q1 = self.data[col].quantile(0.25)
                q3 = self.data[col].quantile(0.75)
                iqr = q3 - q1
                outliers = self.data[
                    (self.data[col] < (q1 - 1.5 * iqr)) | 
                    (self.data[col] > (q3 + 1.5 * iqr))
                ]
                if len(outliers) > 0:
                    outlier_stats[col] = len(outliers)
        
        return {
            "数据规模": {
                "总行数": total_rows,
                "总列数": total_cols,
                "文件大小(MB)": round(self.data.memory_usage(deep=True).sum() / 1024 / 1024, 2)
            },
            "数据完整性": {
                "含空值的列数": int(cols_with_nulls),
                "空值总数": int(total_nulls),
                "空值占比": round(float(total_nulls) / (total_rows * total_cols) * 100, 2)
            },
            "数据重复性": {
                "重复行数": int(full_duplicates),
                "重复率": round(float(full_duplicates) / total_rows * 100, 2)
            },
            "数据类型分布": dtype_counts,
            "异常值统计": {
                "含异常值的列数": len(outlier_stats),
                "异常值详情": outlier_stats
            }
        }

def show_help():
    """显示帮助信息"""
    help_text = """
数据质量检查工具使用说明：

功能：
    检查CSV、Excel、JSON、Parquet等格式文件的数据质量，支持单文件和目录批量处理。

支持的文件格式：
    - .csv  : CSV文件
    - .xlsx : Excel文件
    - .xls  : Excel文件
    - .json : JSON文件
    - .parquet : Parquet文件
    - .txt  : 文本文件（自动识别分隔符）

参数说明：
    path          要检查的文件或目录路径
    -o, --output  指定输出结果的JSON文件路径
    -d, --detail  显示详细的检查结果（不能与-s同时使用）
    -s, --sample  只显示随机样例记录，不进行数据分析
    -f, --format  使用格式化输出（更易读的文本格式）
    -h, --help    显示此帮助信息

输出格式：
    默认输出JSON格式，使用 -f 参数可以输出格式化的文本报告。
    如果输出文件扩展名为.txt，将自动使用格式化输出。

使用示例：
    # 检查单个文件
    python data_quality_check.py data.xlsx

    # 检查整个目录
    python data_quality_check.py ./data_directory

    # 保存检查结果到文件
    python data_quality_check.py data.csv -o result.json

    # 显示详细信息
    python data_quality_check.py data.xlsx -d

    # 只显示随机样例记录
    python data_quality_check.py data.csv -s

    # 使用格式化输出
    python data_quality_check.py data.xlsx -f

    # 保存格式化报告
    python data_quality_check.py data.xlsx -f -o report.txt

    # 组合使用（注意：-s不能与-d同时使用）
    python data_quality_check.py data.xlsx -f -o report.txt
"""
    print(help_text)

def get_directory_summary(results: Dict) -> Dict:
    """获取目录的整体统计信息"""
    if not results:
        return {}
        
    # 初始化统计数据
    summary = {
        "文件统计": {
            "总文件数": len(results) - (1 if "目录统计" in results else 0),  # 排除目录统计本身
            "各类型文件数": {},
            "总数据量": {
                "总行数": 0,
                "平均行数": 0,
                "最大行数": 0,
                "最小行数": float('inf'),
                "总大小(MB)": 0
            }
        },
        "数据质量统计": {
            "空值": {
                "总空值数": 0,
                "平均空值率": 0,
                "空值最多的文件": "",
                "最大空值率": 0
            },
            "重复值": {
                "总重复行数": 0,
                "平均重复率": 0,
                "重复最多的文件": "",
                "最大重复率": 0
            },
            "异常值": {
                "含异常值的文件数": 0,
                "总异常值数": 0
            }
        }
    }
    
    # 收集统计数据
    total_rows = 0
    total_nulls_rate = 0
    total_duplicates_rate = 0
    
    for file_path, result in results.items():
        if file_path == "目录统计":  # 跳过目录统计
            continue
            
        # 文件类型统计
        file_type = Path(file_path).suffix
        summary["文件统计"]["各类型文件数"][file_type] = summary["文件统计"]["各类型文件数"].get(file_type, 0) + 1
        
        # 提取基础统计信息
        if "数据规模" in result:
            rows = result["数据规模"]["总行数"]
            total_rows += rows
            summary["文件统计"]["总数据量"]["总行数"] = total_rows
            summary["文件统计"]["总数据量"]["最大行数"] = max(summary["文件统计"]["总数据量"]["最大行数"], rows)
            summary["文件统计"]["总数据量"]["最小行数"] = min(summary["文件统计"]["总数据量"]["最小行数"], rows)
            summary["文件统计"]["总数据量"]["总大小(MB)"] += result["数据规模"]["文件大小(MB)"]
        
        # 空值统计
        if "数据完整性" in result:
            null_rate = result["数据完整性"]["空值占比"]
            total_nulls_rate += null_rate
            if null_rate > summary["数据质量统计"]["空值"]["最大空值率"]:
                summary["数据质量统计"]["空值"]["最大空值率"] = null_rate
                summary["数据质量统计"]["空值"]["空值最多的文件"] = file_path
            summary["数据质量统计"]["空值"]["总空值数"] += result["数据完整性"]["空值总数"]
        
        # 重复值统计
        if "数据重复性" in result:
            dup_rate = result["数据重复性"]["重复率"]
            total_duplicates_rate += dup_rate
            if dup_rate > summary["数据质量统计"]["重复值"]["最大重复率"]:
                summary["数据质量统计"]["重复值"]["最大重复率"] = dup_rate
                summary["数据质量统计"]["重复值"]["重复最多的文件"] = file_path
            summary["数据质量统计"]["重复值"]["总重复行数"] += result["数据重复性"]["重复行数"]
        
        # 异常值统计
        if "异常值统计" in result:
            if result["异常值统计"]["含异常值的列数"] > 0:
                summary["数据质量统计"]["异常值"]["含异常值的文件数"] += 1
                summary["数据质量统计"]["异常值"]["总异常值数"] += sum(result["异常值统计"]["异常值详情"].values())
    
    # 计算平均值
    file_count = len(results) - (1 if "目录统计" in results else 0)
    if file_count > 0:
        summary["文件统计"]["总数据量"]["平均行数"] = round(total_rows / file_count, 2)
        summary["数据质量统计"]["空值"]["平均空值率"] = round(total_nulls_rate / file_count, 2)
        summary["数据质量统计"]["重复值"]["平均重复率"] = round(total_duplicates_rate / file_count, 2)
    
    # 处理没有找到文件的情况
    if summary["文件统计"]["总数据量"]["最小行数"] == float('inf'):
        summary["文件统计"]["总数据量"]["最小行数"] = 0
    
    return summary

def process_path(path: Union[str, Path], checker: DataQualityChecker, args) -> Dict:
    """处理文件或目录"""
    path = Path(path)
    results = {}
    
    if path.is_file():
        if args.sample:
            # 只读取一条记录
            results[str(path)] = checker.get_single_record(path)
        else:
            # 正常的数据质量检查
            if checker.load_file(path):
                result = checker.run_all_checks() if args.detail else checker.get_summary_stats()
                results[str(path)] = result
    elif path.is_dir():
        # 递归处理目录下的所有支持格式的文件
        for file_path in path.rglob("*"):
            if file_path.is_file() and checker.is_supported_format(file_path):
                if args.sample:
                    # 只读取一条记录
                    results[str(file_path)] = checker.get_single_record(file_path)
                else:
                    # 正常的数据质量检查
                    if checker.load_file(file_path):
                        result = checker.run_all_checks() if args.detail else checker.get_summary_stats()
                        results[str(file_path)] = result
        
        # 如果不是样例模式，且有结果，添加目录统计
        if not args.sample and results:
            results["目录统计"] = get_directory_summary(results)
    else:
        logger.error(f"路径不存在: {path}")
    
    return results

def format_number(num: float) -> str:
    """格式化数字输出"""
    if isinstance(num, (int, np.integer)):
        return f"{num:,}"
    return f"{num:,.2f}"

def format_report(results: Dict, is_detail: bool = False) -> str:
    """格式化报告输出
    Args:
        results: 检查结果
        is_detail: 是否显示详细信息
    Returns:
        格式化后的报告文本
    """
    report = []
    
    for file_path, result in results.items():
        if file_path == "目录统计":
            report.append("\n" + "=" * 80)
            report.append("目录统计报告")
            report.append("=" * 80)
            
            # 文件统计
            file_stats = result["文件统计"]
            report.append("\n📊 文件统计")
            report.append(f"总文件数: {format_number(file_stats['总文件数'])} 个")
            report.append("\n文件类型分布:")
            for ftype, count in file_stats["各类型文件数"].items():
                report.append(f"  {ftype}: {count} 个")
            
            # 数据量统计
            data_stats = file_stats["总数据量"]
            report.append("\n📈 数据规模")
            report.append(f"总行数: {format_number(data_stats['总行数'])} 行")
            report.append(f"平均行数: {format_number(data_stats['平均行数'])} 行")
            report.append(f"最大行数: {format_number(data_stats['最大行数'])} 行")
            report.append(f"最小行数: {format_number(data_stats['最小行数'])} 行")
            report.append(f"总大小: {format_number(data_stats['总大小(MB)'])} MB")
            
            # 数据质量统计
            quality_stats = result["数据质量统计"]
            report.append("\n🔍 数据质量")
            
            # 空值统计
            null_stats = quality_stats["空值"]
            report.append("\n空值统计:")
            report.append(f"  总空值数: {format_number(null_stats['总空值数'])}")
            report.append(f"  平均空值率: {format_number(null_stats['平均空值率'])}%")
            report.append(f"  最大空值率: {format_number(null_stats['最大空值率'])}%")
            report.append(f"  空值最多的文件: {Path(null_stats['空值最多的文件']).name}")
            
            # 重复值统计
            dup_stats = quality_stats["重复值"]
            report.append("\n重复值统计:")
            report.append(f"  总重复行数: {format_number(dup_stats['总重复行数'])}")
            report.append(f"  平均重复率: {format_number(dup_stats['平均重复率'])}%")
            report.append(f"  最大重复率: {format_number(dup_stats['最大重复率'])}%")
            report.append(f"  重复最多的文件: {Path(dup_stats['重复最多的文件']).name}")
            
            # 异常值统计
            outlier_stats = quality_stats["异常值"]
            report.append("\n异常值统计:")
            report.append(f"  含异常值的文件数: {format_number(outlier_stats['含异常值的文件数'])}")
            report.append(f"  总异常值数: {format_number(outlier_stats['总异常值数'])}")
            
        else:
            # 单个文件的统计
            report.append("\n" + "-" * 80)
            report.append(f"文件: {Path(file_path).name}")
            report.append("-" * 80)
            
            if "error" in result:
                report.append(f"错误: {result['error']}")
                continue
            
            # 基本信息
            data_size = result["数据规模"]
            report.append(f"\n📊 数据规模")
            report.append(f"总行数: {format_number(data_size['总行数'])} 行")
            report.append(f"总列数: {format_number(data_size['总列数'])} 列")
            report.append(f"文件大小: {format_number(data_size['文件大小(MB)'])} MB")
            
            # 数据完整性
            completeness = result["数据完整性"]
            report.append(f"\n🔍 数据完整性")
            report.append(f"含空值的列数: {format_number(completeness['含空值的列数'])}")
            report.append(f"空值总数: {format_number(completeness['空值总数'])}")
            report.append(f"空值占比: {format_number(completeness['空值占比'])}%")
            
            # 数据重复性
            duplicates = result["数据重复性"]
            report.append(f"\n🔄 数据重复性")
            report.append(f"重复行数: {format_number(duplicates['重复行数'])}")
            report.append(f"重复率: {format_number(duplicates['重复率'])}%")
            
            # 数据类型分布
            report.append(f"\n📋 数据类型分布")
            for dtype, count in result["数据类型分布"].items():
                report.append(f"{dtype}: {count} 列")
            
            # 异常值统计
            outliers = result["异常值统计"]
            report.append(f"\n⚠️ 异常值统计")
            report.append(f"含异常值的列数: {outliers['含异常值的列数']}")
            if outliers['异常值详情']:
                report.append("异常值详情:")
                for col, count in outliers['异常值详情'].items():
                    report.append(f"  {col}: {format_number(count)} 个")
            
            # 样例记录
            if "样例记录" in result:
                report.append(f"\n📝 随机样例记录")
                for value in result["样例记录"]:
                    report.append(f"{value}")
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="数据质量检查工具", add_help=False)
    parser.add_argument('path', nargs='?', help="要检查的文件或目录路径")
    parser.add_argument('--output', '-o', help="输出结果的JSON文件路径")
    parser.add_argument('--detail', '-d', action='store_true', help="是否显示详细信息（不能与-s同时使用）")
    parser.add_argument('--sample', '-s', action='store_true', help="只显示随机样例记录，不进行数据分析")
    parser.add_argument('--help', '-h', action='store_true', help="显示帮助信息")
    parser.add_argument('--format', '-f', action='store_true', help="是否使用格式化输出")
    
    args = parser.parse_args()
    
    # 显示帮助信息
    if args.help or not args.path:
        show_help()
        return
    
    # 检查参数冲突
    if args.sample and args.detail:
        logger.error("参数错误：-s（样例模式）不能与-d（详细模式）同时使用")
        return
    
    # 创建检查器实例
    checker = DataQualityChecker()
    
    # 处理文件或目录
    results = process_path(args.path, checker, args)
    
    # 输出结果
    if results:
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 根据输出文件扩展名决定格式
            if args.format or output_path.suffix == '.txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(format_report(results, args.detail))
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存到: {output_path}")
        else:
            if args.format:
                print(format_report(results, args.detail))
            else:
                print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        logger.error("没有找到可处理的文件")

if __name__ == "__main__":
    main() 