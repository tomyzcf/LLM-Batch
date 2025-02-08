# LLM批处理工具

[English](README.md) | [中文](README_zh.md)

这是一个用于批量处理数据的LLM工具，支持多种模型API和数据格式。通过简单的配置和灵活的提示词模板，可以批量处理文本数据并获取结构化输出。

## 功能特点

- 支持多种输入格式（CSV、Excel、JSON）
- 支持多个LLM API提供商（DeepSeek、OpenAI等）
- 支持断点续传
- 支持多种输出格式（CSV、Excel、JSON）
- 完善的日志记录
- 异步并发处理
- 可扩展的API提供商接口

## 目录结构

```
llm_batch_processor/
├── src/                   # 源代码
│   ├── providers/        # API提供商实现
│   ├── core/            # 核心处理逻辑
│   └── utils/           # 工具类
├── config/               # 配置文件
├── inputData/           # 输入数据目录
├── outputData/          # 输出数据目录
├── prompts/             # 提示词文件目录
├── logs/                # 日志目录
└── docs/                # 文档目录
```

## 快速开始

### 1. 安装

1. 克隆项目：
```bash
git clone https://github.com/tomyzcf/LLM-Batch.git
cd LLM-Batch
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 2. 配置

1. 复制示例配置文件：
```bash
cp config/config.example.yaml config/config.yaml
```

2. 修改配置文件 `config/config.yaml`，设置API密钥等信息

### 3. 使用

#### 基本用法

```bash
python main.py <input_path> <prompt_file>
```

#### 参数说明

- `input_path`：输入文件或目录路径
- `prompt_file`：提示词文件路径
- `--fields`：要处理的输入字段（可选，格式：1,2,3 或 1-5）
- `--output-name`：输出文件名（可选）
- `--start-pos`：开始处理的位置（可选）
- `--end-pos`：结束处理的位置（可选）
- `--provider`：指定API提供商（可选，将覆盖配置文件中的设置）

#### 使用示例

```bash
# 处理单个文件
python main.py input.csv prompt.txt

# 处理特定字段
python main.py input.csv prompt.txt --fields 1,2,5

# 处理指定范围
python main.py input.csv prompt.txt --start-pos 1 --end-pos 100

# 使用指定提供商
python main.py input.csv prompt.txt --provider openai
```

### 4. Prompt模板

创建提示词文件，使用以下格式：

```
[系统指令]
你是一个专业的数据分析助手...

[任务要求]
请分析下面的数据...

[输出格式]
{
    "field1": "字段1的说明",
    "field2": "字段2的说明"
}
```

## 配置说明

配置文件 `config/config.yaml` 包含以下主要部分：

- API提供商配置：设置不同API提供商的密钥和参数
- 输出配置：设置输出格式和编码
- 日志配置：设置日志级别和输出
- 处理配置：设置批处理大小和重试参数

详细配置说明请参考 [配置文档](docs/requirements.md)。

## 注意事项

- 确保API密钥正确配置
- 大规模处理前先小批量测试
- 注意检查输出格式设置
- 敏感数据处理时注意数据安全

## 贡献指南

欢迎提交问题和改进建议！如果您想贡献代码：

1. Fork 项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 许可证

该项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。 