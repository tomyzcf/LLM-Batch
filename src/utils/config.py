from pathlib import Path
import yaml
from typing import Dict, Any

class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config/config.yaml"):
        self.config_path = Path(config_file)
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
            
        self.config = self._load_config()
        self._setup_directories()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _setup_directories(self):
        """创建必要的目录"""
        directories = [
            'inputData',
            'outputData',
            'prompts',
            'logs'
        ]
        for dir_name in directories:
            Path(dir_name).mkdir(exist_ok=True)
            
    @property
    def default_provider(self) -> str:
        """获取默认API提供商"""
        return self.config.get('default_provider', 'deepseek')
            
    @property
    def api_providers(self) -> Dict[str, Dict[str, Any]]:
        """获取API提供商配置"""
        return self.config.get('api_providers', {})
        
    @property
    def output_config(self) -> Dict[str, Any]:
        """获取输出配置"""
        return self.config.get('output', {})
        
    @property
    def logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.config.get('logging', {})
        
    @property
    def process_config(self) -> Dict[str, Any]:
        """获取处理配置"""
        return self.config.get('process', {}) 