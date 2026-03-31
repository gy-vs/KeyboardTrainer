"""
训练控制器模块

管理针对性训练流程。

Requirements: 4.1, 4.4, 4.5
"""

import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from keyboard_trainer.content_generator import ContentGenerator
from keyboard_trainer.data_store import DataStore
from keyboard_trainer.key_analyzer import KeyAnalyzer
from keyboard_trainer.models import (
    KeystrokeRecord,
    KeystrokeStatus,
    TrainingProgress,
    TrainingSession,
)
from keyboard_trainer.test_controller import KeystrokeResult


class TrainingController:
    """训练控制器，管理针对性训练流程"""
    
    def __init__(
        self, 
        data_store: Optional[DataStore] = None, 
        content_generator: Optional[ContentGenerator] = None
    ):
        """
        初始化训练控制器
        
        Args:
            data_store: 数据存储实例
            content_generator: 内容生成器实例
        """
        self.data_store = data_store
        self.content_generator = content_generator or ContentGenerator()
        self.key_analyzer = KeyAnalyzer()
        self._current_session: Optional[TrainingSession] = None
        self._last_keystroke_time: float = 0
    
    def start_training(self, weak_keys: List[str], length: int = 200) -> TrainingSession:
        """
        开始针对性训练
        
        Args:
            weak_keys: 薄弱按键列表
            length: 训练内容长度
            
        Returns:
            TrainingSession 训练会话
        """
        content = self.generate_training_content(weak_keys, length)
        
        self._current_session = TrainingSession(
            id=str(uuid.uuid4()),
            start_time=datetime.now(),
            target_weak_keys=weak_keys,
            content=content,
            current_position=0,
            keystrokes=[]
        )
        self._last_keystroke_time = time.time() * 1000  # 转换为毫秒
        
        return self._current_session
    
    def generate_training_content(self, weak_keys: List[str], length: int = 200) -> str:
        """
        生成包含薄弱按键的训练内容
        
        Args:
            weak_keys: 薄弱按键列表
            length: 目标字符数
            
        Returns:
            训练内容文本
        """
        return self.content_generator.generate_training_content(weak_keys, length)
    
    def record_keystroke(self, expected: str, actual: str, timestamp: float = None) -> KeystrokeResult:
        """
        记录训练中的按键
        
        Args:
            expected: 期望的字符
            actual: 实际输入的字符
            timestamp: 按键时间戳（毫秒）
            
        Returns:
            KeystrokeResult 按键结果
        """
        if self._current_session is None:
            raise RuntimeError("No active training session")
        
        if timestamp is None:
            timestamp = time.time() * 1000
        
        # 计算响应时间
        response_time = timestamp - self._last_keystroke_time
        self._last_keystroke_time = timestamp
        
        # 判断正确性
        correct = expected == actual
        status = KeystrokeStatus.CORRECT if correct else KeystrokeStatus.INCORRECT
        
        # 创建按键记录
        record = KeystrokeRecord(
            expected_char=expected,
            actual_char=actual,
            timestamp=timestamp,
            response_time=response_time,
            status=status
        )
        
        self._current_session.keystrokes.append(record)
        self._current_session.current_position += 1
        
        return KeystrokeResult(
            correct=correct,
            expected_char=expected,
            actual_char=actual,
            status=status
        )
    
    def get_training_progress(self) -> TrainingProgress:
        """
        获取训练进度
        
        Returns:
            TrainingProgress 训练进度
        """
        if self._current_session is None:
            return TrainingProgress(
                total_characters=0,
                completed_characters=0,
                current_accuracy=0.0,
                weak_key_improvements={}
            )
        
        session = self._current_session
        total = len(session.content)
        completed = session.current_position
        
        # 计算当前准确率
        if session.keystrokes:
            correct = sum(1 for k in session.keystrokes if k.status == KeystrokeStatus.CORRECT)
            accuracy = correct / len(session.keystrokes)
        else:
            accuracy = 0.0
        
        # 计算薄弱按键改善情况
        weak_key_improvements = self._calculate_weak_key_improvements()
        
        return TrainingProgress(
            total_characters=total,
            completed_characters=completed,
            current_accuracy=accuracy,
            weak_key_improvements=weak_key_improvements
        )
    
    def _calculate_weak_key_improvements(self) -> Dict[str, float]:
        """计算薄弱按键的改善情况"""
        if self._current_session is None:
            return {}
        
        session = self._current_session
        improvements = {}
        
        for key in session.target_weak_keys:
            # 统计该按键的表现
            key_keystrokes = [
                k for k in session.keystrokes 
                if k.expected_char.lower() == key.lower()
            ]
            
            if key_keystrokes:
                correct = sum(1 for k in key_keystrokes if k.status == KeystrokeStatus.CORRECT)
                accuracy = correct / len(key_keystrokes)
                improvements[key] = accuracy
        
        return improvements
    
    def get_next_character(self) -> str:
        """获取下一个需要输入的字符"""
        if self._current_session is None:
            return ""
        
        pos = self._current_session.current_position
        content = self._current_session.content
        
        if pos >= len(content):
            return ""
        
        return content[pos]
    
    def is_training_complete(self) -> bool:
        """检查训练是否完成"""
        if self._current_session is None:
            return True
        
        return self._current_session.current_position >= len(self._current_session.content)
