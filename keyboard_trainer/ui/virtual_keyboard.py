"""
虚拟键盘组件

显示键盘布局和按键高亮。

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from typing import Dict, Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QSizePolicy

from keyboard_trainer.models import FingerPosition


# QWERTY 键盘布局定义
KEYBOARD_LAYOUT = [
    # 第一行：数字行
    ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
    # 第二行
    ['Tab', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
    # 第三行
    ['Caps', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", 'Enter'],
    # 第四行
    ['Shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 'Shift'],
    # 第五行：空格行
    ['Ctrl', 'Win', 'Alt', 'Space', 'Alt', 'Win', 'Menu', 'Ctrl'],
]

# 按键到手指位置的映射
KEY_TO_FINGER: Dict[str, FingerPosition] = {
    # 左手小指
    '`': FingerPosition.LEFT_PINKY, '1': FingerPosition.LEFT_PINKY,
    'Tab': FingerPosition.LEFT_PINKY, 'q': FingerPosition.LEFT_PINKY,
    'Caps': FingerPosition.LEFT_PINKY, 'a': FingerPosition.LEFT_PINKY,
    'Shift': FingerPosition.LEFT_PINKY, 'z': FingerPosition.LEFT_PINKY,
    'Ctrl': FingerPosition.LEFT_PINKY,
    # 左手无名指
    '2': FingerPosition.LEFT_RING, 'w': FingerPosition.LEFT_RING,
    's': FingerPosition.LEFT_RING, 'x': FingerPosition.LEFT_RING,
    # 左手中指
    '3': FingerPosition.LEFT_MIDDLE, 'e': FingerPosition.LEFT_MIDDLE,
    'd': FingerPosition.LEFT_MIDDLE, 'c': FingerPosition.LEFT_MIDDLE,
    # 左手食指
    '4': FingerPosition.LEFT_INDEX, '5': FingerPosition.LEFT_INDEX,
    'r': FingerPosition.LEFT_INDEX, 't': FingerPosition.LEFT_INDEX,
    'f': FingerPosition.LEFT_INDEX, 'g': FingerPosition.LEFT_INDEX,
    'v': FingerPosition.LEFT_INDEX, 'b': FingerPosition.LEFT_INDEX,
    # 左手拇指
    'Win': FingerPosition.LEFT_THUMB, 'Alt': FingerPosition.LEFT_THUMB,
    # 右手拇指
    'Space': FingerPosition.RIGHT_THUMB,
    # 右手食指
    '6': FingerPosition.RIGHT_INDEX, '7': FingerPosition.RIGHT_INDEX,
    'y': FingerPosition.RIGHT_INDEX, 'u': FingerPosition.RIGHT_INDEX,
    'h': FingerPosition.RIGHT_INDEX, 'j': FingerPosition.RIGHT_INDEX,
    'n': FingerPosition.RIGHT_INDEX, 'm': FingerPosition.RIGHT_INDEX,
    # 右手中指
    '8': FingerPosition.RIGHT_MIDDLE, 'i': FingerPosition.RIGHT_MIDDLE,
    'k': FingerPosition.RIGHT_MIDDLE, ',': FingerPosition.RIGHT_MIDDLE,
    # 右手无名指
    '9': FingerPosition.RIGHT_RING, 'o': FingerPosition.RIGHT_RING,
    'l': FingerPosition.RIGHT_RING, '.': FingerPosition.RIGHT_RING,
    # 右手小指
    '0': FingerPosition.RIGHT_PINKY, '-': FingerPosition.RIGHT_PINKY,
    '=': FingerPosition.RIGHT_PINKY, 'Backspace': FingerPosition.RIGHT_PINKY,
    'p': FingerPosition.RIGHT_PINKY, '[': FingerPosition.RIGHT_PINKY,
    ']': FingerPosition.RIGHT_PINKY, '\\': FingerPosition.RIGHT_PINKY,
    ';': FingerPosition.RIGHT_PINKY, "'": FingerPosition.RIGHT_PINKY,
    'Enter': FingerPosition.RIGHT_PINKY, '/': FingerPosition.RIGHT_PINKY,
    'Menu': FingerPosition.RIGHT_PINKY,
}

# 特殊字符到按键的映射
CHAR_TO_KEY: Dict[str, str] = {
    ' ': 'Space',
    '\n': 'Enter',
    '\t': 'Tab',
}


class KeyButton(QLabel):
    """单个按键按钮"""
    
    # 颜色定义
    NORMAL_COLOR = "#E0E0E0"
    HIGHLIGHT_COLOR = "#FFD700"  # 金色高亮
    CORRECT_COLOR = "#90EE90"    # 浅绿色
    INCORRECT_COLOR = "#FF6B6B"  # 浅红色
    
    def __init__(self, key: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setText(key.upper() if len(key) == 1 else key)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(40, 40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._set_style(self.NORMAL_COLOR)
    
    def _set_style(self, bg_color: str):
        """设置按钮样式"""
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                border: 1px solid #999;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 4px;
            }}
        """)
    
    def set_normal(self):
        """设置为正常状态"""
        self._set_style(self.NORMAL_COLOR)
    
    def set_highlight(self):
        """设置为高亮状态"""
        self._set_style(self.HIGHLIGHT_COLOR)
    
    def set_correct(self):
        """设置为正确反馈状态"""
        self._set_style(self.CORRECT_COLOR)
    
    def set_incorrect(self):
        """设置为错误反馈状态"""
        self._set_style(self.INCORRECT_COLOR)


