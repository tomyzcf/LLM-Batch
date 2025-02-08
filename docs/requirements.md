# LLM批量处理工具需求文档

## 1. 项目概述

### 1.1 目标
开发一个可扩展的批量数据处理工具，通过调用不同的LLM API，将输入数据批量处理为结构化输出。

### 1.2 核心功能
- 支持多种输入格式（CSV、Excel、JSON）的批量处理
- 支持多种LLM API提供商
- 支持断点续传
- 支持多种输出格式

## 2. 详细需求

### 2.1 输入处理
- 支持单文件或目录输入
- 支持的文件格式：CSV、Excel、JSON
- 支持选择性处理指定字段
- 保持现有的命令行参数方式
- 命令行参数包括：
  - input_path：输入文件或目录路径
  - prompt_file：提示词文件路径
  - --fields：要处理的输入字段（可选）
  - --output-name：输出文件名（可选）
  - --start-pos：开始处理的位置（可选）
  - --end-pos：结束处理的位置（可选）

### 2.2 Prompt处理
- 设计标准的prompt模板格式，包含输出格式定义部分
- 模板格式示例：
```
[系统指令]
你是一个专业的数据分析助手...

[任务要求]
请分析下面的数据...

- 输出格式部分将作为表头和数据验证的依据
- 确保模板格式通用且易于LLM理解

[输出格式]
{
    "field1": "字段1的说明",
    "field2": "字段2的说明"
}
```
### 2.3 API调用
- 支持多个API提供商（DeepSeek、OpenAI、Ollama等）
- 每个提供商独立配置并发限制
- 统一的重试机制：
  - 最大重试次数：5次
  - 重试间隔：指数退避策略
- 错误处理：
  - 记录失败原因
  - 保存失败数据
  - 支持断点续传

### 2.4 输出处理
- 支持多种输出格式：
  - CSV（默认）
  - Excel
  - JSON
- 输出内容：
  - 成功结果文件
  - 失败结果文件（包含失败原因）
  - 原始响应数据
  - 处理进度文件
- 统一的进度文件格式（支持切换API提供商后继续处理）

### 2.5 日志管理
- 通过配置文件设置日志级别
- 日志内容包括：
  - 处理进度
  - 错误信息
  - API调用状态
  - 重要操作记录

## 3. 技术设计

### 3.1 目录结构
```
llm_batch_processor/
├── src/
│   ├── providers/           # API提供商实现
│   ├── core/               # 核心处理逻辑
│   └── utils/              # 工具类
├── config/                 # 配置文件目录
├── inputData/             # 输入数据目录
├── outputData/            # 输出数据目录
├── prompts/               # 提示词文件目录
├── logs/                  # 日志目录
└── main.py               # 入口文件
```

### 3.2 配置文件设计
```yaml
# 示例配置
api_providers:
  deepseek:
    api_key: "your-api-key"
    base_url: "https://api.deepseek.com"
    model: "deepseek-chat"
    concurrent_limit: 10
  openai:
    api_key: "your-api-key"
    base_url: "https://api.openai.com"
    model: "gpt-3.5-turbo"
    concurrent_limit: 5

output:
  format: "csv"  # csv, excel, or json
  save_raw_response: true

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "batch_process.log"

process:
  batch_size: 5
  max_retries: 5
  retry_interval: 0.5
```

### 3.3 关键设计决策
1. **文件IO处理**：
   - 保持现有的分批读取机制
   - 使用异步IO处理提高性能
   - 移除冗余的文件处理逻辑

2. **错误处理策略**：
   - API调用失败：重试机制
   - 解析错误：记录失败并继续
   - 系统错误：保存进度并退出

3. **并发控制**：
   - 基于API提供商限制的并发控制
   - 异步处理机制
   - 统一的任务队列管理

4. **扩展性考虑**：
   - API提供商接口标准化
   - 输出格式处理器可扩展
   - 配置管理模块化

## 4. 注意事项

### 4.1 性能考虑
- 主要瓶颈在API调用，无需过度优化本地处理
- 保持现有的文件IO处理机制
- 内存使用：预期4GB内存足够使用

### 4.2 限制说明
- 不支持运行时切换API提供商
- 不支持动态调整日志级别
- 不支持多机器共享进度
- 不支持环境变量覆盖配置
- 不进行模型输出格式验证

### 4.3 后续优化方向
- 模型输出格式验证机制
- 文件IO性能优化
- 多机器处理支持
- 环境变量配置支持 