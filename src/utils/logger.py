import logging
import sys
from pathlib import Path
from typing import Optional

class Logger:
    """日志工具类"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """设置日志配置"""
        self.logger = logging.getLogger('BatchProcessor')
        self.logger.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '\n%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # 文件处理器
        log_file = Path('logs/batch_process.log')
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    @staticmethod
    def set_level(level: str):
        """设置日志级别"""
        Logger()._instance.logger.setLevel(getattr(logging, level.upper()))
    
    @staticmethod
    def info(msg: str):
        Logger().logger.info(msg)
    
    @staticmethod
    def error(msg: str):
        Logger().logger.error(msg)
    
    @staticmethod
    def warning(msg: str):
        Logger().logger.warning(msg)
    
    @staticmethod
    def debug(msg: str):
        Logger().logger.debug(msg) 