# 数据处理工具集

[English](README.md) | [中文](README_zh.md)

本目录包含一系列用于数据处理的独立工具脚本。每个工具都支持大文件处理和性能优化。

## 工具列表

### 1. CSV分割管理器 (csv_splitter_manager.py)
CSV文件分割和管理工具，支持以下功能：
- 按行数/大小/百分比分割
- 按日期列分割（支持自定义日期格式）
- 列管理（删除指定列）
- 支持大文件分块处理
- 内存使用优化

使用示例：
```bash
# 显示帮助信息
python csv_splitter_manager.py -h

# 显示CSV文件的列名
python csv_splitter_manager.py input.csv --show-columns

# 按行数分割（每1000行一个文件）
python csv_splitter_manager.py input.csv --split-rows 1000 --output output_prefix

# 按大小分割（每个文件10MB）
python csv_splitter_manager.py input.csv --split-size 10 --output output_prefix

# 按百分比分割（60%/40%）
python csv_splitter_manager.py input.csv --split-percent 60 --output output_prefix

# 按日期列分割
python csv_splitter_manager.py input.csv --split-date "date_column" --date-format "%Y-%m-%d" --output output_prefix
```

### 2. JSON格式化工具 (json_format.py)
JSON文件处理工具：
- 支持大文件流式处理
- 自动处理嵌套结构
- 支持批量处理
- 内存使用优化

### 3. 数据格式转换工具 (data_converter.py)
通用数据格式转换工具：
- 支持JSON、CSV、Excel和Parquet格式之间的转换
- 自动检测输入文件格式
- 支持目录批量转换
- 处理嵌套数据结构
- 大文件流式处理
- 内存优化处理大数据集

使用示例：
```bash
# 显示帮助信息
python data_converter.py -h

# 转换单个文件（自动检测输入格式，默认输出为CSV）
python data_converter.py input.json
python data_converter.py input.xlsx --output-format parquet

# 转换目录（自动检测输入格式，默认输出为CSV）
python data_converter.py input_dir

# 指定自定义输出路径
python data_converter.py input.json --output-path custom/output.csv

# 使用自定义批处理大小
python data_converter.py large_data.json --batch-size 5000

# 显示格式转换指南
python data_converter.py --guide
```

### 4. 数据质量检查工具 (data_quality_check.py)
数据质量检查工具：
- 支持多种文件格式
- 数据完整性检查
- 异常值检测
- 生成质量报告

### 5. ID匹配工具 (id_matching.py)
CSV文件ID匹配比对工具：
- 比较两个目录中CSV文件的ID字段
- 输出匹配和未匹配的数据
- 支持自定义匹配列
- 生成详细的匹配统计报告
- 支持大文件处理

使用示例：
```bash
# 显示帮助信息
python id_matching.py -h

# 使用默认配置运行
python id_matching.py

# 指定参考目录和待检查目录
python id_matching.py -r "参考目录路径" -c "待检查目录路径" -o "结果输出目录路径"

# 指定匹配列（使用第二列进行匹配）
python id_matching.py -rk 1 -ck 1

# 同时输出匹配和未匹配的数据
python id_matching.py --matched

# 组合使用多个参数
python id_matching.py -r "参考目录" -c "待检查目录" -o "结果目录" -rk 2 -ck 1 --matched
```

## 性能优化参数
所有工具都支持以下性能优化参数：
```bash
--batch-size     批处理大小（默认：10000）
--memory-threshold 内存使用警告阈值（默认：80%）
--buffer-size    文件缓冲区大小（默认：8MB）
```
## 使用建议

1. 性能优化：
   - 根据机器配置调整内存阈值
   - 对于大文件，适当增加缓冲区大小
   - 通过批处理大小控制内存使用

2. 数据处理：
   - 处理前备份重要数据
   - 先进行小规模测试
   - 注意文件编码格式

3. 错误处理：
   - 查看日志输出
   - 遇到内存警告时适当调整参数
   - 出错时检查输入数据格式

4. 处理完成后：
   - 验证输出文件的完整性
   - 检查数据质量
   - 及时清理临时文件 
