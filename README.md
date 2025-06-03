# LLM批处理工具

一个灵活且功能强大的大语言模型批处理工具，支持多种数据格式和API提供商，能够高效处理大量非结构化数据。

## 🎯 项目简介

LLM-Batch 是一个专业的批处理工具，旨在帮助用户高效地使用大语言模型处理各种类型的非结构化数据，将其转换为结构化信息，降低数据处理门槛，提升数据价值。

## 🌟 核心特性

### 数据处理能力
- **多格式输入支持**：CSV、Excel (xlsx/xls)、JSON 文件
- **灵活字段选择**：支持指定处理特定字段或字段范围
- **位置控制**：可指定开始和结束处理位置
- **断点续传**：支持从中断位置继续处理
- **编码自动检测**：支持多种文件编码格式

### API提供商支持
- **阿里云通义千问**：支持 Qwen 系列模型
- **DeepSeek**：支持 DeepSeek Chat 模型
- **OpenAI**：支持 GPT 系列模型
- **火山引擎**：支持火山方舟平台模型
- **扩展性**：易于添加新的API提供商

### 输出与日志
- **多种输出格式**：CSV、Excel、JSON
- **原始响应保存**：可选择保存API原始响应
- **详细日志记录**：完整的处理过程日志
- **进度跟踪**：实时进度条和处理统计
- **错误处理**：详细的错误记录和分类

### 性能与可靠性
- **异步处理**：支持并发请求处理
- **重试机制**：自动重试失败的请求
- **内存监控**：内存使用率监控和限制
- **批次处理**：可配置的批处理大小
- **自动备份**：处理前自动备份现有文件

## 📁 目录结构

```
项目根目录/
├── src/                      # 源代码
│   ├── providers/           # API提供商实现
│   │   ├── base.py         # 基础提供商接口
│   │   ├── universal_llm.py # 通用LLM提供商
│   │   ├── aliyun_agent.py # 阿里云特殊提供商
│   │   └── factory.py      # 提供商工厂
│   ├── core/               # 核心处理逻辑
│   │   └── processor.py    # 批处理器
│   └── utils/              # 工具类
│       ├── config.py       # 配置管理
│       ├── logger.py       # 日志管理
│       └── file_utils.py   # 文件处理工具
├── config/                  # 配置文件
│   ├── config.yaml         # 主配置文件
│   └── config.example.yaml # 配置示例文件
├── inputData/              # 输入数据目录
├── outputData/             # 输出数据目录
├── prompts/                # 提示词模板文件
├── logs/                   # 日志文件
├── tools/                  # 实用工具
│   ├── data_quality_check.py     # 数据质量检查
│   ├── csv_splitter_manager.py   # CSV分割管理器
│   ├── data_converter.py         # 数据转换工具
│   ├── token_cost_calculator.py  # 成本计算器
│   ├── json_format.py            # JSON格式化工具
│   ├── dedup_csv.py              # CSV去重工具
│   ├── merge_table_data.py       # 表格数据合并
│   ├── compare_keys.py           # 键值比较工具
│   └── id_matching.py            # ID匹配工具
└── main.py                 # 主程序入口
```

## 🚀 快速开始

### 1. 环境准备

1. 克隆或下载项目：
```bash
git clone <repository-url>
cd <project-directory>
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 2. 配置设置

1. 复制配置示例文件：
```bash
copy config\config.example.yaml config\config.yaml
```

2. 编辑 `config/config.yaml` 文件，设置您的API密钥和其他配置

### 3. 基本使用

#### 命令格式
```bash
python main.py <输入路径> <提示词文件> [可选参数]
```

#### 参数说明
- `输入路径`：输入文件或目录的路径
- `提示词文件`：提示词模板文件路径
- `--fields`：要处理的字段 (格式: 1,2,3 或 1-5)
- `--start-pos`：开始处理位置 (从1开始)
- `--end-pos`：结束处理位置 (包含)
- `--provider`：指定API提供商 (覆盖配置文件设置)

#### 使用示例

```bash
# 处理单个文件
python main.py inputData/data.csv prompts/extract.txt

# 处理特定字段
python main.py inputData/data.csv prompts/extract.txt --fields 1,3,5

