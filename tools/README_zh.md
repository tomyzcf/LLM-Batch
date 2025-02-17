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

### 3. JSON转CSV工具 (json_to_csv.py)
JSON转CSV转换工具：
- 支持复杂JSON结构扁平化
- 自动处理编码问题
- 支持流式处理大文件
- 内存使用优化

### 4. 数据质量检查工具 (data_quality_check.py)
数据质量检查工具：
- 支持多种文件格式
- 数据完整性检查
- 异常值检测
- 生成质量报告

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
