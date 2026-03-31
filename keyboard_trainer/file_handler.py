"""
文件处理器模块

处理用户导入的文本文件。

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import os
from typing import Optional

from keyboard_trainer.models import FileInfo, FileLoadResult
from keyboard_trainer.error_handler import InvalidFileFormatError, ContentTooShortError


class FileHandler:
    """文件处理器，处理用户导入的文本文件"""
    
    MIN_CONTENT_LENGTH = 50000  # 最小内容长度
    SUPPORTED_FORMATS = ['.txt']  # 支持的文件格式
    
    def __init__(self):
        """初始化文件处理器"""
        pass
    
    def load_file(self, file_path: str) -> FileLoadResult:
        """
        加载文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            FileLoadResult 包含加载结果
        """
        # 验证文件格式
        if not self.validate_format(file_path):
            return FileLoadResult(
                success=False,
                content=None,
                error_message="仅支持 TXT 格式文件",
                file_info=None
            )
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return FileLoadResult(
                success=False,
                content=None,
                error_message="无法找到所选文件，请重新选择",
                file_info=None
            )
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except Exception:
                return FileLoadResult(
                    success=False,
                    content=None,
                    error_message="文件编码不支持，请使用 UTF-8 编码的文本文件",
                    file_info=None
                )
        except Exception as e:
            return FileLoadResult(
                success=False,
                content=None,
                error_message=f"文件读取失败: {str(e)}",
                file_info=None
            )
        
        # 验证内容长度
        if not self.validate_content_length(content):
            return FileLoadResult(
                success=False,
                content=None,
                error_message=f"文件内容不足 {self.MIN_CONTENT_LENGTH} 字符，请选择更长的文章",
                file_info=None
            )
        
        # 获取文件信息
        file_info = self.get_file_info(file_path)
        file_info.character_count = len(content)
        
        return FileLoadResult(
            success=True,
            content=content,
            error_message=None,
            file_info=file_info
        )
    
    def validate_format(self, file_path: str) -> bool:
        """
        验证文件格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件格式是否有效
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.SUPPORTED_FORMATS
    
    def validate_content_length(self, content: str) -> bool:
        """
        验证内容长度
        
        Args:
            content: 文件内容
            
        Returns:
            内容长度是否满足要求
        """
        return len(content) >= self.MIN_CONTENT_LENGTH
    
    def get_file_info(self, file_path: str) -> FileInfo:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            FileInfo 对象
        """
        stat = os.stat(file_path) if os.path.exists(file_path) else None
        return FileInfo(
            path=file_path,
            name=os.path.basename(file_path),
            size=stat.st_size if stat else 0,
            character_count=0  # 需要读取文件后才能确定
        )
