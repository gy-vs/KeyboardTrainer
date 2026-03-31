"""
报告视图模块

显示熟练度报告和进步报告。

Requirements: 2.3, 2.6, 7.5, 9.4
"""

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGridLayout
)

from keyboard_trainer.models import ProficiencyReport, ProgressReport, WeakKey


class StatCard(QFrame):
    """统计卡片组件"""
    
    def __init__(self, title: str, value: str, color: str = "#4CAF50", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #666;")
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color};")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)


class KeyAccuracyBar(QWidget):
    """按键准确率条形图"""
    
    def __init__(self, key: str, accuracy: float, parent=None):
        super().__init__(parent)
        self.key = key
        self.accuracy = accuracy
        self.setMinimumHeight(30)
        self.setMinimumWidth(200)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 背景
        painter.fillRect(0, 0, width, height, QColor("#F0F0F0"))
        
        # 准确率条
        bar_width = int(width * 0.7 * self.accuracy)
        color = QColor("#4CAF50") if self.accuracy >= 0.9 else QColor("#FF6B6B")
        painter.fillRect(60, 5, bar_width, height - 10, color)
        
        # 按键标签
        painter.setPen(QColor("#333"))
        painter.setFont(QFont("Consolas", 12, QFont.Bold))
        painter.drawText(10, 0, 40, height, Qt.AlignVCenter, self.key.upper())
        
        # 准确率文本
        painter.drawText(width - 50, 0, 50, height, Qt.AlignVCenter | Qt.AlignRight, 
                        f"{self.accuracy * 100:.0f}%")


