# Data Processing Tools

[English](README.md) | [中文](README_zh.md)

A collection of standalone data processing tools. Each tool supports large file processing and performance optimization.

## Tool List

### 1. CSV Splitter Manager (csv_splitter_manager.py)
CSV file splitting and management tool with features:
- Split by rows/size/percentage
- Split by date column (customizable date format)
- Column management (drop columns)
- Large file chunk processing
- Memory usage optimization

### 2. JSON Formatter (json_format.py)
JSON file processing tool:
- Streaming processing for large files
- Automatic nested structure handling
- Batch processing support
- Memory usage optimization

### 3. Data Format Converter (data_converter.py)
Universal data format conversion tool:
- Support for JSON, CSV, Excel, and Parquet formats
- Automatic input format detection
- Directory batch conversion
- Nested structure handling
- Large file streaming processing
- Memory optimization for big datasets

### 4. Data Quality Checker (data_quality_check.py)
Data quality checking tool:
- Multiple file format support
- Data integrity checks
- Anomaly detection
- Quality report generation

## Performance Parameters
All tools support the following performance optimization parameters:
```bash
--batch-size     Batch processing size (default: 10000)
--memory-threshold Memory usage warning threshold (default: 80%)
--buffer-size    File buffer size (default: 8MB)
```

## Usage Guidelines

1. Performance Optimization:
   - Adjust memory threshold based on machine configuration
   - Increase buffer size for large files
   - Control memory usage through batch size

2. Data Processing:
   - Backup important data before processing
   - Perform small-scale testing first
   - Pay attention to file encoding

3. Error Handling:
   - Check log output
   - Adjust parameters when memory warnings occur
   - Verify input data format when errors occur

## 注意事项

- 处理大文件时建议先进行小规模测试
- 确保有足够的磁盘空间
- 注意文件编码格式
- 建议在处理前备份重要数据 