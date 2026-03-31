"""
错误处理模块

提供全局错误处理和用户友好的错误消息映射。

Requirements: 10.1, 10.2, 10.3, 9.6
"""

import logging
import sqlite3
import traceback
from dataclasses import dataclass
from typing import Dict, Optional, Type


# 自定义异常类
class InvalidFileFormatError(Exception):
    """文件格式无效异常"""
    pass


class ContentTooShortError(Exception):
    """内容长度不足异常"""
    pass


class DataCorruptionError(Exception):
    """数据损坏异常"""
    pass


@dataclass
class ErrorResult:
    """错误处理结果"""
    success: bool
    user_message: str
    can_retry: bool
    original_exception: Optional[Exception] = None


class ErrorHandler:
    """全局错误处理器"""
    
    # 错误消息映射表
    ERROR_MESSAGES: Dict[Type[Exception], str] = {
        FileNotFoundError: "无法找到所选文件，请重新选择",
        InvalidFileFormatError: "仅支持 TXT 格式文件",
        ContentTooShortError: "文件内容不足 50000 字符，请选择更长的文章",
        sqlite3.Error: "数据保存失败，请重试",
        DataCorruptionError: "检测到数据损坏，已创建备份",
        PermissionError: "没有访问文件的权限，请检查文件权限",
        IOError: "文件读写错误，请重试",
        ValueError: "数据格式错误，请检查输入",
    }
    
    # 可重试的异常类型
    RETRYABLE_EXCEPTIONS = {
        sqlite3.Error,
        IOError,
        TimeoutError,
    }
    
    DEFAULT_MESSAGE = "发生未知错误，请重启应用"
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化错误处理器
        
        Args:
            logger: 日志记录器，如果为 None 则使用默认 logger
        """
        self.logger = logger or logging.getLogger("keyboard_trainer")
    
    def handle_exception(self, exception: Exception, context: str = "") -> ErrorResult:
        """
        处理异常并返回用户友好的结果
        
        Args:
            exception: 捕获的异常
            context: 异常发生的上下文描述
            
        Returns:
            ErrorResult 包含用户友好的错误信息
        """
        # 记录详细错误信息（包含堆栈跟踪）
        self.logger.error(
            f"Exception in {context}: {type(exception).__name__}: {str(exception)}",
            exc_info=True
        )
        
        # 获取用户友好的错误消息
        user_message = self._get_user_message(exception)
        
        # 判断是否可重试
        can_retry = self._is_retryable(exception)
        
        return ErrorResult(
            success=False,
            user_message=user_message,
            can_retry=can_retry,
            original_exception=exception
        )
    
    def _get_user_message(self, exception: Exception) -> str:
        """
        获取用户友好的错误消息
        
        不包含技术细节、堆栈跟踪或内部变量名。
        
        Args:
            exception: 异常对象
            
        Returns:
            用户友好的错误消息
        """
        # 首先检查精确类型匹配
        exc_type = type(exception)
        if exc_type in self.ERROR_MESSAGES:
            return self.ERROR_MESSAGES[exc_type]
        
        # 检查父类匹配
        for error_type, message in self.ERROR_MESSAGES.items():
            if isinstance(exception, error_type):
                return message
        
        return self.DEFAULT_MESSAGE
    
    def _is_retryable(self, exception: Exception) -> bool:
        """
        判断异常是否可重试
        
        Args:
            exception: 异常对象
            
        Returns:
            是否可以重试操作
        """
        for retryable_type in self.RETRYABLE_EXCEPTIONS:
            if isinstance(exception, retryable_type):
                return True
        return False
    
    def log_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """
        记录错误日志
        
        Args:
            message: 错误消息
            exception: 可选的异常对象
        """
        if exception:
            self.logger.error(f"{message}: {type(exception).__name__}: {str(exception)}")
        else:
            self.logger.error(message)
    
    def log_warning(self, message: str) -> None:
        """
        记录警告日志
        
        Args:
            message: 警告消息
        """
        self.logger.warning(message)
    
    def log_info(self, message: str) -> None:
        """
        记录信息日志
        
        Args:
            message: 信息消息
        """
        self.logger.info(message)


# 全局错误处理器实例
_global_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    获取全局错误处理器实例
    
    Returns:
        ErrorHandler 实例
    """
    global _global_handler
    if _global_handler is None:
        _global_handler = ErrorHandler()
    return _global_handler


def set_error_handler(handler: ErrorHandler) -> None:
    """
    设置全局错误处理器实例
    
    Args:
        handler: ErrorHandler 实例
    """
    global _global_handler
    _global_handler = handler