class VirtualKeyboard(QWidget):
    """虚拟键盘组件，显示键盘布局和按键高亮"""
    
    # 信号定义
    key_highlighted = pyqtSignal(str)  # 按键高亮信号
    
    def __init__(self, parent=None):
        """初始化虚拟键盘"""
        super().__init__(parent)
        self._key_buttons: Dict[str, KeyButton] = {}
        self._current_highlight: Optional[str] = None
        self._feedback_timer = QTimer(self)
        self._feedback_timer.timeout.connect(self._clear_feedback)
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QGridLayout(self)
        layout.setSpacing(4)
        
        for row_idx, row in enumerate(KEYBOARD_LAYOUT):
            col_offset = 0
            for col_idx, key in enumerate(row):
                button = KeyButton(key, self)
                
                # 特殊按键占用多列
                col_span = 1
                if key in ['Backspace', 'Tab', 'Caps', 'Enter', 'Shift']:
                    col_span = 2
                elif key == 'Space':
                    col_span = 6
                
                layout.addWidget(button, row_idx, col_offset, 1, col_span)
                col_offset += col_span
                
                # 存储按键引用（使用小写）
                key_lower = key.lower()
                self._key_buttons[key_lower] = button
        
        self.setLayout(layout)
    
    def highlight_key(self, key: str) -> None:
        """
        高亮指定按键
        
        Args:
            key: 要高亮的按键字符
        """
        # 清除之前的高亮
        if self._current_highlight:
            self._reset_key(self._current_highlight)
        
        # 转换特殊字符
        key_name = CHAR_TO_KEY.get(key, key).lower()
        
        if key_name in self._key_buttons:
            self._key_buttons[key_name].set_highlight()
            self._current_highlight = key_name
            self.key_highlighted.emit(key)
    
    def show_correct_feedback(self, key: str) -> None:
        """
        显示正确输入反馈（绿色）
        
        Args:
            key: 按键字符
        """
        key_name = CHAR_TO_KEY.get(key, key).lower()
        if key_name in self._key_buttons:
            self._key_buttons[key_name].set_correct()
            self._start_feedback_timer()
    
    def show_incorrect_feedback(self, key: str) -> None:
        """
        显示错误输入反馈（红色）
        
        Args:
            key: 按键字符
        """
        key_name = CHAR_TO_KEY.get(key, key).lower()
        if key_name in self._key_buttons:
            self._key_buttons[key_name].set_incorrect()
            self._start_feedback_timer()
    
    def reset_highlight(self) -> None:
        """重置所有高亮"""
        for button in self._key_buttons.values():
            button.set_normal()
        self._current_highlight = None
    
    def get_finger_guide(self, key: str) -> FingerPosition:
        """
        获取按键对应的手指位置指南
        
        Args:
            key: 按键字符
            
        Returns:
            FingerPosition 手指位置
        """
        key_name = CHAR_TO_KEY.get(key, key).lower()
        return KEY_TO_FINGER.get(key_name, FingerPosition.RIGHT_INDEX)
    
    def _reset_key(self, key: str) -> None:
        """重置单个按键状态"""
        if key in self._key_buttons:
            self._key_buttons[key].set_normal()
    
    def _start_feedback_timer(self) -> None:
        """启动反馈定时器"""
        self._feedback_timer.start(200)  # 200ms 后清除反馈
    
    def _clear_feedback(self) -> None:
        """清除反馈状态"""
        self._feedback_timer.stop()
        # 恢复当前高亮
        if self._current_highlight:
            self._key_buttons[self._current_highlight].set_highlight()
