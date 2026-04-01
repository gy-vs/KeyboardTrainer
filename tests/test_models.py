"""
测试数据模型模块
"""
from datetime import datetime
import pytest

from keyboard_trainer.models import (
    KeyStatistics,
    KeystrokeRecord,
    KeystrokeStatus,
    TestResult,
    TestType,
    WeakKey,
    TrainingSession,
    TrainingProgress,
)


class TestKeyStatistics:
    """测试按键统计数据类"""

    def test_is_weak_accuracy_below_threshold(self):
        """测试准确率低于 90% 时判定为薄弱按键"""
        stats = KeyStatistics(
            key="a",
            total_attempts=100,
            correct_attempts=85,
            accuracy=0.85,
            average_response_time=300,
        )
        assert stats.is_weak is True

    def test_is_weak_response_time_above_threshold(self):
        """测试响应时间高于 500ms 时判定为薄弱按键"""
        stats = KeyStatistics(
            key="a",
            total_attempts=100,
            correct_attempts=95,
            accuracy=0.95,
            average_response_time=600,
        )
        assert stats.is_weak is True

    def test_is_weak_both_conditions_met(self):
        """测试两个条件都满足时判定为薄弱按键"""
        stats = KeyStatistics(
            key="a",
            total_attempts=100,
            correct_attempts=80,
            accuracy=0.80,
            average_response_time=700,
        )
        assert stats.is_weak is True

    def test_is_weak_neither_condition_met(self):
        """测试两个条件都不满足时不判定为薄弱按键"""
        stats = KeyStatistics(
            key="a",
            total_attempts=100,
            correct_attempts=95,
            accuracy=0.95,
            average_response_time=300,
        )
        assert stats.is_weak is False

    def test_is_weak_exact_threshold_accuracy(self):
        """测试准确率刚好等于阈值时不判定为薄弱按键"""
        stats = KeyStatistics(
            key="a",
            total_attempts=100,
            correct_attempts=90,
            accuracy=0.90,
            average_response_time=300,
        )
        assert stats.is_weak is False

    def test_is_weak_exact_threshold_response_time(self):
        """测试响应时间刚好等于阈值时不判定为薄弱按键"""
        stats = KeyStatistics(
            key="a",
            total_attempts=100,
            correct_attempts=95,
            accuracy=0.95,
            average_response_time=500,
        )
        assert stats.is_weak is False


class TestDataClassesInstantiation:
    """测试各数据类的实例化和字段默认值"""

    def test_keystroke_record_instantiation(self):
        """测试按键记录实例化"""
        record = KeystrokeRecord(
            expected_char="a",
            actual_char="a",
            timestamp=1234567890.0,
            response_time=150.0,
            status=KeystrokeStatus.CORRECT,
        )
        assert record.expected_char == "a"
        assert record.actual_char == "a"
        assert record.timestamp == 1234567890.0
        assert record.response_time == 150.0
        assert record.status == KeystrokeStatus.CORRECT

    def test_weak_key_instantiation(self):
        """测试薄弱按键实例化"""
        weak_key = WeakKey(
            key="x",
            accuracy=0.85,
            average_response_time=550.0,
            severity_score=20.0,
        )
        assert weak_key.key == "x"
        assert weak_key.accuracy == 0.85
        assert weak_key.average_response_time == 550.0
        assert weak_key.severity_score == 20.0

    def test_test_result_instantiation_with_default_keystrokes(self):
        """测试测试结果实例化，按键记录应该有默认空列表"""
        test_result = TestResult(
            id="test-123",
            test_type=TestType.BASIC,
            timestamp=datetime.now(),
            duration=60.0,
            total_characters=200,
            correct_characters=180,
            wpm=40.0,
            cpm=200.0,
            accuracy=0.90,
            key_statistics={},
        )
        assert test_result.id == "test-123"
        assert test_result.test_type == TestType.BASIC
        assert isinstance(test_result.timestamp, datetime)
        assert test_result.duration == 60.0
        assert test_result.total_characters == 200
        assert test_result.correct_characters == 180
        assert test_result.wpm == 40.0
        assert test_result.cpm == 200.0
        assert test_result.accuracy == 0.90
        assert test_result.key_statistics == {}
        assert test_result.keystrokes == []

    def test_training_session_instantiation_with_default_keystrokes(self):
        """测试训练会话实例化，按键记录应该有默认空列表"""
        session = TrainingSession(
            id="session-123",
            start_time=datetime.now(),
            target_weak_keys=["x", "z"],
            content="example text content",
            current_position=0,
        )
        assert session.id == "session-123"
        assert isinstance(session.start_time, datetime)
        assert session.target_weak_keys == ["x", "z"]
        assert session.content == "example text content"
        assert session.current_position == 0
        assert session.keystrokes == []

    def test_training_progress_instantiation(self):
        """测试训练进度实例化"""
        progress = TrainingProgress(
            total_characters=200,
            completed_characters=100,
            current_accuracy=0.85,
            weak_key_improvements={"x": 0.05, "z": 0.03},
        )
        assert progress.total_characters == 200
        assert progress.completed_characters == 100
        assert progress.current_accuracy == 0.85
        assert progress.weak_key_improvements == {"x": 0.05, "z": 0.03}


class TestEnums:
    """测试枚举类型"""

    def test_test_type_enum_values(self):
        """测试测试类型枚举值"""
        assert TestType.BASIC.value == "basic"
        assert TestType.TRAINING.value == "training"
        assert TestType.ADVANCED.value == "advanced"

    def test_keystroke_status_enum_values(self):
        """测试按键状态枚举值"""
        assert KeystrokeStatus.CORRECT.value == "correct"
        assert KeystrokeStatus.INCORRECT.value == "incorrect"
        assert KeystrokeStatus.MISSED.value == "missed"
