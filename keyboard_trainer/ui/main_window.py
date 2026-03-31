"""
主窗口模块

管理应用程序的整体布局和导航。

Requirements: 9.1, 9.2, 9.3, 9.6, 6.1
"""

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFileDialog,
    QMessageBox
)

from keyboard_trainer.data_store import DataStore
from keyboard_trainer.file_handler import FileHandler
from keyboard_trainer.report_generator import ReportGenerator
from keyboard_trainer.test_controller import TestController
from keyboard_trainer.training_controller import TrainingController
from keyboard_trainer.models import ProficiencyReport, TestResult
from keyboard_trainer.ui.test_view import TestView
from keyboard_trainer.ui.training_view import TrainingView
from keyboard_trainer.ui.report_view import ReportView


class MainWindow(QMainWindow):
    """主窗口类，管理应用程序的整体布局和导航"""
    
    def __init__(self, data_store: Optional[DataStore] = None):
        """初始化主窗口"""
        super().__init__()
        self.data_store = data_store
        self.file_handler = FileHandler()
        self.report_generator = ReportGenerator(data_store)
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("键盘练习工具")
        self.setMinimumSize(900, 700)
        
        # 设置全局样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F5;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #3D8B40;
            }
        """)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 堆叠窗口
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # 创建各个视图
        self._create_menu_view()
        self._create_test_view()
        self._create_training_view()
        self._create_report_view()
        
        # 显示主菜单
        self.stack.setCurrentIndex(0)
    
    def _create_menu_view(self):
        """创建主菜单视图"""
        menu_widget = QWidget()
        layout = QVBoxLayout(menu_widget)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # 标题
        title = QLabel("键盘练习工具")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)
        
        # 副标题
        subtitle = QLabel("提升您的打字技能")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)
        
        layout.addStretch()
        
        # 按钮区域
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        
        # 基础测试按钮
        self.basic_test_btn = QPushButton("基础打字测试")
        self.basic_test_btn.setMinimumHeight(60)
        self.basic_test_btn.setFont(QFont("Arial", 14))
        button_layout.addWidget(self.basic_test_btn)
        
        # 针对性训练按钮
        self.training_btn = QPushButton("针对性训练")
        self.training_btn.setMinimumHeight(60)
        self.training_btn.setFont(QFont("Arial", 14))
        self.training_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(self.training_btn)
        
        # 进阶测试按钮
        self.advanced_test_btn = QPushButton("进阶测试（自定义文章）")
        self.advanced_test_btn.setMinimumHeight(60)
        self.advanced_test_btn.setFont(QFont("Arial", 14))
        self.advanced_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        button_layout.addWidget(self.advanced_test_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # 版本信息
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #999;")
        layout.addWidget(version_label)
        
        self.stack.addWidget(menu_widget)
    
    def _create_test_view(self):
        """创建测试视图"""
        self.test_controller = TestController(self.data_store)
        self.test_view = TestView(self.test_controller)
        self.stack.addWidget(self.test_view)
    
    def _create_training_view(self):
        """创建训练视图"""
        self.training_controller = TrainingController(self.data_store)
        self.training_view = TrainingView(self.training_controller)
        self.stack.addWidget(self.training_view)
    
    def _create_report_view(self):
        """创建报告视图"""
        self.report_view = ReportView()
        self.stack.addWidget(self.report_view)
    
    def _connect_signals(self):
        """连接信号"""
        # 主菜单按钮
        self.basic_test_btn.clicked.connect(self.show_basic_test)
        self.training_btn.clicked.connect(self.show_training)
        self.advanced_test_btn.clicked.connect(self.show_advanced_test)
        
        # 测试视图信号
        self.test_view.test_completed.connect(self._on_test_completed)
        self.test_view.back_requested.connect(self._show_menu)
        
        # 训练视图信号
        self.training_view.training_completed.connect(self._on_training_completed)
        self.training_view.back_requested.connect(self._show_menu)
        
        # 报告视图信号
        self.report_view.start_training_requested.connect(self._start_training_with_keys)
        self.report_view.back_requested.connect(self._show_menu)
    
    def show_basic_test(self) -> None:
        """显示基础测试界面"""
        self.stack.setCurrentWidget(self.test_view)
    
    def show_training(self) -> None:
        """显示针对性训练界面"""
        # 获取薄弱按键
        weak_keys = []
        if self.data_store:
            weak_key_objs = self.data_store.get_weak_keys()
            weak_keys = [wk.key for wk in weak_key_objs]
        
        self.training_view.set_weak_keys(weak_keys)
        self.stack.setCurrentWidget(self.training_view)
    
    def show_advanced_test(self) -> None:
        """显示进阶测试界面"""
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文本文件",
            "",
            "文本文件 (*.txt)"
        )
        
        if not file_path:
            return
        
        # 加载文件
        result = self.file_handler.load_file(file_path)
        
        if not result.success:
            self.show_error(result.error_message)
            return
        
        # 设置测试内容并开始
        self.test_view.set_content(result.content)
        self.stack.setCurrentWidget(self.test_view)
    
    def show_report(self, report: ProficiencyReport) -> None:
        """显示熟练度报告"""
        self.report_view.show_proficiency_report(report)
        self.stack.setCurrentWidget(self.report_view)
    
    def show_error(self, message: str) -> None:
        """显示错误消息"""
        QMessageBox.warning(self, "错误", message)
    
    def _show_menu(self):
        """显示主菜单"""
        self.stack.setCurrentIndex(0)
    
    def _on_test_completed(self, result: TestResult):
        """测试完成处理"""
        # 生成报告
        report = self.report_generator.generate_proficiency_report(result)
        self.show_report(report)
    
    def _on_training_completed(self):
        """训练完成处理"""
        QMessageBox.information(self, "训练完成", "恭喜完成本次训练！")
        self._show_menu()
    
    def _start_training_with_keys(self, weak_keys: list):
        """使用指定薄弱按键开始训练"""
        self.training_view.set_weak_keys(weak_keys)
        self.stack.setCurrentWidget(self.training_view)
