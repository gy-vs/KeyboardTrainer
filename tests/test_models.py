import pytest
from datetime import datetime
from keyboard_trainer.models import (
    KeyStatistics,
    KeystrokeRecord,
    KeystrokeStatus,
    TestResult,
    TestType,
    WeakKey,
    TrainingSession,
    ProficiencyReport,
    ProgressReport,
    TrainingProgress,
    FileLoadResult,
    FileInfo,
    FingerPosition
)


class TestKeyStatistics:
    """测试 KeyStatistics 数据类"""

    def test_is_weak_accuracy_below_threshold(self):
        """测试准确率低于 90% 时 is_weak 返回 True"""
        stats = KeyStatistics(
            key='a',
            total_attempts=100,
            correct_attempts=85,
            accuracy=0.85,
            average_response_time=400
        )
        assert stats.is_weak is True

    def test_is_weak_response_time_above_threshold(self):
        """测试响应时间高于 500ms 时 is_weak 返回 True"""
        stats = KeyStatistics(
            key='b',
            total_attempts=100,
            correct_attempts=95,
            accuracy=0.95,
            average_response_time=600
        )
        assert stats.is_weak is True

    def test_is_weak_both_conditions_met(self):
        """测试两个条件都满足时 is_weak 返回 True"""
        stats = KeyStatistics(
            key='c',
            total_attempts=100,
            correct_attempts=80,
            accuracy=0.80,
            average_response_time=550
        )
        assert stats.is_weak is True

    def test_is_weak_neither_condition_met(self):
        """测试两个条件都不满足时 is_weak 返回 False"""
        stats = KeyStatistics(
            key='d',
            total_attempts=100,
            correct_attempts=95,
            accuracy=0.95,
            average_response_time=400
        )
        assert stats.is_weak is False

    def test_is_weak_exact_thresholds(self):
        """测试边界值情况"""
        stats_accuracy = KeyStatistics(
            key='e',
            total_attempts=100,
            correct_attempts=90,
            accuracy=0.90,
            average_response_time=400
        )
        assert stats_accuracy.is_weak is False

        stats_time = KeyStatistics(
            key='f',
            total_attempts=100,
            correct_attempts=95,
            accuracy=0.95,
            average_response_time=500
        )
        assert stats_time.is_weak is False

    def test_is_weak_edge_cases(self):
        """测试极端情况"""
        stats_zero_accuracy = KeyStatistics(
            key='g',
            total_attempts=10,
            correct_attempts=0,
            accuracy=0.0,
            average_response_time=100
        )
        assert stats_zero_accuracy.is_weak is True

        stats_high_time = KeyStatistics(
            key='h',
            total_attempts=10,
            correct_attempts=10,
            accuracy=1.0,
            average_response_time=9999
        )
        assert stats_high_time.is_weak is True


