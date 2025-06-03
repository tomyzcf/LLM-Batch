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

### 提示词系统
- **双格式支持**：支持JSON和TXT两种提示词格式
- **智能解析**：自动识别提示词格式并解析
- **变量替换**：JSON格式支持动态变量替换
- **成本优化**：JSON格式相比TXT格式节省60-80% token消耗
- **可选字段**：支持examples、variables等增强功能

### API提供商支持
- **LLM兼容API** (`api_type: "llm_compatible"`)：支持所有OpenAI兼容的API接口
  - DeepSeek、OpenAI、阿里云百炼、火山引擎等
- **阿里云百炼Agent** (`api_type: "aliyun_agent"`)：专门的Agent API接口
- **统一配置管理**：通过 `api_type` 字段统一管理不同类型的API
- **自动类型检测**：未指定 `api_type` 时自动根据配置字段检测
- **高度可扩展**：易于添加新的API类型和提供商

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
│   │   ├── universal_llm.py # LLM兼容API提供商
│   │   ├── aliyun_agent.py # 阿里云Agent提供商
│   │   └── factory.py      # 提供商工厂（统一管理）
│   ├── core/               # 核心处理逻辑
│   │   └── processor.py    # 批处理器
│   └── utils/              # 工具类
│       ├── config.py       # 配置管理
│       ├── logger.py       # 日志管理
│       └── file_utils.py   # 文件处理工具
├── config/                  # 配置文件
│   ├── config.yaml         # 主配置文件
│   └── config.example.yaml # 配置示例文件（简化版）
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

2. 编辑 `config\config.yaml` 文件，设置您的API密钥和配置：

```yaml
# 支持的api_type类型：
# - llm_compatible: 适用于所有OpenAI兼容的API
# - aliyun_agent: 阿里云百炼Agent专用API

api_providers:
  # LLM兼容API示例（推荐）
  deepseek:
    api_type: "llm_compatible"  # 指定API类型
    api_key: "sk-your-deepseek-key-here"
    base_url: "https://api.deepseek.com"
    model: "deepseek-chat"
    
  # 阿里云Agent示例  
  aliyun-agent:
    api_type: "aliyun_agent"  # 指定API类型
    api_key: "sk-your-aliyun-key-here"
    base_url: "https://dashscope.aliyuncs.com"
    app_id: "your-app-id"
```

3. 编辑 `prompts\example.txt` 文件，设置您的模型提示词

### 3. 配置提示词

工具支持两种提示词格式，建议使用JSON格式以获得更好的性能和灵活性：

#### 📝 JSON格式（推荐）

##### 基本结构
```json
{
  "system": "系统角色描述",
  "task": "任务描述", 
  "output": "输出格式定义"
}
```

##### 字段说明

**必需字段（必须包含）：**
- `system`：系统角色描述，定义AI助手的身份和基本规则
- `task`：任务描述，说明要执行的具体任务
- `output`：输出格式定义，可以是JSON对象或字符串

**可选字段（按需使用）：**
- `variables`：变量替换，在system和task中使用 `{变量名}` 格式
- `examples`：示例数据，会自动添加到任务描述中
- `metadata`：元数据信息，如版本、作者等

##### 填写注意事项
1. **JSON格式规范**：所有字符串需要用双引号包围
2. **转义字符**：JSON内部的引号需要转义（`\"`）
3. **变量替换**：使用 `{变量名}` 格式，在variables中定义
4. **格式有效性**：确保JSON格式完全有效，不支持注释
5. **中文支持**：完全支持中文字段名和内容

##### 完整示例
```json
{
  "system": "你是数据提取助手。规则：输出JSON，字符串用引号，数字不用引号，缺失值用\"NA\"",
  "task": "从{数据类型}中提取以下信息：1. 名称 2. 类型 3. 数量",
  "output": {
    "名称": "string",
    "类型": "string", 
    "数量": "number"
  },
  "variables": {
    "数据类型": "文档内容"
  },
  "examples": [
    "输入：苹果手机5台 输出：{\"名称\":\"苹果手机\",\"类型\":\"电子产品\",\"数量\":5}"
  ],
  "metadata": {
    "version": "1.0",
    "author": "数据提取团队"
  }
}
```

**JSON格式优势：**
- 🚀 **Token更少**：相比TXT格式节省40-60% token消耗
- 🔧 **灵活配置**：支持变量替换、示例、可选字段
- 📊 **成本优化**：大规模调用时显著降低成本
- 📋 **结构清晰**：字段分离，易于维护和版本管理

**示例文件：**
- `prompts/example.json` - 基础示例模板

#### 📄 TXT格式（兼容）
传统的分节格式，编辑现有的 `prompts\example.txt` 文件：

```txt
[系统]
你是数据提取助手...

[任务] 
从输入中提取以下信息...

[输出格式]
{
    "字段1": "string",
    "字段2": "number"
}
```

### 4. Token消耗对比

| 格式类型 | Token数 | 相比TXT格式 | 百万次调用成本 | 成本节省 |
|---------|---------|-------------|----------------|---------|
| **TXT格式** | 156 tokens | 基准 | ¥156 | - |
| **JSON格式** | 157 tokens | +0.6% | ¥157 | -¥1 |
| **最小JSON** | 64 tokens | **-59.0%** | ¥64 | **¥92** |

*基于DeepSeek定价 ¥0.001/1K tokens计算

### 5. 基本使用

#### 命令格式
```bash
python main.py <输入路径> <提示词文件> [可选参数]
```

#### 参数说明
- `输入路径`：输入文件或目录的路径
- `提示词文件`：提示词模板文件路径（支持.json和.txt格式）
- `--fields`：要处理的字段 (格式: 1,2,3 或 1-5)
- `--start-pos`：开始处理位置 (从1开始)
- `--end-pos`：结束处理位置 (包含)
- `--provider`：指定API提供商 (覆盖配置文件设置)

#### 使用示例

```bash
# 使用JSON格式提示词（推荐）
python main.py inputData/data.csv prompts/extract.json

# 使用TXT格式提示词
python main.py inputData/data.csv prompts/extract.txt

# 处理特定字段
python main.py inputData/data.csv prompts/extract.json --fields 1,3,5

# 处理指定范围的记录
python main.py inputData/data.csv prompts/extract.json --start-pos 1 --end-pos 100

# 使用特定API提供商
python main.py inputData/data.csv prompts/extract.json --provider aliyun

# 处理字段范围
python main.py inputData/data.xlsx prompts/analyze.json --fields 2-6
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
A: 有两种方式：
1. **添加新的API类型**：继承 `BaseProvider` 类创建新Provider，在 `factory.py` 中注册新的 `api_type`
2. **使用现有类型**：如果是OpenAI兼容的API，直接使用 `api_type: "llm_compatible"` 即可

### Q: api_type字段是必须的吗？
A: 不是必须的。如果未指定，系统会根据配置字段自动检测：
- 有 `app_id` 字段 → `aliyun_agent`
- 有 `model` 字段 → `llm_compatible`
- 默认 → `llm_compatible`

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