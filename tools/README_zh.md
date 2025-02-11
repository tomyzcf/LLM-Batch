# 数据处理工具集

[English](README.md) | [中文](README_zh.md)

本目录包含一系列用于数据处理的独立工具脚本。

## 工具列表

### 1. CSV分割管理器 (csv_splitter_manager.py)

一个功能强大的CSV文件分割和管理工具，支持多种分割方式：

- 按行数分割：将CSV文件按指定行数分割成多个文件
- 按文件大小分割：将CSV文件按指定大小（MB）分割
- 按百分比分割：将文件分割成两部分（如60%/40%）
- 按日期分割：根据日期列按月份分割文件
- 按列值分割：根据某列的不同值分割成多个文件
- 随机分割：随机将文件分割成N份
- 列管理：支持删除指定列

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

用于处理和格式化JSON文件的工具：

- JSON文件格式化和验证
- 支持嵌套结构处理
- 支持批量处理
- 自动修复常见JSON格式问题

### 3. JSON转CSV工具 (json_to_csv.py)

将JSON格式数据转换为CSV格式：

- 支持复杂JSON结构的扁平化
- 支持自定义字段映射
- 批量转换功能
- 支持多层嵌套结构

### 4. 数据质量检查工具 (data_quality_check.py)

全面的数据质量检查工具：

- 支持多种文件格式（CSV、Excel、JSON、Parquet等）
- 数据完整性检查
- 数据类型验证
- 异常值检测
- 空值统计
- 数据分布分析
- 生成质量报告

## 使用建议

1. 数据处理前：
   - 对数据进行备份
   - 检查磁盘空间是否充足
   - 进行小规模测试

2. 处理过程中：
   - 注意文件编码格式
   - 监控系统资源使用情况
   - 保存处理日志

3. 处理完成后：
   - 验证输出文件的完整性
   - 检查数据质量
   - 及时清理临时文件 