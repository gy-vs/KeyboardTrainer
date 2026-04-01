import pytest
from typing import List
from keyboard_trainer.key_analyzer import KeyAnalyzer, KeyAnalysisResult
from keyboard_trainer.models import (
    KeyStatistics,
    KeystrokeRecord,
    KeystrokeStatus,
    WeakKey,
)


@pytest.fixture
def analyzer():
    """创建 KeyAnalyzer 实例"""
    return KeyAnalyzer()


class TestKeyAnalyzerStatistics:
    """测试按键统计计算"""

    def test_analyze_empty_keystrokes(self, analyzer):
        """测试空按键记录列表"""
        result = analyzer.analyze_keystrokes([])
        assert isinstance(result, KeyAnalysisResult)
        assert result.overall_accuracy == 0.0
        assert result.overall_wpm == 0.0
        assert result.overall_cpm == 0.0
        assert result.duration == 0.0
        assert result.per_key_statistics == {}

    def test_calculate_per_key_statistics_single_key(self, analyzer):
        """测试单个按键的统计计算"""
        keystrokes = [
            KeystrokeRecord('a', 'a', 1000.0, 200.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('a', 'a', 1001.0, 250.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('a', 's', 1002.0, 300.0, KeystrokeStatus.INCORRECT),
        ]
        stats = analyzer._calculate_per_key_statistics(keystrokes)

        assert 'a' in stats
        assert stats['a'].total_attempts == 3
        assert stats['a'].correct_attempts == 2
        assert stats['a'].accuracy == 2/3
        assert stats['a'].average_response_time == (200 + 250 + 300) / 3

    def test_calculate_per_key_statistics_multiple_keys(self, analyzer):
        """测试多个按键的统计计算"""
        keystrokes = [
            KeystrokeRecord('a', 'a', 1000.0, 200.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('b', 'b', 1001.0, 250.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('a', 's', 1002.0, 300.0, KeystrokeStatus.INCORRECT),
            KeystrokeRecord('b', 'x', 1003.0, 350.0, KeystrokeStatus.INCORRECT),
            KeystrokeRecord('b', 'b', 1004.0, 400.0, KeystrokeStatus.CORRECT),
        ]
        stats = analyzer._calculate_per_key_statistics(keystrokes)

        assert 'a' in stats
        assert 'b' in stats
        assert stats['a'].total_attempts == 2
        assert stats['a'].correct_attempts == 1
        assert stats['a'].accuracy == 0.5
        assert stats['b'].total_attempts == 3
        assert stats['b'].correct_attempts == 2
        assert stats['b'].accuracy == 2/3

    def test_analyze_keystrokes_overall_accuracy(self, analyzer):
        """测试整体准确率计算"""
        keystrokes = [
            KeystrokeRecord('a', 'a', 1000.0, 200.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('b', 'b', 1001.0, 250.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('c', 'x', 1002.0, 300.0, KeystrokeStatus.INCORRECT),
            KeystrokeRecord('d', 'd', 1003.0, 350.0, KeystrokeStatus.CORRECT),
        ]
        result = analyzer.analyze_keystrokes(keystrokes, duration=60.0)
        assert result.overall_accuracy == 3/4

    def test_analyze_keystrokes_wpm_calculation(self, analyzer):
        """测试 WPM 计算"""
        keystrokes = [
            KeystrokeRecord(chr(ord('a') + i), chr(ord('a') + i), 1000.0 + i, 200.0, KeystrokeStatus.CORRECT)
            for i in range(50)  # 50 个正确字符 = 10 词
        ]
        result = analyzer.analyze_keystrokes(keystrokes, duration=60.0)  # 1 分钟
        assert result.overall_wpm == 10.0  # 10 WPM
        assert result.overall_cpm == 50.0  # 50 CPM

    def test_analyze_keystrokes_cpm_calculation(self, analyzer):
        """测试 CPM 计算"""
        keystrokes = [
            KeystrokeRecord(chr(ord('a') + i), chr(ord('a') + i), 1000.0 + i, 200.0, KeystrokeStatus.CORRECT)
            for i in range(120)
        ]
        result = analyzer.analyze_keystrokes(keystrokes, duration=60.0)
        assert result.overall_cpm == 120.0

    def test_calculate_per_key_accuracy(self, analyzer):
        """测试每个按键准确率计算"""
        keystrokes = [
            KeystrokeRecord('a', 'a', 1000.0, 200.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('a', 's', 1001.0, 250.0, KeystrokeStatus.INCORRECT),
            KeystrokeRecord('b', 'b', 1002.0, 300.0, KeystrokeStatus.CORRECT),
        ]
        accuracy = analyzer.calculate_per_key_accuracy(keystrokes)
        assert accuracy['a'] == 0.5
        assert accuracy['b'] == 1.0

    def test_calculate_per_key_speed(self, analyzer):
        """测试每个按键响应时间计算"""
        keystrokes = [
            KeystrokeRecord('a', 'a', 1000.0, 200.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('a', 'a', 1001.0, 300.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('b', 'b', 1002.0, 400.0, KeystrokeStatus.CORRECT),
        ]
        speed = analyzer.calculate_per_key_speed(keystrokes)
        assert speed['a'] == 250.0
        assert speed['b'] == 400.0

    def test_duration_calculation_from_timestamps(self, analyzer):
        """测试从时间戳计算持续时间"""
        keystrokes = [
            KeystrokeRecord('a', 'a', 0.0, 200.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('b', 'b', 60000.0, 250.0, KeystrokeStatus.CORRECT),
        ]
        result = analyzer.analyze_keystrokes(keystrokes)
        assert result.duration == 60.0  # 60 秒

    def test_duration_zero_for_single_keystroke(self, analyzer):
        """测试单个按键记录时持续时间为 0"""
        keystrokes = [
            KeystrokeRecord('a', 'a', 1000.0, 200.0, KeystrokeStatus.CORRECT),
        ]
        result = analyzer.analyze_keystrokes(keystrokes)
        assert result.duration == 0.0


class TestWeakKeyIdentification:
    """测试薄弱按键识别"""

    def test_identify_weak_keys_by_accuracy(self, analyzer):
        """测试通过准确率识别薄弱按键"""
        keystrokes = [
            KeystrokeRecord('a', 'a', 1000.0, 200.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('a', 'x', 1001.0, 200.0, KeystrokeStatus.INCORRECT),
            KeystrokeRecord('b', 'b', 1002.0, 200.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('b', 'b', 1003.0, 200.0, KeystrokeStatus.CORRECT),
        ]
        analysis = analyzer.analyze_keystrokes(keystrokes)
        weak_keys = analyzer.identify_weak_keys(analysis)

        weak_key_chars = [wk.key for wk in weak_keys]
        assert 'a' in weak_key_chars  # a: 50% 准确率
        assert 'b' not in weak_key_chars  # b: 100% 准确率

    def test_identify_weak_keys_by_response_time(self, analyzer):
        """测试通过响应时间识别薄弱按键"""
        keystrokes = []
        for i in range(10):
            keystrokes.append(KeystrokeRecord('x', 'x', 1000.0 + i, 600.0, KeystrokeStatus.CORRECT))
            keystrokes.append(KeystrokeRecord('y', 'y', 2000.0 + i, 400.0, KeystrokeStatus.CORRECT))

        analysis = analyzer.analyze_keystrokes(keystrokes)
        weak_keys = analyzer.identify_weak_keys(analysis)

        weak_key_chars = [wk.key for wk in weak_keys]
        assert 'x' in weak_key_chars  # x: 平均 600ms > 500ms
        assert 'y' not in weak_key_chars  # y: 平均 400ms < 500ms

    def test_identify_weak_keys_both_criteria(self, analyzer):
        """测试同时满足两个条件的薄弱按键"""
        keystrokes = []
        for i in range(10):
            keystrokes.append(KeystrokeRecord('z', 'z', 1000.0 + i, 550.0, KeystrokeStatus.CORRECT))
        for i in range(5):
            keystrokes.append(KeystrokeRecord('z', 'x', 2000.0 + i, 550.0, KeystrokeStatus.INCORRECT))

        analysis = analyzer.analyze_keystrokes(keystrokes)
        weak_keys = analyzer.identify_weak_keys(analysis)

        weak_key_chars = [wk.key for wk in weak_keys]
        assert 'z' in weak_key_chars  # z: 低准确率 + 高响应时间

    def test_no_weak_keys_when_all_good(self, analyzer):
        """测试当所有按键表现良好时无薄弱按键"""
        keystrokes = []
        for i in range(10):
            keystrokes.append(KeystrokeRecord('a', 'a', 1000.0 + i, 400.0, KeystrokeStatus.CORRECT))
            keystrokes.append(KeystrokeRecord('b', 'b', 2000.0 + i, 400.0, KeystrokeStatus.CORRECT))

        analysis = analyzer.analyze_keystrokes(keystrokes)
        weak_keys = analyzer.identify_weak_keys(analysis)
        assert len(weak_keys) == 0

    def test_calculate_severity_score(self, analyzer):
        """测试严重程度评分计算"""
        stats_accuracy = KeyStatistics('x', 10, 8, 0.8, 400.0)
        severity_accuracy = analyzer._calculate_severity(stats_accuracy)
        assert pytest.approx(severity_accuracy) == 20.0  # (1 - 0.8) * 100 = 20

        stats_time = KeyStatistics('y', 10, 10, 1.0, 600.0)
        severity_time = analyzer._calculate_severity(stats_time)
        assert pytest.approx(severity_time) == 10.0  # (600 - 500) / 10 = 10

        stats_both = KeyStatistics('z', 10, 8, 0.8, 600.0)
        severity_both = analyzer._calculate_severity(stats_both)
        assert pytest.approx(severity_both) == 30.0  # 20 + 10

    def test_rank_weak_keys(self, analyzer):
        """测试薄弱按键排序"""
        weak_keys = [
            WeakKey('a', 0.95, 300.0, 5.0),    # 高准确率
            WeakKey('b', 0.70, 400.0, 30.0),   # 低准确率
            WeakKey('c', 0.70, 600.0, 40.0),   # 低准确率 + 高响应时间
        ]
        ranked = analyzer.rank_weak_keys(weak_keys)

        assert ranked[0].key == 'c'  # 相同准确率，响应时间高的在前
        assert ranked[1].key == 'b'
        assert ranked[2].key == 'a'

    def test_rank_weak_keys_same_accuracy_different_time(self, analyzer):
        """测试相同准确率不同响应时间的排序"""
        weak_keys = [
            WeakKey('a', 0.80, 400.0, 20.0),
            WeakKey('b', 0.80, 600.0, 30.0),
            WeakKey('c', 0.80, 500.0, 25.0),
        ]
        ranked = analyzer.rank_weak_keys(weak_keys)

        assert ranked[0].key == 'b'  # 响应时间降序
        assert ranked[1].key == 'c'
        assert ranked[2].key == 'a'
