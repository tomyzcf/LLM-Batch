import asyncio
import argparse
from pathlib import Path
from src.utils.config import Config
from src.utils.logger import Logger
from src.core.processor import BatchProcessor
from src.providers.factory import ProviderFactory

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='批量处理数据脚本')
    
    # 必选参数
    parser.add_argument('input_path', type=str,
                       help='输入文件或目录的路径')
    parser.add_argument('prompt_file', type=str,
                       help='提示词文件路径')
    
    # 可选参数
    parser.add_argument('--fields', type=str,
                       help='要处理的输入字段，格式：1,2,3 或 1-5')
    parser.add_argument('--start-pos', type=int, default=1,
                       help='开始处理的位置（从1开始）')
    parser.add_argument('--end-pos', type=int,
                       help='结束处理的位置（包含）')
    parser.add_argument('--provider', type=str,
                       help='指定API提供商（将覆盖配置文件中的设置）')
    
    return parser.parse_args()

def parse_fields(fields_str: str) -> list:
    """解析字段参数"""
    if not fields_str:
        return None
        
    try:
        if '-' in fields_str:
            start, end = map(int, fields_str.split('-'))
            return list(range(start - 1, end))
        else:
            return [int(f) - 1 for f in fields_str.split(',')]
    except ValueError:
        raise ValueError("字段参数格式错误，应为：1,2,3 或 1-5")

async def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 加载配置
        config = Config()
        
        # 设置日志级别
        Logger.set_level(config.logging_config.get('level', 'INFO'))
        
        # 解析字段参数
        fields = parse_fields(args.fields) if args.fields else None
        
        # 确定使用的API提供商
        provider_name = args.provider or config.default_provider
        
        # 创建API提供商实例
        provider = ProviderFactory.create_provider(provider_name, config.config)
        
        # 创建处理器
        processor = BatchProcessor(config, provider)
        
        # 开始处理
        await processor.process_files(
            Path(args.input_path),
            Path(args.prompt_file),
            fields,
            args.start_pos,
            args.end_pos
        )
        
    except KeyboardInterrupt:
        Logger.warning("\n检测到中断，正在退出...")
    except Exception as e:
        Logger.error(f"程序执行出错: {str(e)}")
        raise

if __name__ == '__main__':
    asyncio.run(main()) 