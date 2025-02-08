import logging
import sys
from pathlib import Path
from typing import Optional
from ..utils.config import Config

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
        config = Config()
        log_config = config.logging_config
        
        self.logger = logging.getLogger('BatchProcessor')
        self.logger.setLevel(getattr(logging, log_config.get('level', 'INFO').upper()))
        
        # 清除现有的处理器
        self.logger.handlers = []
        
        # 控制台处理器
        if log_config.get('console_output', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_config.get('level', 'INFO').upper()))
            console_format = logging.Formatter(
                log_config.get('format', '%(asctime)s [%(levelname)s] %(message)s'),
                datefmt=log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
        
        self.show_progress = log_config.get('show_progress', True)
        self.stats_interval = log_config.get('stats_interval', 1)
    
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
    
    @staticmethod
    def set_log_file(log_file: Path):
        """设置日志文件"""
        instance = Logger()
        config = Config()
        log_config = config.logging_config
        
        # 如果不需要文件输出，直接返回
        if not log_config.get('file_output', True):
            return
            
        # 移除旧的文件处理器
        for handler in instance.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                instance.logger.removeHandler(handler)
        
        # 创建新的文件处理器
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_file, 
            encoding=log_config.get('encoding', 'utf-8')
        )
        file_handler.setLevel(getattr(logging, log_config.get('level', 'INFO').upper()))
        file_format = logging.Formatter(
            log_config.get('format', '%(asctime)s [%(levelname)s] %(message)s'),
            datefmt=log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
        )
        file_handler.setFormatter(file_format)
        instance.logger.addHandler(file_handler)
    
    @staticmethod
    def should_show_progress():
        """是否显示详细进度"""
        return Logger()._instance.show_progress
    
    @staticmethod
    def should_show_stats(batch_count: int):
        """是否应该显示统计信息"""
        return batch_count % Logger()._instance.stats_interval == 0 