# 处理指定范围的记录
python main.py inputData/data.csv prompts/extract.txt --start-pos 1 --end-pos 100

# 使用特定API提供商
python main.py inputData/data.csv prompts/extract.txt --provider aliyun

# 处理字段范围
python main.py inputData/data.xlsx prompts/analyze.txt --fields 2-6
```

### 4. 提示词模板

在 `prompts` 目录中创建提示词文件，格式示例：

```
[系统指令]
你是一个专业的数据分析助手，擅长处理和分析各种类型的数据。

[任务要求]
请分析以下数据并提取关键信息：

{输入数据}

[输出格式]
请严格按照以下JSON格式输出：
{
    "字段1": "字段1的描述",
    "字段2": "字段2的描述",
    "confidence": 0.95
}
```

## ⚙️ 配置说明

### API提供商配置
配置文件支持以下API提供商：
- **阿里云 (aliyun)**：通义千问API，支持多种模型
- **DeepSeek (deepseek)**：高性价比的API选择
- **OpenAI (openai)**：GPT系列模型支持
- **火山引擎 (volcengine)**：字节跳动的大模型平台

### 输出配置
- 支持CSV、Excel、JSON格式输出
- 可配置是否保存原始API响应
- 自定义文件编码设置

### 处理配置
- 批处理大小控制
- 重试次数和间隔设置
- 内存使用限制
- 并发请求数限制

### 日志配置
- 可配置日志级别和格式
- 支持控制台和文件输出
- 进度条和统计信息显示

## 🔧 实用工具

项目包含多个实用工具，位于 `tools/` 目录：

### 数据质量检查工具
```bash
python tools/data_quality_check.py <文件路径>
```
- 检查文件格式和编码
- 分析数据质量指标
- 生成详细的质量报告

### CSV分割管理器
```bash
python tools/csv_splitter_manager.py <输入文件> --method rows --size 1000
```
- 按行数分割文件
- 按文件大小分割
- 按日期列分割
- 随机分割

### 数据转换工具
```bash
python tools/data_converter.py <输入文件> <输出格式>
```
- 支持多种格式之间的转换
- 自动处理编码问题
- 保持数据完整性

### 成本计算器
```bash
python tools/token_cost_calculator.py <文件路径> <提示词文件>
```
- 估算处理成本
- 支持多种模型的token计算
- 提供详细的成本分析

### JSON格式化工具
```bash
python tools/json_format.py <输入文件>
```
- 格式化JSON文件
- 支持嵌套结构处理
- 批量处理功能

### CSV去重工具
```bash
python tools/dedup_csv.py <输入文件>
```
- 基于指定列去重
- 保持数据完整性
- 生成去重报告

## 📋 最佳实践

### 1. 数据准备
- 确保输入数据格式正确
- 处理前进行数据质量检查
- 对大文件考虑先分割处理

### 2. 提示词设计
- 明确输出格式要求
- 提供足够的上下文信息
- 测试提示词效果

### 3. 处理优化
- 合理设置批处理大小
- 监控内存使用情况
- 利用断点续传功能

### 4. 安全注意事项
- 妥善保管API密钥
- 谨慎处理敏感数据
- 定期检查输出结果

## 🤝 贡献指南

欢迎贡献代码！请遵循以下流程：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

对于重大更改，请先开启 issue 讨论。

## 📄 许可证

本项目采用 MIT 许可证 - 详情请见 [LICENSE](LICENSE) 文件。

## ❓ 常见问题

### Q: 如何添加新的API提供商？
A: 继承 `BaseProvider` 类并在 `factory.py` 中注册即可。

### Q: 处理大文件时内存不足怎么办？
A: 调整配置中的 `batch_size` 和 `max_memory_percent` 参数。

### Q: 如何处理API限流？
A: 调整 `concurrent_limit` 和 `retry_interval` 参数。

### Q: 支持哪些文件格式？
A: 目前支持CSV、Excel (xlsx/xls)、JSON格式的输入和输出。

### Q: 如何使用断点续传功能？
A: 工具会自动保存处理进度，再次运行相同命令时会从中断位置继续。

---

如有问题或建议，请提交 issue 或联系项目维护者。 