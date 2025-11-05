# raw.json 格式说明

## 概述

从此版本开始，`raw.json` 文件将保存**所有API返回的原始响应**，而不仅仅是成功解析的JSON数据。这样即使解析失败，您也可以查看模型的实际输出内容，便于调试和问题分析。

## 新格式结构

每条记录包含以下字段：

```json
{
  "raw_response": "完整的API响应JSON字符串",
  "raw_content": "LLM返回的原始文本内容",
  "input": "输入的提示内容"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `raw_response` | string | 完整的API响应，包含choices、usage等所有信息，以JSON字符串形式保存 |
| `raw_content` | string | 从API响应中提取的LLM实际返回的文本内容（即`result['choices'][0]['message']['content']`） |
| `input` | string | 发送给LLM的用户输入内容 |

## 示例

### 成功解析的记录

```json
{
  "raw_response": "{\"id\":\"chatcmpl-xxx\",\"object\":\"chat.completion\",\"created\":1699999999,\"model\":\"gpt-4\",\"choices\":[{\"index\":0,\"message\":{\"role\":\"assistant\",\"content\":\"```json\\n{\\\"name\\\":\\\"产品名称\\\",\\\"category\\\":\\\"类别\\\"}\\n```\"},\"finish_reason\":\"stop\"}],\"usage\":{\"prompt_tokens\":100,\"completion_tokens\":50,\"total_tokens\":150}}",
  "raw_content": "```json\n{\"name\":\"产品名称\",\"category\":\"类别\"}\n```",
  "input": "请分析这个产品：xxx"
}
```

### 解析失败的记录

```json
{
  "raw_response": "{\"id\":\"chatcmpl-yyy\",\"object\":\"chat.completion\",\"created\":1699999999,\"model\":\"gpt-4\",\"choices\":[{\"index\":0,\"message\":{\"role\":\"assistant\",\"content\":\"抱歉，我无法分析这个产品，因为信息不足。\"},\"finish_reason\":\"stop\"}],\"usage\":{\"prompt_tokens\":100,\"completion_tokens\":30,\"total_tokens\":130}}",
  "raw_content": "抱歉，我无法分析这个产品，因为信息不足。",
  "input": "请分析这个产品：xxx"
}
```

在这个例子中，LLM没有返回JSON格式，而是返回了普通文本。这条记录会被记录到 `error` 文件，但原始响应仍然被完整保存到 `raw.json`。

## 与旧版本的区别

### 旧版本（问题）
```json
{"name":"产品名称","category":"类别"}
```
- ❌ 只保存成功解析的JSON
- ❌ 解析失败的响应被丢弃
- ❌ 无法查看API实际返回了什么
- ❌ 难以调试解析错误

### 新版本（改进）
```json
{
  "raw_response": "{...完整API响应...}",
  "raw_content": "LLM返回的原始文本",
  "input": "输入内容"
}
```
- ✅ 保存所有API响应，无论是否解析成功
- ✅ 保留完整的API元数据（tokens、模型等）
- ✅ 保留LLM的原始输出文本
- ✅ 便于调试和问题分析
- ✅ 可以追溯每条输入对应的输出

## 使用场景

### 1. 调试JSON解析错误

当遇到JSON解析错误时，可以从 `raw.json` 中查找对应记录：

```python
import json

# 读取raw.json
with open('outputData/xxx_raw.json', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        # 查看解析失败的原始内容
        if '特定输入' in data['input']:
            print("原始响应:", data['raw_content'])
```

### 2. 分析token使用情况

```python
import json

total_tokens = 0
for line in open('outputData/xxx_raw.json', 'r', encoding='utf-8'):
    data = json.loads(line)
    response = json.loads(data['raw_response'])
    tokens = response.get('usage', {}).get('total_tokens', 0)
    total_tokens += tokens

print(f"总共使用了 {total_tokens} tokens")
```

### 3. 对比输入输出

```python
import json

for line in open('outputData/xxx_raw.json', 'r', encoding='utf-8'):
    data = json.loads(line)
    print(f"输入: {data['input'][:50]}...")
    print(f"输出: {data['raw_content'][:50]}...")
    print("-" * 50)
```

### 4. 提取完整对话历史

如果需要重现或分析某次API调用：

```python
import json

# 找到特定记录
with open('outputData/xxx_raw.json', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if '关键词' in data['input']:
            # 完整的API响应可以用于重现问题
            full_response = json.loads(data['raw_response'])
            print(json.dumps(full_response, indent=2, ensure_ascii=False))
```

## 注意事项

### 文件大小

由于保存了完整的API响应，`raw.json` 文件会比之前更大：
- **旧版本**：只有解析后的业务数据
- **新版本**：包含完整API响应（包括元数据、tokens等）

建议定期清理不需要的raw.json文件，或者使用压缩存储。

### 敏感信息

`raw_response` 中可能包含：
- API密钥（通常不会，但要注意）
- 模型名称
- 使用统计
- 时间戳等元数据

如果需要分享raw.json文件，请先检查是否包含敏感信息。

### 向后兼容

代码保留了对旧格式的兼容处理：
- 如果遇到旧格式的响应（直接返回字典而不包含 `_raw_response`），会继续按旧逻辑处理
- 但新产生的所有记录都会使用新格式

## 处理流程

```
API调用
   ↓
返回响应
   ↓
立即保存到 raw.json (包含原始响应)
   ↓
尝试解析JSON
   ↓
  成功 → 写入 output 文件
   ↓
  失败 → 写入 error 文件 (但raw.json已保存)
```

**关键改进**：无论后续解析是否成功，原始响应都会被保存。

## 故障排查

### 问题1：找不到某条记录的原始输出

**解决方案**：检查 `raw.json` 文件，使用 `input` 字段查找：

```bash
# Linux/Mac
grep "关键词" outputData/xxx_raw.json

# 或使用 jq
jq 'select(.input | contains("关键词"))' outputData/xxx_raw.json
```

### 问题2：想知道为什么某条记录解析失败

**解决方案**：
1. 从 `error` 文件找到输入内容
2. 在 `raw.json` 中搜索该输入
3. 查看 `raw_content` 字段，了解LLM实际返回了什么
4. 检查是否是格式问题、是否包含JSON代码块等

### 问题3：想统计不同类型的响应

**解决方案**：分析 `raw_content` 的模式：

```python
import json
import re

markdown_json = 0  # 包含```json```的
plain_json = 0     # 纯JSON
plain_text = 0     # 普通文本

with open('outputData/xxx_raw.json', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        content = data.get('raw_content', '')
        
        if re.search(r'```.*?```', content, re.DOTALL):
            markdown_json += 1
        elif content.strip().startswith('{'):
            plain_json += 1
        else:
            plain_text += 1

print(f"Markdown格式: {markdown_json}")
print(f"纯JSON: {plain_json}")
print(f"普通文本: {plain_text}")
```

## 总结

新的 `raw.json` 格式提供了：
- ✅ **完整性**：保存所有API响应，不丢失任何信息
- ✅ **可追溯性**：每条输入都能找到对应的原始输出
- ✅ **可调试性**：解析失败时能看到LLM实际返回了什么
- ✅ **可分析性**：可以分析token使用、响应模式等
- ✅ **向后兼容**：不影响现有功能

这个改进让您能够更好地理解和调试LLM的行为，特别是在遇到解析错误时。

