# LLM-Batch

[English](README.md) | [中文](README_zh.md)

A flexible batch processing tool for large language models (LLMs). Process large amounts of data through various LLM providers with configurable input/output formats and asynchronous processing.

## Features

- Multiple input formats support (CSV, Excel, JSON)
- Multiple LLM provider support (DeepSeek, OpenAI, etc.)
- Configurable output formats (CSV, Excel, JSON)
- Asynchronous processing with concurrent control
- Checkpoint support for resuming interrupted tasks
- Comprehensive logging system
- Extensible provider interface

## Directory Structure

```
llm_batch_processor/
├── src/                   # Source code
│   ├── providers/        # API provider implementations
│   ├── core/            # Core processing logic
│   └── utils/           # Utility classes
├── config/               # Configuration files
├── inputData/           # Input data directory
├── outputData/          # Output data directory
├── prompts/             # Prompt template files
├── logs/                # Log files
└── docs/                # Documentation
```

## Quick Start

### 1. Installation

1. Clone the repository:
```bash
git clone https://github.com/tomyzcf/LLM-Batch.git
cd LLM-Batch
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configuration

1. Copy the example configuration file:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Edit `config/config.yaml` and set your API keys and other settings

### 3. Usage

#### Basic Usage

```bash
python main.py <input_path> <prompt_file>
```

#### Parameters

- `input_path`: Path to input file or directory
- `prompt_file`: Path to prompt template file
- `--fields`: Input fields to process (optional, format: 1,2,3 or 1-5)
- `--output-name`: Output file name (optional)
- `--start-pos`: Start position (optional, 1-based)
- `--end-pos`: End position (optional, inclusive)
- `--provider`: Specify API provider (optional, overrides config file)

#### Examples

```bash
# Process a single file
python main.py input.csv prompt.txt

# Process specific fields
python main.py input.csv prompt.txt --fields 1,2,5

# Process a range of records
python main.py input.csv prompt.txt --start-pos 1 --end-pos 100

# Use specific provider
python main.py input.csv prompt.txt --provider openai
```

### 4. Prompt Template

Create a prompt file using the following format:

```
[System Instruction]
You are a professional data analysis assistant...

[Task Requirements]
Please analyze the following data...

[Output Format]
{
    "field1": "Description of field1",
    "field2": "Description of field2"
}
```

## Configuration

The `config/config.yaml` file contains:

- API provider configurations
- Output format settings
- Logging settings
- Processing parameters

See [configuration documentation](docs/requirements.md) for details.

## Notes

- Ensure API keys are properly configured
- Test with small batches before large-scale processing
- Check output format settings
- Handle sensitive data with care

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 