class ReportView(QWidget):
    """报告视图，显示熟练度报告和进步报告"""
    
    # 信号
    start_training_requested = pyqtSignal(list)  # 开始训练信号，传递薄弱按键列表
    back_requested = pyqtSignal()  # 返回主菜单信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_report: Optional[ProficiencyReport] = None
        self._progress_report: Optional[ProgressReport] = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 标题
        self.title_label = QLabel("测试报告")
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.back_button = QPushButton("返回")
        self.back_button.setFont(QFont("Arial", 12))
        self.back_button.setMinimumSize(100, 40)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        self.back_button.clicked.connect(self._go_back)
        
        self.train_button = QPushButton("开始针对性训练")
        self.train_button.setFont(QFont("Arial", 12))
        self.train_button.setMinimumSize(150, 40)
        self.train_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.train_button.clicked.connect(self._start_training)
        
        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        button_layout.addWidget(self.train_button)
        layout.addLayout(button_layout)
    
    def show_proficiency_report(self, report: ProficiencyReport):
        """显示熟练度报告"""
        self._current_report = report
        self._progress_report = None
        self.title_label.setText("熟练度报告")
        self._clear_content()
        
        result = report.test_result
        
        # 整体统计卡片
        stats_layout = QHBoxLayout()
        
        stats_layout.addWidget(StatCard("WPM", f"{result.wpm:.1f}", "#4CAF50"))
        stats_layout.addWidget(StatCard("CPM", f"{result.cpm:.1f}", "#2196F3"))
        stats_layout.addWidget(StatCard("准确率", f"{result.accuracy * 100:.1f}%", 
                                       "#4CAF50" if result.accuracy >= 0.9 else "#FF6B6B"))
        stats_layout.addWidget(StatCard("评级", report.overall_grade, 
                                       self._get_grade_color(report.overall_grade)))
        
        stats_widget = QWidget()
        stats_widget.setLayout(stats_layout)
        self.content_layout.addWidget(stats_widget)
        
        # 薄弱按键
        if report.weak_keys:
            weak_section = self._create_section("薄弱按键")
            weak_layout = QVBoxLayout()
            
            for wk in report.weak_keys[:10]:  # 最多显示 10 个
                bar = KeyAccuracyBar(wk.key, wk.accuracy)
                weak_layout.addWidget(bar)
            
            weak_widget = QWidget()
            weak_widget.setLayout(weak_layout)
            weak_section.layout().addWidget(weak_widget)
            self.content_layout.addWidget(weak_section)
        
        # 建议
        if report.recommendations:
            rec_section = self._create_section("改进建议")
            rec_layout = QVBoxLayout()
            
            for rec in report.recommendations:
                rec_label = QLabel(f"• {rec}")
                rec_label.setFont(QFont("Arial", 11))
                rec_label.setWordWrap(True)
                rec_layout.addWidget(rec_label)
            
            rec_widget = QWidget()
            rec_widget.setLayout(rec_layout)
            rec_section.layout().addWidget(rec_widget)
            self.content_layout.addWidget(rec_section)
        
        self.content_layout.addStretch()
    
    def show_progress_report(self, report: ProgressReport):
        """显示进步报告"""
        self._progress_report = report
        self._current_report = None
        self.title_label.setText("进步报告")
        self._clear_content()
        
        # 进步统计
        stats_layout = QHBoxLayout()
        
        wpm_color = "#4CAF50" if report.wpm_improvement >= 0 else "#FF6B6B"
        acc_color = "#4CAF50" if report.accuracy_improvement >= 0 else "#FF6B6B"
        
        stats_layout.addWidget(StatCard("WPM 变化", 
                                       f"{'+' if report.wpm_improvement >= 0 else ''}{report.wpm_improvement:.1f}%",
                                       wpm_color))
        stats_layout.addWidget(StatCard("准确率变化",
                                       f"{'+' if report.accuracy_improvement >= 0 else ''}{report.accuracy_improvement:.1f}%",
                                       acc_color))
        
        stats_widget = QWidget()
        stats_widget.setLayout(stats_layout)
        self.content_layout.addWidget(stats_widget)
        
        # 改善的按键
        if report.improved_keys:
            improved_section = self._create_section("已改善的按键")
            improved_label = QLabel(", ".join(report.improved_keys))
            improved_label.setFont(QFont("Consolas", 14))
            improved_label.setStyleSheet("color: #4CAF50;")
            improved_section.layout().addWidget(improved_label)
            self.content_layout.addWidget(improved_section)
        
        # 仍需加强的按键
        if report.still_weak_keys:
            weak_section = self._create_section("仍需加强的按键")
            weak_label = QLabel(", ".join(report.still_weak_keys))
            weak_label.setFont(QFont("Consolas", 14))
            weak_label.setStyleSheet("color: #FF6B6B;")
            weak_section.layout().addWidget(weak_label)
            self.content_layout.addWidget(weak_section)
        
        # 总结
        conclusion_section = self._create_section("总结")
        conclusion_label = QLabel(report.conclusion)
        conclusion_label.setFont(QFont("Arial", 12))
        conclusion_label.setWordWrap(True)
        conclusion_section.layout().addWidget(conclusion_label)
        self.content_layout.addWidget(conclusion_section)
        
        self.content_layout.addStretch()
    
    def _create_section(self, title: str) -> QFrame:
        """创建报告区块"""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #DDD;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(section)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("border: none;")
        layout.addWidget(title_label)
        
        return section
    
    def _clear_content(self):
        """清除内容"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _get_grade_color(self, grade: str) -> str:
        """获取评级颜色"""
        colors = {
            "A": "#4CAF50",
            "B": "#8BC34A",
            "C": "#FFC107",
            "D": "#FF9800",
            "F": "#F44336"
        }
        return colors.get(grade, "#666")
    
    def _start_training(self):
        """开始针对性训练"""
        weak_keys = []
        if self._current_report and self._current_report.weak_keys:
            weak_keys = [wk.key for wk in self._current_report.weak_keys]
        elif self._progress_report and self._progress_report.still_weak_keys:
            weak_keys = self._progress_report.still_weak_keys
        
        self.start_training_requested.emit(weak_keys)
    
    def _go_back(self):
        """返回主菜单"""
        self.back_requested.emit()
