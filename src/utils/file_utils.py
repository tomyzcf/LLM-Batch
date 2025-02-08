from pathlib import Path
import pandas as pd
import json
from typing import List, Dict, Any, Iterator

class FileProcessor:
    """文件处理工具类"""
    
    @staticmethod
    def get_input_files(input_path: Path) -> List[Path]:
        """获取输入目录下的所有支持的文件"""
        if input_path.is_dir():
            files = []
            for ext in ['.csv', '.json', '.xlsx', '.xls']:
                files.extend(input_path.glob(f'*{ext}'))
            return sorted(files)
        else:
            return [input_path] if input_path.suffix.lower() in ['.csv', '.json', '.xlsx', '.xls'] else []
    
    @staticmethod
    def read_file_batch(file_path: Path, start_pos: int, batch_size: int, fields: List[int] = None) -> List[Dict[str, Any]]:
        """读取文件的一个批次数据"""
        ext = file_path.suffix.lower()
        if ext == '.json':
            return FileProcessor._read_json_batch(file_path, start_pos, batch_size, fields)
        elif ext == '.csv':
            return FileProcessor._read_csv_batch(file_path, start_pos, batch_size, fields)
        elif ext in ['.xlsx', '.xls']:
            return FileProcessor._read_excel_batch(file_path, start_pos, batch_size, fields)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    @staticmethod
    def _read_json_batch(file_path: Path, start_pos: int, batch_size: int, fields: List[int] = None) -> List[Dict[str, Any]]:
        """读取JSON文件批次"""
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for _ in range(start_pos):
                next(f, None)
            
            count = 0
            for line in f:
                if count >= batch_size:
                    break
                try:
                    item = json.loads(line.strip())
                    items.append(FileProcessor._process_row(item, fields))
                    count += 1
                except json.JSONDecodeError:
                    continue
        return items
    
    @staticmethod
    def _read_csv_batch(file_path: Path, start_pos: int, batch_size: int, fields: List[int] = None) -> List[Dict[str, Any]]:
        """读取CSV文件批次"""
        try:
            encodings = ['utf-8-sig', 'gbk', 'gb18030']
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, skiprows=range(1, start_pos + 1), nrows=batch_size)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("无法使用支持的编码读取文件")
            
            if fields is not None:
                df = df.iloc[:, fields]
                
            return [FileProcessor._process_row(row) for _, row in df.iterrows()]
        except Exception as e:
            raise ValueError(f"读取CSV文件失败: {str(e)}")
    
    @staticmethod
    def _read_excel_batch(file_path: Path, start_pos: int, batch_size: int, fields: List[int] = None) -> List[Dict[str, Any]]:
        """读取Excel文件批次"""
        try:
            df = pd.read_excel(file_path, skiprows=range(1, start_pos + 1), nrows=batch_size)
            if fields is not None:
                df = df.iloc[:, fields]
            return [FileProcessor._process_row(row) for _, row in df.iterrows()]
        except Exception as e:
            raise ValueError(f"读取Excel文件失败: {str(e)}")
    
    @staticmethod
    def _process_row(row: Any, fields: List[int] = None) -> Dict[str, str]:
        """处理单行数据"""
        if isinstance(row, pd.Series):
            values = row.values.tolist()
        elif isinstance(row, dict):
            values = list(row.values())
        elif isinstance(row, (list, tuple)):
            values = row
        else:
            values = [row]
        
        if fields is not None:
            values = [values[i] for i in fields if i < len(values)]
            
        text = ' '.join(str(v).strip() for v in values if pd.notna(v) and str(v).strip())
        return {"content": text} 