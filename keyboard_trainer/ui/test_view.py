"""
测试视图模块

显示打字测试界面。

Requirements: 1.1, 4.4, 9.3
"""

import time
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QKeyEvent
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QTextEdit
)

from keyboard_trainer.models import TestType
from keyboard_trainer.test_controller import TestController
from keyboard_trainer.ui.virtual_keyboard import VirtualKeyboard


class TestView(QWidget):
    """测试视图，显示打字测试界面"""
    
    # 信号
    test_completed = pyqtSignal(object)  # 测试完成信号，传递 TestResult
    back_requested = pyqtSignal()  # 返回主菜单信号
    
    def __init__(self, test_controller: Optional[TestController] = None, parent=None):
        super().__init__(parent)
        self.test_controller = test_controller or TestController()
        self._init_ui()
        self._is_test_active = False
        self._pending_content = None  # 用于进阶测试的待加载内容
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("基础打字测试")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 测试文本显示区域
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
        
        # 当前字符提示
        char_layout = QHBoxLayout()
        char_label = QLabel("下一个字符:")
        char_label.setFont(QFont("Arial", 12))
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
        char_layout.addStretch()
        layout.addLayout(char_layout)
        
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
                background-color: #4CAF50;
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
        self.start_button = QPushButton("开始测试")
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
        self.start_button.clicked.connect(self._start_test)
        
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
    
    def _start_test(self):
        """开始测试"""
        session = self.test_controller.start_test(TestType.BASIC)
        self._is_test_active = True
        self.start_button.setEnabled(False)
        self.start_button.setText("测试中...")
        
        # 显示测试内容
        self._update_display()
        self.setFocus()
    
    def _update_display(self):
        """更新显示"""
        if not self._is_test_active:
            return
        
        session = self.test_controller._current_session
        if session is None:
            return
        
        content = session.content
        pos = session.current_position
        
        # 构建带高亮的文本
        html = '<span style="color: #4CAF50;">'  # 已完成部分（绿色）
        html += content[:pos].replace(' ', '&nbsp;').replace('\n', '<br>')
        html += '</span>'
        
        if pos < len(content):
            # 当前字符（高亮）
            current_char = content[pos]
            display_char = '␣' if current_char == ' ' else current_char
            html += f'<span style="background-color: #FFD700; font-weight: bold;">{display_char}</span>'
            
            # 剩余部分
            html += content[pos + 1:].replace(' ', '&nbsp;').replace('\n', '<br>')
            
            # 更新当前字符提示
            self.current_char_label.setText(display_char)
            
            # 高亮虚拟键盘
            self.virtual_keyboard.highlight_key(current_char)
        
        self.text_display.setHtml(html)
        
        # 更新进度
        progress = self.test_controller.get_progress()
        self.progress_bar.setValue(int(progress * 100))
    
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if not self._is_test_active:
            super().keyPressEvent(event)
            return
        
        # 获取输入的字符
        text = event.text()
        if not text:
            super().keyPressEvent(event)
            return
        
        # 获取期望的字符
        expected = self.test_controller.get_next_character()
        if not expected:
            self._finish_test()
            return
        
        # 记录按键
        timestamp = time.time() * 1000
        result = self.test_controller.record_keystroke(expected, text, timestamp)
        
        # 显示反馈
        if result.correct:
            self.virtual_keyboard.show_correct_feedback(expected)
        else:
            self.virtual_keyboard.show_incorrect_feedback(expected)
        
        # 更新显示
        self._update_display()
        
        # 检查是否完成
        if self.test_controller.is_test_complete():
            self._finish_test()
    
    def _finish_test(self):
        """完成测试"""
        self._is_test_active = False
        result = self.test_controller.finish_test()
        
        self.start_button.setEnabled(True)
        self.start_button.setText("重新测试")
        self.virtual_keyboard.reset_highlight()
        
        self.test_completed.emit(result)
    
    def _go_back(self):
        """返回主菜单"""
        self._is_test_active = False
        self._reset_view()
        self.back_requested.emit()
    
    def _reset_view(self):
        """重置视图状态"""
        self._is_test_active = False
        self.start_button.setEnabled(True)
        self.start_button.setText("开始测试")
        self.text_display.clear()
        self.current_char_label.setText("")
        self.progress_bar.setValue(0)
        self.virtual_keyboard.reset_highlight()
        # 重置控制器状态
        self.test_controller._current_session = None
        self._pending_content = None
    
    def showEvent(self, event):
        """视图显示时处理状态"""
        super().showEvent(event)
        # 如果有待加载的内容（进阶测试），则加载它
        if self._pending_content is not None:
            self._load_pending_content()
        else:
            self._reset_view()
    
    def _load_pending_content(self):
        """加载待处理的内容"""
        content = self._pending_content
        self._pending_content = None
        self.test_controller.start_test(TestType.ADVANCED, content)
        self._is_test_active = True
        self.start_button.setEnabled(False)
        self.start_button.setText("测试中...")
        self._update_display()
        self.setFocus()
    
    def set_content(self, content: str):
        """设置测试内容（用于进阶测试）"""
        # 保存内容，等待 showEvent 时加载
        self._pending_content = content
