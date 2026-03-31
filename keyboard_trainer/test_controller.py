"""
测试控制器模块

管理打字测试的生命周期和数据收集。

Requirements: 1.1, 1.2, 1.6, 6.5
"""

import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from keyboard_trainer.content_generator import ContentGenerator
from keyboard_trainer.data_store import DataStore
from keyboard_trainer.key_analyzer import KeyAnalyzer
from keyboard_trainer.models import (
    KeystrokeRecord,
    KeystrokeStatus,
    TestResult,
    TestType,
)


@dataclass
class TestSession:
    """测试会话"""
    id: str
    test_type: TestType
    content: str
    start_time: float
    current_position: int
    keystrokes: List[KeystrokeRecord]


@dataclass
class KeystrokeResult:
    """按键结果"""
    correct: bool
    expected_char: str
    actual_char: str
    status: KeystrokeStatus


class TestController:
    """测试控制器，管理打字测试流程"""
    
    def __init__(self, data_store: Optional[DataStore] = None):
        """
        初始化测试控制器
        
        Args:
            data_store: 数据存储实例
        """
        self.data_store = data_store
        self.content_generator = ContentGenerator()
        self.key_analyzer = KeyAnalyzer()
        self._current_session: Optional[TestSession] = None
        self._last_keystroke_time: float = 0
    
    def start_test(self, test_type: TestType, content: str = None) -> TestSession:
        """
        开始新的测试会话
        
        Args:
            test_type: 测试类型
            content: 测试内容，如果为 None 则自动生成
            
        Returns:
            TestSession 测试会话
        """
        if content is None:
            content = self.content_generator.generate_basic_test_content(200)
        
        self._current_session = TestSession(
            id=str(uuid.uuid4()),
            test_type=test_type,
            content=content,
            start_time=time.time(),
            current_position=0,
            keystrokes=[]
        )
        self._last_keystroke_time = self._current_session.start_time * 1000  # 转换为毫秒
        
        return self._current_session
    
    def record_keystroke(self, expected: str, actual: str, timestamp: float = None) -> KeystrokeResult:
        """
        记录单次按键
        
        Args:
            expected: 期望的字符
            actual: 实际输入的字符
            timestamp: 按键时间戳（毫秒），如果为 None 则使用当前时间
            
        Returns:
            KeystrokeResult 按键结果
        """
        if self._current_session is None:
            raise RuntimeError("No active test session")
        
        if timestamp is None:
            timestamp = time.time() * 1000  # 转换为毫秒
        
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
    
    def finish_test(self) -> TestResult:
        """
        完成测试并返回结果
        
        Returns:
            TestResult 测试结果
        """
        if self._current_session is None:
            raise RuntimeError("No active test session")
        
        session = self._current_session
        end_time = time.time()
        duration = end_time - session.start_time
        
        # 分析按键数据
        analysis = self.key_analyzer.analyze_keystrokes(session.keystrokes, duration)
        
        # 计算统计数据
        total_chars = len(session.keystrokes)
        correct_chars = sum(1 for k in session.keystrokes if k.status == KeystrokeStatus.CORRECT)
        
        # 创建测试结果
        result = TestResult(
            id=session.id,
            test_type=session.test_type,
            timestamp=datetime.now(),
            duration=duration,
            total_characters=total_chars,
            correct_characters=correct_chars,
            wpm=analysis.overall_wpm,
            cpm=analysis.overall_cpm,
            accuracy=analysis.overall_accuracy,
            key_statistics=analysis.per_key_statistics,
            keystrokes=session.keystrokes
        )
        
        # 保存结果
        if self.data_store:
            self.data_store.save_test_result(result)
        
        # 清除当前会话
        self._current_session = None
        
        return result
    
    def get_current_position(self) -> int:
        """
        获取当前测试位置
        
        Returns:
            当前位置索引
        """
        if self._current_session is None:
            return 0
        return self._current_session.current_position
    
    def get_next_character(self) -> str:
        """
        获取下一个需要输入的字符
        
        Returns:
            下一个字符，如果测试结束则返回空字符串
        """
        if self._current_session is None:
            return ""
        
        pos = self._current_session.current_position
        content = self._current_session.content
        
        if pos >= len(content):
            return ""
        
        return content[pos]
    
    def is_test_complete(self) -> bool:
        """
        检查测试是否完成
        
        Returns:
            测试是否完成
        """
        if self._current_session is None:
            return True
        
        return self._current_session.current_position >= len(self._current_session.content)
    
    def get_progress(self) -> float:
        """
        获取测试进度
        
        Returns:
            进度百分比 (0.0 - 1.0)
        """
        if self._current_session is None:
            return 0.0
        
        total = len(self._current_session.content)
        if total == 0:
            return 1.0
        
        return self._current_session.current_position / total
