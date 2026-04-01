
import pytest
from datetime import datetime
from keyboard_trainer.models import (
    TestType,
    KeystrokeStatus,
    FingerPosition,
    KeystrokeRecord,
    KeyStatistics,
    WeakKey,
    TestResult,
    ProficiencyReport,
    ProgressReport,
    TrainingSession,
    TrainingProgress,
    FileLoadResult,
    FileInfo
)


class TestKeyStatistics:
    def test_is_weak_with_low_accuracy(self):
        stats = KeyStatistics(
            key='a',
            total_attempts=10,
            correct_attempts=8,
            accuracy=0.80,
            average_response_time=400
        )
        assert stats.is_weak is True

    def test_is_weak_with_high_response_time(self):
        stats = KeyStatistics(
            key='a',
            total_attempts=10,
            correct_attempts=10,
            accuracy=1.0,
            average_response_time=600
        )
        assert stats.is_weak is True

    def test_is_weak_with_both_issues(self):
        stats = KeyStatistics(
            key='a',
            total_attempts=10,
            correct_attempts=8,
            accuracy=0.80,
            average_response_time=600
        )
        assert stats.is_weak is True

    def test_is_weak_with_good_performance(self):
        stats = KeyStatistics(
            key='a',
            total_attempts=10,
            correct_attempts=10,
            accuracy=0.95,
            average_response_time=400
        )
        assert stats.is_weak is False

    def test_is_weak_at_threshold_accuracy(self):
        stats = KeyStatistics(
            key='a',
            total_attempts=10,
            correct_attempts=9,
            accuracy=0.90,
            average_response_time=400
        )
        assert stats.is_weak is False

    def test_is_weak_at_threshold_response_time(self):
        stats = KeyStatistics(
            key='a',
            total_attempts=10,
            correct_attempts=10,
            accuracy=0.95,
            average_response_time=500
        )
        assert stats.is_weak is False


class TestDataClasses:
    def test_keystroke_record_instantiation(self):
        record = KeystrokeRecord(
            expected_char='a',
            actual_char='a',
            timestamp=1234567890.0,
            response_time=150.0,
            status=KeystrokeStatus.CORRECT
        )
        assert record.expected_char == 'a'
        assert record.actual_char == 'a'
        assert record.timestamp == 1234567890.0
        assert record.response_time == 150.0
        assert record.status == KeystrokeStatus.CORRECT

    def test_weak_key_instantiation(self):
        weak_key = WeakKey(
            key='x',
            accuracy=0.75,
            average_response_time=650.0,
            severity_score=35.0
        )
        assert weak_key.key == 'x'
        assert weak_key.accuracy == 0.75
        assert weak_key.average_response_time == 650.0
        assert weak_key.severity_score == 35.0

    def test_test_result_instantiation_with_defaults(self):
        key_stats = {
            'a': KeyStatistics('a', 5, 5, 1.0, 200),
            'b': KeyStatistics('b', 3, 2, 0.666, 300)
        }
        result = TestResult(
            id='test-123',
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
        assert result.id == 'test-123'
        assert result.test_type == TestType.BASIC
        assert result.keystrokes == []

    def test_test_result_with_keystrokes(self):
        keystrokes = [
            KeystrokeRecord('a', 'a', 1.0, 100, KeystrokeStatus.CORRECT),
            KeystrokeRecord('b', 'c', 2.0, 150, KeystrokeStatus.INCORRECT)
        ]
        result = TestResult(
            id='test-456',
            test_type=TestType.TRAINING,
            timestamp=datetime.now(),
            duration=10.0,
            total_characters=2,
            correct_characters=1,
            wpm=6.0,
            cpm=30.0,
            accuracy=0.5,
            key_statistics={},
            keystrokes=keystrokes
        )
        assert len(result.keystrokes) == 2

    def test_training_session_defaults(self):
        session = TrainingSession(
            id='session-1',
            start_time=datetime.now(),
            target_weak_keys=['x', 'y'],
            content='test content',
            current_position=0
        )
        assert session.keystrokes == []

    def test_file_load_result_instantiation(self):
        result = FileLoadResult(
            success=True,
            content='file content',
            error_message=None,
            file_info=None
        )
        assert result.success is True
        assert result.content == 'file content'
        assert result.error_message is None

    def test_file_info_instantiation(self):
        info = FileInfo(
            path='/test/path.txt',
            name='test.txt',
            size=1024,
            character_count=500
        )
        assert info.path == '/test/path.txt'
        assert info.name == 'test.txt'
        assert info.size == 1024
        assert info.character_count == 500

    def test_enum_values(self):
        assert TestType.BASIC.value == 'basic'
        assert TestType.TRAINING.value == 'training'
        assert TestType.ADVANCED.value == 'advanced'

        assert KeystrokeStatus.CORRECT.value == 'correct'
        assert KeystrokeStatus.INCORRECT.value == 'incorrect'
        assert KeystrokeStatus.MISSED.value == 'missed'

        assert FingerPosition.LEFT_INDEX.value == 'left_index'
        assert FingerPosition.RIGHT_PINKY.value == 'right_pinky'

