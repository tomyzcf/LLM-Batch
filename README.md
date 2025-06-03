# LLM批处理工具

一个灵活且功能强大的大语言模型批处理工具，支持多种数据格式和API提供商，能够高效处理大量非结构化数据。

## 🎯 项目简介

LLM-Batch 是一个专业的批处理工具，旨在帮助用户高效地使用大语言模型处理各种类型的调用请求，包括不限于数据标签提取，批量智能体内容生成，模型/智能体效果评估

## 🌟 核心特性

### 数据处理能力
- **多格式输入支持**：CSV、Excel (xlsx/xls)、JSON 文件
- **灵活字段选择**：支持指定处理特定字段或字段范围
- **位置控制**：可指定开始和结束处理位置
- **断点续传**：支持从中断位置继续处理
- **编码自动检测**：支持多种文件编码格式

### API提供商支持
- **OpenAI风格API**：支持deepseek,阿里百炼，火山等openai风格模型接口
- **阿里百炼agent**：阿里百炼Agent API 接口
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

2. 编辑 `config\config.yaml` 文件，设置您的API密钥和其他配置

3. 编辑 `prompts\example.txt` 文件，设置您的模型提示词

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

## 🔧 实用工具

项目包含多个实用数据工具，位于 `tools/` 目录，详情请参考 tools/README.md
- 数据质量检查工具
- 数据去重工具
- 数据分割工具
- 数据格式转换工具
- 模型API成本计算器

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