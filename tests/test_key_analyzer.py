"""
测试按键分析器模块
"""
import pytest

from keyboard_trainer.key_analyzer import KeyAnalyzer, KeyAnalysisResult
from keyboard_trainer.models import KeystrokeRecord, KeystrokeStatus, WeakKey


class TestKeyAnalyzer:
    """测试按键分析器"""

    def setup_method(self):
        """初始化测试用的按键分析器"""
        self.analyzer = KeyAnalyzer()

    def test_analyze_empty_keystrokes(self):
        """测试分析空的按键记录列表"""
        result = self.analyzer.analyze_keystrokes([])
        assert isinstance(result, KeyAnalysisResult)
        assert result.overall_accuracy == 0.0
        assert result.overall_wpm == 0.0
        assert result.overall_cpm == 0.0
        assert result.duration == 0.0
        assert result.per_key_statistics == {}

    def test_calculate_per_key_statistics_single_key(self):
        """测试计算单个按键的统计数据"""
        keystrokes = [
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=1000.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=2000.0,
                response_time=300.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="a",
                actual_char="s",
                timestamp=3000.0,
                response_time=400.0,
                status=KeystrokeStatus.INCORRECT,
            ),
        ]

        stats = self.analyzer._calculate_per_key_statistics(keystrokes)

        assert "a" in stats
        assert stats["a"].total_attempts == 3
        assert stats["a"].correct_attempts == 2
        assert stats["a"].accuracy == 2 / 3
        assert stats["a"].average_response_time == (200 + 300 + 400) / 3

    def test_calculate_per_key_statistics_multiple_keys(self):
        """测试计算多个按键的统计数据"""
        keystrokes = [
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=1000.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="b",
                actual_char="b",
                timestamp=2000.0,
                response_time=300.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="a",
                actual_char="s",
                timestamp=3000.0,
                response_time=400.0,
                status=KeystrokeStatus.INCORRECT,
            ),
            KeystrokeRecord(
                expected_char="b",
                actual_char="b",
                timestamp=4000.0,
                response_time=250.0,
                status=KeystrokeStatus.CORRECT,
            ),
        ]

        stats = self.analyzer._calculate_per_key_statistics(keystrokes)

        assert "a" in stats
        assert stats["a"].total_attempts == 2
        assert stats["a"].correct_attempts == 1
        assert stats["a"].accuracy == 0.5
        assert stats["a"].average_response_time == 300.0

        assert "b" in stats
        assert stats["b"].total_attempts == 2
        assert stats["b"].correct_attempts == 2
        assert stats["b"].accuracy == 1.0
        assert stats["b"].average_response_time == 275.0

    def test_calculate_per_key_accuracy(self):
        """测试计算每个按键的准确率"""
        keystrokes = [
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=1000.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="a",
                actual_char="s",
                timestamp=2000.0,
                response_time=300.0,
                status=KeystrokeStatus.INCORRECT,
            ),
            KeystrokeRecord(
                expected_char="b",
                actual_char="b",
                timestamp=3000.0,
                response_time=400.0,
                status=KeystrokeStatus.CORRECT,
            ),
        ]

        accuracy = self.analyzer.calculate_per_key_accuracy(keystrokes)

        assert accuracy["a"] == 0.5
        assert accuracy["b"] == 1.0

    def test_calculate_per_key_speed(self):
        """测试计算每个按键的平均响应时间"""
        keystrokes = [
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=1000.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=2000.0,
                response_time=400.0,
                status=KeystrokeStatus.CORRECT,
            ),
        ]

        speed = self.analyzer.calculate_per_key_speed(keystrokes)

        assert speed["a"] == 300.0

    def test_analyze_keystrokes_overall_metrics(self):
        """测试分析按键记录的整体指标"""
        keystrokes = [
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=0.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="b",
                actual_char="b",
                timestamp=60000.0,
                response_time=300.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="c",
                actual_char="d",
                timestamp=120000.0,
                response_time=400.0,
                status=KeystrokeStatus.INCORRECT,
            ),
        ]

        result = self.analyzer.analyze_keystrokes(keystrokes)

        assert result.overall_accuracy == 2 / 3
        assert result.duration == 120.0
        assert result.overall_cpm == 1.0
        assert result.overall_wpm == 0.2

    def test_identify_weak_keys_based_on_accuracy(self):
        """测试基于准确率识别薄弱按键"""
        keystrokes = [
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=1000.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="x",
                actual_char="z",
                timestamp=2000.0,
                response_time=300.0,
                status=KeystrokeStatus.INCORRECT,
            ),
        ]

        analysis = self.analyzer.analyze_keystrokes(keystrokes)
        weak_keys = self.analyzer.identify_weak_keys(analysis)

        assert len(weak_keys) == 1
        assert weak_keys[0].key == "x"
        assert weak_keys[0].accuracy == 0.0

    def test_identify_weak_keys_based_on_response_time(self):
        """测试基于响应时间识别薄弱按键"""
        keystrokes = [
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=1000.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=2000.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="z",
                actual_char="z",
                timestamp=3000.0,
                response_time=600.0,
                status=KeystrokeStatus.CORRECT,
            ),
        ]

        analysis = self.analyzer.analyze_keystrokes(keystrokes)
        weak_keys = self.analyzer.identify_weak_keys(analysis)

        assert len(weak_keys) == 1
        assert weak_keys[0].key == "z"
        assert weak_keys[0].average_response_time == 600.0

    def test_identify_no_weak_keys(self):
        """测试没有薄弱按键的情况"""
        keystrokes = [
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=1000.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="b",
                actual_char="b",
                timestamp=2000.0,
                response_time=300.0,
                status=KeystrokeStatus.CORRECT,
            ),
        ]

        analysis = self.analyzer.analyze_keystrokes(keystrokes)
        weak_keys = self.analyzer.identify_weak_keys(analysis)

        assert len(weak_keys) == 0

    def test_calculate_severity_score(self):
        """测试计算严重程度评分"""
        from keyboard_trainer.models import KeyStatistics

        stats_low_accuracy = KeyStatistics(
            key="x",
            total_attempts=10,
            correct_attempts=5,
            accuracy=0.5,
            average_response_time=300.0,
        )

        stats_slow_response = KeyStatistics(
            key="z",
            total_attempts=10,
            correct_attempts=9,
            accuracy=0.9,
            average_response_time=700.0,
        )

        severity_low_accuracy = self.analyzer._calculate_severity(stats_low_accuracy)
        severity_slow_response = self.analyzer._calculate_severity(stats_slow_response)

        assert severity_low_accuracy == 50.0
        assert severity_slow_response == 30.0

    def test_rank_weak_keys(self):
        """测试按严重程度排序薄弱按键"""
        weak_keys = [
            WeakKey(key="a", accuracy=0.95, average_response_time=200.0, severity_score=5.0),
            WeakKey(key="x", accuracy=0.70, average_response_time=400.0, severity_score=30.0),
            WeakKey(key="z", accuracy=0.85, average_response_time=600.0, severity_score=25.0),
        ]

        ranked = self.analyzer.rank_weak_keys(weak_keys)

        assert ranked[0].key == "x"
        assert ranked[1].key == "z"
        assert ranked[2].key == "a"
