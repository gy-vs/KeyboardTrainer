"""
日志系统模块

配置应用程序的日志记录，使用 RotatingFileHandler 实现日志轮转。

Requirements: 10.4, 10.5
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    log_dir: str,
    log_file: str = "keyboard_trainer.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    level: int = logging.DEBUG
) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        log_dir: 日志文件目录
        log_file: 日志文件名
        max_bytes: 单个日志文件最大大小（字节），默认 10MB
        backup_count: 保留的备份文件数量
        level: 日志级别
        
    Returns:
        配置好的 Logger 实例
    """
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_path = os.path.join(log_dir, log_file)
    
    # 获取或创建 logger
    logger = logging.getLogger("keyboard_trainer")
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 文件处理器 - 10MB 轮转
    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    
    # 控制台处理器（仅显示警告及以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(
        "%(levelname)s: %(message)s"
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("Logging system initialized")
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取 logger 实例
    
    Args:
        name: logger 名称，如果为 None 则返回根 logger
        
    Returns:
        Logger 实例
    """
    if name:
        return logging.getLogger(f"keyboard_trainer.{name}")
    return logging.getLogger("keyboard_trainer")
