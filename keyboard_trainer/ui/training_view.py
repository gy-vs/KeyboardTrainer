"""
训练视图模块

显示针对性训练界面。

Requirements: 4.4, 4.5, 9.5
"""

import time
from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QKeyEvent
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QTextEdit
)

from keyboard_trainer.training_controller import TrainingController
from keyboard_trainer.ui.virtual_keyboard import VirtualKeyboard


class TrainingView(QWidget):
    """训练视图，显示针对性训练界面"""
    
    # 信号
    training_completed = pyqtSignal()  # 训练完成信号
    back_requested = pyqtSignal()  # 返回主菜单信号
    
    def __init__(self, training_controller: Optional[TrainingController] = None, parent=None):
        super().__init__(parent)
        self.training_controller = training_controller or TrainingController()
        self._weak_keys: List[str] = []
        self._is_training_active = False
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("针对性训练")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 薄弱按键提示
        self.weak_keys_label = QLabel("目标按键: 无")
        self.weak_keys_label.setFont(QFont("Arial", 12))
        self.weak_keys_label.setStyleSheet("""
            QLabel {
                background-color: #FFF3CD;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #FFEEBA;
            }
        """)
        layout.addWidget(self.weak_keys_label)
        
        # 训练文本显示区域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Consolas", 14))
        self.text_display.setMinimumHeight(100)
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #F5F5F5;
                border: 2px solid #DDD;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.text_display)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        
        # 当前字符
        char_layout = QVBoxLayout()
        char_label = QLabel("下一个字符")
        char_label.setAlignment(Qt.AlignCenter)
        self.current_char_label = QLabel("")
        self.current_char_label.setFont(QFont("Consolas", 24, QFont.Bold))
        self.current_char_label.setStyleSheet("""
            QLabel {
                background-color: #FFD700;
                padding: 10px 20px;
                border-radius: 8px;
                min-width: 60px;
            }
        """)
        self.current_char_label.setAlignment(Qt.AlignCenter)
        char_layout.addWidget(char_label)
        char_layout.addWidget(self.current_char_label)
        stats_layout.addLayout(char_layout)
        
        stats_layout.addStretch()
        
        # 准确率
        accuracy_layout = QVBoxLayout()
        accuracy_label = QLabel("当前准确率")
        accuracy_label.setAlignment(Qt.AlignCenter)
        self.accuracy_label = QLabel("0%")
        self.accuracy_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.accuracy_label.setAlignment(Qt.AlignCenter)
        accuracy_layout.addWidget(accuracy_label)
        accuracy_layout.addWidget(self.accuracy_label)
        stats_layout.addLayout(accuracy_layout)
        
        layout.addLayout(stats_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_label = QLabel("进度:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #DDD;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        # 虚拟键盘
        self.virtual_keyboard = VirtualKeyboard()
        layout.addWidget(self.virtual_keyboard)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("开始训练")
        self.start_button.setFont(QFont("Arial", 12))
        self.start_button.setMinimumSize(120, 40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:disabled {
                background-color: #A5D6A7;
            }
        """)
        self.start_button.clicked.connect(self._start_training)
        
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
        
        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        layout.addLayout(button_layout)
        
        # 设置焦点策略
        self.setFocusPolicy(Qt.StrongFocus)
    
    def set_weak_keys(self, weak_keys: List[str]):
        """设置薄弱按键"""
        self._weak_keys = weak_keys
        if weak_keys:
            self.weak_keys_label.setText(f"目标按键: {', '.join(weak_keys)}")
        else:
            self.weak_keys_label.setText("目标按键: 无（将进行常规练习）")
    
    def _start_training(self):
        """开始训练"""
        self.training_controller.start_training(self._weak_keys)
        self._is_training_active = True
        self.start_button.setEnabled(False)
        self.start_button.setText("训练中...")
        
        self._update_display()
        self.setFocus()
    
    def _update_display(self):
        """更新显示"""
        if not self._is_training_active:
            return
        
        session = self.training_controller._current_session
        if session is None:
            return
        
        content = session.content
        pos = session.current_position
        
        # 构建带高亮的文本
        html = '<span style="color: #4CAF50;">'
        html += content[:pos].replace(' ', '&nbsp;').replace('\n', '<br>')
        html += '</span>'
        
        if pos < len(content):
            current_char = content[pos]
            display_char = '␣' if current_char == ' ' else current_char
            html += f'<span style="background-color: #FFD700; font-weight: bold;">{display_char}</span>'
            html += content[pos + 1:].replace(' ', '&nbsp;').replace('\n', '<br>')
            
            self.current_char_label.setText(display_char)
            self.virtual_keyboard.highlight_key(current_char)
        
        self.text_display.setHtml(html)
        
        # 更新进度和准确率
        progress = self.training_controller.get_training_progress()
        if progress.total_characters > 0:
            percent = (progress.completed_characters / progress.total_characters) * 100
            self.progress_bar.setValue(int(percent))
        
        self.accuracy_label.setText(f"{progress.current_accuracy * 100:.1f}%")
    
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if not self._is_training_active:
            super().keyPressEvent(event)
            return
        
        text = event.text()
        if not text:
            super().keyPressEvent(event)
            return
        
        expected = self.training_controller.get_next_character()
        if not expected:
            self._finish_training()
            return
        
        timestamp = time.time() * 1000
        result = self.training_controller.record_keystroke(expected, text, timestamp)
        
        if result.correct:
            self.virtual_keyboard.show_correct_feedback(expected)
        else:
            self.virtual_keyboard.show_incorrect_feedback(expected)
        
        self._update_display()
        
        if self.training_controller.is_training_complete():
            self._finish_training()
    
    def _finish_training(self):
        """完成训练"""
        self._is_training_active = False
        
        self.start_button.setEnabled(True)
        self.start_button.setText("重新训练")
        self.virtual_keyboard.reset_highlight()
        
        self.training_completed.emit()
    
    def _go_back(self):
        """返回主菜单"""
        self._is_training_active = False
        self._reset_view()
        self.back_requested.emit()
    
    def _reset_view(self):
        """重置视图状态"""
        self._is_training_active = False
        self.start_button.setEnabled(True)
        self.start_button.setText("开始训练")
        self.text_display.clear()
        self.current_char_label.setText("")
        self.accuracy_label.setText("0%")
        self.progress_bar.setValue(0)
        self.virtual_keyboard.reset_highlight()
        # 重置控制器状态
        self.training_controller._current_session = None
    
    def showEvent(self, event):
        """视图显示时重置状态"""
        super().showEvent(event)
        # 不完全重置，保留薄弱按键设置
        self.start_button.setEnabled(True)
        self.start_button.setText("开始训练")
        self.text_display.clear()
        self.current_char_label.setText("")
        self.accuracy_label.setText("0%")
        self.progress_bar.setValue(0)
        self.virtual_keyboard.reset_highlight()
        self._is_training_active = False
        self.training_controller._current_session = None
