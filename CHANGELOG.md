# 更新日志

## [2.0.0] - 2025-11-05

### 🎯 重大改进

#### 1. raw.json 现在保存完整的原始API响应

**问题：**
- 旧版本只保存成功解析的JSON数据
- 解析失败的响应被丢弃，无法调试
- 无法查看LLM实际返回了什么内容

**改进：**
- ✅ `raw.json` 现在保存**所有**API响应，包括解析失败的
- ✅ 每条记录包含完整的API响应、LLM原始文本内容和输入内容
- ✅ 便于调试、分析和问题排查
- ✅ 可以追溯token使用、查看响应模式等

**新格式：**
```json
{
  "raw_response": "完整的API响应JSON字符串",
  "raw_content": "LLM返回的原始文本内容",
  "input": "输入的提示内容"
}
```

详见：[raw_json格式说明.md](docs/raw_json格式说明.md)

#### 2. 错误统计修复

**问题：**
- JSON解析错误没有被正确统计到 `progress.json`
- 导致看起来所有记录都成功了，实际有失败

**改进：**
- ✅ 修复统计逻辑，所有错误现在都会被正确计数
- ✅ 区分不同类型的错误：
  - `json_error`: JSON解析错误
  - `api_error`: API调用错误
  - `other_error`: 其他错误

#### 3. 失败重试功能

**新功能：**
- ✅ 新增 `--retry-errors` 命令行参数
- ✅ 自动读取 `error` 文件并重试失败的记录
- ✅ 自动备份错误文件
- ✅ 支持多次重试
- ✅ 成功的记录追加到输出文件，不覆盖已有数据

**使用方法：**
```bash
python main.py <input_file> <prompt_file> --retry-errors
```

详见：[失败重试功能说明.md](docs/失败重试功能说明.md)

### 🔧 技术细节

#### 修改的文件

1. **src/providers/universal_llm.py**
   - 修改 `_parse_success_response()` 方法
   - 返回包含原始响应和解析结果的结构化数据
   - 解析失败时返回错误信息而不是抛出异常（在processor层处理）

2. **src/core/processor.py**
   - 修改结果处理逻辑，先保存原始响应再处理解析结果
   - 修复错误统计逻辑
   - 新增 `retry_failed_records()` 方法用于重试失败记录
   - 支持CSV、Excel、JSON格式的错误文件读取

3. **main.py**
   - 新增 `--retry-errors` 命令行参数
   - 根据参数选择正常处理或重试模式

#### 新增的文件

- `docs/失败重试功能说明.md` - 失败重试功能完整文档
- `docs/raw_json格式说明.md` - raw.json格式详细说明
- `CHANGELOG.md` - 更新日志（本文件）

### 📊 影响

#### 正面影响
- ✅ 更好的可调试性：能看到所有原始响应
- ✅ 更准确的统计：错误不再被忽略
- ✅ 更高的容错性：失败可以重试
- ✅ 更完整的数据：不丢失任何API响应

#### 需要注意
- ⚠️ `raw.json` 文件会变大（包含完整API响应）
- ⚠️ 需要更多存储空间
- ℹ️ 建议定期清理不需要的raw.json文件

### 🔄 向后兼容

- ✅ 代码保留了对旧格式响应的兼容处理
- ✅ 旧版本产生的文件仍然可以被处理
- ✅ 不影响现有功能和工作流

### 📖 文档

新增文档：
- [raw_json格式说明.md](docs/raw_json格式说明.md) - 详细说明新的raw.json格式
- [失败重试功能说明.md](docs/失败重试功能说明.md) - 失败重试功能使用指南

### 🚀 使用示例

#### 查看解析失败的原始内容
```python
import json

with open('outputData/xxx_raw.json', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        print(f"输入: {data['input'][:50]}...")
        print(f"输出: {data['raw_content'][:50]}...")
```

#### 重试失败的记录
```bash
# 首次处理
python main.py "inputData/data.xlsx" "prompts/prompt.txt"

# 查看 progress.json 发现有失败记录

# 重试失败记录
python main.py "inputData/data.xlsx" "prompts/prompt.txt" --retry-errors
```

#### 分析token使用
```python
import json

total_tokens = 0
with open('outputData/xxx_raw.json', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        response = json.loads(data['raw_response'])
        tokens = response.get('usage', {}).get('total_tokens', 0)
        total_tokens += tokens

print(f"总共使用: {total_tokens} tokens")
```

### 💡 最佳实践

1. **定期检查progress.json**
   - 确保没有遗漏的错误
   - 及时发现和处理失败记录

2. **使用重试功能**
   - 对于偶发性错误，重试通常能解决
   - 可以多次重试直到成功

3. **利用raw.json调试**
   - 当遇到解析错误时，查看raw.json了解LLM实际返回
   - 根据原始响应调整提示词

4. **管理存储空间**
   - 定期清理不需要的raw.json文件
   - 或者使用压缩存储

### 🐛 已知问题

无

### 🎉 致谢

感谢用户反馈，帮助我们发现并修复了这些问题！

---

## [1.0.0] - 2025-11-04

初始版本

