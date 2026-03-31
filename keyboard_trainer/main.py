"""
应用程序入口

初始化并启动键盘练习工具。

Requirements: 10.5
"""

import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from keyboard_trainer.data_store import DataStore
from keyboard_trainer.logger import setup_logging, get_logger
from keyboard_trainer.error_handler import ErrorHandler, set_error_handler


def get_app_data_dir() -> Path:
    """获取应用数据目录"""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"
    
    app_dir = base / "KeyboardTrainer"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def setup_exception_handler(error_handler: ErrorHandler):
    """设置全局异常处理"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_handler.handle_exception(exc_value, "Uncaught exception")
    
    sys.excepthook = handle_exception


def main():
    """主函数"""
    # 获取应用数据目录
    app_dir = get_app_data_dir()
    
    # 初始化日志系统
    log_dir = app_dir / "logs"
    logger = setup_logging(str(log_dir))
    logger.info("Application starting...")
    
    # 初始化错误处理器
    error_handler = ErrorHandler(logger)
    set_error_handler(error_handler)
    setup_exception_handler(error_handler)
    
    # 初始化数据存储
    db_path = app_dir / "keyboard_trainer.db"
    data_store = DataStore(str(db_path))
    logger.info(f"Database initialized at: {db_path}")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("Keyboard Trainer")
    app.setApplicationVersion("1.0.0")
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    try:
        # 导入并创建主窗口
        from keyboard_trainer.ui.main_window import MainWindow
        
        window = MainWindow(data_store)
        window.show()
        
        logger.info("Main window displayed")
        
        # 运行应用
        exit_code = app.exec_()
        
    except Exception as e:
        error_handler.handle_exception(e, "Application startup")
        exit_code = 1
    
    finally:
        # 清理资源
        data_store.close()
        logger.info("Application closed")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