class TestDataClassInstantiation:
    """测试各数据类的实例化和字段默认值"""

    def test_keystroke_record_instantiation(self):
        """测试 KeystrokeRecord 实例化"""
        record = KeystrokeRecord(
            expected_char='a',
            actual_char='a',
            timestamp=1000.0,
            response_time=150.0,
            status=KeystrokeStatus.CORRECT
        )
        assert record.expected_char == 'a'
        assert record.actual_char == 'a'
        assert record.timestamp == 1000.0
        assert record.response_time == 150.0
        assert record.status == KeystrokeStatus.CORRECT

    def test_weak_key_instantiation(self):
        """测试 WeakKey 实例化"""
        weak_key = WeakKey(
            key='x',
            accuracy=0.75,
            average_response_time=550.0,
            severity_score=30.5
        )
        assert weak_key.key == 'x'
        assert weak_key.accuracy == 0.75
        assert weak_key.average_response_time == 550.0
        assert weak_key.severity_score == 30.5

    def test_test_result_instantiation_with_defaults(self):
        """测试 TestResult 实例化及默认值"""
        key_stats = {
            'a': KeyStatistics('a', 10, 9, 0.9, 200.0)
        }
        result = TestResult(
            id='test_001',
            test_type=TestType.BASIC,
            timestamp=datetime.now(),
            duration=60.0,
            total_characters=100,
            correct_characters=90,
            wpm=40.0,
            cpm=200.0,
            accuracy=0.9,
            key_statistics=key_stats
        )
        assert result.id == 'test_001'
        assert result.test_type == TestType.BASIC
        assert result.keystrokes == []  # 默认值
        assert isinstance(result.keystrokes, list)

    def test_test_result_with_keystrokes(self):
        """测试 TestResult 带按键记录"""
        keystrokes = [
            KeystrokeRecord('a', 'a', 1.0, 100.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('b', 'c', 2.0, 150.0, KeystrokeStatus.INCORRECT)
        ]
        key_stats = {}
        result = TestResult(
            id='test_002',
            test_type=TestType.TRAINING,
            timestamp=datetime.now(),
            duration=30.0,
            total_characters=2,
            correct_characters=1,
            wpm=10.0,
            cpm=50.0,
            accuracy=0.5,
            key_statistics=key_stats,
            keystrokes=keystrokes
        )
        assert len(result.keystrokes) == 2

    def test_training_session_default_keystrokes(self):
        """测试 TrainingSession 的默认值"""
        session = TrainingSession(
            id='session_001',
            start_time=datetime.now(),
            target_weak_keys=['x', 'y'],
            content='practice makes perfect',
            current_position=0
        )
        assert session.keystrokes == []  # 默认空列表

    def test_proficiency_report_instantiation(self):
        """测试 ProficiencyReport 实例化"""
        key_stats = {}
        test_result = TestResult(
            id='test_003',
            test_type=TestType.BASIC,
            timestamp=datetime.now(),
            duration=60.0,
            total_characters=100,
            correct_characters=90,
            wpm=40.0,
            cpm=200.0,
            accuracy=0.9,
            key_statistics=key_stats
        )
        weak_keys = [WeakKey('z', 0.8, 550.0, 25.0)]
        report = ProficiencyReport(
            test_result=test_result,
            weak_keys=weak_keys,
            overall_grade='A',
            recommendations=['Practice more', 'Focus on z key']
        )
        assert report.overall_grade == 'A'
        assert len(report.recommendations) == 2

    def test_progress_report_instantiation(self):
        """测试 ProgressReport 实例化"""
        key_stats = {}
        current = TestResult(
            id='current',
            test_type=TestType.BASIC,
            timestamp=datetime.now(),
            duration=60.0,
            total_characters=100,
            correct_characters=95,
            wpm=50.0,
            cpm=250.0,
            accuracy=0.95,
            key_statistics=key_stats
        )
        baseline = TestResult(
            id='baseline',
            test_type=TestType.BASIC,
            timestamp=datetime.now(),
            duration=60.0,
            total_characters=100,
            correct_characters=85,
            wpm=40.0,
            cpm=200.0,
            accuracy=0.85,
            key_statistics=key_stats
        )
        progress = ProgressReport(
            current_result=current,
            baseline_result=baseline,
            wpm_improvement=25.0,
            accuracy_improvement=11.76,
            improved_keys=['a', 's'],
            still_weak_keys=['x'],
            conclusion='Good progress!'
        )
        assert progress.wpm_improvement == 25.0
        assert progress.improved_keys == ['a', 's']

    def test_training_progress_instantiation(self):
        """测试 TrainingProgress 实例化"""
        progress = TrainingProgress(
            total_characters=200,
            completed_characters=100,
            current_accuracy=0.88,
            weak_key_improvements={'x': 5.0, 'y': 3.2}
        )
        assert progress.total_characters == 200
        assert progress.current_accuracy == 0.88
        assert progress.weak_key_improvements['x'] == 5.0

    def test_file_load_result_instantiation(self):
        """测试 FileLoadResult 实例化"""
        success_result = FileLoadResult(
            success=True,
            content='hello world',
            error_message=None,
            file_info=FileInfo('/path/test.txt', 'test.txt', 11, 11)
        )
        assert success_result.success is True
        assert success_result.content == 'hello world'

        fail_result = FileLoadResult(
            success=False,
            content=None,
            error_message='File not found',
            file_info=None
        )
        assert fail_result.success is False
        assert fail_result.error_message == 'File not found'

    def test_file_info_instantiation(self):
        """测试 FileInfo 实例化"""
        info = FileInfo(
            path='/home/user/doc.txt',
            name='doc.txt',
            size=1024,
            character_count=500
        )
        assert info.path == '/home/user/doc.txt'
        assert info.size == 1024

    def test_enum_values(self):
        """测试枚举值"""
        assert TestType.BASIC.value == 'basic'
        assert TestType.TRAINING.value == 'training'
        assert TestType.ADVANCED.value == 'advanced'

        assert KeystrokeStatus.CORRECT.value == 'correct'
        assert KeystrokeStatus.INCORRECT.value == 'incorrect'
        assert KeystrokeStatus.MISSED.value == 'missed'

        assert FingerPosition.LEFT_PINKY.value == 'left_pinky'
        assert FingerPosition.RIGHT_INDEX.value == 'right_index'
