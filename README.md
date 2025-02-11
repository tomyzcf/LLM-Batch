# LLM-Batch

[English](README.md) | [中文](README_zh.md)

A flexible batch processing tool for large language models (LLMs). Process large amounts of data through various LLM providers with configurable input/output formats and asynchronous processing.

## 🎯 Vision

LLM-Batch aims to be a powerful, flexible, and user-friendly platform for processing unstructured data using large language models and multimodal models. Our goal is to help users efficiently transform various types of unstructured data into structured information, lowering the barrier to data processing and enhancing data value.

## 🌟 Core Features

- Multiple input formats support (CSV, Excel, JSON)
- Multiple LLM provider support (DeepSeek, OpenAI, etc.)
- Configurable output formats (CSV, Excel, JSON)
- Asynchronous processing with concurrent control
- Checkpoint support for resuming interrupted tasks
- Comprehensive logging system
- Extensible provider interface

## 🗺️ Roadmap Overview

- ✅ **Phase 1**: Core Capabilities (Current)
  - Basic text processing
  - Multiple LLM providers support
  - Configuration-driven processing

- 🚀 **Phase 2**: Enhanced Features
  - Multimodal model support
  - Data pre/post processing toolkit
  - Batch processing interface

- 📋 **Phase 3**: Vertical Solutions
  - Industry best practices
  - Multi-language support
  - Processing templates

- 🌐 **Phase 4**: Ecosystem
  - Web interface
  - Plugin system
  - API service

[View Full Roadmap](ROADMAP.md)

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
├── tools/               # Utility tools
│   └── data_quality_check.py  # Data quality checking tool
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

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Tools

### Data Quality Check

A standalone tool for checking data quality of various file formats (CSV, Excel, JSON, Parquet, etc.). 
Run `python tools/data_quality_check.py --help` for detailed usage information.

### CSV Splitter Manager

A powerful CSV file splitting and management tool that supports various splitting methods:
- Split by number of rows
- Split by file size (MB)
- Split by percentage (e.g., 60%/40%)
- Split by date column (monthly)
- Split by column values
- Random splitting
- Column management (deletion)

Run `python tools/csv_splitter_manager.py --help` for detailed usage information.

### JSON Format Tool

A tool for processing and formatting JSON files with support for nested structures and batch processing.
Run `python tools/json_format.py --help` for detailed usage information.

### JSON to CSV Converter

A tool for converting JSON data to CSV format with support for flattening complex structures and custom field mapping.
Run `python tools/json_to_csv.py --help` for detailed usage information. 